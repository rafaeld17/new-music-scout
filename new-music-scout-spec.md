# New Music Scout Agent - Technical Specification

**Last Updated:** 2025-10-18
**Project Status:** Phase 3.5 - 90% Complete (Database rebuilt with 6 working sources, metadata enrichment operational)

---

## Project Overview

A personal music discovery tool focused on **prog/rock/metal genres** that aggregates album reviews from 8 curated sources, enriches metadata via Spotify API, and provides a browsable web interface for discovering new music and building playlists.

**Primary Use Case:** Browse recent 2025 album reviews from trusted sources, see scores and genres, discover tracks, and add them to Spotify playlists.

**Design Philosophy:** Start simple, iterate based on real usage. Quality over complexity.

---

## Current Architecture (Phase 3.5 - Oct 2025)

### What's Working (Updated 2025-10-18)
- ✅ **Backend API:** FastAPI with 5 endpoints serving album/review data
- ✅ **Database:** SQLite with SQLModel ORM (389 reviews from 6 working sources)
- ✅ **RSS Ingestion:** 6 RSS feeds successfully pulling content
- ✅ **Content Processing:** Artist/album extraction, review score parsing, genre classification
- ✅ **Frontend:** React + TypeScript UI with filtering, sorting, and pagination
- ✅ **Spotify Integration:** Client credentials OAuth + metadata enrichment (67.5% coverage)
- ✅ **Enhanced Metadata:** Cascading Spotify → MusicBrainz fetcher operational
- ✅ **Content Classification:** URL-based detection for Metal Storm, pattern-based for MetalSucks

### Working Sources (6/8)
1. **Sonic Perspectives** - 300 reviews (excellent coverage!)
2. **MetalSucks** - 50 reviews (artist/album extraction fixed)
3. **Metal Storm** - 20 reviews (content type detection fixed)
4. **The Prog Report** - 10 reviews
5. **Heavy Music HQ** - 6 reviews
6. **Rock & Blues Muse** - 3 reviews

### Blocked Sources (2/8 - Require Browser Automation)
7. **Blabbermouth** - JavaScript-rendered page (needs Selenium/Playwright)
8. **Kerrang** - React/Next.js app (needs Selenium/Playwright)

---

## Strategic Pivot: Focused Source List + Database Rebuild

### New Core Sources (8 Total)

**Focus:** High-quality prog/rock/metal reviews from 2025 with good coverage

| Source | Type | RSS Available | Reviews URL | Focus | Weight |
|--------|------|---------------|-------------|-------|--------|
| **Kerrang!** | HTML | Yes (general) | https://www.kerrang.com/categories/reviews | Rock, hard rock, alt/modern heavy | 1.3 |
| **Blabbermouth** | RSS+HTML | Yes | https://blabbermouth.net/reviews | Hard rock & metal reviews | 1.0 |
| **MetalSucks** | RSS+HTML | Yes (Feedburner) | https://www.metalsucks.net/category/reviews/ | Metal & hard rock, opinionated | 1.0 |
| **Metal Storm** | HTML | Yes (general) | https://metalstorm.net/pub/reviews.php | Broad metal/heavy rock with ratings | 1.2 |
| **Sonic Perspectives** | HTML | No | https://www.sonicperspectives.com/album-reviews/ | Prog, fusion, hard rock, technical | 1.5 |
| **The Prog Report** | RSS+HTML | Yes (reviews) | https://progreport.com/category/progressive-rock-reviews/ | Progressive rock and prog-metal | 1.2 |
| **Heavy Music HQ** | RSS+HTML | Yes | https://heavymusichq.com/category/album-reviews/ | Hard rock, metal, blues-rock | 1.2 |
| **Rock & Blues Muse** | HTML | No | https://www.rockandbluesmuse.com/category/album-reviews/ | Blues-rock, rootsy, classic-leaning | 1.0 |

### Ingestion Strategy

**Two-Tiered Approach:**

