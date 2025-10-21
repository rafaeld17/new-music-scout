"""
Main FastAPI application for the Music Scout.
Updated to include reviews router.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import create_db_and_tables
from .core.logging import logger
from .api import health, content, reviews, admin

# Create FastAPI app
app = FastAPI(
    title="New Music Scout",
    description="Personal music discovery agent for prog/rock/metal",
    version="0.1.0",
    debug=settings.debug,
)

# Add CORS middleware
# In production, use ALLOWED_ORIGINS env var + localhost for development
if settings.debug:
    allowed_origins = ["*"]
else:
    # Parse allowed origins from env var
    configured_origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]

    # If no origins configured, default to Railway frontend domain
    if not configured_origins:
        logger.warning("ALLOWED_ORIGINS not set, using default Railway domain")
        configured_origins = ["https://music-scout-frontend-production.up.railway.app"]

    # Always allow localhost for development/testing
    allowed_origins = configured_origins + [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

# Log CORS configuration for debugging
logger.info(f"CORS allowed origins: {allowed_origins}")
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
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    """Root endpoint for basic connectivity test."""
    return {"message": "New Music Scout API", "status": "running"}


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        logger.info("Starting New Music Scout application")

        # Create database tables (if they don't exist)
        create_db_and_tables()
        logger.info("Database tables created/verified")
        logger.info("Application startup complete!")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise


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