# New Music Scout - Official Project Todo List

**Last Updated:** 2025-10-19
**Current Phase:** Phase 3.6 - Production-Ready Web App (Deployment infrastructure complete!)
**Overall Progress:** 85% complete (Phases 1-3.5 done, Phase 3.6 deployment ready)

---

## 🎯 Current Sprint: Phase 3.6 - Production-Ready Web App (2-3 weeks)

**Goal:** Deploy a working web app that displays reviews and can run in production
**Status:** 🚧 IN PROGRESS (0% complete)
**Started:** 2025-10-18

### 📋 Week 1: Core UI Improvements (3-4 days)

**Goal:** Make the UI actually display review content

- [x] **Display review content in UI** (Priority: CRITICAL) - COMPLETED 2025-10-18
  - [x] Add review excerpt/content to AlbumCard component
  - [x] Show full review content in AlbumDetail page
  - [x] Ensure API returns content field from database
  - [x] Test with real review data

- [ ] **Improve metadata coverage** (Priority: HIGH)
  - [ ] Analyze 140 items without Spotify metadata
  - [ ] Enhance artist/album extraction patterns
  - [ ] Re-run enrichment on failed items
  - [ ] Target: 85%+ metadata coverage

- [ ] **UI polish** (Priority: MEDIUM)
  - [ ] Update footer to show all 6 active sources
  - [ ] Add loading states for review content
  - [ ] Handle missing metadata gracefully
  - [ ] Improve error messages

### 📋 Week 2: Production Infrastructure (3-4 days)

**Goal:** Create deployment-ready infrastructure

- [x] **Docker setup** (Priority: CRITICAL) - COMPLETED 2025-10-19
  - [x] Create Dockerfile for backend (multi-stage build)
  - [x] Create Dockerfile for frontend with nginx
  - [x] Add .dockerignore files for faster builds
  - [x] Configure nginx for React Router support

- [x] **Database configuration** (Priority: HIGH) - COMPLETED 2025-10-19
  - [x] Keep SQLite for production (free tier, perfect for single user)
  - [x] Update DATABASE_URL env var handling for persistent volume
  - [x] Document PostgreSQL migration path for future
  - [x] Add persistent disk configuration in render.yaml

- [x] **Configuration management** (Priority: HIGH) - COMPLETED 2025-10-19
  - [x] Environment-based CORS configuration
  - [x] Add ALLOWED_ORIGINS env var support
  - [x] Add VITE_API_URL for frontend API calls
  - [x] Document all required env vars in DEPLOY.md

- [ ] **Fix deprecation warnings** (Priority: MEDIUM)
  - [ ] Fix Pydantic v2 warnings (schema_extra → json_schema_extra)
  - [ ] Fix FastAPI lifespan event handlers
  - [ ] Update to latest dependency versions

### 📋 Week 3: Deployment & Automation (2-3 days)

**Goal:** Deploy to production and automate ingestion

- [x] **Choose hosting platform** (Priority: CRITICAL) - COMPLETED 2025-10-19
  - [x] Evaluated: Render, Railway, DigitalOcean, Fly.io
  - [x] Decision: Render.com (free tier, SQLite support, cron jobs)
  - [x] Created render.yaml deployment configuration

- [x] **Deployment configuration** (Priority: CRITICAL) - COMPLETED 2025-10-19
  - [x] Created comprehensive DEPLOY.md guide
  - [x] Configured backend service with persistent disk
  - [x] Configured frontend static site
  - [x] Configured cron job for scheduled ingestion
  - [x] Documented all deployment steps

- [ ] **Deploy to production** (Priority: CRITICAL) - READY TO GO!
  - [ ] Push code to GitHub
  - [ ] Create Render account
  - [ ] Deploy backend service
  - [ ] Deploy frontend service
  - [ ] Set up cron job for ingestion
  - [ ] Run initial data seed
  - [ ] Test end-to-end functionality

- [x] **Production ingestion automation** (Priority: HIGH) - COMPLETED 2025-10-19
  - [x] Configured daily cron job (3 AM UTC)
  - [x] Shared persistent disk with backend
  - [x] Logging configured
  - [ ] Test in production (after deployment)

- [ ] **Monitoring & health checks** (Priority: MEDIUM)
  - [x] /health endpoint already exists
  - [ ] Set up uptime monitoring (UptimeRobot recommended)
  - [ ] Monitor ingestion cron job logs
  - [ ] Optional: Add error tracking (Sentry)

### Success Criteria for Phase 3.6

- ✅ Review content visible in UI
- ✅ 85%+ metadata coverage
- ✅ Deployed to production with custom domain
- ✅ Weekly ingestion running automatically
- ✅ 99%+ uptime over first month
- ✅ All 389 reviews accessible and browsable