1. **RSS Sources (Quick wins):**
   - Blabbermouth, MetalSucks, The Prog Report, Heavy Music HQ
   - **Initial:** Fetch last 100 items from RSS (covers last few months)
   - **Weekly:** Poll for last 50 items

2. **HTML Pagination (Historical scraping):**
   - Kerrang, Metal Storm, Sonic Perspectives, Rock & Blues Muse
   - **Initial:** Scrape paginated review archives back to Jan 1, 2025
   - **Weekly:** Scrape first 2-3 pages (covers latest ~50 reviews)

**Implementation:**
- Build `HistoricalScraper` framework with pagination logic
- Site-specific scrapers for each HTML source
- Rate limiting: 1 sec between pages, 5 sec between sources
- Store `last_scraped_page` in Source table for resume capability

---

## Enhanced Metadata Strategy

### Problem Statement
Current MusicBrainz-only approach has poor coverage for modern releases:
- ❌ Failed: Porcupine Tree - Closure/Continuation (2022)
- ✅ Worked: Dream Theater - Metropolis Pt. 2 (1999)
- ✅ Worked: Tool - Fear Inoculum (2019)

**Conclusion:** Need Spotify as primary metadata source

### Solution: Multi-API Cascading Enrichment

**Architecture:**
```
Album/Artist → 1. Try Spotify (Primary)
              ↓
              2. Fallback to MusicBrainz
              ↓
              3. Store best result
```

**Why Spotify Primary:**
1. **Best coverage** for 2020+ releases (target: 2025 reviews)
2. **Rich metadata:** Genres, popularity, cover art, release dates
3. **Already needed:** Phase 4 requires Spotify for playlist building
4. **Rate limits:** Very reasonable (429 req/30sec = ~1440 albums/min)

### Metadata Fields to Capture

**From Spotify:**
```python
{
  "spotify_album_id": "xyz123",
  "spotify_artist_id": "abc456",
  "artist_name": "Tool",
  "album_title": "Fear Inoculum",
  "release_date": "2019-08-07",
  "album_type": "album",  # or "single", "EP"
  "genres": ["progressive metal", "alternative metal", "progressive rock"],
  "cover_art_url": "https://i.scdn.co/image/...",
  "artist_popularity": 82,  # 0-100
  "artist_followers": 3200000,
  "label": "RCA Records"
}
```

**From MusicBrainz (fallback):**
```python
{
  "musicbrainz_id": "a0b21967-...",
  "genres": ["progressive metal", "alternative metal"],
  "cover_art_url": "https://coverartarchive.org/..."
}
```

### Auto-Enrichment During Ingestion

**Flow:**
```
RSS/HTML Parse → Extract Artist/Album → Spotify Search → Store Metadata → Save to DB
                                       ↓ (if fails)
                                       MusicBrainz Search
```

**Benefits:**
- Every album gets rich metadata from the start
- No manual refresh step required
- Immediate value for browsing/filtering

---

## Data Models (Updated for Metadata)

### Enhanced MusicItem Model

```python
class MusicItem(SQLModel, table=True):
    """Core content item with embedded metadata."""

    # Core fields (existing)
    id: Optional[int] = Field(primary_key=True)
    source_id: int = Field(foreign_key="source.id")
    url: str = Field(unique=True)
    title: str
    published_date: datetime
    content_type: ContentType  # REVIEW, NEWS, PREMIERE, etc.

    # Extracted content (existing)
    artists: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    album: Optional[str]
    review_score: Optional[float]  # Normalized 0-10
    review_score_raw: Optional[str]  # "8/10", "4/5", etc.
    genres: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    tracks: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    # NEW: Spotify metadata
    spotify_album_id: Optional[str] = Field(default=None, max_length=100)
    spotify_artist_id: Optional[str] = Field(default=None, max_length=100)
    artist_popularity: Optional[int]  # 0-100
    album_popularity: Optional[int]

    # NEW: MusicBrainz metadata (fallback)
    musicbrainz_id: Optional[str] = Field(default=None, max_length=100)

    # NEW: Enriched metadata
    album_genres: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    album_cover_url: Optional[str] = Field(default=None, max_length=500)
    release_date: Optional[date]
    album_type: Optional[str]  # "album", "single", "EP"
    label: Optional[str]

    # NEW: Metadata tracking
    metadata_source: Optional[str]  # "spotify", "musicbrainz", "none"
    metadata_fetched_at: Optional[datetime]
```

