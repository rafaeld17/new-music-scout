"""
CLI tool for testing content ingestion.
"""
import argparse
import sys
from typing import Optional

from sqlmodel import Session

from ..core.database import engine, create_db_and_tables
from ..core.logging import logger
from ..services import IngestionService, SourceManager
from ..models import Source


def ingest_from_source(source_name: Optional[str] = None, source_id: Optional[int] = None, reviews_only: bool = False) -> bool:
    """Ingest content from a specific source or all sources."""
    create_db_and_tables()

    with Session(engine) as session:
        source_manager = SourceManager(session)
        ingestion_service = IngestionService(session)

        # Create default sources if they don't exist
        source_manager.create_default_sources()

        if source_name or source_id:
            # Ingest from specific source
            if source_name:
                source = source_manager.get_source_by_name(source_name)
                if not source:
                    logger.error(f"Source not found: {source_name}")
                    return False
            else:
                source = session.get(Source, source_id)
                if not source:
                    logger.error(f"Source not found with ID: {source_id}")
                    return False

            logger.info(f"Ingesting from source: {source.name}")
            items = ingestion_service.ingest_from_source(source)

            # Filter for reviews only if requested
            if reviews_only:
                from ..models import ContentType
                review_items = [item for item in items if item.content_type == ContentType.REVIEW]
                logger.info(f"Ingested {len(items)} total items, {len(review_items)} reviews from {source.name}")
                _display_items(review_items, reviews_only=True)
            else:
                logger.info(f"Ingested {len(items)} items from {source.name}")
                _display_items(items)

        else:
            # Ingest from all enabled sources
            sources = source_manager.get_enabled_sources()
            total_items = 0
            total_reviews = 0

            for source in sources:
                logger.info(f"Ingesting from source: {source.name}")
                items = ingestion_service.ingest_from_source(source)
                total_items += len(items)

                if reviews_only:
                    from ..models import ContentType
                    review_items = [item for item in items if item.content_type == ContentType.REVIEW]
                    total_reviews += len(review_items)
                    logger.info(f"Ingested {len(items)} total items, {len(review_items)} reviews from {source.name}")
                    _display_items(review_items, reviews_only=True)
                else:
                    logger.info(f"Ingested {len(items)} items from {source.name}")

            if reviews_only:
                logger.info(f"Total items ingested: {total_items}, Reviews: {total_reviews}")
            else:
                logger.info(f"Total items ingested: {total_items}")

    return True


def _display_items(items, reviews_only: bool = False):
    """Display items in a formatted way."""
    if not items:
        return

    print(f"\n{'Reviews' if reviews_only else 'Items'} Found:")
    print("-" * 80)

    for item in items[:10]:  # Show first 10 items
        # Format content type
        content_type = item.content_type.value if hasattr(item.content_type, 'value') else str(item.content_type)

        # Extract artist and album info
        artists = ", ".join(item.artists) if item.artists else "Unknown"
        album = item.album if item.album else "Unknown"

        # Safe string formatting to avoid encoding issues
        try:
            title = item.title[:60] + "..." if len(item.title) > 60 else item.title
            print(f"[{content_type}] {title}")
            print(f"  Artist: {artists} | Album: {album}")
            print(f"  Published: {item.published_date.strftime('%Y-%m-%d') if item.published_date else 'Unknown'}")
        except UnicodeEncodeError:
            # Fallback for encoding issues
            print(f"[{content_type}] [Title contains special characters]")
            print(f"  Artist: {artists} | Album: {album}")
            print(f"  Published: {item.published_date.strftime('%Y-%m-%d') if item.published_date else 'Unknown'}")
        print()

    if len(items) > 10:
        print(f"... and {len(items) - 10} more items")


def list_sources():
    """List all configured sources."""
    create_db_and_tables()

    with Session(engine) as session:
        from sqlmodel import select, func
        from ..models import MusicItem

        source_manager = SourceManager(session)
        sources = source_manager.get_enabled_sources()

        print("\nConfigured Sources:")
        print("-" * 60)
        for source in sources:
            # Use ASCII characters to avoid encoding issues
            status = "YES" if source.enabled else "NO"
            health = f"{source.health_score:.1f}"

            # Get item count for this source
            count = session.exec(select(func.count(MusicItem.id)).where(MusicItem.source_id == source.id)).one()

            try:
                print(f"{status:3s} {source.id:2d} | {source.name:25s} | {source.source_type:4s} | Items: {count:3d} | Health: {health} | Weight: {source.weight}")
            except UnicodeEncodeError:
                # Fallback for any remaining encoding issues
                print(f"{status:3s} {source.id:2d} | [Source name contains special chars] | {source.source_type:4s} | Items: {count:3d} | Health: {health} | Weight: {source.weight}")

        print(f"\nTotal: {len(sources)} sources")


