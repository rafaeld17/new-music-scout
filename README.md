# New Music Scout 🎸

A personal music discovery tool that aggregates album reviews from curated prog/rock/metal sources, enriches them with Spotify metadata, and provides a browsable web interface for discovering new music.

**Status:** Production-ready, deployed on Railway.app ✅

---

## Features

- 📰 **Automated Review Aggregation** - Daily ingestion from 8 trusted sources
- 🎵 **Spotify Metadata Enrichment** - Rich album data, cover art, genres
- 🌐 **Web Interface** - Browse, filter, and sort recent reviews
- 📅 **Daily Updates** - Scheduled cron job keeps content fresh
- 📱 **Mobile-Friendly** - Access from anywhere with HTTPS

---

## Quick Start

### Development Setup

```bash
# 1. Clone repository
git clone https://github.com/rafaeld17/new-music-scout.git
cd new-music-scout

# 2. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 3. Set up environment
cp .env.example .env
# Add your Spotify credentials to .env

# 4. Run database migrations
alembic upgrade head

# 5. Start backend (terminal 1)
python -m src.music_scout.main

# 6. Start frontend (terminal 2)
cd frontend && npm run dev

# 7. Visit http://localhost:5173
```

### Production Deployment

**Recommended:** Railway.app (free tier with $5 credit/month)

👉 **[See DEPLOY_RAILWAY.md for complete deployment guide](./DEPLOY_RAILWAY.md)** 👈

**Alternative:** Render.com (requires $7/mo paid plan for persistent storage)

- See [DEPLOY.md](./DEPLOY.md) for Render deployment

---

## Architecture

```
┌─────────────────┐
│  8 RSS/HTML     │
│  Review Sources │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  FastAPI        │────▶│  Spotify API │
│  Ingestion      │     │  (Metadata)  │
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │
│  (389 reviews)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  FastAPI        │────▶│  React UI    │
│  REST API       │     │  (Frontend)  │
└─────────────────┘     └──────────────┘
```

**Tech Stack:**
- Backend: Python 3.13, FastAPI, SQLModel, SQLite
- Frontend: React 19, TypeScript, Vite
- External APIs: Spotify Web API, MusicBrainz
- Deployment: Railway.app (Docker containers)

---

## Review Sources

1. **Sonic Perspectives** - Prog, fusion, hard rock (300 reviews)
2. **MetalSucks** - Metal & hard rock (50 reviews)
3. **Metal Storm** - Broad metal/heavy rock (20 reviews)
4. **The Prog Report** - Progressive rock/metal (10 reviews)
5. **Heavy Music HQ** - Hard rock, metal, blues-rock (6 reviews)
6. **Rock & Blues Muse** - Blues-rock, rootsy (3 reviews)
7. **Blabbermouth** - Hard rock & metal (requires Selenium - TODO)
8. **Kerrang!** - Rock, hard rock, modern heavy (requires Selenium - TODO)

Currently: **6 working sources**, 2 blocked by JavaScript rendering

---

## Project Structure

```
new-music-scout/
├── src/music_scout/          # Backend Python code
│   ├── api/                  # FastAPI endpoints
│   ├── cli/                  # CLI tools (ingest, cleanup)
│   ├── core/                 # Database, config, logging
│   ├── models/               # SQLModel data models
│   └── services/             # Business logic
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api.ts           # API client
│   │   └── types.ts         # TypeScript types
│   ├── Dockerfile           # Frontend container
│   └── nginx.conf           # nginx config
├── tests/                    # Pytest tests
├── alembic/                  # Database migrations
├── Dockerfile                # Backend container
├── railway.json              # Railway.app config
├── DEPLOY_RAILWAY.md         # Deployment guide
├── CLAUDE.md                 # AI development guide
├── todo.md                   # Project roadmap
└── new-music-scout-spec.md   # Technical specification
```

---

## Documentation

- **[DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md)** - Production deployment guide
- **[CLAUDE.md](./CLAUDE.md)** - Development workflow and best practices
- **[todo.md](./todo.md)** - Project roadmap and task tracking
- **[new-music-scout-spec.md](./new-music-scout-spec.md)** - Complete technical spec

---

## Development Commands

```bash
# Daily Development
python -m src.music_scout.main              # Start backend
cd frontend && npm run dev                  # Start frontend
python -m src.music_scout.cli.ingest ingest # Run ingestion

# Database
alembic upgrade head                        # Run migrations
alembic revision --autogenerate -m "msg"    # Create migration
cp music_scout.db music_scout.db.backup     # Backup database

# Testing
pytest                                      # Run all tests
pytest --cov=src/music_scout               # With coverage
pytest tests/unit/test_metadata_fetcher.py  # Specific test

# Deployment
docker build -t music-scout-backend .       # Build backend
docker build -t music-scout-frontend ./frontend  # Build frontend
```

---

## Current Stats

- **Total Reviews:** 389
- **Active Sources:** 6/8 (2 blocked by JS rendering)
- **Metadata Coverage:** 67.5% (Spotify 61.3%, MusicBrainz 6.3%)
- **Date Range:** 2022-11-11 to 2025-10-18
- **Test Coverage:** 25 passing tests

---

## Roadmap

### ✅ Phase 1-3: Foundation (Complete)
- Content ingestion, processing, basic UI

### ✅ Phase 3.5: Database Rebuild + Metadata (Complete)
- Spotify integration, focused 8 sources, 67.5% metadata coverage

### ✅ Phase 3.6: Production Deployment (Complete)
- Railway.app deployment with persistent volumes and cron jobs

### 📋 Phase 4: Enhanced Spotify Integration (Next)
- OAuth2 user authentication
- Playlist management
- "Add to Playlist" workflow
- Spotify embeds in UI

### 📋 Phase 5: Advanced Features (Future)
- Fuzzy album matching
- Review analytics and consensus metrics
- Personalized recommendations
- Weekly email digests
- Automated discovery playlists

---

## Contributing

This is a personal project, but issues and suggestions are welcome!

1. Check [todo.md](./todo.md) for current priorities
2. Read [CLAUDE.md](./CLAUDE.md) for development workflow
3. Open an issue to discuss changes
4. Submit PR with tests

---

## License

This project is for personal use. Not licensed for commercial use.

---

## Acknowledgments

- **Spotify Web API** - Metadata enrichment
- **MusicBrainz** - Fallback metadata
- **8 Review Sources** - Quality music journalism
- **Railway.app** - Generous free tier hosting

---

**Built with Claude Code** 🤖
