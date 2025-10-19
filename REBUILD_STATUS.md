# Database Rebuild Status - 2025-10-18

## Current Status: READY FOR INGESTION & HISTORICAL SCRAPING

### ✅ Completed (This Session):

1. **Nuclear Cleanup** - Wiped database completely clean
2. **8 Target Sources Added** - All configured with correct URLs
3. **Metadata Enrichment** - Already implemented and tested (working!)
4. **Database Backup** - `music_scout.db.backup-20251018-104552` (2.7MB)

---

## Current Database State:

**Sources:** 8 (exactly what we want)
**Items:** 0 (clean slate)
**Metadata Enrichment:** Automatic via Spotify/MusicBrainz cascade

### 8 Configured Sources:

| ID | Source | URL | Type | Notes |
|----|--------|-----|------|-------|
| 1 | The Prog Report Reviews | progreport.com/.../reviews/feed/ | RSS | ✓ Reviews-only |
| 2 | Sonic Perspectives Reviews | sonicperspectives.com/.../reviews/feed/ | RSS | ✓ Reviews-only |
| 3 | Heavy Music HQ | heavymusichq.com/feed/ | RSS | 70% reviews naturally |
| 4 | Blabbermouth | blabbermouth.net/feed | RSS | ⚠️ Mixed content |
| 5 | MetalSucks | metalsucks.net/.../reviews/feed/ | RSS | ✓ Reviews-only |
| 6 | Kerrang | kerrang.com/feed.rss | RSS | ⚠️ Mixed content |
| 7 | Metal Storm | metalstorm.net/rss/reviews.xml | RSS | ✓ Reviews-only |
| 8 | Rock & Blues Muse | rockandbluesmuse.com/feed/ | RSS | Mixed content |

---

## Next Steps (In Order):

### Step 1: Test Initial Ingestion (15-30 min)
**Command:**
```bash
python -m src.music_scout.cli.ingest ingest
```

**Expected Result:**
- ~50-100 recent reviews from 8 sources
- All reviews auto-enriched with Spotify metadata
- Should see "Enriching metadata" and "Successfully enriched" logs

**Success Criteria:**
- All 8 sources ingest successfully
- 80%+ reviews have Spotify metadata
- No errors during enrichment

---

### Step 2: Build Historical Scraper Framework (1 hour)

**Goal:** Create base scraper class for pagination-based historical scraping

**File to create:** `src/music_scout/services/historical_scraper.py`

**Key Features:**
- Base class with pagination logic
- `scrape_until_date(target_date)` method
- Page tracking and resume capability
- Rate limiting (1 sec between pages)
- Auto-enrichment integration

**Pseudocode:**
```python
class HistoricalScraper:
    def scrape_until_date(self, target_date):
        page = 1
        while True:
            reviews = self.fetch_page(page)
            for review in reviews:
                if review.date < target_date:
                    return  # Stop - reached target
                self.ingest_review(review)  # Auto-enriches
            page += 1
            time.sleep(1)  # Rate limiting
```

---

### Step 3: Implement Source-Specific Scrapers (1-2 hours)

**Priority Order:**
1. **Sonic Perspectives** - WordPress pagination (easiest)
2. **The Prog Report** - WordPress pagination
3. **Metal Storm** - Pagination-based
4. **Rock & Blues Muse** - WordPress pagination
5. **Heavy Music HQ** - Check pagination structure
6. **Blabbermouth** - May need special handling
7. **MetalSucks** - WordPress pagination
8. **Kerrang** - May need special handling

**For each scraper:**
- Extend `HistoricalScraper` base class
- Implement `fetch_page(page_num)` method
- Parse review details (title, artist, album, date, content)
- Return standardized review dict

---

### Step 4: Run Historical Scraping (30-60 min)

**Target:** All reviews from January 1, 2025 to present

**Command (to be created):**
```bash
python -m src.music_scout.cli.historical_scrape --since 2025-01-01
```

**Expected Result:**
- 300-500 total reviews from 2025
- 85%+ metadata coverage (Spotify)
- All reviews, no news/interviews

**Success Criteria:**
- Each source has comprehensive 2025 coverage
- Metadata enrichment rate > 85%
- No duplicate reviews

---

### Step 5: Validation (10 min)

