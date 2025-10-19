"""
Album model for music metadata.
"""
from datetime import datetime, date
from typing import Optional, List

from sqlmodel import SQLModel, Field, JSON, Column


class Album(SQLModel, table=True):
    """Model for album information."""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=300)
    normalized_title: str = Field(max_length=300, description="Normalized title for matching")
    artist_id: int = Field(foreign_key="artist.id")

    # Release information
    release_date: Optional[date] = Field(default=None)
    release_year: Optional[int] = Field(default=None)

    # External IDs
    musicbrainz_id: Optional[str] = Field(default=None, max_length=100)
    spotify_id: Optional[str] = Field(default=None, max_length=100)

    # Album metadata
    album_type: Optional[str] = Field(default=None, max_length=50)  # album, EP, single, etc.
    label: Optional[str] = Field(default=None, max_length=200)
    genres: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    cover_art_url: Optional[str] = Field(default=None, max_length=500, description="URL to album cover art")

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "title": "Closure/Continuation",
                "normalized_title": "closure continuation",
                "artist_id": 1,
                "release_date": "2022-06-24",
                "release_year": 2022,
                "album_type": "album"
            }
        }