"""
Populate tracks field for existing music items.

Extracts track/single names from item titles and stores them in the database.
"""

from sqlmodel import Session, select
from ..core.database import engine
from ..models import MusicItem
from ..services.track_extractor import get_track_extractor


def populate_tracks():
    """Extract and populate track names for all music items."""
    session = Session(engine)
    extractor = get_track_extractor()

    # Get all items
    items = session.exec(select(MusicItem)).all()

    updated_count = 0
    track_count = 0

    print(f"Processing {len(items)} items...")

    for item in items:
        # Extract tracks from title
        tracks = extractor.extract_all_tracks(item.title)

        if tracks:
            item.tracks = tracks
            session.add(item)
            updated_count += 1
            track_count += len(tracks)

            # Commit every 50 items
            if updated_count % 50 == 0:
                session.commit()
                print(f"  Processed {updated_count} items with tracks...")

    # Final commit
    session.commit()
    session.close()

    print(f"\n✓ Complete!")
    print(f"  Updated {updated_count} items")
    print(f"  Extracted {track_count} total track names")
    print(f"  Average: {track_count / updated_count:.1f} tracks per item" if updated_count > 0 else "")


if __name__ == "__main__":
    populate_tracks()
