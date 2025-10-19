# New Music Scout

A personalized music discovery agent focused on prog/rock/metal sources. The system monitors trusted music journalism sources, applies intelligent filtering and ranking, and delivers curated weekly digests with optional Spotify playlists.

## Features

- **Content Ingestion**: RSS feed parsing and HTML scraping from trusted sources
- **Smart Classification**: Automatic content type detection (reviews, news, interviews, premieres)
- **Music Metadata Extraction**: Artist and album identification from titles and content
- **Review Aggregation**: Consolidate reviews across sources with smart album matching
- **Personalized Scoring**: Weighted scoring based on source credibility and genre preferences
- **Multiple Delivery Formats**: Email digests, web interface, and Spotify playlists

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Setup

1. Clone the repository and navigate to the project directory

2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Set up the project (starts database, installs dependencies):
   ```bash
   make setup
   ```

   Or manually:
   ```bash
   docker-compose up -d postgres redis
   pip install -r requirements.txt
   ```

### Development Commands

```bash
# Start development server
make dev

# Run tests
make test

# Run tests with coverage
make test-cov

# Run linting
make lint

# Format code
make format

# Set up default sources
make cli-ingest setup

# List configured sources
python -m src.music_scout.cli.ingest list

# Test ingestion from all sources
python -m src.music_scout.cli.ingest ingest

# Test specific RSS feed
python -m src.music_scout.cli.ingest test --rss "https://example.com/feed/"
```

## Architecture

The system follows a layered architecture:

- **API Layer**: FastAPI web application with health checks
- **Service Layer**: Business logic for ingestion, source management
- **Data Layer**: SQLModel/SQLAlchemy with PostgreSQL
- **Models**: Database models for sources, music items, artists, albums

### Current Sources

- **The Prog Report**: Main feed and reviews feed
- **Sonic Perspectives**: Main feed and album reviews feed

## Development Phases

This project follows a 6-milestone development approach:

1. ✅ **Basic Data Pipeline** - FastAPI + PostgreSQL + RSS ingestion
2. 🔄 **Content Processing** - Review score parsing + metadata extraction
3. ⏳ **Review Aggregation MVP** - Album matching + web interface
4. ⏳ **Scoring & Digest Generation** - Personal preference scoring + email system
5. ⏳ **Advanced Sources & Polish** - Scale to 6+ sources + performance optimization
6. ⏳ **Personalization** - Spotify integration + playlist generation

## Milestone 1 Success Criteria

- ✅ FastAPI application with health checks
- ✅ PostgreSQL database with proper models
- ✅ RSS ingestion from The Prog Report and Sonic Perspectives
- ✅ CLI tool for testing and management
- ✅ Unit and integration tests
- 🎯 **Target**: Successfully fetch and store 50+ items from each source

## Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=src/music_scout --cov-report=html
```

## Project Structure

```
src/music_scout/
├── api/              # FastAPI routes and endpoints
├── cli/              # Command-line tools
├── core/             # Core utilities (config, database, logging)
├── models/           # Database models
├── services/         # Business logic services
└── main.py           # FastAPI application entry point

tests/
├── unit/             # Unit tests
├── integration/      # Integration tests
└── conftest.py       # Test configuration and fixtures

config/               # Configuration files
alembic/              # Database migrations
```

## Contributing

1. Follow the development best practices outlined in `CLAUDE.md`
2. Write tests for new functionality
3. Use conventional commit messages
4. Ensure code quality with linting and formatting
5. Update documentation for new features

## License

This is a personal project for music discovery and review aggregation.