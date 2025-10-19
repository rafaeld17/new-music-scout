"""
Base class for historical scrapers that fetch older reviews via pagination.

Historical scrapers are used to backfill the database with reviews from before
the RSS feed started or beyond the RSS feed's limit (typically 10-50 items).
"""
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session

import requests
from bs4 import BeautifulSoup

from ..models import Source, MusicItem, ContentType
from ..core.logging import logger
from .score_parser import ScoreParser
from .enhanced_metadata_fetcher import get_enhanced_metadata_fetcher


class HistoricalScraper(ABC):
    """
    Base class for pagination-based historical scrapers.

    Subclasses should implement:
    - fetch_page(page_num) - Fetch and parse a single page of reviews
    - extract_review_data(soup, url) - Extract review data from a review page
    """

    def __init__(self, session: Session, source: Source):
        self.session = session
        self.source = source
        self.user_agent = "Mozilla/5.0 (compatible; NewMusicScout/0.1.0; +https://github.com/user/music-scout)"
        self.score_parser = ScoreParser()
        self.metadata_fetcher = get_enhanced_metadata_fetcher()
        self.rate_limit_delay = 1.0  # Seconds between requests

    @abstractmethod
    def fetch_page(self, page_num: int) -> List[Dict[str, Any]]:
        """
        Fetch a single page of review listings.

        Args:
            page_num: Page number to fetch (1-indexed)

        Returns:
            List of review preview dicts with keys:
            - url: Full URL to the review
            - title: Review title
            - published_date: Publication date (datetime object)
            - artist: Artist name (optional, can extract from title)
            - album: Album name (optional, can extract from title)
        """
        pass

    @abstractmethod
    def extract_review_data(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract full review data from a review page.

        Args:
            soup: BeautifulSoup object of the review page
            url: URL of the review

        Returns:
            Dict with keys:
            - content: Full review text
            - author: Review author
            - review_score: Normalized score (0-10)
            - review_score_raw: Original score string
            Or None if extraction fails
        """
        pass

    def scrape_until_date(
        self,
        target_date: datetime,
        max_pages: Optional[int] = None,
        start_page: int = 1
    ) -> int:
        """
        Scrape reviews until reaching the target date.

        Args:
            target_date: Stop when reviews older than this date are encountered
            max_pages: Maximum number of pages to scrape (safety limit)
            start_page: Page number to start from (for resuming)

        Returns:
            Number of new reviews added
        """
        logger.info(f"Starting historical scrape for {self.source.name} until {target_date}")

        page = start_page
        total_added = 0
        consecutive_errors = 0
        max_consecutive_errors = 3

        while True:
            # Safety check
            if max_pages and page > max_pages:
                logger.info(f"Reached maximum page limit ({max_pages})")
                break

            # Check for too many errors
            if consecutive_errors >= max_consecutive_errors:
                logger.error(f"Too many consecutive errors ({consecutive_errors}), stopping")
                break

            try:
                logger.info(f"Fetching page {page}...")
                review_previews = self.fetch_page(page)

                if not review_previews:
                    logger.info(f"No more reviews found on page {page}, stopping")
                    break

                # Reset error counter on successful page fetch
                consecutive_errors = 0

                # Process each review on the page
                reached_target_date = False
                for preview in review_previews:
                    # Check if we've reached the target date
                    if preview.get('published_date') and preview['published_date'] < target_date:
                        logger.info(f"Reached target date: {preview['published_date']} < {target_date}")
                        reached_target_date = True
                        break

                    # Check if review already exists
                    if self._review_exists(preview['url']):
                        logger.debug(f"Review already exists: {preview['url']}")
                        continue

                    # Fetch and process the full review
                    added = self._ingest_review(preview)
                    if added:
                        total_added += 1
                        logger.info(f"Added review {total_added}: {preview['title']}")

                    # Rate limiting between individual review fetches
                    time.sleep(self.rate_limit_delay)

                if reached_target_date:
                    logger.info(f"Reached target date on page {page}, stopping")
                    break

                # Move to next page
                page += 1

                # Rate limiting between pages
                time.sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                consecutive_errors += 1
                time.sleep(self.rate_limit_delay * 2)  # Longer delay on error

        logger.info(f"Historical scrape complete. Added {total_added} new reviews from {self.source.name}")
        return total_added

    def _review_exists(self, url: str) -> bool:
        """Check if a review with this URL already exists in the database."""
        from sqlmodel import select
        statement = select(MusicItem).where(MusicItem.url == url)
        return self.session.exec(statement).first() is not None

    def _ingest_review(self, preview: Dict[str, Any]) -> bool:
        """
        Fetch full review data and add to database.

        Args:
            preview: Review preview dict from fetch_page()

        Returns:
            True if review was successfully added, False otherwise
        """
        try:
            # Fetch the full review page
            response = requests.get(
                preview['url'],
                headers={'User-Agent': self.user_agent},
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract full review data
            review_data = self.extract_review_data(soup, preview['url'])

            if not review_data:
                logger.warning(f"Could not extract review data from {preview['url']}")
                return False

            # Determine artist and album (from preview or extract from title)
            artist = preview.get('artist')
            album = preview.get('album')

            if not artist or not album:
                # Try to extract from title
                from .ingestion import IngestionService
                temp_service = IngestionService(self.session)
                artists, extracted_album = temp_service._extract_music_metadata(
                    preview['title'],
                    review_data.get('content', '')
                )
                artist = artists[0] if artists else None
                album = extracted_album or album

            # Create MusicItem
            music_item = MusicItem(
                source_id=self.source.id,
                url=preview['url'],
                title=preview['title'],
                published_date=preview.get('published_date', datetime.utcnow()),
                content_type=ContentType.REVIEW,
                raw_content=review_data.get('content', ''),
                processed_content=review_data.get('content', ''),
                author=review_data.get('author'),
                artists=[artist] if artist else [],
                album=album,
                review_score=review_data.get('review_score'),
                review_score_raw=review_data.get('review_score_raw'),
                is_processed=True
            )

            # Enrich with Spotify/MusicBrainz metadata
            if artist and album:
                self._enrich_metadata(music_item)

            # Save to database
            self.session.add(music_item)
            self.session.commit()

            return True

        except Exception as e:
            logger.error(f"Error ingesting review {preview['url']}: {e}")
            return False

    def _enrich_metadata(self, music_item: MusicItem) -> None:
        """
        Enrich MusicItem with metadata from Spotify/MusicBrainz.
        Same logic as IngestionService._enrich_metadata()
        """
        if not music_item.artists or not music_item.album:
            return
        if music_item.metadata_source:
            return

        try:
            artist = music_item.artists[0]
            album = music_item.album

            logger.info(f"Enriching metadata for {artist} - {album}")

            metadata = self.metadata_fetcher.fetch_album_metadata(artist, album)

            if metadata:
                music_item.spotify_album_id = metadata.get('spotify_album_id')
                music_item.spotify_artist_id = metadata.get('spotify_artist_id')
                music_item.musicbrainz_id = metadata.get('musicbrainz_id')
                music_item.album_genres = metadata.get('genres', [])
                music_item.album_cover_url = metadata.get('cover_art_url')
                music_item.release_date = metadata.get('release_date')
                music_item.album_type = metadata.get('album_type')
                music_item.label = metadata.get('label')
                music_item.total_tracks = metadata.get('total_tracks')
                music_item.artist_popularity = metadata.get('artist_popularity')
                music_item.album_popularity = metadata.get('album_popularity')
                music_item.artist_followers = metadata.get('artist_followers')
                music_item.metadata_source = metadata.get('metadata_source')
                music_item.metadata_confidence = metadata.get('confidence')
                music_item.metadata_fetched_at = datetime.utcnow()

                logger.info(f"Successfully enriched {artist} - {album} from {metadata['metadata_source']}")

        except Exception as e:
            logger.error(f"Error enriching metadata for {music_item.title}: {e}")

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Helper method to fetch and parse a URL."""
        try:
            response = requests.get(
                url,
                headers={'User-Agent': self.user_agent},
                timeout=30
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
