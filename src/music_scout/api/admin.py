"""
Admin API endpoints for management operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..core.database import get_session
from ..core.logging import logger
from ..services import IngestionService, SourceManager
from ..models import Source

router = APIRouter()


@router.get("/sources")
def list_sources(session: Session = Depends(get_session)) -> List[dict]:
    """List all content sources."""
    try:
        source_manager = SourceManager(session)
        sources = source_manager.list_sources()

        return [
            {
                "id": source.id,
                "name": source.name,
                "url": source.url,
                "source_type": source.source_type.value,
                "enabled": source.enabled,
                "weight": source.weight,
            }
            for source in sources
        ]
    except Exception as e:
        logger.error(f"Error listing sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/create-defaults")
def create_default_sources(session: Session = Depends(get_session)) -> dict:
    """Create default sources if they don't exist."""
    try:
        source_manager = SourceManager(session)
        sources = source_manager.create_default_sources()

        return {
            "message": f"Created {len(sources)} default sources",
            "sources": [
                {
                    "id": source.id,
                    "name": source.name,
                    "enabled": source.enabled,
                }
                for source in sources
            ]
        }
    except Exception as e:
        logger.error(f"Error creating default sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
def trigger_ingestion(
    source_id: Optional[int] = None,
    source_name: Optional[str] = None,
    session: Session = Depends(get_session)
) -> dict:
    """
    Trigger content ingestion.

    - If source_id or source_name provided, ingest from that specific source
    - Otherwise, ingest from all enabled sources
    """
    try:
        source_manager = SourceManager(session)
        ingestion_service = IngestionService(session)

        # Create default sources if they don't exist
        source_manager.create_default_sources()

        if source_name or source_id:
            # Ingest from specific source
            if source_name:
                source = source_manager.get_source_by_name(source_name)
                if not source:
                    raise HTTPException(status_code=404, detail=f"Source not found: {source_name}")
            else:
                source = session.get(Source, source_id)
                if not source:
                    raise HTTPException(status_code=404, detail=f"Source not found with ID: {source_id}")

            logger.info(f"Starting ingestion from source: {source.name}")
            items = ingestion_service.ingest_from_source(source)

            return {
                "message": f"Ingested {len(items)} items from {source.name}",
                "source": source.name,
                "items_count": len(items)
            }
        else:
            # Ingest from all enabled sources
            logger.info("Starting ingestion from all enabled sources")
            sources = source_manager.list_sources(enabled_only=True)

            total_items = 0
            results = []

            for source in sources:
                try:
                    items = ingestion_service.ingest_from_source(source)
                    total_items += len(items)
                    results.append({
                        "source": source.name,
                        "items_count": len(items),
                        "status": "success"
                    })
                except Exception as e:
                    logger.error(f"Error ingesting from {source.name}: {e}", exc_info=True)
                    results.append({
                        "source": source.name,
                        "items_count": 0,
                        "status": "error",
                        "error": str(e)
                    })

            return {
                "message": f"Ingested {total_items} items from {len(sources)} sources",
                "total_items": total_items,
                "sources_processed": len(sources),
                "results": results
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
