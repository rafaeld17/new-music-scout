# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

**Last Updated:** 2025-10-18

---

## 📚 CRITICAL: Documentation Maintenance

**READ THIS SECTION AT THE START OF EVERY SESSION**

### Three Core Files

1. **`CLAUDE.md`** (this file) - General guidelines and workflow
2. **`new-music-scout-spec.md`** - Technical architecture and design
3. **`todo.md`** - Official project todo list

### When to Update Documentation

**Update `new-music-scout-spec.md` when:**
- Adding/removing content sources
- Changing data models or API endpoints
- Integrating new external APIs
- Completing a development phase

**Update `todo.md` when:**
- Starting a task (mark in progress)
- Completing a task (mark done with date)
- Discovering new work
- At end of every work session

**Update `CLAUDE.md` when:**
- Changing development workflow
- Adding new CLI commands

### Workflow Checklist

**Before starting work:**
1. Read this file for context
2. Check `todo.md` for current priorities
3. Review `new-music-scout-spec.md` if touching architecture

**After completing a task:**
1. Update `todo.md` (mark complete, add date)
2. Update spec if architecture changed
3. Update "Last Updated" dates
4. Commit with descriptive message

---

## Project Overview

**New Music Scout** - Personal music discovery tool for prog/rock/metal genres.

**Current Phase:** Phase 3.5 - Database Rebuild + Spotify Metadata Integration

**Status:** Focusing on 8 curated sources with rich Spotify metadata enrichment.

### Core Architecture

```
RSS/HTML Sources → Ingestion → Metadata Enrichment (Spotify) → Database → Web Interface
```

**Key Components:**
- **Backend:** FastAPI + SQLite + SQLModel ORM
- **Frontend:** React 19 + TypeScript + Vite
- **External APIs:** Spotify Web API (primary), MusicBrainz (fallback)
- **Data Processing:** feedparser (RSS), BeautifulSoup (HTML scraping)

### 8 Core Sources

1. Kerrang! - Rock, hard rock, alt/modern heavy
2. Blabbermouth - Hard rock & metal reviews
3. MetalSucks - Metal & hard rock, opinionated
4. Metal Storm - Broad metal/heavy rock with ratings
5. Sonic Perspectives - Prog, fusion, hard rock, technical
6. The Prog Report - Progressive rock and prog-metal
7. Heavy Music HQ - Hard rock, metal, blues-rock
8. Rock & Blues Muse - Blues-rock, rootsy, classic-leaning

---

## Quick Reference Commands

### Daily Development
```bash
# Backend
python -m src.music_scout.main

# Frontend
cd frontend && npm run dev

# Ingestion
python -m src.music_scout.cli.ingest ingest
python -m src.music_scout.cli.ingest list
```

### Database
```bash
# Migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Backup before cleanup
cp music_scout.db music_scout.db.backup

# Cleanup (Phase 3.5)
python -m src.music_scout.cli.cleanup --keep-ids 1,2,3,4,5,6,7,8
```

### Testing
```bash
pytest                                    # All tests
pytest tests/unit/test_metadata_fetcher.py  # Specific file
pytest --cov=src/music_scout              # With coverage
```

---

## Development Best Practices

### Code Quality
- Follow PEP 8 for Python style
- Use type hints throughout
- Write docstrings for public functions
- Comprehensive error handling
- Keep functions focused and single-purpose

### Testing
- Write tests before implementing features
- Test each processing step independently
- Create integration tests for workflows
- Aim for >80% coverage on business logic
- Test edge cases (malformed feeds, missing data)

### Git Workflow
- Atomic commits (one logical change per commit)
- Conventional commit messages:
  - `feat: add Spotify metadata enrichment`
  - `fix: handle missing review scores`
  - `docs: update spec with new sources`
- Reference todo items in commits

### Performance
- Profile expensive operations
- Use proper logging levels (DEBUG dev, INFO prod)
- Cache frequently accessed data
- Use database migrations for schema changes

### Security
- Never commit API keys or credentials
- Validate/sanitize external content
- Implement rate limiting for external APIs
- Use environment variables for sensitive config

---

## Important Files

- `new-music-scout-spec.md` - Complete technical specification
- `todo.md` - Official project todo list
- `.env.example` - Environment variable template
- `requirements.txt` - Python dependencies

---

## Development Philosophy

1. **Working software over perfect architecture** - Ship simple features first
2. **Iterate based on real usage** - Let actual needs drive development
3. **Build minimum, then enhance** - Deliver value quickly, add complexity when justified
4. **Document decisions** - Explain why choices were made
5. **Test with real data early** - Validate assumptions with actual feeds

---

**Remember:** Update documentation at the end of every work session!
