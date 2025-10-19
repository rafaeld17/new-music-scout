"""
Automated scheduler for weekly ingestion.

This provides a cross-platform Python-based scheduler as an alternative
to OS-specific schedulers (cron/Task Scheduler).

Usage:
    python -m src.music_scout.cli.scheduler
"""

import schedule
import time
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.music_scout.core.database import get_session
from src.music_scout.services.ingestion import IngestionService
from src.music_scout.models import Source
from src.music_scout.core.logging import logger


def run_weekly_ingestion():
    """Run the weekly ingestion process."""
    logger.info("=" * 80)
    logger.info(f"Starting weekly ingestion at {datetime.now()}")
    logger.info("=" * 80)

    try:
        with get_session() as session:
            # Get all enabled sources
            sources = session.query(Source).filter(Source.enabled == True).all()

            if not sources:
                logger.warning("No enabled sources found!")
                return

            logger.info(f"Found {len(sources)} enabled sources")

            ingestion_service = IngestionService(session)
            total_items = 0

            for source in sources:
                try:
                    logger.info(f"\nProcessing source: {source.name}")
                    items = ingestion_service.ingest_from_source(source)
                    total_items += len(items)
                    logger.info(f"✓ Ingested {len(items)} items from {source.name}")

                    # Brief pause between sources to be polite
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"✗ Failed to ingest from {source.name}: {e}")
                    continue

            logger.info("=" * 80)
            logger.info(f"Weekly ingestion completed: {total_items} total items ingested")
            logger.info(f"Finished at {datetime.now()}")
            logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Fatal error during weekly ingestion: {e}")
        raise


def main():
    """Main scheduler loop."""
    logger.info("Music Scout Scheduler started")
    logger.info("Scheduled: Every Sunday at 9:00 AM")
    logger.info("Press Ctrl+C to stop")

    # Schedule weekly ingestion every Sunday at 9 AM
    schedule.every().sunday.at("09:00").do(run_weekly_ingestion)

    # Also allow manual trigger on startup with --now flag
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        logger.info("Running ingestion immediately (--now flag)")
        run_weekly_ingestion()

    # Main scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
