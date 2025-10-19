"""
CLI tool to refresh metadata (genres, cover art) for all albums in the database.
"""
import sys
import logging
from sqlmodel import Session, select
from ..core.database import engine
from ..models import MusicItem, ContentType
from ..services.metadata_fetcher import get_metadata_fetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def refresh_all_metadata():
    """Fetch and cache metadata for all albums in the database."""
    session = Session(engine)

    try:
        # Get all review items with albums
        query = select(MusicItem).where(
            MusicItem.content_type == ContentType.REVIEW,
            MusicItem.album.isnot(None),
            MusicItem.artists != []
        )

        items = session.exec(query).all()

        # Group by artist + album to avoid duplicate fetches
        seen_albums = set()
        fetcher = get_metadata_fetcher()

        updated_count = 0
        skipped_count = 0
        failed_count = 0

        for item in items:
            if not item.artists or not item.album:
                continue

            artist = item.artists[0]
            album = item.album
            key = (artist.lower(), album.lower())

            if key in seen_albums:
                continue

            seen_albums.add(key)

            # Check if already has metadata
            if item.album_genres and item.album_cover_url:
                logger.info(f"Skipping {artist} - {album} (already has metadata)")
                skipped_count += 1
                continue

            logger.info(f"Fetching metadata for: {artist} - {album}")

            # Fetch metadata
            metadata = fetcher.search_album(artist, album)

            if metadata:
                genres = metadata.get("genres", [])
                cover_url = metadata.get("cover_art_url")
                musicbrainz_id = metadata.get("musicbrainz_id")

                # Update all reviews for this album
                update_query = select(MusicItem).where(
                    MusicItem.content_type == ContentType.REVIEW,
                    MusicItem.album == album
                )

                matching_items = session.exec(update_query).all()

                for matching_item in matching_items:
                    if matching_item.artists and matching_item.artists[0].lower() == artist.lower():
                        matching_item.album_genres = genres
                        matching_item.album_cover_url = cover_url
                        matching_item.musicbrainz_id = musicbrainz_id
                        session.add(matching_item)

                updated_count += 1
                logger.info(f"✓ Updated {artist} - {album} with {len(genres)} genres")

                # Commit every 10 albums to avoid losing progress
                if updated_count % 10 == 0:
                    session.commit()
                    logger.info(f"Progress: {updated_count} updated, {skipped_count} skipped, {failed_count} failed")
            else:
                failed_count += 1
                logger.warning(f"✗ Could not fetch metadata for {artist} - {album}")

        # Final commit
        session.commit()

        logger.info(f"\n=== Refresh Complete ===")
        logger.info(f"Updated: {updated_count}")
        logger.info(f"Skipped: {skipped_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Total unique albums: {len(seen_albums)}")

    except Exception as e:
        logger.error(f"Error refreshing metadata: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Starting metadata refresh...")
    refresh_all_metadata()
    logger.info("Done!")