---

## 🎯 Previous Sprint: Phase 3.5 - Database Rebuild + Metadata (1-2 weeks)

**Goal:** Clean focused database (8 sources) with rich Spotify metadata
**Status:** ✅ COMPLETE
**Completed:** 2025-10-18

### ✅ Completed Tasks (2025-10-18)

**Metadata Integration:**
- [x] Research metadata APIs
- [x] Implement Spotify client integration
  - [x] Client credentials OAuth flow
  - [x] Album search API
  - [x] Artist metadata API
  - [x] Rate limiting and retry logic
- [x] Create Enhanced Metadata Fetcher
  - [x] Cascading logic (Spotify → MusicBrainz)
  - [x] Auto-enrichment during ingestion
- [x] Add metadata fields to MusicItem model
- [x] Create Alembic migration for new fields

**Database Cleanup:**
- [x] Create cleanup CLI script
- [x] Remove non-target sources (kept 8 core sources)
- [x] Database backup before cleanup
- [x] Validation: confirmed 8 sources configured

**Content Classification Fixes:**
- [x] Fix Metal Storm content type detection (URL-based with review.php)
- [x] Fix MetalSucks artist/album extraction (Review: prefix handling)
- [x] Re-classify 20 Metal Storm items as REVIEW
- [x] Re-extract metadata for 8 MetalSucks reviews

**Ingestion & Validation:**
- [x] Initial ingestion from 6 working RSS sources
- [x] Auto-enrichment operational (67.5% coverage)
- [x] Created source overview report tool
- [x] Validated results: 389 reviews total

**Historical Scraping:**
- [x] Create base HistoricalScraper class
- [x] Evaluate Blabbermouth scraping (BLOCKED - requires Selenium)
- [x] Evaluate Kerrang scraping (BLOCKED - requires Selenium)

### 📋 Deferred Items (Moved to Phase 3.6 or Later)

**1. Weekly Auto-Ingestion Setup** → **Moved to Phase 3.6 Week 3**
- ✅ Created automation scripts (run_weekly_ingestion.bat, scheduler.py)
- ✅ Documented setup in AUTOMATION_SETUP.md
- ⏳ Deployment to production pending

**2. Improve Metadata Coverage** → **Moved to Phase 3.6 Week 1**
- ⏳ Analyze 140 items without metadata
- ⏳ Improve artist/album extraction patterns
- ⏳ Re-run enrichment on failed items
- ⏳ Target: 85%+ coverage

**3. JavaScript Scrapers** → **Deferred to Phase 5**
- ⏳ Evaluate Selenium/Playwright for Blabbermouth
- ⏳ Evaluate Selenium/Playwright for Kerrang
- ⏳ Implement if value justifies complexity

---

## 📋 Phase 4: Enhanced Spotify Integration (2-3 weeks)

**Goal:** Full OAuth2 for playlist management
**Status:** 📋 PLANNED
**Estimated Start:** After Phase 3.6 completion (~2025-11-10)

### Tasks
- [ ] Implement OAuth2 authorization code flow
  - User login redirect to Spotify
  - Token exchange and storage
  - Refresh token logic
- [ ] Playlist management endpoints
  - List user playlists
  - Create new playlist
  - Add tracks to playlist
  - Remove tracks from playlist
- [ ] Frontend integration
  - "Add to Playlist" buttons
  - Track selection basket/queue
  - Playlist picker modal
  - Spotify embeds on album detail page
- [ ] Track search and matching
  - Search Spotify by track name + artist
  - Confidence scoring for matches
  - Handle tracks not found on Spotify

**Success Criteria:**
- Can authenticate with Spotify
- Can create and manage playlists from UI
- Can add tracks from reviews to playlists
- 80%+ track search accuracy

---

## 📋 Phase 5: Advanced Features (FUTURE - 3-4 weeks)

**Status:** 📋 DEFERRED

### Features
- **Smart Album Matching**
  - Fuzzy string matching (rapidfuzz)
  - Handle deluxe editions, remasters
  - Spotify ID-based deduplication

- **Review Analytics**
  - Weighted average scores
  - Consensus strength metrics
  - Controversy scores
  - Source agreement visualization

- **Additional Sources**
  - Expand beyond 8 core sources
  - More niche sources (doom metal, stoner rock, etc.)

- **Personalization**
  - User preference profiles
  - Spotify library integration
  - Personalized recommendations
  - Weekly email digests
  - Automated discovery playlists

---

## 🐛 Known Issues & Tech Debt

