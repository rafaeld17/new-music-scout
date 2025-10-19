#!/usr/bin/env python3
"""
Validation script for Milestone 1 success criteria.

Success Criteria:
- Successfully fetch and store 50+ items from each source
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlmodel import Session, select, func
from music_scout.core.database import engine, create_db_and_tables
from music_scout.models import Source, MusicItem
from music_scout.services import SourceManager, IngestionService
from music_scout.core.logging import logger


def validate_milestone1():
    """Validate Milestone 1 success criteria."""
    logger.info("Starting Milestone 1 validation...")

    # Ensure database exists
    create_db_and_tables()

    with Session(engine) as session:
        source_manager = SourceManager(session)
        ingestion_service = IngestionService(session)

        # Step 1: Set up default sources
        logger.info("Setting up default sources...")
        created_sources = source_manager.create_default_sources()
        logger.info(f"Created {len(created_sources)} new sources")

        # Step 2: Get all enabled sources
        sources = source_manager.get_enabled_sources()
        logger.info(f"Found {len(sources)} enabled sources")

        # Step 3: Check existing items in database for each source
        results = {}

        for source in sources:
            logger.info(f"Checking items from: {source.name}")
            try:
                # Count existing items for this source
                item_count = session.exec(select(func.count(MusicItem.id)).where(MusicItem.source_id == source.id)).one()
                results[source.name] = item_count
                logger.info(f"Found {item_count} existing items from {source.name}")
            except Exception as e:
                logger.error(f"Failed to count items from {source.name}: {str(e)}")
                results[source.name] = 0

        # Step 4: Validate success criteria
        logger.info("\n" + "="*60)
        logger.info("MILESTONE 1 VALIDATION RESULTS")
        logger.info("="*60)

        success = True
        for source_name, item_count in results.items():
            status = "PASS" if item_count >= 50 else "FAIL"
            logger.info(f"{source_name:30} | {item_count:3d} items | {status}")

            if item_count < 50:
                success = False

        # Get total items in database
        total_db_items = session.exec(select(func.count(MusicItem.id))).one()

        logger.info("-" * 60)
        logger.info(f"Total items in database: {total_db_items}")

        # Final result
        if success:
            logger.info("\nMILESTONE 1: SUCCESS!")
            logger.info("Successfully validated existing data meets success criteria")
        else:
            logger.info("\nMILESTONE 1: NOT YET COMPLETE")
            logger.info("Some sources did not reach the 50-item threshold")

        logger.info("="*60)
        return success


if __name__ == "__main__":
    try:
        success = validate_milestone1()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        sys.exit(1)