### Updated Source Model

```python
class Source(SQLModel, table=True):
    """Content source with scraping configuration."""

    id: Optional[int] = Field(primary_key=True)
    name: str = Field(unique=True)
    url: str
    source_type: SourceType  # RSS, HTML
    weight: float = 1.0
    enabled: bool = True

    # Scraping state
    last_crawled: Optional[datetime]
    last_scraped_page: Optional[int]  # For pagination resume
    scrape_depth: int = 3  # How many pages to scrape weekly

    # Health tracking
    health_score: float = 1.0
    consecutive_failures: int = 0
```

---

## Implementation Phases (Revised)

### ✅ Phase 1-3: Foundation (COMPLETED)
- Infrastructure, content processing, basic album browser
- **Status:** 900 items, 17 sources, working frontend

### ✅ Phase 3.5: Database Rebuild + Metadata Enrichment (90% COMPLETE)

**Duration:** 1-2 weeks
**Goal:** Clean focused database with rich Spotify metadata

**Tasks:**
1. ✅ **Research metadata APIs** (Spotify, MusicBrainz comparison)
2. ✅ **Implement Spotify integration**
   - ✅ Client credentials OAuth flow
   - ✅ Album search API
   - ✅ Artist metadata API
   - ✅ Caching and rate limiting
3. ✅ **Create EnhancedMetadataFetcher**
   - ✅ Spotify primary, MusicBrainz fallback
   - ✅ Auto-enrichment during ingestion
4. ✅ **Database cleanup script**
   - ✅ Remove 9 non-target sources
   - ✅ Keep only 8 core sources
   - ✅ Vacuum database
5. ✅ **Content classification fixes**
   - ✅ Metal Storm URL-based detection (review.php)
   - ✅ MetalSucks artist/album extraction (Review: prefix handling)
   - ✅ Re-classified 20 Metal Storm items
   - ✅ Extracted metadata for 8 MetalSucks reviews
6. ✅ **Initial ingestion with enrichment**
   - ✅ Pull 2025 content from 6 working RSS sources
   - ✅ Auto-enrich with Spotify metadata
   - ✅ Validated coverage (67.5% metadata coverage)
7. ⏳ **Historical scraping framework** (DEFERRED - see notes)
   - ✅ Base scraper class created
   - ❌ Blabbermouth scraper (requires Selenium - JS-rendered)
   - ❌ Kerrang scraper (requires Selenium - React/Next.js)
8. ⏳ **Weekly auto-ingestion setup** (NEXT)

**Success Achieved:**
- ✅ 6/8 sources configured and ingesting (2 blocked by JS rendering)
- ✅ 67.5% of albums have Spotify metadata (291/431 items)
- ✅ Cover art, genres, release dates populated
- ✅ Performance: < 1 sec per album enrichment
- ✅ 389 reviews total (369 reviews + 20 other content)

**Deferred:**
- Blabbermouth & Kerrang scrapers require browser automation (Selenium/Playwright)
- Decision: Focus on 6 working sources, add JS scrapers in Phase 5 if needed

### 📋 Phase 4: Enhanced Spotify Integration (NEXT)

**Duration:** 2-3 weeks
**Goal:** Full Spotify OAuth for playlist management

**Tasks:**
- OAuth2 authorization code flow (user authentication)
- Playlist management (create, add tracks, list playlists)
- Track search and matching
- "Add to Playlist" workflow in UI
- Spotify embeds on album detail pages

### 📋 Phase 5: Advanced Features (FUTURE)

**Smart Album Matching:**
- Fuzzy string matching with `rapidfuzz`
- Handle remasters, deluxe editions
- MusicBrainz canonical data

**Review Analytics:**
- Weighted averages with source weights
- Consensus strength metrics
- Controversy scores

