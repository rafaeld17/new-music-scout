"""
Review aggregation service for consolidating reviews across sources.
"""
import statistics
from datetime import datetime
from typing import List, Dict, Optional
from sqlmodel import Session, select

from ..models import (
    Album,
    MusicItem,
    ContentType,
    AlbumReviewAggregate,
    Source,
)
from ..core.logging import logger
from .album_matcher import AlbumMatcher


class ReviewAggregator:
    """Service for aggregating reviews across multiple sources."""

    def __init__(self, session: Session):
        self.session = session
        self.matcher = AlbumMatcher(session)

    def aggregate_reviews_for_album(self, album_id: int) -> Optional[AlbumReviewAggregate]:
        """
        Aggregate all reviews for a specific album.

        Args:
            album_id: The album ID to aggregate reviews for

        Returns:
            AlbumReviewAggregate object with consensus metrics
        """
        # Get the album and artist info
        album = self.session.get(Album, album_id)
        if not album:
            logger.warning(f"Album {album_id} not found")
            return None

        from ..models import Artist
        artist = self.session.get(Artist, album.artist_id)
        if not artist:
            logger.warning(f"Artist {album.artist_id} not found")
            return None

        # Get all review items and filter to those matching this album
        statement = select(MusicItem).where(MusicItem.content_type == ContentType.REVIEW)
        all_reviews = self.session.exec(statement).all()

        # Match reviews to this specific album
        reviews = []
        for review in all_reviews:
            matched_album = self.matcher.match_music_item_to_album(review, create_if_missing=False)
            if matched_album and matched_album.id == album_id:
                reviews.append(review)

        if not reviews:
            logger.warning(f"No reviews found for album {album_id}")
            return None

        # Filter reviews with scores
        scored_reviews = [r for r in reviews if r.review_score is not None]

        if not scored_reviews:
            logger.warning(f"No scored reviews found for album {album_id}")
            return None

        # Calculate statistics
        scores = [r.review_score for r in scored_reviews]
        source_ids = list(set(r.source_id for r in reviews))
        review_item_ids = [r.id for r in reviews]

        # Get source weights for weighted average
        source_weights = self._get_source_weights(source_ids)
        weighted_scores = []
        for review in scored_reviews:
            weight = source_weights.get(review.source_id, 1.0)
            weighted_scores.append(review.review_score * weight)

        # Calculate metrics
        average_score = statistics.mean(scores)
        weighted_average = sum(weighted_scores) / sum(
            source_weights.get(r.source_id, 1.0) for r in scored_reviews
        )
        median_score = statistics.median(scores)
        score_stddev = statistics.stdev(scores) if len(scores) > 1 else 0.0

        # Calculate consensus strength (inverse of coefficient of variation)
        # Higher consensus = lower variation relative to mean
        consensus_strength = self._calculate_consensus_strength(scores)

        # Calculate controversy score (normalized standard deviation)
        controversy_score = min(score_stddev / 10.0, 1.0)

        # Score distribution
        score_distribution = self._calculate_score_distribution(scores)

        # Temporal data
        review_dates = [r.published_date for r in reviews if r.published_date]
        first_review_date = min(review_dates) if review_dates else None
        latest_review_date = max(review_dates) if review_dates else None

        # Calculate days since release
        album = self.session.get(Album, album_id)
        days_since_release = None
        if album and album.release_date and first_review_date:
            days_since_release = (first_review_date.date() - album.release_date).days

        # Check if aggregate already exists
        statement = select(AlbumReviewAggregate).where(
            AlbumReviewAggregate.album_id == album_id
        )
        aggregate = self.session.exec(statement).first()

        if aggregate:
            # Update existing aggregate
            aggregate.review_count = len(reviews)
            aggregate.average_score = average_score
            aggregate.weighted_average = weighted_average
            aggregate.median_score = median_score
            aggregate.score_stddev = score_stddev
            aggregate.consensus_strength = consensus_strength
            aggregate.controversy_score = controversy_score
            aggregate.source_ids = source_ids
            aggregate.review_item_ids = review_item_ids
            aggregate.score_distribution = score_distribution
            aggregate.first_review_date = first_review_date
            aggregate.latest_review_date = latest_review_date
            aggregate.days_since_release = days_since_release
            aggregate.updated_at = datetime.utcnow()
        else:
            # Create new aggregate
            aggregate = AlbumReviewAggregate(
                album_id=album_id,
                review_count=len(reviews),
                average_score=average_score,
                weighted_average=weighted_average,
                median_score=median_score,
                score_stddev=score_stddev,
                consensus_strength=consensus_strength,
                controversy_score=controversy_score,
                source_ids=source_ids,
                review_item_ids=review_item_ids,
                score_distribution=score_distribution,
                first_review_date=first_review_date,
                latest_review_date=latest_review_date,
                days_since_release=days_since_release,
            )
            self.session.add(aggregate)

        self.session.commit()
        self.session.refresh(aggregate)

        logger.info(
            f"Aggregated {len(reviews)} reviews for album {album_id}: "
            f"avg={average_score:.2f}, weighted={weighted_average:.2f}, "
            f"consensus={consensus_strength:.2f}"
        )

        return aggregate

    def aggregate_all_reviews(self) -> List[AlbumReviewAggregate]:
        """
        Match all unprocessed reviews to albums and aggregate them.

        Returns:
            List of AlbumReviewAggregate objects
        """
        # Get all review items
        statement = select(MusicItem).where(MusicItem.content_type == ContentType.REVIEW)
        reviews = self.session.exec(statement).all()

        logger.info(f"Processing {len(reviews)} reviews for aggregation")

        # Match reviews to albums
        matched_albums = set()
        for review in reviews:
            album = self.matcher.match_music_item_to_album(review, create_if_missing=True)
            if album:
                matched_albums.add(album.id)
            else:
                logger.warning(
                    f"Could not match review to album: {review.title} (missing artist/album data)"
                )

        logger.info(f"Matched reviews to {len(matched_albums)} unique albums")

        # Aggregate reviews for each album
        aggregates = []
        for album_id in matched_albums:
            aggregate = self.aggregate_reviews_for_album(album_id)
            if aggregate:
                aggregates.append(aggregate)

        logger.info(f"Created/updated {len(aggregates)} album review aggregates")
        return aggregates

    def _get_source_weights(self, source_ids: List[int]) -> Dict[int, float]:
        """Get credibility weights for sources."""
        weights = {}
        for source_id in source_ids:
            source = self.session.get(Source, source_id)
            if source:
                weights[source_id] = source.weight
            else:
                weights[source_id] = 1.0
        return weights

    def _calculate_consensus_strength(self, scores: List[float]) -> float:
        """
        Calculate consensus strength from review scores.

        Returns a 0-1 score where:
        - 1.0 = perfect consensus (all scores identical)
        - 0.5 = moderate agreement
        - 0.0 = extreme disagreement
        """
        if len(scores) <= 1:
            return 1.0

        # Calculate coefficient of variation (std/mean)
        mean_score = statistics.mean(scores)
        if mean_score == 0:
            return 1.0

        stddev = statistics.stdev(scores)
        cv = stddev / mean_score

        # Normalize to 0-1 scale (inverse relationship)
        # CV of 0 = perfect consensus (1.0)
        # CV of 0.5 = moderate disagreement (0.5)
        # CV > 1 = extreme disagreement (approaching 0)
        consensus = max(0.0, 1.0 - cv)

        return round(consensus, 3)

    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate distribution of scores across ranges."""
        distribution = {
            "0-3": 0,  # Poor
            "3-5": 0,  # Below average
            "5-7": 0,  # Average
            "7-8": 0,  # Good
            "8-9": 0,  # Great
            "9-10": 0,  # Excellent
        }

        for score in scores:
            if score < 3:
                distribution["0-3"] += 1
            elif score < 5:
                distribution["3-5"] += 1
            elif score < 7:
                distribution["5-7"] += 1
            elif score < 8:
                distribution["7-8"] += 1
            elif score < 9:
                distribution["8-9"] += 1
            else:
                distribution["9-10"] += 1

        return distribution

    def get_top_rated_albums(
        self, limit: int = 10, min_reviews: int = 2
    ) -> List[AlbumReviewAggregate]:
        """
        Get top-rated albums based on weighted average.

        Args:
            limit: Maximum number of results
            min_reviews: Minimum number of reviews required

        Returns:
            List of AlbumReviewAggregate objects sorted by weighted average
        """
        statement = (
            select(AlbumReviewAggregate)
            .where(AlbumReviewAggregate.review_count >= min_reviews)
            .order_by(AlbumReviewAggregate.weighted_average.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_controversial_albums(
        self, limit: int = 10, min_reviews: int = 2
    ) -> List[AlbumReviewAggregate]:
        """
        Get most controversial albums (high score variance).

        Args:
            limit: Maximum number of results
            min_reviews: Minimum number of reviews required

        Returns:
            List of AlbumReviewAggregate objects sorted by controversy score
        """
        statement = (
            select(AlbumReviewAggregate)
            .where(AlbumReviewAggregate.review_count >= min_reviews)
            .order_by(AlbumReviewAggregate.controversy_score.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_recent_aggregates(
        self, days: int = 7, limit: int = 20
    ) -> List[AlbumReviewAggregate]:
        """
        Get recently updated album aggregates.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of AlbumReviewAggregate objects sorted by latest review date
        """
        statement = (
            select(AlbumReviewAggregate)
            .where(AlbumReviewAggregate.latest_review_date.isnot(None))
            .order_by(AlbumReviewAggregate.latest_review_date.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
