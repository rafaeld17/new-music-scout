"""
Migration script to re-classify Blabbermouth items based on URL patterns.

This script finds all items from Blabbermouth that have /reviews/ in their URL
but are currently classified as NEWS, and re-classifies them as REVIEW.
"""
import sys
sys.path.insert(0, 'src')

from music_scout.core.database import get_session
from music_scout.models import MusicItem, ContentType
from sqlmodel import select

def main():
    session = next(get_session())

    print("=" * 80)
    print("Blabbermouth Review Re-Classification Migration")
    print("=" * 80)

    # Find all Blabbermouth items with /reviews/ in URL that aren't classified as REVIEW
    items = session.exec(
        select(MusicItem)
        .where(MusicItem.source_id == 11)  # Blabbermouth
        .where(MusicItem.content_type != ContentType.REVIEW)
    ).all()

    reviews_to_fix = []
    for item in items:
        if '/reviews/' in item.url.lower() or '/review/' in item.url.lower():
            reviews_to_fix.append(item)

    print(f"\nFound {len(reviews_to_fix)} items to re-classify from {item.content_type} to REVIEW\n")

    if not reviews_to_fix:
        print("No items to fix. Exiting.")
        session.close()
        return

    print("Items to be re-classified:")
    print("-" * 80)
    for item in reviews_to_fix[:10]:  # Show first 10
        print(f"  ID {item.id:4d}: {item.title[:60]}")
        print(f"         URL: {item.url}")
        print(f"         Current type: {item.content_type}")
        print()

    if len(reviews_to_fix) > 10:
        print(f"  ... and {len(reviews_to_fix) - 10} more")
        print()

    # Ask for confirmation
    response = input(f"Re-classify {len(reviews_to_fix)} items as REVIEW? (y/N): ")

    if response.lower() != 'y':
        print("Aborted.")
        session.close()
        return

    # Update items
    updated_count = 0
    for item in reviews_to_fix:
        item.content_type = ContentType.REVIEW
        session.add(item)
        updated_count += 1

    session.commit()

    print(f"\n✅ Successfully re-classified {updated_count} items as REVIEW")

    # Show summary stats
    review_count = session.exec(
        select(MusicItem)
        .where(MusicItem.source_id == 11)
        .where(MusicItem.content_type == ContentType.REVIEW)
    ).all()

    print(f"\nBlabbermouth now has {len(review_count)} reviews in the database")

    session.close()
    print("\n" + "=" * 80)
    print("Migration complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