**Automation:**
- Weekly email digests
- Automated discovery playlists
- Personalized recommendations

---

## Technical Stack

### Backend
- **Framework:** FastAPI (Python 3.13)
- **Database:** SQLite (dev) → PostgreSQL (production)
- **ORM:** SQLModel
- **RSS:** feedparser
- **HTML:** BeautifulSoup4, requests
- **APIs:** Spotify Web API, MusicBrainz API

### Frontend
- **Framework:** React 19 + TypeScript
- **Build:** Vite
- **Routing:** React Router
- **Styling:** Plain CSS (component-scoped)

### External APIs
- **Spotify Web API:**
  - Client Credentials (metadata enrichment)
  - Authorization Code Flow (playlist management)
- **MusicBrainz API:**
  - Album/artist search (fallback)
  - Cover Art Archive

### Infrastructure
- **Development:** Local SQLite + npm dev server
- **Production:** Docker (future)
- **CI/CD:** Not yet implemented

---

## API Endpoints (Current)

```
GET /api/items                    # All music items with filtering
GET /api/reviews                  # Reviews with score filtering
GET /api/news                     # News items
GET /api/sources                  # Available sources with counts
GET /api/albums                   # Albums grouped by artist+album
    ?limit=50
    &offset=0
    &source=1,2,3                 # Filter by source IDs
    &genre=prog+rock,prog+metal   # Filter by genres
```

**Future endpoints:**
```
GET /api/albums/{id}              # Album detail with all reviews
GET /api/tracks                   # Extracted tracks/singles
POST /api/spotify/playlist        # Create Spotify playlist
GET /api/spotify/search           # Search Spotify catalog
```

---

## Configuration

### Environment Variables (.env)

```bash
# Database
DATABASE_URL=sqlite:///./music_scout.db

# Spotify API (Required for Phase 3.5+)
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here

# MusicBrainz (Optional - has defaults)
MUSICBRAINZ_API_URL=https://musicbrainz.org/ws/2

# Server
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
LOG_LEVEL=INFO
```

### Source Configuration (In Code)

```python
CORE_SOURCES = [
    {
        "name": "Kerrang!",
        "url": "https://www.kerrang.com/categories/reviews",
        "rss": "https://www.kerrang.com/feed.rss",
        "type": "HTML",
        "weight": 1.3
    },
    {
        "name": "Blabbermouth",
        "url": "https://blabbermouth.net/reviews",
        "rss": "https://www.blabbermouth.net/feed.rss",
        "type": "RSS",
        "weight": 1.0
    },
    # ... 6 more sources
]
```

---

## Development Commands

### Initial Setup
```bash
# Environment
cp .env.example .env
# Add Spotify credentials to .env

# Dependencies
pip install -r requirements.txt
cd frontend && npm install

# Database
alembic upgrade head
```

### Daily Development
```bash
# Backend (terminal 1)
python -m src.music_scout.main

# Frontend (terminal 2)
cd frontend && npm run dev

# Ingestion (terminal 3)
python -m src.music_scout.cli.ingest ingest
```

### Database Management
```bash
# List sources
python -m src.music_scout.cli.ingest list

# Add new source
python -m src.music_scout.cli.ingest add \
  --name "Source Name" \
  --url "https://example.com/reviews" \
  --type HTML \
  --weight 1.2

# Cleanup database (remove non-target sources)
python -m src.music_scout.cli.cleanup --keep-ids 1,2,3,4,5,6,7,8

# Refresh metadata
python -m src.music_scout.cli.refresh_metadata --source spotify
```

---

## Success Metrics

### Phase 3.5 Targets
- **Metadata Coverage:** 85%+ albums with Spotify metadata
- **Source Count:** Exactly 8 active sources
- **Data Quality:** 90%+ reviews with valid scores
- **Performance:** < 2 sec album list load time
- **Historical Coverage:** All 2025 reviews from target sources

### Long-term Targets (Phase 4+)
- **User Engagement:** 70%+ retention after 4 weeks
- **Playlist Creation:** 60%+ users create playlists
- **Source Reliability:** 95%+ uptime per source
- **Recommendation Quality:** 80%+ user satisfaction

