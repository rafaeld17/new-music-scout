"""
Service for ingesting content from various sources.
"""
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from ..models import Source, MusicItem, ContentType, SourceType
from ..core.logging import logger
from .score_parser import ScoreParser
from .enhanced_metadata_fetcher import get_enhanced_metadata_fetcher


class IngestionService:
    """Service for ingesting content from RSS feeds and HTML sources."""

    def __init__(self, session: Session):
        self.session = session
        self.user_agent = "Mozilla/5.0 (compatible; NewMusicScout/0.1.0; +https://github.com/user/music-scout)"
        self.score_parser = ScoreParser()
        self.metadata_fetcher = get_enhanced_metadata_fetcher()

    def ingest_from_source(self, source: Source) -> List[MusicItem]:
        """Ingest content from a single source."""
        logger.info(f"Starting ingestion from source: {source.name}")

        try:
            if source.source_type == SourceType.RSS:
                items = self._ingest_rss(source)
            elif source.source_type == SourceType.HTML:
                items = self._ingest_html(source)
            else:
                logger.warning(f"Unsupported source type: {source.source_type}")
                return []

            # Update source last_crawled time
            source.last_crawled = datetime.utcnow()
            self.session.add(source)
            self.session.commit()

            logger.info(f"Successfully ingested {len(items)} items from {source.name}")
            return items

        except Exception as e:
            logger.error(f"Error ingesting from {source.name}: {str(e)}")
            # Could update source health score here
            return []

    def _ingest_rss(self, source: Source) -> List[MusicItem]:
        """Ingest content from RSS feed."""
        try:
            # Set user agent for respectful crawling
            headers = {"User-Agent": self.user_agent}

            # Parse RSS feed
            feed = feedparser.parse(source.url, agent=self.user_agent)

            if feed.bozo:
                logger.warning(f"RSS feed has issues: {source.url}")

            items = []
            for entry in feed.entries:
                # Check if item already exists
                existing = self._get_existing_item(entry.link)
                if existing:
                    logger.debug(f"Item already exists: {entry.link}")
                    continue

                # Extract basic information
                music_item = self._create_music_item_from_rss(source, entry)
                if music_item:
                    # Enrich with metadata from Spotify/MusicBrainz
                    self._enrich_metadata(music_item)
                    self.session.add(music_item)
                    items.append(music_item)

            self.session.commit()
            return items

        except Exception as e:
            logger.error(f"Error parsing RSS feed {source.url}: {str(e)}")
            return []

    def _create_music_item_from_rss(self, source: Source, entry: Any) -> Optional[MusicItem]:
        """Create a MusicItem from an RSS entry."""
        try:
            # Parse published date
            published_date = datetime.utcnow()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_date = datetime(*entry.updated_parsed[:6])

            # Extract content
            content = ""
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            elif hasattr(entry, 'content'):
                content = entry.content[0].value if entry.content else ""

            # Clean HTML from content
            clean_content = self._clean_html(content)

            # Determine content type based on title, content, and URL
            content_type = self._classify_content_type(entry.title, clean_content, entry.link)

            # Extract artist and album information from title
            artists, album = self._extract_music_metadata(entry.title, clean_content)

            # Parse review score if this is a review
            review_score = None
            review_score_raw = None
            if content_type == ContentType.REVIEW:
                parsed_score = self.score_parser.parse_score(clean_content, source.name)
                if parsed_score:
                    review_score = parsed_score.normalized_score
                    review_score_raw = parsed_score.raw_score
                    logger.info(f"Extracted score: {review_score}/10 from '{parsed_score.raw_score}' (confidence: {parsed_score.confidence})")

            return MusicItem(
                source_id=source.id,
                url=entry.link,
                title=entry.title,
                published_date=published_date,
                content_type=content_type,
                raw_content=content,
                processed_content=clean_content,
                author=getattr(entry, 'author', None),
                artists=artists,
                album=album,
                review_score=review_score,
                review_score_raw=review_score_raw,
                is_processed=False
            )

        except Exception as e:
            logger.error(f"Error creating MusicItem from RSS entry: {str(e)}")
            return None

    def _ingest_html(self, source: Source) -> List[MusicItem]:
        """Ingest content from HTML source using web scrapers."""
        from .scrapers import SeaOfTranquilityScraper, MetalTempleScraper, UltimateClassicRockScraper

        # Map source names to scrapers
        scrapers = {
            'Sea of Tranquility': SeaOfTranquilityScraper,
            'Metal Temple': MetalTempleScraper,
            'Ultimate Classic Rock Scraper': UltimateClassicRockScraper,
        }

        scraper_class = scrapers.get(source.name)
        if not scraper_class:
            logger.warning(f"No scraper available for {source.name}")
            return []

        try:
            scraper = scraper_class()
            reviews_data = scraper.scrape_reviews(limit=50)
            scraper.close()

            items = []
            for review_data in reviews_data:
                # Check if item already exists
                existing = self._get_existing_item(review_data['url'])
                if existing:
                    logger.debug(f"Item already exists: {review_data['url']}")
                    continue

                # Create MusicItem from scraped data
                music_item = MusicItem(
                    source_id=source.id,
                    url=review_data['url'],
                    title=review_data['title'],
                    published_date=review_data['published_date'],
                    content_type=ContentType.REVIEW,  # Scrapers only get reviews
                    raw_content=review_data['content'],
                    processed_content=review_data['content'],
                    author=review_data['author'],
                    artists=[review_data['artist']] if review_data['artist'] != "Unknown Artist" else [],
                    album=review_data['album'] if review_data['album'] != "Unknown Album" else None,
                    review_score=review_data['review_score'],
                    review_score_raw=review_data['review_score_raw'],
                    is_processed=True
                )

                # Enrich with metadata from Spotify/MusicBrainz
                self._enrich_metadata(music_item)

                self.session.add(music_item)
                items.append(music_item)

            self.session.commit()
            logger.info(f"Successfully scraped {len(items)} reviews from {source.name}")
            return items

        except Exception as e:
            logger.error(f"Error scraping {source.name}: {str(e)}")
            return []

    def _get_existing_item(self, url: str) -> Optional[MusicItem]:
        """Check if an item with this URL already exists."""
        statement = select(MusicItem).where(MusicItem.url == url)
        return self.session.exec(statement).first()

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML tags from content."""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text and clean whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return ' '.join(chunk for chunk in chunks if chunk)

    def _classify_content_type(self, title: str, content: str, url: str = "") -> ContentType:
        """Classify content type based on title, content, and URL."""
        title_lower = title.lower()
        content_lower = content.lower()
        url_lower = url.lower()

        # Check URL path first (most reliable for sites like Blabbermouth and Metal Storm)
        if any(pattern in url_lower for pattern in ['/review/', '/reviews/', '/album-review', 'review.php']):
            return ContentType.REVIEW

        # Review indicators in title
        if any(word in title_lower for word in ['review', 'rating', 'score']):
            return ContentType.REVIEW

        # Interview indicators
        if any(word in title_lower for word in ['interview', 'talks', 'speaks', 'discusses']):
            return ContentType.INTERVIEW

        # Premiere indicators
        if any(word in title_lower for word in ['premiere', 'debuts', 'releases', 'unveils']):
            return ContentType.PREMIERE

        # Album of the day indicators
        if any(phrase in title_lower for phrase in ['album of the day', 'aotd']):
            return ContentType.ALBUM_OF_DAY

        # Best of indicators
        if any(phrase in title_lower for phrase in ['best of', 'top 10', 'top albums', 'best albums', 'best progressive']):
            return ContentType.BEST_OF

        # Default to news
        return ContentType.NEWS

    def _extract_music_metadata(self, title: str, content: str) -> tuple[List[str], Optional[str]]:
        """Extract artist and album information from title and content."""
        artists = []
        album = None

        # Remove "Review:" prefix common in MetalSucks titles
        title_clean = re.sub(r'^\s*Review:\s*', '', title, flags=re.IGNORECASE)
        title_clean = re.sub(r'\s*\(.*?\)\s*', ' ', title_clean).strip()
        title_lower = title_clean.lower()

        # Skip extraction for non-album content
        if any(keyword in title_lower for keyword in ['concert review', 'tour', 'announce', 'shares', 'reveals', 'premiere', 'interview', 'best of', 'best albums', 'best progressive']):
            return [], None

        # Special patterns for album reviews (order matters - more specific first!)
        album_review_patterns = [
            # "Artist Do Something on Album" (MetalSucks style)
            r'^(.+?)\s+(?:Preserve|Deliver|Remain|Blend|Channel|Masterfully|Return|Continue|Embrace|Explore)\s+.+?\s+on\s+(.+?)$',
            # "Album Title by Artist" (check first - more specific than dash patterns)
            r'^(.+?)\s+by\s+(.+?)(?:\s*[-–—]|$)',
            # "ARTIST – Album Title (Album Review)"
            r'^([A-Z\s&]+)\s*[-–—]\s*(.+?)\s*\(?album review\)?',
            # "Artist - Album Title Review"
            r'^(.+?)\s*[-–—]\s*(.+?)\s*(?:album\s+)?review',
            # "Artist: Album Title"
            r'^(.+?)\s*:\s*(.+?)$',
        ]

        # Try album review patterns first
        for pattern in album_review_patterns:
            match = re.search(pattern, title_clean, re.IGNORECASE)
            if match:
                part1, part2 = match.groups()

                # Clean up the parts
                part1 = part1.strip()
                part2 = part2.strip()

                # For "by" pattern, first part is album, second is artist
                # Check if the matched text contains "by" to determine if it's an "Album by Artist" pattern
                if ' by ' in title_clean.lower():
                    album = part1
                    artists = [part2]
                else:
                    # Standard "Artist - Album" format
                    artists = [part1]
                    album = part2

                # Clean album title - remove quotes and extra text
                album = re.sub(r'^[\'"\s]+|[\'"\s]+$', '', album)  # Remove quotes from start/end
                album = re.sub(r'\s*\(?(?:album\s+)?review\)?.*$', '', album, flags=re.IGNORECASE).strip()

                # Clean artist names - remove quotes and extra text
                if artists:
                    cleaned_artists = []
                    for artist in artists:
                        artist = re.sub(r'^[\'"\s]+|[\'"\s]+$', '', artist)  # Remove quotes from start/end
                        artist = re.sub(r'\s*[-–—]\s*\d+.*$', '', artist).strip()  # Remove " - 20th Anniversary" etc
                        artist = re.sub(r'\s*\(?(?:album\s+)?review\)?.*$', '', artist, flags=re.IGNORECASE).strip()  # Remove "Review" suffix
                        if artist and len(artist) > 1:
                            cleaned_artists.append(artist.strip())
                    artists = cleaned_artists

                break

        # If no match found, try simpler patterns
        if not artists and not album:
            simple_patterns = [
                # "Artist - Something" (but not concert/tour related)
                r'^(.+?)\s*[-–—]\s*(.+?)$',
            ]

            for pattern in simple_patterns:
                match = re.search(pattern, title_clean, re.IGNORECASE)
                if match:
                    part1, part2 = match.groups()

                    # Skip if it looks like a concert or news item
                    if any(keyword in part2.lower() for keyword in ['concert', 'tour', 'announce', 'return', 'deliver']):
                        break

                    artists = [part1.strip()]
                    album = part2.strip()
                    break

        # Clean up extracted data
        if album:
            # Remove common suffixes and prefixes
            album = re.sub(r'^[-–—"\'\s]+|[-–—"\'\s]+$', '', album)
            album = re.sub(r'\s*\(?(?:album\s+)?(?:review|rating|score)\)?.*$', '', album, flags=re.IGNORECASE).strip()

            # Reject if too short or contains non-album keywords (but allow "live" albums)
            if (not album or len(album) < 2 or
                any(keyword in album.lower() for keyword in ['concert', 'tour', 'show']) or
                (album.lower() == 'live')):  # Only reject standalone "live", not "Live 2025" etc.
                album = None

        # Clean up artist names
        if artists:
            cleaned_artists = []
            for artist in artists:
                artist = re.sub(r'^[-–—"\'\s]+|[-–—"\'\s]+$', '', artist)
                # Skip if contains location/venue information
                if (artist and len(artist.strip()) > 1 and
                    not any(keyword in artist.lower() for keyword in ['omaha', 'philadelphia', 'lauderdale', 'returns to', 'blew the roof'])):
                    cleaned_artists.append(artist.strip())
            artists = cleaned_artists

        return artists, album

    def _enrich_metadata(self, music_item: MusicItem) -> None:
        """
        Enrich MusicItem with metadata from Spotify/MusicBrainz.

        Only enriches if:
        - Item is a review with artist and album information
        - Metadata hasn't been fetched yet
        """
        # Skip if not a review or missing artist/album info
        if music_item.content_type != ContentType.REVIEW:
            return
        if not music_item.artists or not music_item.album:
            return
        # Skip if already enriched
        if music_item.metadata_source:
            return

        try:
            artist = music_item.artists[0]  # Use first artist
            album = music_item.album

            logger.info(f"Enriching metadata for {artist} - {album}")

            metadata = self.metadata_fetcher.fetch_album_metadata(artist, album)

            if metadata:
                # Update MusicItem with metadata
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
            else:
                logger.warning(f"Could not fetch metadata for {artist} - {album}")

        except Exception as e:
            logger.error(f"Error enriching metadata for {music_item.title}: {e}")