"""
Enhanced metadata fetcher with cascading API strategy.

Tries Spotify first (best coverage for modern releases),
falls back to MusicBrainz for older or obscure albums.
"""
import logging
from typing import Optional, Dict
from .spotify_client import get_spotify_client
from .metadata_fetcher import get_metadata_fetcher

logger = logging.getLogger(__name__)


class EnhancedMetadataFetcher:
    """
    Metadata fetcher with intelligent cascading between multiple APIs.

    Strategy:
    1. Try Spotify first (best coverage for 2020+ releases)
    2. Fall back to MusicBrainz if Spotify fails
    3. Return best available metadata with source tracking
    """

    def __init__(self):
        """Initialize with Spotify and MusicBrainz clients."""
        self.spotify_client = get_spotify_client()
        self.musicbrainz_client = get_metadata_fetcher()
        self._cache = {}  # Simple in-memory cache

    def fetch_album_metadata(self, artist: str, album: str) -> Optional[Dict]:
        """
        Fetch album metadata with cascading API strategy.

        Args:
            artist: Artist name
            album: Album name

        Returns:
            Dictionary with unified metadata format, or None if all sources fail
        """
        # Check cache first
        cache_key = f"{artist.lower()}::{album.lower()}"
        if cache_key in self._cache:
            logger.debug(f"Cache hit for {artist} - {album}")
            return self._cache[cache_key]

        logger.info(f"Fetching metadata for {artist} - {album}")

        # Try Spotify first
        spotify_data = self._fetch_from_spotify(artist, album)
        if spotify_data and self._has_sufficient_data(spotify_data):
            result = self._normalize_spotify_metadata(spotify_data)
            self._cache[cache_key] = result
            return result

        # Fall back to MusicBrainz
        logger.info(f"Spotify failed for {artist} - {album}, trying MusicBrainz")
        mb_data = self._fetch_from_musicbrainz(artist, album)
        if mb_data:
            result = self._normalize_musicbrainz_metadata(mb_data)
            self._cache[cache_key] = result
            return result

        # Both failed
        logger.warning(f"All metadata sources failed for {artist} - {album}")
        return None

    def _fetch_from_spotify(self, artist: str, album: str) -> Optional[Dict]:
        """
        Fetch metadata from Spotify.

        Returns:
            Raw Spotify data or None
        """
        try:
            return self.spotify_client.get_album_with_genres(artist, album)
        except Exception as e:
            logger.error(f"Spotify fetch error for {artist} - {album}: {e}")
            return None

    def _fetch_from_musicbrainz(self, artist: str, album: str) -> Optional[Dict]:
        """
        Fetch metadata from MusicBrainz.

        Returns:
            Raw MusicBrainz data or None
        """
        try:
            return self.musicbrainz_client.search_album(artist, album)
        except Exception as e:
            logger.error(f"MusicBrainz fetch error for {artist} - {album}: {e}")
            return None

    def _has_sufficient_data(self, data: Dict) -> bool:
        """
        Check if metadata has sufficient information to be useful.

        Args:
            data: Metadata dictionary

        Returns:
            True if has useful data (genres or IDs)
        """
        if not data:
            return False

        # Must have at least artist/album names
        if not data.get("artist") or not data.get("title"):
            return False

        # Prefer data with genres or IDs
        has_genres = bool(data.get("genres"))
        has_ids = bool(data.get("spotify_album_id") or data.get("musicbrainz_id"))

        return has_genres or has_ids

    def _normalize_spotify_metadata(self, data: Dict) -> Dict:
        """
        Normalize Spotify metadata to unified format.

        Args:
            data: Raw Spotify metadata

        Returns:
            Normalized metadata dictionary
        """
        return {
            # Source tracking
            "metadata_source": "spotify",
            "confidence": 0.95,  # High confidence for Spotify

            # IDs
            "spotify_album_id": data.get("spotify_album_id"),
            "spotify_artist_id": data.get("spotify_artist_id"),
            "musicbrainz_id": None,

            # Basic info
            "artist": data.get("artist"),
            "album": data.get("title"),
            "release_date": data.get("release_date"),
            "album_type": data.get("album_type"),  # album, single, EP

            # Rich metadata
            "genres": data.get("genres", []),
            "cover_art_url": data.get("cover_art_url"),
            "label": data.get("label"),

            # Popularity metrics
            "artist_popularity": data.get("artist_popularity"),
            "album_popularity": data.get("popularity"),
            "artist_followers": data.get("artist_followers"),

            # Additional
            "total_tracks": data.get("total_tracks")
        }

    def _normalize_musicbrainz_metadata(self, data: Dict) -> Dict:
        """
        Normalize MusicBrainz metadata to unified format.

        Args:
            data: Raw MusicBrainz metadata

        Returns:
            Normalized metadata dictionary
        """
        return {
            # Source tracking
            "metadata_source": "musicbrainz",
            "confidence": 0.80,  # Lower confidence than Spotify

            # IDs
            "spotify_album_id": None,
            "spotify_artist_id": None,
            "musicbrainz_id": data.get("musicbrainz_id"),

            # Basic info
            "artist": data.get("artist"),
            "album": data.get("title"),
            "release_date": data.get("release_date"),
            "album_type": None,

            # Rich metadata (MusicBrainz has limited data)
            "genres": data.get("genres", []),
            "cover_art_url": data.get("cover_art_url"),
            "label": None,

            # Popularity metrics (not available in MusicBrainz)
            "artist_popularity": None,
            "album_popularity": None,
            "artist_followers": None,

            # Additional
            "total_tracks": None
        }

    def fetch_artist_metadata(self, artist: str) -> Optional[Dict]:
        """
        Fetch artist metadata (primarily for genres).

        Args:
            artist: Artist name

        Returns:
            Dictionary with artist metadata or None
        """
        # For now, we primarily need this for Spotify
        try:
            # Search for artist's most recent album to get artist ID
            # This is a workaround since we need an artist ID
            logger.info(f"Fetching artist metadata for {artist}")

            # Try to get artist info via Spotify search
            search_result = self.spotify_client.get_album_with_genres(artist, artist)
            if search_result and search_result.get("spotify_artist_id"):
                artist_id = search_result["spotify_artist_id"]
                artist_data = self.spotify_client.get_artist(artist_id)
                if artist_data:
                    return {
                        "metadata_source": "spotify",
                        "spotify_artist_id": artist_data["spotify_id"],
                        "name": artist_data["name"],
                        "genres": artist_data["genres"],
                        "popularity": artist_data["popularity"],
                        "followers": artist_data["followers"]
                    }

            logger.warning(f"Could not fetch artist metadata for {artist}")
            return None

        except Exception as e:
            logger.error(f"Error fetching artist metadata for {artist}: {e}")
            return None

    def clear_cache(self):
        """Clear the metadata cache."""
        self._cache.clear()
        logger.info("Metadata cache cleared")


# Global instance
_enhanced_fetcher: Optional[EnhancedMetadataFetcher] = None


def get_enhanced_metadata_fetcher() -> EnhancedMetadataFetcher:
    """Get or create the global EnhancedMetadataFetcher instance."""
    global _enhanced_fetcher
    if _enhanced_fetcher is None:
        _enhanced_fetcher = EnhancedMetadataFetcher()
    return _enhanced_fetcher
