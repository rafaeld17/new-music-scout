"""
Spotify API client for metadata enrichment.

Uses Client Credentials flow for album/artist metadata.
No user authentication required for metadata-only operations.
"""
import time
import logging
from typing import Optional, Dict, List
import requests
from ..core.config import settings

logger = logging.getLogger(__name__)


class SpotifyClient:
    """
    Spotify API client using Client Credentials flow.

    This client is used for metadata enrichment (album/artist info)
    and does not require user authentication.
    """

    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        Initialize Spotify client.

        Args:
            client_id: Spotify app client ID (defaults to settings)
            client_secret: Spotify app client secret (defaults to settings)
        """
        self.client_id = client_id or settings.spotify_client_id
        self.client_secret = client_secret or settings.spotify_client_secret

        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify credentials not configured. Check .env file.")

        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.session = requests.Session()

    def _get_access_token(self) -> str:
        """
        Get or refresh access token using client credentials flow.

        Returns:
            Valid access token
        """
        # Return cached token if still valid
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        # Request new token
        logger.info("Requesting new Spotify access token")

        auth_url = "https://accounts.spotify.com/api/token"
        auth_data = {
            "grant_type": "client_credentials"
        }

        try:
            response = requests.post(
                auth_url,
                data=auth_data,
                auth=(self.client_id, self.client_secret),
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Subtract 60 seconds for safety margin
            self.token_expires_at = time.time() + token_data["expires_in"] - 60

            logger.info("Successfully obtained Spotify access token")
            return self.access_token

        except requests.RequestException as e:
            logger.error(f"Error obtaining Spotify access token: {e}")
            raise

    def search_album(self, artist: str, album: str) -> Optional[Dict]:
        """
        Search for an album on Spotify.

        Args:
            artist: Artist name
            album: Album name

        Returns:
            Dictionary with album metadata or None if not found
        """
        token = self._get_access_token()

        search_url = "https://api.spotify.com/v1/search"
        params = {
            "q": f"artist:{artist} album:{album}",
            "type": "album",
            "limit": 1
        }
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = self.session.get(
                search_url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            albums = data.get("albums", {}).get("items", [])

            if not albums:
                logger.info(f"No Spotify results for {artist} - {album}")
                return None

            album_data = albums[0]

            # Extract metadata
            result = {
                "spotify_album_id": album_data["id"],
                "spotify_artist_id": album_data["artists"][0]["id"],
                "title": album_data["name"],
                "artist": album_data["artists"][0]["name"],
                "release_date": album_data.get("release_date"),
                "album_type": album_data.get("album_type"),  # album, single, compilation
                "cover_art_url": album_data["images"][0]["url"] if album_data.get("images") else None,
                "total_tracks": album_data.get("total_tracks"),
                "label": album_data.get("label"),
                "popularity": album_data.get("popularity", 0),  # 0-100
                "genres": []  # Need to fetch from artist endpoint
            }

            logger.info(f"Found Spotify album: {artist} - {album}")
            return result

        except requests.RequestException as e:
            logger.error(f"Error searching Spotify for {artist} - {album}: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Spotify response for {artist} - {album}: {e}")
            return None

    def get_artist(self, artist_id: str) -> Optional[Dict]:
        """
        Get artist metadata including genres.

        Args:
            artist_id: Spotify artist ID

        Returns:
            Dictionary with artist metadata or None if error
        """
        token = self._get_access_token()

        artist_url = f"https://api.spotify.com/v1/artists/{artist_id}"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = self.session.get(
                artist_url,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            artist_data = response.json()

            result = {
                "spotify_id": artist_data["id"],
                "name": artist_data["name"],
                "genres": artist_data.get("genres", []),
                "popularity": artist_data.get("popularity", 0),  # 0-100
                "followers": artist_data.get("followers", {}).get("total", 0),
                "image_url": artist_data["images"][0]["url"] if artist_data.get("images") else None
            }

            logger.info(f"Found Spotify artist: {artist_data['name']} with {len(result['genres'])} genres")
            return result

        except requests.RequestException as e:
            logger.error(f"Error fetching Spotify artist {artist_id}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Error parsing Spotify artist response: {e}")
            return None

    def get_album_with_genres(self, artist: str, album: str) -> Optional[Dict]:
        """
        Search for album and enrich with artist genres.

        This is a convenience method that combines album search with artist lookup
        to get complete metadata including genres.

        Args:
            artist: Artist name
            album: Album name

        Returns:
            Dictionary with complete album and artist metadata
        """
        # Search for album
        album_data = self.search_album(artist, album)
        if not album_data:
            return None

        # Get artist genres
        artist_id = album_data.get("spotify_artist_id")
        if artist_id:
            artist_data = self.get_artist(artist_id)
            if artist_data:
                album_data["genres"] = artist_data["genres"]
                album_data["artist_popularity"] = artist_data["popularity"]
                album_data["artist_followers"] = artist_data["followers"]

        return album_data


# Global instance
_spotify_client: Optional[SpotifyClient] = None


def get_spotify_client() -> SpotifyClient:
    """Get or create the global Spotify client instance."""
    global _spotify_client
    if _spotify_client is None:
        _spotify_client = SpotifyClient()
    return _spotify_client
