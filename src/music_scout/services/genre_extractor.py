"""
Service for extracting genre tags from music item content.
"""
import re
from typing import List, Set


class GenreExtractor:
    """Extracts genre information from titles and content."""

    # Primary genre keywords (exact matches)
    GENRES = {
        'progressive rock': ['progressive rock', 'prog rock', 'prog-rock'],
        'progressive metal': ['progressive metal', 'prog metal', 'prog-metal'],
        'power metal': ['power metal'],
        'death metal': ['death metal'],
        'black metal': ['black metal'],
        'doom metal': ['doom metal', 'stoner doom', 'funeral doom'],
        'thrash metal': ['thrash metal', 'thrash'],
        'heavy metal': ['heavy metal', 'traditional metal', 'trad metal'],
        'metalcore': ['metalcore', 'metal-core'],
        'deathcore': ['deathcore'],
        'jazz fusion': ['jazz fusion', 'fusion'],
        'hard rock': ['hard rock'],
        'classic rock': ['classic rock'],
        'blues rock': ['blues rock'],
        'post-rock': ['post-rock', 'post rock'],
        'post-metal': ['post-metal', 'post metal'],
        'folk metal': ['folk metal'],
        'symphonic metal': ['symphonic metal'],
        'gothic metal': ['gothic metal', 'goth metal'],
        'industrial metal': ['industrial metal'],
        'alternative metal': ['alternative metal', 'alt-metal'],
        'groove metal': ['groove metal'],
        'sludge metal': ['sludge metal', 'sludge'],
        'experimental': ['experimental', 'avant-garde'],
        'instrumental': ['instrumental'],
        'atmospheric': ['atmospheric'],
    }

    # Secondary descriptors (can appear alongside genres)
    DESCRIPTORS = [
        'melodic', 'technical', 'brutal', 'atmospheric', 'epic',
        'symphonic', 'blackened', 'old-school', 'modern', 'classic'
    ]

    def __init__(self):
        # Create lowercase mapping for case-insensitive matching
        self.genre_patterns = {}
        for main_genre, variants in self.GENRES.items():
            for variant in variants:
                self.genre_patterns[variant.lower()] = main_genre

    def extract_genres(self, title: str, content: str = '') -> List[str]:
        """
        Extract genre tags from title and content.

        Args:
            title: The title of the music item
            content: The content/description text

        Returns:
            List of extracted genre tags (deduplicated)
        """
        text = f"{title} {content}".lower()
        found_genres: Set[str] = set()

        # Look for genre keywords
        for pattern, main_genre in self.genre_patterns.items():
            if pattern in text:
                found_genres.add(main_genre)

        # Generic "metal" classification if no specific metal subgenre found
        if 'metal' in text and not any('metal' in g for g in found_genres):
            # Check if it's a band name (avoid "Metallica" matches)
            if not re.search(r'\bmetallica\b', text, re.IGNORECASE):
                found_genres.add('metal')

        # Generic "rock" classification
        if 'rock' in text and not any('rock' in g for g in found_genres):
            # Avoid matching "rock and roll" or proper nouns
            if not re.search(r'\brock\s+(and|&|n)\s+roll\b', text, re.IGNORECASE):
                if re.search(r'\brock\b', text, re.IGNORECASE):
                    found_genres.add('rock')

        return sorted(list(found_genres))

    def extract_from_tags(self, tags: List[str]) -> List[str]:
        """
        Extract genres from existing tag list.

        Args:
            tags: List of existing tags

        Returns:
            List of genre tags found in the tag list
        """
        found_genres: Set[str] = set()

        for tag in tags:
            tag_lower = tag.lower()
            for pattern, main_genre in self.genre_patterns.items():
                if pattern in tag_lower:
                    found_genres.add(main_genre)

        return sorted(list(found_genres))
