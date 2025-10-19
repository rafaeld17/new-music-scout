"""
CLI script to scrape HTML pages and extract tracklists for album reviews.
"""
import argparse
from sqlmodel import Session, select
from ..core.database import engine
from ..models import MusicItem, ContentType
from ..services.html_scraper import get_html_scraper
from ..core.logging import logger


def scrape_review_tracks(limit: int = None, force: bool = False):
    """
    Scrape review pages and extract tracklists.

    Args:
        limit: Maximum number of reviews to process (None = all)
        force: Re-scrape reviews that already have tracks
    """
    session = Session(engine)
    scraper = get_html_scraper()

    # Get reviews that need scraping
    query = select(MusicItem).where(MusicItem.content_type == ContentType.REVIEW)

    if not force:
        # Only scrape reviews without tracks
        query = query.where(MusicItem.tracks == [])

    if limit:
        query = query.limit(limit)

    reviews = session.exec(query).all()

    logger.info(f"Found {len(reviews)} reviews to scrape")

    scraped_count = 0
    error_count = 0
    tracks_found_count = 0

    for review in reviews:
        try:
            logger.info(f"Scraping: {review.title[:60]}... ({review.url})")

            result = scraper.scrape_page(review.url)

            if result and result['tracks']:
                # Update review with extracted tracks
                review.tracks = result['tracks']
                session.add(review)
                session.commit()

                tracks_found_count += 1
                logger.info(f"  + Extracted {len(result['tracks'])} tracks")
            else:
                logger.info(f"  - No tracks found")

            scraped_count += 1

        except Exception as e:
            error_count += 1
            logger.error(f"  ! Error scraping {review.url}: {e}")
            continue

    session.close()

    logger.info("\n" + "=" * 60)
    logger.info("Scraping Summary:")
    logger.info(f"  Reviews scraped: {scraped_count}")
    logger.info(f"  Tracks found: {tracks_found_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info("=" * 60)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape HTML pages to extract track listings"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help="Maximum number of reviews to scrape (default: all)"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Re-scrape reviews that already have tracks"
    )

    args = parser.parse_args()

    scrape_review_tracks(limit=args.limit, force=args.force)


if __name__ == "__main__":
    main()
