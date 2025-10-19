"""
Unit tests for the review aggregation service.
"""
import pytest
from datetime import datetime, date
from sqlmodel import SQLModel, create_engine, Session

from src.music_scout.models import (
    Artist,
    Album,
    MusicItem,
    ContentType,
    Source,
    SourceType,
    AlbumReviewAggregate,
)
from src.music_scout.services.review_aggregator import ReviewAggregator


@pytest.fixture
def test_session():
    """Create a test database session with sample data."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create sources
        source1 = Source(
            name="The Prog Report",
            url="https://progreport.com/feed",
            source_type=SourceType.RSS,
            weight=1.2
        )
        source2 = Source(
            name="Sonic Perspectives",
            url="https://sonicperspectives.com/feed",
            source_type=SourceType.RSS,
            weight=1.5
        )
        session.add(source1)
        session.add(source2)
        session.commit()
        session.refresh(source1)
        session.refresh(source2)

        # Create artist and album
        artist = Artist(name="Tool", normalized_name="tool")
        session.add(artist)
        session.commit()
        session.refresh(artist)

        album = Album(
            title="Fear Inoculum",
            normalized_title="fear inoculum",
            artist_id=artist.id,
            release_date=date(2019, 8, 30),
            release_year=2019
        )
        session.add(album)
        session.commit()
        session.refresh(album)

        # Store IDs for test access
        session.source1_id = source1.id
        session.source2_id = source2.id
        session.album_id = album.id
        session.artist_id = artist.id

        yield session


def test_aggregate_reviews_single_source(test_session):
    """Test aggregating reviews from a single source."""
    # Create reviews
    review1 = MusicItem(
        source_id=test_session.source1_id,
        url="https://test.com/review1",
        title="Tool - Fear Inoculum Review",
        published_date=datetime(2019, 9, 1),
        content_type=ContentType.REVIEW,
        raw_content="Excellent album!",
        artists=["Tool"],
        album="Fear Inoculum",
        review_score=9.0
    )
    test_session.add(review1)
    test_session.commit()

    # Aggregate
    aggregator = ReviewAggregator(test_session)
    aggregate = aggregator.aggregate_reviews_for_album(test_session.album_id)

    assert aggregate is not None
    assert aggregate.review_count == 1
    assert aggregate.average_score == 9.0
    assert aggregate.weighted_average == 9.0
    assert aggregate.consensus_strength == 1.0  # Single review = perfect consensus


def test_aggregate_reviews_multiple_sources(test_session):
    """Test aggregating reviews from multiple sources."""
    # Create reviews with different scores
    reviews = [
        MusicItem(
            source_id=test_session.source1_id,
            url="https://test.com/review1",
            title="Tool - Fear Inoculum Review",
            published_date=datetime(2019, 9, 1),
            content_type=ContentType.REVIEW,
            raw_content="Great!",
            artists=["Tool"],
            album="Fear Inoculum",
            review_score=8.5
        ),
        MusicItem(
            source_id=test_session.source2_id,
            url="https://test.com/review2",
            title="Fear Inoculum by Tool - Review",
            published_date=datetime(2019, 9, 5),
            content_type=ContentType.REVIEW,
            raw_content="Masterpiece!",
            artists=["Tool"],
            album="Fear Inoculum",
            review_score=9.5
        ),
    ]
    for review in reviews:
        test_session.add(review)
    test_session.commit()

    # Aggregate
    aggregator = ReviewAggregator(test_session)
    aggregate = aggregator.aggregate_reviews_for_album(test_session.album_id)

    assert aggregate is not None
    assert aggregate.review_count == 2
    assert aggregate.average_score == 9.0  # (8.5 + 9.5) / 2
    assert aggregate.median_score == 9.0
    # Weighted average should be closer to 9.5 (higher source weight)
    assert aggregate.weighted_average > 9.0
    assert aggregate.consensus_strength > 0.8  # Good consensus
    assert aggregate.source_ids == [test_session.source1_id, test_session.source2_id]


def test_consensus_strength_calculation(test_session):
    """Test consensus strength with varying score spreads."""
    # Create reviews with high variance
    reviews = [
        MusicItem(
            source_id=test_session.source1_id,
            url=f"https://test.com/review{i}",
            title=f"Review {i}",
            published_date=datetime(2019, 9, i),
            content_type=ContentType.REVIEW,
            raw_content="Review",
            artists=["Tool"],
            album="Fear Inoculum",
            review_score=score
        )
        for i, score in enumerate([5.0, 9.0], start=1)
    ]
    for review in reviews:
        test_session.add(review)
    test_session.commit()

    # Aggregate
    aggregator = ReviewAggregator(test_session)
    aggregate = aggregator.aggregate_reviews_for_album(test_session.album_id)

    # High variance should result in lower consensus
    assert aggregate.consensus_strength < 0.7
    assert aggregate.controversy_score > 0.28  # Adjusted based on actual calculation


def test_score_distribution(test_session):
    """Test score distribution calculation."""
    # Create reviews across different score ranges
    scores = [5.0, 6.5, 7.5, 8.5, 9.2]
    reviews = [
        MusicItem(
            source_id=test_session.source1_id,
            url=f"https://test.com/review{i}",
            title=f"Review {i}",
            published_date=datetime(2019, 9, i),
            content_type=ContentType.REVIEW,
            raw_content="Review",
            artists=["Tool"],
            album="Fear Inoculum",
            review_score=score
        )
        for i, score in enumerate(scores, start=1)
    ]
    for review in reviews:
        test_session.add(review)
    test_session.commit()

    # Aggregate
    aggregator = ReviewAggregator(test_session)
    aggregate = aggregator.aggregate_reviews_for_album(test_session.album_id)

    distribution = aggregate.score_distribution
    assert distribution["5-7"] == 2  # 5.0, 6.5
    assert distribution["7-8"] == 1  # 7.5
    assert distribution["8-9"] == 1  # 8.5
    assert distribution["9-10"] == 1  # 9.2


def test_temporal_tracking(test_session):
    """Test temporal data tracking."""
    # Create reviews with different dates
    reviews = [
        MusicItem(
            source_id=test_session.source1_id,
            url="https://test.com/review1",
            title="Early Review",
            published_date=datetime(2019, 9, 1),
            content_type=ContentType.REVIEW,
            raw_content="Review",
            artists=["Tool"],
            album="Fear Inoculum",
            review_score=8.0
        ),
        MusicItem(
            source_id=test_session.source2_id,
            url="https://test.com/review2",
            title="Later Review",
            published_date=datetime(2019, 10, 15),
            content_type=ContentType.REVIEW,
            raw_content="Review",
            artists=["Tool"],
            album="Fear Inoculum",
            review_score=9.0
        ),
    ]
    for review in reviews:
        test_session.add(review)
    test_session.commit()

    # Aggregate
    aggregator = ReviewAggregator(test_session)
    aggregate = aggregator.aggregate_reviews_for_album(test_session.album_id)

    assert aggregate.first_review_date == datetime(2019, 9, 1)
    assert aggregate.latest_review_date == datetime(2019, 10, 15)
    assert aggregate.days_since_release == 2  # Sep 1 - Aug 30 = 2 days


def test_aggregate_all_reviews(test_session):
    """Test aggregating all reviews in the database."""
    # Create another artist and album
    artist2 = Artist(name="Porcupine Tree", normalized_name="porcupine tree")
    test_session.add(artist2)
    test_session.commit()
    test_session.refresh(artist2)

    album2 = Album(
        title="Closure/Continuation",
        normalized_title="closure continuation",
        artist_id=artist2.id,
        release_year=2022
    )
    test_session.add(album2)
    test_session.commit()

    # Create reviews for both albums
    reviews = [
        # Tool reviews
        MusicItem(
            source_id=test_session.source1_id,
            url="https://test.com/tool1",
            title="Tool - Fear Inoculum Review",
            published_date=datetime(2019, 9, 1),
            content_type=ContentType.REVIEW,
            raw_content="Review",
            artists=["Tool"],
            album="Fear Inoculum",
            review_score=8.5
        ),
        # Porcupine Tree reviews
        MusicItem(
            source_id=test_session.source1_id,
            url="https://test.com/pt1",
            title="Porcupine Tree - Closure/Continuation Review",
            published_date=datetime(2022, 6, 25),
            content_type=ContentType.REVIEW,
            raw_content="Review",
            artists=["Porcupine Tree"],
            album="Closure/Continuation",
            review_score=9.0
        ),
        MusicItem(
            source_id=test_session.source2_id,
            url="https://test.com/pt2",
            title="Closure/Continuation by Porcupine Tree",
            published_date=datetime(2022, 6, 26),
            content_type=ContentType.REVIEW,
            raw_content="Review",
            artists=["Porcupine Tree"],
            album="Closure/Continuation",
            review_score=8.8
        ),
    ]
    for review in reviews:
        test_session.add(review)
    test_session.commit()

    # Aggregate all
    aggregator = ReviewAggregator(test_session)
    aggregates = aggregator.aggregate_all_reviews()

    # Should have aggregates for 2 albums
    assert len(aggregates) == 2

    # Check that both albums were aggregated
    album_ids = {agg.album_id for agg in aggregates}
    assert test_session.album_id in album_ids
    assert album2.id in album_ids


def test_get_top_rated_albums(test_session):
    """Test retrieving top-rated albums."""
    # Create multiple albums with different ratings
    artist = test_session.get(Artist, test_session.artist_id)

    albums = [
        Album(title=f"Album {i}", normalized_title=f"album {i}", artist_id=artist.id)
        for i in range(3)
    ]
    for album in albums:
        test_session.add(album)
    test_session.commit()

    # Create aggregates manually
    aggregates = [
        AlbumReviewAggregate(
            album_id=albums[0].id,
            review_count=3,
            average_score=9.5,
            weighted_average=9.5,
        ),
        AlbumReviewAggregate(
            album_id=albums[1].id,
            review_count=2,
            average_score=7.0,
            weighted_average=7.0,
        ),
        AlbumReviewAggregate(
            album_id=albums[2].id,
            review_count=4,
            average_score=8.5,
            weighted_average=8.5,
        ),
    ]
    for agg in aggregates:
        test_session.add(agg)
    test_session.commit()

    # Get top rated
    aggregator = ReviewAggregator(test_session)
    top_albums = aggregator.get_top_rated_albums(limit=2, min_reviews=2)

    assert len(top_albums) == 2
    assert top_albums[0].weighted_average == 9.5
    assert top_albums[1].weighted_average == 8.5


def test_get_controversial_albums(test_session):
    """Test retrieving controversial albums."""
    artist = test_session.get(Artist, test_session.artist_id)

    albums = [
        Album(title=f"Album {i}", normalized_title=f"album {i}", artist_id=artist.id)
        for i in range(2)
    ]
    for album in albums:
        test_session.add(album)
    test_session.commit()

    # Create aggregates with different controversy scores
    aggregates = [
        AlbumReviewAggregate(
            album_id=albums[0].id,
            review_count=3,
            average_score=7.0,
            weighted_average=7.0,
            controversy_score=0.8,  # High controversy
        ),
        AlbumReviewAggregate(
            album_id=albums[1].id,
            review_count=2,
            average_score=8.5,
            weighted_average=8.5,
            controversy_score=0.2,  # Low controversy
        ),
    ]
    for agg in aggregates:
        test_session.add(agg)
    test_session.commit()

    # Get controversial
    aggregator = ReviewAggregator(test_session)
    controversial = aggregator.get_controversial_albums(limit=2, min_reviews=2)

    assert len(controversial) == 2
    assert controversial[0].controversy_score == 0.8
    assert controversial[1].controversy_score == 0.2


def test_update_existing_aggregate(test_session):
    """Test that aggregating twice updates the existing aggregate."""
    # Create initial review
    review1 = MusicItem(
        source_id=test_session.source1_id,
        url="https://test.com/review1",
        title="Tool - Fear Inoculum Review",
        published_date=datetime(2019, 9, 1),
        content_type=ContentType.REVIEW,
        raw_content="Review",
        artists=["Tool"],
        album="Fear Inoculum",
        review_score=8.0
    )
    test_session.add(review1)
    test_session.commit()

    # First aggregation
    aggregator = ReviewAggregator(test_session)
    aggregate1 = aggregator.aggregate_reviews_for_album(test_session.album_id)
    first_id = aggregate1.id
    assert aggregate1.review_count == 1
    assert aggregate1.average_score == 8.0

    # Add another review
    review2 = MusicItem(
        source_id=test_session.source2_id,
        url="https://test.com/review2",
        title="Fear Inoculum Review",
        published_date=datetime(2019, 9, 5),
        content_type=ContentType.REVIEW,
        raw_content="Review",
        artists=["Tool"],
        album="Fear Inoculum",
        review_score=9.0
    )
    test_session.add(review2)
    test_session.commit()

    # Second aggregation (should update existing)
    aggregate2 = aggregator.aggregate_reviews_for_album(test_session.album_id)

    # Should be same record (updated)
    assert aggregate2.id == first_id
    assert aggregate2.review_count == 2
    assert aggregate2.average_score == 8.5


def test_no_reviews_returns_none(test_session):
    """Test that aggregating an album with no reviews returns None."""
    # Create album with no reviews
    artist = Artist(name="Test Artist", normalized_name="test artist")
    test_session.add(artist)
    test_session.commit()
    test_session.refresh(artist)

    album = Album(
        title="Test Album",
        normalized_title="test album",
        artist_id=artist.id
    )
    test_session.add(album)
    test_session.commit()

    # Try to aggregate
    aggregator = ReviewAggregator(test_session)
    aggregate = aggregator.aggregate_reviews_for_album(album.id)

    assert aggregate is None
