"""
Source model for music content providers.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class SourceType(str, Enum):
    """Type of content source."""
    RSS = "rss"
    HTML = "html"
    API = "api"


class Source(SQLModel, table=True):
    """Model for content sources (websites, RSS feeds, etc.)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=100)
    url: str = Field(max_length=500)
    source_type: SourceType
    weight: float = Field(default=1.0, description="Source credibility weight for scoring")
    enabled: bool = Field(default=True)
    last_crawled: Optional[datetime] = Field(default=None)
    health_score: float = Field(default=1.0, description="Source reliability score (0-1)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "name": "The Prog Report",
                "url": "https://progreport.com/",
                "source_type": "html",
                "weight": 1.2,
                "enabled": True
            }
        }