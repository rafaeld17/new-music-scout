"""
Artist model for music metadata.
"""
from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, JSON, Column


class Artist(SQLModel, table=True):
    """Model for artist information."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=200)
    normalized_name: str = Field(max_length=200, description="Normalized name for matching")

    # External IDs
    musicbrainz_id: Optional[str] = Field(default=None, max_length=100)
    spotify_id: Optional[str] = Field(default=None, max_length=100)

    # Metadata
    genres: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    country: Optional[str] = Field(default=None, max_length=100)
    formed_year: Optional[int] = Field(default=None)

    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "name": "Porcupine Tree",
                "normalized_name": "porcupine tree",
                "genres": ["progressive rock", "progressive metal"],
                "country": "United Kingdom",
                "formed_year": 1987
            }
        }