### High Priority
- [ ] **Metadata coverage gaps** - MusicBrainz insufficient (Phase 3.5 addresses)
- [ ] **Too many sources** - Need to focus (Phase 3.5 addresses)

### Medium Priority
- [ ] **Missing review scores** - RSS feeds don't contain full scores
  - Solution: HTML scraping for full article content
- [ ] **No historical data** - Only recent RSS items (~50 per feed)
  - Solution: Historical scraping (Phase 3.5)
- [ ] **Complex aggregation code** - Built but not aligned with goals
  - Solution: Remove in Phase 5 or repurpose

### Low Priority
- [ ] Pydantic deprecation warnings (non-blocking)
- [ ] FastAPI event handler deprecations (non-blocking)
- [ ] Unicode encoding issues in CLI output

---

## 📊 Project Stats

### Actual State (Post-Rebuild - 2025-10-18)
- **Total Items:** 431
- **Sources:** 8 configured (6 working, 2 blocked by JS)
- **Reviews:** 389 (90.3%)
- **Metadata Coverage:** 67.5% (Spotify 61.3%, MusicBrainz 6.3%)
  - 291 items with metadata
  - 264 via Spotify
  - 27 via MusicBrainz
- **Date Range:** 2022-11-11 to 2025-10-18
- **Test Coverage:** 25 tests passing

### By Source
1. Sonic Perspectives: 300 reviews (⭐ star performer!)
2. MetalSucks: 50 reviews
3. Metal Storm: 20 reviews
4. The Prog Report: 10 reviews
5. Heavy Music HQ: 6 reviews
6. Rock & Blues Muse: 3 reviews
7. Blabbermouth: 0 reviews (blocked - JS-rendered)
8. Kerrang: 0 reviews (blocked - React/Next.js)

### Assessment vs Targets
- ✅ **Exceeded review count** (389 vs 350 target)
- ⚠️ **Below metadata coverage** (67.5% vs 85% target)
  - Reason: Artist/album extraction needs improvement
  - Action: Phase 4 enhancement
- ✅ **Database cleaned** (8 sources)
- ⚠️ **75% source success rate** (6/8 working)

---

## 🎓 Development Best Practices

### Before Starting Work
1. ✅ Read CLAUDE.md for project context
2. ✅ Check this todo.md for current priorities
3. ✅ Review new-music-scout-spec.md if touching architecture

### During Development
1. ✅ Mark todo item as in progress
2. ✅ Commit frequently with descriptive messages
3. ✅ Test changes before moving on
4. ✅ Update documentation if architecture changes

### After Completing Task
1. ✅ Mark todo item as complete with date
2. ✅ Update new-music-scout-spec.md if needed
3. ✅ Update this todo.md with new tasks discovered
4. ✅ Run tests to ensure nothing broke
5. ✅ Commit with reference to completed todo item

### Documentation Update Triggers

**MUST update new-music-scout-spec.md when:**
- Adding/removing sources
- Changing data models (new fields, migrations)
- Adding/modifying API endpoints
- Changing external API integrations
- Completing a phase

**MUST update todo.md when:**
- Starting new task
- Completing task
- Discovering new work
- Changing priorities
- Weekly progress review

**MUST update CLAUDE.md when:**
- Changing development workflow
- Adding new make commands
- Updating setup instructions

---

## 📝 Quick Reference Commands

### Daily Development
```bash
# Start backend
python -m src.music_scout.main

# Start frontend
cd frontend && npm run dev

# Ingest content
python -m src.music_scout.cli.ingest ingest

# List sources
python -m src.music_scout.cli.ingest list
```

### Database Management
```bash
# Backup database
cp music_scout.db music_scout.db.backup

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"

# Cleanup database (Phase 3.5)
python -m src.music_scout.cli.cleanup --keep-ids 1,2,3,4,5,6,7,8
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_metadata_fetcher.py

# Run with coverage
pytest --cov=src/music_scout
```

---

## 🎯 Success Metrics

### Phase 3.5 Targets
- ✅ Spotify client implemented and tested
- ✅ Metadata enrichment working (85%+ coverage)
- ✅ Database cleaned (8 sources only)
- ✅ Historical scraping operational
- ✅ 300-400 reviews from 2025 ingested
- ✅ Performance: < 2 sec album list load

### Long-term Vision
A focused music discovery tool that:
- Aggregates reviews from 8 trusted prog/rock/metal sources
- Provides rich metadata (Spotify-powered) for every album
- Allows browsing and filtering by genre, source, score
- Enables playlist building via Spotify integration
- Learns user preferences over time (Phase 5)
- Generates weekly discovery playlists automatically (Phase 5)

---

**Remember:** Update this file at start and end of every work session!
