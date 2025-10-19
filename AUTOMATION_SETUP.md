# Weekly Auto-Ingestion Setup Guide

This guide explains how to set up automated weekly ingestion for New Music Scout.

## Overview

The system will automatically fetch new reviews from all enabled sources every week, enriching them with Spotify metadata.

**Recommended Schedule:** Every Sunday at 9:00 AM

---

## Option 1: Windows Task Scheduler (Recommended for Windows)

### Setup Steps

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create New Task**
   - Click "Create Basic Task" in the right panel
   - Name: `Music Scout Weekly Ingestion`
   - Description: `Automatically fetch new music reviews every week`

3. **Set Trigger**
   - Trigger: Weekly
   - Start: Choose next Sunday
   - Time: 9:00 AM
   - Recur every: 1 week
   - Day: Sunday

4. **Set Action**
   - Action: Start a program
   - Program/script: Browse to `run_weekly_ingestion.bat`
   - Full path: `C:\Users\rafae\Projects\personal-music-tracker\run_weekly_ingestion.bat`
   - Start in: `C:\Users\rafae\Projects\personal-music-tracker`

5. **Finish & Test**
   - Check "Open Properties dialog when I click Finish"
   - In Properties → Settings:
     - ✓ Run task as soon as possible after a scheduled start is missed
     - ✓ If task fails, restart every: 10 minutes
   - Click OK, enter your Windows password if prompted

6. **Test the Task**
   - Right-click the task → "Run"
   - Check that ingestion runs successfully

### View Logs

Task Scheduler logs can be viewed in:
- Task Scheduler → Task Scheduler Library → Your task → History tab

---

## Option 2: Python Scheduler (Cross-Platform)

If you want a cross-platform solution or need more control:

### Install Dependencies

```bash
pip install schedule
```

### Run the Scheduler

```bash
# Start scheduler (runs continuously)
python -m src.music_scout.cli.scheduler

# Test immediately without waiting for schedule
python -m src.music_scout.cli.scheduler --now
```

### Keep Running in Background

**Windows:**
Create a batch file `start_scheduler.bat`:
```batch
@echo off
cd /d "C:\Users\rafae\Projects\personal-music-tracker"
start /min python -m src.music_scout.cli.scheduler
```

**Linux/Mac (as a service):**
Create `/etc/systemd/system/music-scout-scheduler.service`:
```ini
[Unit]
Description=Music Scout Scheduler
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/personal-music-tracker
ExecStart=/usr/bin/python3 -m src.music_scout.cli.scheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable music-scout-scheduler
sudo systemctl start music-scout-scheduler
```

---

## Option 3: Manual Cron (Linux/Mac)

### Edit Crontab

```bash
crontab -e
```

### Add Cron Entry

```bash
# Run every Sunday at 9 AM
0 9 * * 0 cd /path/to/personal-music-tracker && python -m src.music_scout.cli.ingest ingest >> logs/ingestion.log 2>&1
```

---

## Monitoring & Troubleshooting

### Check if Ingestion is Working

After the scheduled run, check:

```bash
# View recent reviews
python -m src.music_scout.cli.cleanup show-items

# Check source status
python -m src.music_scout.cli.ingest list

# Generate overview report
python -m src.music_scout.cli.source_report
```

### Common Issues

**Problem:** Task runs but no new items
- **Solution:** Check if sources have new content. RSS feeds may not always have updates.

**Problem:** Authentication errors with Spotify
- **Solution:** Check `.env` file has valid `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`

**Problem:** Database locked errors
- **Solution:** Ensure backend server is not running during ingestion

**Problem:** Task doesn't run at all
- **Solution:** Check Task Scheduler → Task History for error messages

---

## Backup Strategy

Before automated ingestion starts, ensure you have backups:

```bash
# Create backup before each run (add to your batch script)
copy src\music_scout.db src\music_scout.db.backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%
```

Or automate it:
```batch
REM Add to run_weekly_ingestion.bat before ingestion
set BACKUP_NAME=music_scout.db.backup-%date:~-4,4%%date:~-10,2%%date:~-7,2%
copy src\music_scout.db src\%BACKUP_NAME%
```

---

## Customization

### Change Schedule

Edit the schedule in:
- **Task Scheduler:** Right-click task → Properties → Triggers
- **Python Scheduler:** Edit `src/music_scout/cli/scheduler.py`:
  ```python
  # Change from:
  schedule.every().sunday.at("09:00").do(run_weekly_ingestion)

  # To (for example, every Wednesday at 6 PM):
  schedule.every().wednesday.at("18:00").do(run_weekly_ingestion)
  ```

### Notifications

To get email notifications on completion, you could:
1. Add email sending to the scheduler script
2. Use Task Scheduler's "Send an email" action (deprecated but may still work)
3. Use a monitoring service like Healthchecks.io

---

## Verification

After setup, verify it works:

1. **Manual test:**
   ```bash
   python -m src.music_scout.cli.ingest ingest
   ```

2. **Check database:**
   ```bash
   python -m src.music_scout.cli.source_report
   ```

3. **Wait for scheduled run** and check:
   - New items appear in database
   - Logs show successful execution
   - No error messages

---

## Current Configuration

**Enabled Sources:** 8 (6 working)
- Sonic Perspectives
- MetalSucks
- Metal Storm
- The Prog Report
- Heavy Music HQ
- Rock & Blues Muse
- Blabbermouth (disabled - requires JS scraper)
- Kerrang (disabled - requires JS scraper)

**Expected Weekly Volume:** ~20-50 new reviews

**Metadata Enrichment:** Automatic (Spotify → MusicBrainz fallback)

---

## Success Metrics

Your automation is working if:
- ✅ New reviews appear weekly
- ✅ Metadata is populated (Spotify fields)
- ✅ No persistent errors in logs
- ✅ Database grows steadily

---

**Need Help?** Check the logs or run manually to diagnose issues.
