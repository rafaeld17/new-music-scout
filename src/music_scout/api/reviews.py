"""
Review aggregation API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..core.database import get_session
from ..models import AlbumReviewAggregate, Album, Artist, MusicItem
from ..services.review_aggregator import ReviewAggregator
from pydantic import BaseModel

router = APIRouter()


# Response models
class ArtistResponse(BaseModel):
    """Artist information response."""
    id: int
    name: str
    genres: List[str] = []
    country: Optional[str] = None


class AlbumResponse(BaseModel):
    """Album information response."""
    id: int
    title: str
    artist: ArtistResponse
    release_year: Optional[int] = None
    album_type: Optional[str] = None


class ReviewItemResponse(BaseModel):
    """Individual review response."""
    id: int
    source_name: str
    url: str
    title: str
    published_date: str
    author: Optional[str] = None
    review_score: Optional[float] = None
    review_score_raw: Optional[str] = None


class AlbumAggregateResponse(BaseModel):
    """Aggregated album review response."""
    id: int
    album: AlbumResponse
    review_count: int
    average_score: Optional[float] = None
    weighted_average: Optional[float] = None
    median_score: Optional[float] = None
    score_stddev: Optional[float] = None
    consensus_strength: Optional[float] = None
    controversy_score: Optional[float] = None
    score_distribution: dict = {}
    first_review_date: Optional[str] = None
    latest_review_date: Optional[str] = None
    reviews: List[ReviewItemResponse] = []


@router.get("/albums/recent", response_model=List[AlbumAggregateResponse])
async def get_recent_albums(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    session: Session = Depends(get_session),
):
    """
    Get recently reviewed albums with aggregated metrics.
    """
    aggregator = ReviewAggregator(session)
    aggregates = aggregator.get_recent_aggregates(days=days, limit=limit)

    return [
        _build_aggregate_response(aggregate, session) for aggregate in aggregates
    ]


@router.get("/albums/top-rated", response_model=List[AlbumAggregateResponse])
async def get_top_rated_albums(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    min_reviews: int = Query(default=2, ge=1, le=10, description="Minimum number of reviews"),
    session: Session = Depends(get_session),
):
    """
    Get top-rated albums based on weighted average scores.
    """
    aggregator = ReviewAggregator(session)
    aggregates = aggregator.get_top_rated_albums(limit=limit, min_reviews=min_reviews)

    return [
        _build_aggregate_response(aggregate, session) for aggregate in aggregates
    ]


@router.get("/albums/controversial", response_model=List[AlbumAggregateResponse])
async def get_controversial_albums(
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    min_reviews: int = Query(default=2, ge=1, le=10, description="Minimum number of reviews"),
    session: Session = Depends(get_session),
):
    """
    Get most controversial albums (high score variance across reviews).
    """
    aggregator = ReviewAggregator(session)
    aggregates = aggregator.get_controversial_albums(limit=limit, min_reviews=min_reviews)

    return [
        _build_aggregate_response(aggregate, session) for aggregate in aggregates
    ]


@router.get("/albums/{album_id}", response_model=AlbumAggregateResponse)
async def get_album_aggregate(
    album_id: int,
    session: Session = Depends(get_session),
):
    """
    Get aggregated review data for a specific album.
    """
    aggregator = ReviewAggregator(session)
    aggregate = aggregator.aggregate_reviews_for_album(album_id)

    if not aggregate:
        raise HTTPException(
            status_code=404,
            detail=f"No reviews found for album {album_id}"
        )

    return _build_aggregate_response(aggregate, session)


@router.get("/aggregate/run")
async def run_aggregation(
    session: Session = Depends(get_session),
):
    """
    Manually trigger review aggregation for all reviews.
    This will match reviews to albums and calculate consensus metrics.
    """
    aggregator = ReviewAggregator(session)
    aggregates = aggregator.aggregate_all_reviews()

    return {
        "status": "success",
        "aggregates_created": len(aggregates),
        "message": f"Successfully aggregated reviews for {len(aggregates)} albums"
    }


@router.get("/reviews/latest", response_model=List[ReviewItemResponse])
async def get_latest_reviews(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    session: Session = Depends(get_session),
):
    """
    Get the latest reviews across all sources.
    """
    from ..models import ContentType
    from sqlmodel import select

    statement = (
        select(MusicItem)
        .where(MusicItem.content_type == ContentType.REVIEW)
        .order_by(MusicItem.published_date.desc())
        .limit(limit)
    )
    reviews = session.exec(statement).all()

    return [_build_review_response(review, session) for review in reviews]


# Helper functions
def _build_aggregate_response(
    aggregate: AlbumReviewAggregate, session: Session
) -> AlbumAggregateResponse:
    """Build a complete aggregate response with album and review details."""
    # Get album and artist
    album = session.get(Album, aggregate.album_id)
    if not album:
        raise HTTPException(status_code=404, detail=f"Album {aggregate.album_id} not found")

    artist = session.get(Artist, album.artist_id)
    if not artist:
        raise HTTPException(status_code=404, detail=f"Artist {album.artist_id} not found")

    # Get all reviews
    reviews = []
    for review_id in aggregate.review_item_ids:
        review = session.get(MusicItem, review_id)
        if review:
            reviews.append(_build_review_response(review, session))

    return AlbumAggregateResponse(
        id=aggregate.id,
        album=AlbumResponse(
            id=album.id,
            title=album.title,
            artist=ArtistResponse(
                id=artist.id,
                name=artist.name,
                genres=artist.genres,
                country=artist.country,
            ),
            release_year=album.release_year,
            album_type=album.album_type,
        ),
        review_count=aggregate.review_count,
        average_score=aggregate.average_score,
        weighted_average=aggregate.weighted_average,
        median_score=aggregate.median_score,
        score_stddev=aggregate.score_stddev,
        consensus_strength=aggregate.consensus_strength,
        controversy_score=aggregate.controversy_score,
        score_distribution=aggregate.score_distribution,
        first_review_date=aggregate.first_review_date.isoformat() if aggregate.first_review_date else None,
        latest_review_date=aggregate.latest_review_date.isoformat() if aggregate.latest_review_date else None,
        reviews=reviews,
    )


def _build_review_response(review: MusicItem, session: Session) -> ReviewItemResponse:
    """Build a review item response."""
    from ..models import Source

    source = session.get(Source, review.source_id)
    source_name = source.name if source else "Unknown"

    return ReviewItemResponse(
        id=review.id,
        source_name=source_name,
        url=review.url,
        title=review.title,
        published_date=review.published_date.isoformat() if review.published_date else "",
        author=review.author,
        review_score=review.review_score,
        review_score_raw=review.review_score_raw,
    )
