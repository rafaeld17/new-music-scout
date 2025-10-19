"""
CLI tool for extracting and backfilling genre information from existing content.
"""
import argparse
import json
from sqlmodel import Session, select
from ..core.database import get_session
from ..core.logging import logger
from ..models import MusicItem
from ..services.genre_extractor import GenreExtractor


def extract_genres_command(args):
    """Extract genres from all music items."""
    session = next(get_session())
    extractor = GenreExtractor()

    # Get all music items
    statement = select(MusicItem)
    if args.content_type:
        statement = statement.where(MusicItem.content_type == args.content_type.upper())

    items = session.exec(statement).all()
    logger.info(f"Processing {len(items)} items for genre extraction")

    updated_count = 0
    for item in items:
        # Extract genres from title and content
        content = item.processed_content or item.raw_content or ''
        genres = extractor.extract_genres(item.title, content)

        # Also check existing tags
        if item.tags:
            try:
                existing_tags = json.loads(item.tags) if isinstance(item.tags, str) else item.tags
                tag_genres = extractor.extract_from_tags(existing_tags)
                genres.extend(tag_genres)
                genres = sorted(list(set(genres)))  # Deduplicate
            except (json.JSONDecodeError, TypeError):
                pass

        if genres:
            # Update album_genres field
            item.album_genres = json.dumps(genres)
            session.add(item)
            updated_count += 1

            if args.verbose:
                print(f"[{item.content_type}] {item.title[:60]}")
                print(f"  Genres: {', '.join(genres)}")
                print()

    session.commit()
    logger.info(f"Updated {updated_count} items with genre information")
    print(f"\nExtracted genres for {updated_count}/{len(items)} items")


def main():
    parser = argparse.ArgumentParser(
        description="Extract genre information from music items"
    )

    parser.add_argument(
        '--content-type',
        choices=['review', 'news', 'interview', 'premiere', 'best_of', 'album_of_day'],
        help='Only process items of this content type'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output for each item'
    )

    args = parser.parse_args()
    extract_genres_command(args)


if __name__ == '__main__':
    main()
