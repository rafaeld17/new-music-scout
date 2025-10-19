"""
Service for managing content sources and their configurations.
"""
from typing import List, Optional
from sqlmodel import Session, select
from ..models import Source, SourceType
from ..core.database import get_session
from ..core.logging import logger


class SourceManager:
    """Manages content sources and their configurations."""

    def __init__(self, session: Session):
        self.session = session

    def create_default_sources(self) -> List[Source]:
        """Create default sources for the application."""
        default_sources = [
            Source(
                name="The Prog Report",
                url="https://progreport.com/feed/",
                source_type=SourceType.RSS,
                weight=1.2,
                enabled=True
            ),
            Source(
                name="The Prog Report Reviews",
                url="https://progreport.com/category/progressive-rock-reviews/feed/",
                source_type=SourceType.RSS,
                weight=1.2,
                enabled=True
            ),
            Source(
                name="Sonic Perspectives",
                url="https://www.sonicperspectives.com/feed/",
                source_type=SourceType.RSS,
                weight=1.5,
                enabled=True
            ),
            Source(
                name="Sonic Perspectives Reviews",
                url="https://www.sonicperspectives.com/category/album-reviews/feed/",
                source_type=SourceType.RSS,
                weight=1.5,
                enabled=True
            ),
            Source(
                name="Metal Injection",
                url="https://metalinjection.net/feed",
                source_type=SourceType.RSS,
                weight=1.0,
                enabled=True
            ),
            Source(
                name="Ultimate Classic Rock",
                url="https://ultimateclassicrock.com/feed/",
                source_type=SourceType.RSS,
                weight=1.3,
                enabled=True
            ),
            Source(
                name="The Prog Mind",
                url="https://theprogmind.com/feed/",
                source_type=SourceType.RSS,
                weight=1.4,
                enabled=True
            ),
            Source(
                name="Heavy Music HQ",
                url="https://heavymusichq.com/feed/",
                source_type=SourceType.RSS,
                weight=1.2,
                enabled=True
            ),
            Source(
                name="Proglodytes",
                url="https://www.proglodytes.com/feed/",
                source_type=SourceType.RSS,
                weight=1.4,
                enabled=True
            ),
            Source(
                name="Blabbermouth",
                url="https://www.blabbermouth.net/feed/",
                source_type=SourceType.RSS,
                weight=1.0,
                enabled=True
            ),
            Source(
                name="Louder Sound Prog",
                url="https://www.loudersound.com/prog/feed",
                source_type=SourceType.RSS,
                weight=1.3,
                enabled=True
            ),
            Source(
                name="MetalSucks",
                url="https://www.metalsucks.net/feed/",
                source_type=SourceType.RSS,
                weight=1.0,
                enabled=True
            ),
            Source(
                name="Brooklyn Vegan",
                url="https://www.brooklynvegan.com/feed/",
                source_type=SourceType.RSS,
                weight=0.8,
                enabled=True
            ),
        ]

        created_sources = []
        for source_data in default_sources:
            # Check if source already exists
            existing = self.get_source_by_name(source_data.name)
            if not existing:
                self.session.add(source_data)
                created_sources.append(source_data)
                logger.info(f"Created source: {source_data.name}")
            else:
                logger.info(f"Source already exists: {source_data.name}")

        self.session.commit()
        return created_sources

    def get_source_by_name(self, name: str) -> Optional[Source]:
        """Get a source by name."""
        statement = select(Source).where(Source.name == name)
        return self.session.exec(statement).first()

    def get_enabled_sources(self) -> List[Source]:
        """Get all enabled sources."""
        statement = select(Source).where(Source.enabled == True)
        return list(self.session.exec(statement).all())

    def get_rss_sources(self) -> List[Source]:
        """Get all RSS sources."""
        statement = select(Source).where(
            Source.source_type == SourceType.RSS,
            Source.enabled == True
        )
        return list(self.session.exec(statement).all())

    def update_source_health(self, source_id: int, health_score: float, error: Optional[str] = None):
        """Update source health score."""
        source = self.session.get(Source, source_id)
        if source:
            source.health_score = max(0.0, min(1.0, health_score))  # Clamp to 0-1
            if error:
                logger.warning(f"Source health issue for {source.name}: {error}")
            self.session.add(source)
            self.session.commit()