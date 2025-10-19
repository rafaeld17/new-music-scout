"""
Track name extraction service.

Extracts track/single names from content titles for playlist building.
"""

import re
from typing import List, Optional


class TrackExtractor:
    """Extract track names from content titles."""

    # Patterns for track names in quotes
    QUOTED_PATTERNS = [
        r"['\"]([^'\"]+)['\"]",  # Single or double quotes
        r"�([^�]+)�",  # Replacement character from encoding issues
        r"'([^']+)'",  # Smart single quotes (U+2018, U+2019)
        r"\u201C([^\u201D]+)\u201D",  # Smart double quotes (U+201C, U+201D)
    ]

    # Keywords indicating track/single content
    TRACK_KEYWORDS = [
        "single",
        "video",
        "premiere",
        "releases",
        "unveils",
        "shares",
        "drops",
        "animated video",
        "music video",
        "lyric video",
    ]

    def extract_track_name(self, title: str) -> Optional[str]:
        """
        Extract a track name from a title.

        Looks for quoted strings in titles that mention singles, videos, or premieres.

        Args:
            title: The content title

        Returns:
            Extracted track name or None
        """
        # Check if title contains track-related keywords
        title_lower = title.lower()
        has_track_keyword = any(keyword in title_lower for keyword in self.TRACK_KEYWORDS)

        if not has_track_keyword:
            return None

        # Try each quoted pattern
        for pattern in self.QUOTED_PATTERNS:
            matches = re.findall(pattern, title)
            if matches:
                # Return the first quoted string (usually the track name)
                track_name = matches[0].strip()

                # Remove trailing punctuation (comma, period, etc)
                track_name = track_name.rstrip(',.;:!?')

                # Filter out common false positives
                if self._is_valid_track_name(track_name):
                    return track_name

        return None

    def extract_all_tracks(self, title: str) -> List[str]:
        """
        Extract all potential track names from a title.

        Useful for track-by-track reviews or multi-track premieres.

        Args:
            title: The content title

        Returns:
            List of track names (may be empty)
        """
        tracks = []

        # Extract all quoted strings
        for pattern in self.QUOTED_PATTERNS:
            matches = re.findall(pattern, title)
            for match in matches:
                track_name = match.strip()
                if self._is_valid_track_name(track_name):
                    tracks.append(track_name)

        return tracks

    def _is_valid_track_name(self, track_name: str) -> bool:
        """
        Validate that a string looks like a track name.

        Filters out common false positives like album names in quotes.

        Args:
            track_name: The potential track name

        Returns:
            True if it looks like a valid track name
        """
        # Minimum length check
        if len(track_name) < 2:
            return False

        # Maximum length check (most track names are < 100 chars)
        if len(track_name) > 100:
            return False

        # Filter out common false positives
        false_positive_keywords = [
            "featuring",
            "ft.",
            "feat.",
            "members",
            "ex-",
            "former",
        ]

        track_lower = track_name.lower()
        if any(keyword in track_lower for keyword in false_positive_keywords):
            return False

        return True


def get_track_extractor() -> TrackExtractor:
    """Get a track extractor instance."""
    return TrackExtractor()
