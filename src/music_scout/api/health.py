"""
Health check API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..core.database import get_session

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "New Music Scout",
        "version": "0.1.0"
    }


@router.get("/health/db")
async def database_health_check(session: Session = Depends(get_session)):
    """Database connectivity health check."""
    try:
        # Simple query to test database connection
        from sqlmodel import text
        session.exec(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }