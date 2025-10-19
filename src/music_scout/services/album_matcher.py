"""
Album matching service for identifying the same albums across different sources.
"""
import re
from typing import Optional, List, Tuple
from difflib import SequenceMatcher
from sqlmodel import Session, select

from ..models import Album, Artist, MusicItem
from ..core.logging import logger


class AlbumMatcher:
    """Service for matching albums across different sources using fuzzy matching."""

    def __init__(self, session: Session):
        self.session = session
        # Matching thresholds
        self.exact_match_threshold = 0.95
        self.strong_match_threshold = 0.85
        self.weak_match_threshold = 0.70

    def normalize_string(self, text: str) -> str:
        """Normalize a string for comparison."""
        if not text:
            return ""

        # Convert to lowercase
        normalized = text.lower()

        # Remove common punctuation and special characters
        normalized = re.sub(r'[\'\".,!?:;()\[\]{}]', '', normalized)

        # Replace special dashes/hyphens with standard dash
        normalized = re.sub(r'[–—―‐‑]', '-', normalized)

        # Remove "the" at the beginning
        normalized = re.sub(r'^the\s+', '', normalized)

        # Remove common suffixes
        normalized = re.sub(r'\s*\(.*?\)\s*', ' ', normalized)  # Remove parentheses content
        normalized = re.sub(r'\s*\[.*?\]\s*', ' ', normalized)  # Remove bracket content

        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings using sequence matching."""
        if not str1 or not str2:
            return 0.0

        # Exact match
        if str1 == str2:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, str1, str2).ratio()

    def match_artist(
        self, artist_name: str, create_if_missing: bool = True
    ) -> Optional[Artist]:
        """
        Find or create an artist by name using fuzzy matching.

        Args:
            artist_name: The artist name to match
            create_if_missing: If True, create a new artist if no match found

        Returns:
            Artist object or None if not found and create_if_missing=False
        """
        if not artist_name:
            return None

        normalized_name = self.normalize_string(artist_name)

        # Try exact match first
        statement = select(Artist).where(Artist.normalized_name == normalized_name)
        existing_artist = self.session.exec(statement).first()

        if existing_artist:
            logger.debug(
                f"Exact artist match: '{artist_name}' -> {existing_artist.name}"
            )
            return existing_artist

        # Try fuzzy matching against all artists
        statement = select(Artist)
        all_artists = self.session.exec(statement).all()

        best_match = None
        best_score = 0.0

        for artist in all_artists:
            score = self.similarity_score(normalized_name, artist.normalized_name)
            if score > best_score and score >= self.strong_match_threshold:
                best_score = score
                best_match = artist

        if best_match:
            logger.info(
                f"Fuzzy artist match: '{artist_name}' -> {best_match.name} (score: {best_score:.2f})"
            )
            return best_match

        # Create new artist if requested
        if create_if_missing:
            new_artist = Artist(name=artist_name, normalized_name=normalized_name)
            self.session.add(new_artist)
            self.session.commit()
            self.session.refresh(new_artist)
            logger.info(f"Created new artist: {artist_name}")
            return new_artist

        return None

    def match_album(
        self,
        album_title: str,
        artist_name: str,
        create_if_missing: bool = True,
        release_year: Optional[int] = None,
    ) -> Optional[Album]:
        """
        Find or create an album by title and artist using fuzzy matching.

        Args:
            album_title: The album title to match
            artist_name: The artist name to match
            create_if_missing: If True, create a new album if no match found
            release_year: Optional release year for better matching

        Returns:
            Album object or None if not found and create_if_missing=False
        """
        if not album_title or not artist_name:
            return None

        # First, match the artist
        artist = self.match_artist(artist_name, create_if_missing=create_if_missing)
        if not artist:
            return None

        normalized_title = self.normalize_string(album_title)

        # Try exact match first
        statement = (
            select(Album)
            .where(Album.artist_id == artist.id)
            .where(Album.normalized_title == normalized_title)
        )
        existing_album = self.session.exec(statement).first()

        if existing_album:
            logger.debug(
                f"Exact album match: '{album_title}' by {artist_name} -> {existing_album.title}"
            )
            return existing_album

        # Try fuzzy matching against albums by this artist
        statement = select(Album).where(Album.artist_id == artist.id)
        artist_albums = self.session.exec(statement).all()

        best_match = None
        best_score = 0.0

        for album in artist_albums:
            score = self.similarity_score(normalized_title, album.normalized_title)

            # Bonus points for matching release year
            if release_year and album.release_year and album.release_year == release_year:
                score += 0.1

            if score > best_score and score >= self.strong_match_threshold:
                best_score = score
                best_match = album

        if best_match:
            logger.info(
                f"Fuzzy album match: '{album_title}' by {artist_name} -> {best_match.title} (score: {best_score:.2f})"
            )
            return best_match

        # Create new album if requested
        if create_if_missing:
            new_album = Album(
                title=album_title,
                normalized_title=normalized_title,
                artist_id=artist.id,
                release_year=release_year,
            )
            self.session.add(new_album)
            self.session.commit()
            self.session.refresh(new_album)
            logger.info(f"Created new album: {album_title} by {artist_name}")
            return new_album

        return None

    def match_music_item_to_album(
        self, music_item: MusicItem, create_if_missing: bool = True
    ) -> Optional[Album]:
        """
        Match a MusicItem to an Album based on extracted metadata.

        Args:
            music_item: The MusicItem to match
            create_if_missing: If True, create new Album/Artist if no match found

        Returns:
            Album object or None if matching fails
        """
        # Skip if no album or artist information
        if not music_item.album or not music_item.artists:
            return None

        # Use the first artist for matching (primary artist)
        artist_name = music_item.artists[0] if music_item.artists else None
        if not artist_name:
            return None

        # Extract release year if available from published date or title
        release_year = None
        if music_item.published_date:
            release_year = music_item.published_date.year

        return self.match_album(
            album_title=music_item.album,
            artist_name=artist_name,
            create_if_missing=create_if_missing,
            release_year=release_year,
        )

    def find_similar_albums(
        self, album_title: str, artist_name: str, limit: int = 5
    ) -> List[Tuple[Album, float]]:
        """
        Find similar albums based on fuzzy matching.

        Args:
            album_title: The album title to search for
            artist_name: The artist name
            limit: Maximum number of results

        Returns:
            List of (Album, similarity_score) tuples, sorted by score descending
        """
        normalized_title = self.normalize_string(album_title)
        normalized_artist = self.normalize_string(artist_name)

        # Get all albums
        statement = select(Album)
        all_albums = self.session.exec(statement).all()

        # Calculate similarity scores
        matches = []
        for album in all_albums:
            # Get artist for this album
            artist = self.session.get(Artist, album.artist_id)
            if not artist:
                continue

            # Calculate combined score (album + artist)
            album_score = self.similarity_score(normalized_title, album.normalized_title)
            artist_score = self.similarity_score(normalized_artist, artist.normalized_name)

            # Weighted average (album title is more important)
            combined_score = (album_score * 0.7) + (artist_score * 0.3)

            if combined_score >= self.weak_match_threshold:
                matches.append((album, combined_score))

        # Sort by score descending and limit results
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
