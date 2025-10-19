"""
Service for fetching album metadata from external APIs (MusicBrainz, Cover Art Archive).
"""
import requests
import logging
from typing import Optional, Dict, List
from urllib.parse import quote

logger = logging.getLogger(__name__)

# MusicBrainz API endpoint
MUSICBRAINZ_API = "https://musicbrainz.org/ws/2"
COVER_ART_ARCHIVE_API = "https://coverartarchive.org"

# User agent required by MusicBrainz
USER_AGENT = "NewMusicScout/1.0 (personal music tracker)"


class MetadataFetcher:
    """Fetches album metadata from MusicBrainz and Cover Art Archive."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def search_album(self, artist: str, album: str) -> Optional[Dict]:
        """
        Search for an album on MusicBrainz.

        Args:
            artist: Artist name
            album: Album name

        Returns:
            Dictionary with album metadata or None if not found
        """
        try:
            # Build search query
            query = f'artist:"{artist}" AND release:"{album}"'

            # Search for the release
            url = f"{MUSICBRAINZ_API}/release"
            params = {
                "query": query,
                "fmt": "json",
                "limit": 1
            }

            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            if not data.get("releases"):
                logger.info(f"No MusicBrainz results for {artist} - {album}")
                return None

            release = data["releases"][0]

            # Extract basic info
            result = {
                "musicbrainz_id": release.get("id"),
                "title": release.get("title"),
                "artist": release.get("artist-credit", [{}])[0].get("artist", {}).get("name"),
                "release_date": release.get("date"),
                "genres": [],
                "cover_art_url": None
            }

            # Fetch genres from the release
            if release.get("id"):
                genres = self._fetch_genres(release["id"])

                # If no release-level genres, try artist-level genres
                if not genres and release.get("artist-credit"):
                    artist_id = release["artist-credit"][0].get("artist", {}).get("id")
                    if artist_id:
                        genres = self._fetch_artist_genres(artist_id)

                if genres:
                    result["genres"] = genres

                # Fetch cover art
                cover_url = self._fetch_cover_art(release["id"])
                if cover_url:
                    result["cover_art_url"] = cover_url

            logger.info(f"Found metadata for {artist} - {album}: {result}")
            return result

        except requests.RequestException as e:
            logger.error(f"Error fetching metadata for {artist} - {album}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching metadata: {e}")
            return None

    def _fetch_genres(self, release_id: str) -> List[str]:
        """
        Fetch genres/tags for a release from MusicBrainz.

        Args:
            release_id: MusicBrainz release ID

        Returns:
            List of genre names
        """
        try:
            url = f"{MUSICBRAINZ_API}/release/{release_id}"
            params = {
                "inc": "tags",
                "fmt": "json"
            }

            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()
            tags = data.get("tags", [])

            # Get top 5 tags with count > 0
            genres = [
                tag["name"]
                for tag in sorted(tags, key=lambda x: x.get("count", 0), reverse=True)[:5]
                if tag.get("count", 0) > 0
            ]

            return genres

        except Exception as e:
            logger.debug(f"Error fetching genres for release {release_id}: {e}")
            return []

    def _fetch_artist_genres(self, artist_id: str) -> List[str]:
        """
        Fetch genres/tags for an artist from MusicBrainz.

        Args:
            artist_id: MusicBrainz artist ID

        Returns:
            List of genre names
        """
        try:
            url = f"{MUSICBRAINZ_API}/artist/{artist_id}"
            params = {
                "inc": "tags",
                "fmt": "json"
            }

            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()
            tags = data.get("tags", [])

            # Get top 5 tags with count > 0
            genres = [
                tag["name"]
                for tag in sorted(tags, key=lambda x: x.get("count", 0), reverse=True)[:5]
                if tag.get("count", 0) > 0
            ]

            return genres

        except Exception as e:
            logger.debug(f"Error fetching artist genres for artist {artist_id}: {e}")
            return []

    def _fetch_cover_art(self, release_id: str) -> Optional[str]:
        """
        Fetch cover art URL from Cover Art Archive.

        Args:
            release_id: MusicBrainz release ID

        Returns:
            URL to cover art image or None
        """
        try:
            url = f"{COVER_ART_ARCHIVE_API}/release/{release_id}"

            response = self.session.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()

            # Get the front cover image (small thumbnail)
            images = data.get("images", [])
            for image in images:
                if image.get("front", False):
                    # Use the small thumbnail (250px)
                    return image.get("thumbnails", {}).get("small") or image.get("image")

            # If no front cover, use first image
            if images:
                return images[0].get("thumbnails", {}).get("small") or images[0].get("image")

            return None

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"No cover art found for release {release_id}")
            else:
                logger.debug(f"Error fetching cover art for release {release_id}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error fetching cover art: {e}")
            return None


# Global instance
_metadata_fetcher = None


def get_metadata_fetcher() -> MetadataFetcher:
    """Get or create the global MetadataFetcher instance."""
    global _metadata_fetcher
    if _metadata_fetcher is None:
        _metadata_fetcher = MetadataFetcher()
    return _metadata_fetcher