def setup_sources():
    """Set up default sources."""
    create_db_and_tables()

    with Session(engine) as session:
        source_manager = SourceManager(session)
        created_sources = source_manager.create_default_sources()

        if created_sources:
            print(f"Created {len(created_sources)} new sources:")
            for source in created_sources:
                print(f"  - {source.name} ({source.source_type})")
        else:
            print("All default sources already exist.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Music Scout Ingestion CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest content from sources')
    ingest_parser.add_argument('--source', '-s', help='Source name to ingest from')
    ingest_parser.add_argument('--source-id', '-i', type=int, help='Source ID to ingest from')
    ingest_parser.add_argument('--reviews-only', '-r', action='store_true', help='Show only review content')

    # List command
    subparsers.add_parser('list', help='List all configured sources')

    # Setup command
    subparsers.add_parser('setup', help='Set up default sources')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test specific functionality')
    test_parser.add_argument('--rss', help='Test RSS parsing for a URL')
    test_parser.add_argument('--score-parsing', action='store_true', help='Test score parsing on existing reviews')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'ingest':
            success = ingest_from_source(args.source, args.source_id, args.reviews_only)
            sys.exit(0 if success else 1)

        elif args.command == 'list':
            list_sources()

        elif args.command == 'setup':
            setup_sources()

        elif args.command == 'test':
            if args.rss:
                test_rss_parsing(args.rss)
            elif args.score_parsing:
                test_score_parsing()
            else:
                print("Please specify --rss URL to test or --score-parsing")

    except Exception as e:
        logger.error(f"CLI error: {str(e)}")
        sys.exit(1)


def test_rss_parsing(url: str):
    """Test RSS parsing for a specific URL."""
    import feedparser

    print(f"Testing RSS feed: {url}")
    print("-" * 60)

    try:
        feed = feedparser.parse(url)

        print(f"Feed title: {feed.feed.get('title', 'N/A')}")
        print(f"Feed description: {feed.feed.get('description', 'N/A')}")
        print(f"Number of entries: {len(feed.entries)}")
        print(f"Bozo (has errors): {feed.bozo}")

        if feed.entries:
            print("\nFirst 3 entries:")
            for i, entry in enumerate(feed.entries[:3]):
                print(f"\n{i+1}. {entry.get('title', 'No title')}")
                print(f"   Link: {entry.get('link', 'No link')}")
                print(f"   Published: {entry.get('published', 'No date')}")
                print(f"   Summary: {entry.get('summary', 'No summary')[:100]}...")

    except Exception as e:
        print(f"Error parsing RSS feed: {str(e)}")


def test_score_parsing():
    """Test score parsing on existing reviews."""
    create_db_and_tables()

    with Session(engine) as session:
        from sqlmodel import select
        from ..models import MusicItem, ContentType, Source
        from ..services.score_parser import ScoreParser

        parser = ScoreParser()

        # Get some reviews to test
        query = select(MusicItem, Source).join(Source).where(MusicItem.content_type == ContentType.REVIEW).limit(10)
        results = session.exec(query).all()

        print("\nTesting Score Parsing on Existing Reviews:")
        print("=" * 80)

        tested_count = 0
        success_count = 0

        for music_item, source in results:
            tested_count += 1

            print(f"\n{tested_count}. {music_item.title}")
            print(f"   Source: {source.name}")
            print(f"   Current score: {music_item.review_score}")

            # Test score parsing
            if music_item.processed_content:
                parsed_score = parser.parse_score(music_item.processed_content, source.name)
                if parsed_score:
                    success_count += 1
                    print(f"   Parsed score: {parsed_score.normalized_score}/10")
                    print(f"   Raw score: {parsed_score.raw_score}")
                    print(f"   Confidence: {parsed_score.confidence}")
                    print(f"   Format: {parsed_score.format_type}")
                    if parsed_score.sub_scores:
                        print(f"   Sub-scores: {parsed_score.sub_scores}")
                else:
                    print(f"   FAIL: No score found")
            else:
                print(f"   WARN: No content to parse")

        print(f"\n" + "=" * 80)
        print(f"Score Parsing Results:")
        print(f"  Total reviews tested: {tested_count}")
        print(f"  Scores successfully parsed: {success_count}")
        print(f"  Success rate: {(success_count/tested_count)*100:.1f}%" if tested_count > 0 else "N/A")
        print("=" * 80)


if __name__ == "__main__":
    main()