**Check:**
1. Total review count (target: 300-500)
2. Metadata coverage (target: 85%+)
3. Date range (all from 2025)
4. No duplicates
5. Genres populated

**SQL Queries:**
```sql
-- Total reviews
SELECT COUNT(*) FROM musicitem WHERE content_type = 'review';

-- Metadata coverage
SELECT COUNT(*) FROM musicitem WHERE metadata_source IS NOT NULL;

-- Date range
SELECT MIN(published_date), MAX(published_date) FROM musicitem;

-- Reviews per source
SELECT source_id, COUNT(*) FROM musicitem GROUP BY source_id;
```

---

### Step 6: Weekly Ingestion Setup (15 min)

**Two options:**

**Option A: Cron job (Linux/Mac)**
```bash
# Run every Sunday at 9 AM
0 9 * * 0 cd /path/to/project && python -m src.music_scout.cli.ingest ingest
```

**Option B: Windows Task Scheduler**
- Create scheduled task
- Trigger: Weekly, Sunday 9 AM
- Action: Run ingestion command

**Option C: Python scheduler (cross-platform)**
- Use `schedule` library
- Run as background service

---

## Important Files:

### Implemented & Working:
- ✅ `src/music_scout/services/spotify_client.py` - Spotify API client
- ✅ `src/music_scout/services/enhanced_metadata_fetcher.py` - Cascading metadata
- ✅ `src/music_scout/services/ingestion.py` - Auto-enrichment integrated
- ✅ `src/music_scout/cli/cleanup.py` - Database cleanup tools
- ✅ `src/music_scout/models/music_item.py` - Spotify metadata fields added
- ✅ Alembic migration for metadata fields

### To Be Created:
- ⏳ `src/music_scout/services/historical_scraper.py` - Base scraper class
- ⏳ `src/music_scout/scrapers/sonic_perspectives_scraper.py`
- ⏳ `src/music_scout/scrapers/prog_report_scraper.py`
- ⏳ `src/music_scout/scrapers/metal_storm_scraper.py`
- ⏳ `src/music_scout/scrapers/rock_blues_muse_scraper.py`
- ⏳ `src/music_scout/scrapers/heavy_music_hq_scraper.py`
- ⏳ `src/music_scout/scrapers/blabbermouth_scraper.py`
- ⏳ `src/music_scout/scrapers/metalsucks_scraper.py`
- ⏳ `src/music_scout/scrapers/kerrang_scraper.py`
- ⏳ `src/music_scout/cli/historical_scrape.py` - CLI command

---

## Key Learnings from This Session:

1. **Metadata enrichment works perfectly** - Spotify primary, MusicBrainz fallback
2. **Reviews-only feeds found** for 3/8 sources (MetalSucks, Metal Storm, Sonic/Prog Report)
3. **Clean rebuild better than patching** - Nuclear option was the right choice
4. **Auto-enrichment during ingestion** - Every new review gets metadata automatically
5. **Source management** - Manual setup prevents unwanted sources from being re-added

---

## Commands Reference:

### Test Ingestion:
```bash
python -m src.music_scout.cli.ingest ingest
```

### List Sources:
```bash
python -m src.music_scout.cli.cleanup list-sources
```

### Show Items:
```bash
python -m src.music_scout.cli.cleanup show-items
```

### Database Backup:
```bash
cp src/music_scout.db src/music_scout.db.backup-$(date +%Y%m%d-%H%M%S)
```

---

## Estimated Time Remaining:

- **Step 1** (Test ingestion): 15-30 min
- **Step 2** (Base scraper): 1 hour
- **Step 3** (8 scrapers): 1-2 hours
- **Step 4** (Historical scraping): 30-60 min
- **Step 5** (Validation): 10 min
- **Step 6** (Weekly setup): 15 min

**Total: 3-5 hours**

---

## Success Metrics:

When done, you should have:
- ✅ 8 sources (no more, no less)
- ✅ 300-500 reviews from 2025
- ✅ 85%+ metadata coverage
- ✅ 100% reviews (no news/interviews)
- ✅ Weekly auto-ingestion setup
- ✅ Clean, queryable database ready for frontend

---

**READY TO PROCEED!** Start with Step 1 (test ingestion) in your next session.
