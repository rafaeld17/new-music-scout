"""
Database cleanup utility.

Removes sources and items not in the target list,
and vacuums the database to reclaim space.
"""
import sys
import click
from sqlmodel import Session, select, delete
from ..core.database import engine
from ..models import Source, MusicItem

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Database cleanup utilities."""
    pass


@cli.command()
@click.option(
    '--keep-ids',
    required=True,
    help='Comma-separated list of source IDs to keep (e.g., "1,2,3,4,5,6,7,8")'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be deleted without actually deleting'
)
@click.option(
    '--backup',
    is_flag=True,
    default=True,
    help='Remind to backup database before cleanup (default: True)'
)
@click.option(
    '--yes',
    is_flag=True,
    help='Skip confirmation prompts (auto-confirm)'
)
def cleanup_sources(keep_ids: str, dry_run: bool, backup: bool, yes: bool):
    """
    Remove sources and their items not in the keep list.

    Example:
        python -m src.music_scout.cli.cleanup cleanup-sources --keep-ids "1,2,3,4,5,6,7,8"
    """
    # Parse keep IDs
    try:
        keep_id_list = [int(x.strip()) for x in keep_ids.split(',')]
    except ValueError:
        logger.error("Invalid keep-ids format. Must be comma-separated integers.")
        sys.exit(1)

    if backup and not dry_run and not yes:
        logger.warning("⚠️  IMPORTANT: Make sure you have backed up your database!")
        logger.warning("   Recommended: cp music_scout.db music_scout.db.backup")
        response = input("Have you backed up the database? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Cleanup cancelled. Please backup your database first.")
            sys.exit(0)

    session = Session(engine)

    try:
        # Get all sources
        all_sources = session.exec(select(Source)).all()

        # Identify sources to keep and remove
        sources_to_keep = [s for s in all_sources if s.id in keep_id_list]
        sources_to_remove = [s for s in all_sources if s.id not in keep_id_list]

        if not sources_to_remove:
            logger.info("✅ No sources to remove. Database is already clean!")
            return

        # Display summary
        logger.info(f"\n{'=' * 60}")
        logger.info(f"DATABASE CLEANUP SUMMARY")
        logger.info(f"{'=' * 60}")
        logger.info(f"\n📊 SOURCES TO KEEP ({len(sources_to_keep)}):")
        for source in sources_to_keep:
            item_count = session.exec(
                select(MusicItem).where(MusicItem.source_id == source.id)
            ).all()
            logger.info(f"  ✓ [{source.id}] {source.name} - {len(item_count)} items")

        logger.info(f"\n🗑️  SOURCES TO REMOVE ({len(sources_to_remove)}):")
        total_items_to_delete = 0
        for source in sources_to_remove:
            items = session.exec(
                select(MusicItem).where(MusicItem.source_id == source.id)
            ).all()
            total_items_to_delete += len(items)
            logger.info(f"  ✗ [{source.id}] {source.name} - {len(items)} items")

        logger.info(f"\n📈 TOTALS:")
        logger.info(f"  • Sources to keep: {len(sources_to_keep)}")
        logger.info(f"  • Sources to remove: {len(sources_to_remove)}")
        logger.info(f"  • Items to delete: {total_items_to_delete}")
        logger.info(f"{'=' * 60}\n")

        if dry_run:
            logger.info("🔍 DRY RUN - No changes made to database")
            return

        # Confirm deletion
        if not yes:
            response = input(f"⚠️  Delete {len(sources_to_remove)} sources and {total_items_to_delete} items? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Cleanup cancelled.")
                return

        # Delete items first (foreign key constraint)
        logger.info(f"\n🗑️  Deleting {total_items_to_delete} items...")
        for source in sources_to_remove:
            deleted_count = session.exec(
                delete(MusicItem).where(MusicItem.source_id == source.id)
            )
            session.commit()
            logger.info(f"  ✓ Deleted items from {source.name}")

        # Delete sources
        logger.info(f"\n🗑️  Deleting {len(sources_to_remove)} sources...")
        for source in sources_to_remove:
            source_name = source.name  # Store name before deletion
            session.delete(source)
            logger.info(f"  ✓ Deleted source: {source_name}")

        session.commit()

        # Vacuum database (SQLite only)
        logger.info("\n🧹 Vacuuming database to reclaim space...")
        try:
            session.exec("VACUUM")
            logger.info("  ✓ Database vacuumed successfully")
        except Exception as e:
            logger.warning(f"  ⚠️  Could not vacuum database: {e}")
            logger.warning("     (This is expected if not using SQLite)")

        # Final summary
        remaining_sources = session.exec(select(Source)).all()
        remaining_items = session.exec(select(MusicItem)).all()

        logger.info(f"\n{'=' * 60}")
        logger.info(f"✅ CLEANUP COMPLETE")
        logger.info(f"{'=' * 60}")
        logger.info(f"  • Remaining sources: {len(remaining_sources)}")
        logger.info(f"  • Remaining items: {len(remaining_items)}")
        logger.info(f"  • Deleted sources: {len(sources_to_remove)}")
        logger.info(f"  • Deleted items: {total_items_to_delete}")
        logger.info(f"{'=' * 60}\n")

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        session.rollback()
        raise
    finally:
        session.close()


@cli.command()
def list_sources():
    """List all sources with item counts."""
    session = Session(engine)

    try:
        sources = session.exec(select(Source)).all()

        logger.info(f"\n{'=' * 70}")
        logger.info(f"ALL SOURCES IN DATABASE")
        logger.info(f"{'=' * 70}\n")

        for source in sources:
            items = session.exec(
                select(MusicItem).where(MusicItem.source_id == source.id)
            ).all()

            enabled_marker = "✓" if source.enabled else "✗"
            logger.info(
                f"{enabled_marker} [{source.id:2d}] {source.name:30s} "
                f"| {source.source_type:8s} | {len(items):4d} items | "
                f"weight: {source.weight}"
            )

        logger.info(f"\n{'=' * 70}")
        logger.info(f"Total sources: {len(sources)}")
        logger.info(f"{'=' * 70}\n")

    finally:
        session.close()


@cli.command()
@click.option(
    '--source-id',
    type=int,
    help='Show items for specific source ID'
)
def show_items(source_id: int = None):
    """Show items in database, optionally filtered by source."""
    session = Session(engine)

    try:
        if source_id:
            items = session.exec(
                select(MusicItem).where(MusicItem.source_id == source_id)
            ).all()
            source = session.get(Source, source_id)
            source_name = source.name if source else "Unknown"
            logger.info(f"\nItems from source [{source_id}] {source_name}:\n")
        else:
            items = session.exec(select(MusicItem)).all()
            logger.info(f"\nAll items in database:\n")

        for item in items[:50]:  # Limit to first 50
            logger.info(
                f"[{item.id:4d}] {item.title[:60]:60s} | "
                f"{item.content_type:10s} | {item.published_date.date()}"
            )

        if len(items) > 50:
            logger.info(f"\n... and {len(items) - 50} more items")

        logger.info(f"\nTotal items: {len(items)}\n")

    finally:
        session.close()


if __name__ == '__main__':
    cli()
