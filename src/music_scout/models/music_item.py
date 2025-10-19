"""
Music item model for storing content from sources.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlmodel import SQLModel, Field, JSON, Column


class ContentType(str, Enum):
    """Type of music content."""
    REVIEW = "review"
    NEWS = "news"
    PREMIERE = "premiere"
    INTERVIEW = "interview"
    BEST_OF = "best_of"
    ALBUM_OF_DAY = "album_of_day"


class MusicItem(SQLModel, table=True):
    """Model for storing music-related content from sources."""

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="source.id")
    url: str = Field(unique=True, max_length=1000)
    title: str = Field(max_length=500)
    published_date: datetime
    discovered_date: datetime = Field(default_factory=datetime.utcnow)
    content_type: ContentType
    raw_content: str = Field(description="Original content text")
    processed_content: Optional[str] = Field(default=None, description="Cleaned/processed content")

    # Author information
    author: Optional[str] = Field(default=None, max_length=200)

    # Content metadata
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    artists: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    album: Optional[str] = Field(default=None, max_length=300)
    track: Optional[str] = Field(default=None, max_length=300)
    tracks: List[str] = Field(default_factory=list, sa_column=Column(JSON), description="Extracted track/single names")

    # Album metadata (enriched from Spotify/MusicBrainz)
    album_genres: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    album_cover_url: Optional[str] = Field(default=None, max_length=500)
    release_date: Optional[str] = Field(default=None, max_length=50, description="Album release date (YYYY-MM-DD or YYYY)")
    album_type: Optional[str] = Field(default=None, max_length=50, description="album, single, EP, compilation")
    label: Optional[str] = Field(default=None, max_length=200, description="Record label")
    total_tracks: Optional[int] = Field(default=None, description="Total number of tracks on album")

    # Spotify metadata
    spotify_album_id: Optional[str] = Field(default=None, max_length=100, description="Spotify album ID")
    spotify_artist_id: Optional[str] = Field(default=None, max_length=100, description="Spotify artist ID")
    artist_popularity: Optional[int] = Field(default=None, description="Spotify artist popularity (0-100)")
    album_popularity: Optional[int] = Field(default=None, description="Spotify album popularity (0-100)")
    artist_followers: Optional[int] = Field(default=None, description="Spotify artist follower count")

    # MusicBrainz metadata
    musicbrainz_id: Optional[str] = Field(default=None, max_length=100)

    # Metadata enrichment tracking
    metadata_source: Optional[str] = Field(default=None, max_length=50, description="spotify, musicbrainz, or None")
    metadata_confidence: Optional[float] = Field(default=None, description="Confidence score 0-1")
    metadata_fetched_at: Optional[datetime] = Field(default=None, description="When metadata was last fetched")

    # Review-specific fields
    review_score: Optional[float] = Field(default=None, description="Normalized 0-10 scale")
    review_score_raw: Optional[str] = Field(default=None, max_length=50, description="Original score format")
    review_text: Optional[str] = Field(default=None, description="Extracted review content")

    # Processing metadata
    is_processed: bool = Field(default=False)
    processing_error: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "url": "https://progreport.com/reviews/porcupine-tree-closure",
                "title": "Porcupine Tree - Closure/Continuation Review",
                "content_type": "review",
                "artists": ["Porcupine Tree"],
                "album": "Closure/Continuation",
                "review_score": 8.5,
                "review_score_raw": "8.5/10"
            }
        }