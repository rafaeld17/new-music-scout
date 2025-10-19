"""
Main FastAPI application for the Music Scout.
Updated to include reviews router.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import create_db_and_tables
from .core.logging import logger
from .api import health, content, reviews

# Create FastAPI app
app = FastAPI(
    title="New Music Scout",
    description="Personal music discovery agent for prog/rock/metal",
    version="0.1.0",
    debug=settings.debug,
)

# Add CORS middleware
# In production, use ALLOWED_ORIGINS env var. In debug mode, allow all.
allowed_origins = (
    ["*"] if settings.debug
    else [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(content.router, prefix="/api", tags=["content"])
app.include_router(reviews.router, prefix="/api", tags=["reviews"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting New Music Scout application")

    # Create database tables
    create_db_and_tables()
    logger.info("Database tables created/verified")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down New Music Scout application")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "music_scout.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )