"""
Album review aggregation model for consensus metrics.
"""
from datetime import datetime
from typing import Optional, Dict, List

from sqlmodel import SQLModel, Field, JSON, Column


class AlbumReviewAggregate(SQLModel, table=True):
    """Model for aggregated review data across multiple sources."""

    __tablename__ = "album_review_aggregate"

    id: Optional[int] = Field(default=None, primary_key=True)
    album_id: int = Field(foreign_key="album.id")

    # Review statistics
    review_count: int = Field(default=0, description="Total number of reviews")
    average_score: Optional[float] = Field(
        default=None, description="Simple average of all review scores (0-10 scale)"
    )
    weighted_average: Optional[float] = Field(
        default=None, description="Weighted average based on source credibility"
    )
    median_score: Optional[float] = Field(
        default=None, description="Median review score"
    )
    score_stddev: Optional[float] = Field(
        default=None, description="Standard deviation of scores"
    )

    # Consensus metrics
    consensus_strength: Optional[float] = Field(
        default=None,
        description="0-1 score indicating reviewer agreement (1=unanimous, 0=highly divided)",
    )
    controversy_score: Optional[float] = Field(
        default=None,
        description="0-1 score for controversial albums (high score variance)",
    )

    # Source tracking
    source_ids: List[int] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of source IDs that reviewed this album",
    )
    review_item_ids: List[int] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="List of MusicItem IDs for all reviews",
    )

    # Score distribution
    score_distribution: Dict[str, int] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Distribution of scores by range (e.g., {'9-10': 2, '7-8': 1})",
    )

    # Temporal tracking
    first_review_date: Optional[datetime] = Field(
        default=None, description="Date of earliest review"
    )
    latest_review_date: Optional[datetime] = Field(
        default=None, description="Date of most recent review"
    )
    days_since_release: Optional[int] = Field(
        default=None, description="Days between album release and first review"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "album_id": 1,
                "review_count": 3,
                "average_score": 8.3,
                "weighted_average": 8.5,
                "median_score": 8.5,
                "consensus_strength": 0.85,
                "controversy_score": 0.15,
                "source_ids": [1, 2],
                "score_distribution": {"9-10": 1, "8-9": 2},
            }
        }