---

## Risk Assessment & Mitigation

### Technical Risks

**1. Spotify API Rate Limits**
- **Risk:** 429 errors during bulk enrichment
- **Mitigation:** Request batching, caching, exponential backoff

**2. HTML Structure Changes**
- **Risk:** Scrapers break when sites redesign
- **Mitigation:** Graceful degradation, health monitoring, alerts

**3. Poor Metadata Matches**
- **Risk:** Spotify returns wrong album/artist
- **Mitigation:** Confidence scoring, manual override system

### Data Quality Risks

**1. Missing Review Scores**
- **Risk:** RSS doesn't contain full score data
- **Mitigation:** HTML scraping fallback, score extraction from text

**2. Duplicate Albums**
- **Risk:** "Album" vs "Album (Deluxe)" creates duplicates
- **Mitigation:** Fuzzy matching in Phase 5, Spotify ID deduplication

---

## Documentation Maintenance Protocol

### When to Update This File (new-music-scout-spec.md)

**REQUIRED Updates:**
1. **Architecture changes** - New models, APIs, or major refactors
2. **Source list changes** - Adding/removing sources
3. **Phase completion** - Mark phases complete, update status
4. **API endpoint changes** - New endpoints or parameter changes
5. **Data model changes** - New fields or schema migrations

**Process:**
1. Make change in code
2. Update spec immediately
3. Update `Last Updated` date at top
4. Commit spec with code changes

### When to Update todo.md

**REQUIRED Updates:**
1. **Starting new task** - Mark task as in progress
2. **Completing task** - Mark as complete, add completion date
3. **Discovering new work** - Add new tasks to appropriate phase
4. **Changing priorities** - Reorder tasks, update status
5. **Weekly reviews** - Update overall progress, adjust estimates

**Process:**
1. Update at start and end of each work session
2. Add context notes for blockers
3. Update percentage complete for phases
4. Keep top-level status summary current

### Enforcing Documentation Updates

**In CLAUDE.md instructions:**
```markdown
## Documentation Update Requirements

**CRITICAL:** After any significant change, you MUST:
1. Update new-music-scout-spec.md if architecture/API changed
2. Update todo.md with task progress
3. Update CLAUDE.md if development workflow changed

**How to remember:**
- Read CLAUDE.md at start of every session
- Check if changes affect documented architecture
- Update docs BEFORE marking task complete
```

---

## Appendix: Current Stats

**Last Census:** 2025-10-18 (Post-Rebuild)

### Actual Results
- **Total Items:** 431 (from 6 working sources + 2 inactive)
- **Reviews:** 389 (90.3%)
- **Metadata Coverage:** 291 items (67.5%)
  - Spotify: 264 items (61.3%)
  - MusicBrainz: 27 items (6.3%)
- **Sources:** 8 configured (6 working, 2 blocked by JS)
- **Date Range:** 2022-11-11 to 2025-10-18
- **Test Coverage:** 25 tests passing
- **API Response Time:** < 2 sec average
- **Frontend Load Time:** < 1 sec

### By Source
1. Sonic Perspectives: 300 reviews
2. MetalSucks: 50 reviews
3. Metal Storm: 20 reviews
4. The Prog Report: 10 reviews
5. Heavy Music HQ: 6 reviews
6. Rock & Blues Muse: 3 reviews
7. Blabbermouth: 0 reviews (JS-rendered page - blocked)
8. Kerrang: 0 reviews (React app - blocked)

### Phase 3.5 Assessment
- ✅ **Exceeded review count target** (389 vs 350 target)
- ⚠️ **Below metadata coverage target** (67.5% vs 85% target)
  - Reason: Many reviews lack proper artist/album extraction
  - Solution: Improved extraction patterns in Phase 4
- ✅ **Database cleaned** (8 sources configured)
- ✅ **Spotify enrichment operational**
- ⚠️ **6/8 sources working** (2 blocked by JS rendering)
