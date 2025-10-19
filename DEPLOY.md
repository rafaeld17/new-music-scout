# Deployment Guide - New Music Scout

Complete guide for deploying New Music Scout to Render.com with SQLite database.

**Last Updated:** 2025-10-19

---

## Overview

This guide covers deploying New Music Scout as a production web application accessible from anywhere.

**Architecture:**
- **Backend:** FastAPI (Python 3.13) with SQLite on persistent disk
- **Frontend:** React 19 static site served via nginx
- **Database:** SQLite file on 1GB persistent volume (free tier)
- **Scheduler:** Cron job for daily album ingestion
- **Platform:** Render.com (100% free tier)

**What You'll Get:**
- Public HTTPS URLs for frontend and backend
- Automatic daily ingestion at 3 AM UTC
- Mobile-accessible from anywhere
- Zero monthly cost

---

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Render Account** - Sign up at https://render.com (free)
3. **Spotify API Credentials** - Get from https://developer.spotify.com/dashboard
   - Create an app
   - Copy Client ID and Client Secret

---

## Step 1: Push Code to GitHub

If you haven't already:

```bash
# Initialize git repository (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "feat: add deployment configuration for Render"

# Create GitHub repository and push
gh repo create personal-music-tracker --private --source=. --push
# OR manually create repo on github.com and:
git remote add origin https://github.com/YOUR_USERNAME/personal-music-tracker.git
git branch -M main
git push -u origin main
```

---

## Step 2: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended)
4. Authorize Render to access your repositories

---

## Step 3: Deploy Backend Service

### 3.1 Create Web Service

1. In Render dashboard, click "New +" → "Web Service"
2. Connect your `personal-music-tracker` repository
3. Configure the service:

**Basic Settings:**
- **Name:** `music-scout-api`
- **Region:** Oregon (or closest to you)
- **Branch:** `main`
- **Runtime:** Docker
- **Dockerfile Path:** `./Dockerfile`
- **Docker Context:** (leave blank, uses repo root)

**Instance Type:**
- **Plan:** Free

**Advanced Settings:**
- **Health Check Path:** `/api/health`
- **Auto-Deploy:** Yes (recommended)

### 3.2 Add Environment Variables

Click "Environment" tab and add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite:////data/music_scout.db` |
| `API_HOST` | `0.0.0.0` |
| `API_PORT` | `8000` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `SPOTIFY_CLIENT_ID` | (your Spotify client ID) |
| `SPOTIFY_CLIENT_SECRET` | (your Spotify client secret) |

**Important:** For `ALLOWED_ORIGINS`, we'll add this after deploying the frontend.

### 3.3 Add Persistent Disk

1. Scroll to "Disks" section
2. Click "Add Disk"
3. Configure:
   - **Name:** `music-scout-data`
   - **Mount Path:** `/data`
   - **Size:** 1 GB (free tier limit)

### 3.4 Deploy

1. Click "Create Web Service"
2. Wait for deployment (3-5 minutes)
3. Once deployed, note your backend URL:
   - Example: `https://music-scout-api.onrender.com`

### 3.5 Verify Backend

Visit: `https://music-scout-api.onrender.com/api/health`

You should see:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "0.1.0"
}
```

---

## Step 4: Deploy Frontend Service

### 4.1 Create Static Site

1. Click "New +" → "Static Site"
2. Connect your `personal-music-tracker` repository
3. Configure:

**Basic Settings:**
- **Name:** `music-scout-frontend`
- **Region:** Oregon (same as backend)
- **Branch:** `main`
- **Runtime:** Docker
- **Dockerfile Path:** `./frontend/Dockerfile`
- **Docker Context:** `./frontend`

**Build Settings:**
- Leave default (Docker handles everything)

### 4.2 Add Environment Variables

Click "Environment" tab and add:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://music-scout-api.onrender.com` |

(Replace with YOUR actual backend URL from Step 3.4)

### 4.3 Deploy

1. Click "Create Static Site"
2. Wait for deployment (2-3 minutes)
3. Note your frontend URL:
   - Example: `https://music-scout.onrender.com`

---

## Step 5: Update CORS Configuration

Now that you have the frontend URL, update the backend:

1. Go to backend service (`music-scout-api`)
2. Click "Environment"
3. Add new environment variable:

| Key | Value |
|-----|-------|
| `ALLOWED_ORIGINS` | `https://music-scout.onrender.com` |

(Replace with YOUR actual frontend URL)

4. Service will auto-redeploy (1-2 minutes)

---

## Step 6: Set Up Scheduled Ingestion

### 6.1 Create Cron Job Service

1. Click "New +" → "Cron Job"
2. Connect your repository
3. Configure:

**Basic Settings:**
- **Name:** `music-scout-ingestion`
- **Region:** Oregon
- **Branch:** `main`
- **Runtime:** Docker
- **Dockerfile Path:** `./Dockerfile`
- **Schedule:** `0 3 * * *` (daily at 3 AM UTC)
- **Docker Command:** `python -m src.music_scout.cli.ingest ingest`

### 6.2 Add Environment Variables

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `sqlite:////data/music_scout.db` |
| `SPOTIFY_CLIENT_ID` | (your Spotify client ID) |
| `SPOTIFY_CLIENT_SECRET` | (your Spotify client secret) |
| `LOG_LEVEL` | `INFO` |

### 6.3 Add Persistent Disk (IMPORTANT!)

**Critical:** Must share the same disk as the backend!

1. Scroll to "Disks"
2. Click "Add Disk"
3. Select **existing disk:** `music-scout-data`
4. Mount path: `/data`

### 6.4 Create Job

Click "Create Cron Job"

---

## Step 7: Initial Data Setup

Since the database starts empty, you need to seed it with the 8 core sources and run initial ingestion.

### 7.1 Access Backend Shell

1. Go to backend service (`music-scout-api`)
2. Click "Shell" tab
3. Wait for shell to connect

### 7.2 Seed Sources

Run this Python script in the shell:

```python
python -c "
from sqlmodel import Session, create_engine
from src.music_scout.models.source import Source, SourceType

engine = create_engine('sqlite:////data/music_scout.db')

sources = [
    {'name': 'Kerrang!', 'url': 'https://www.kerrang.com/categories/reviews', 'source_type': SourceType.HTML, 'weight': 1.3},
    {'name': 'Blabbermouth', 'url': 'https://blabbermouth.net/reviews', 'source_type': SourceType.RSS, 'weight': 1.0},
    {'name': 'MetalSucks', 'url': 'https://www.metalsucks.net/category/reviews/', 'source_type': SourceType.RSS, 'weight': 1.0},
    {'name': 'Metal Storm', 'url': 'https://metalstorm.net/pub/reviews.php', 'source_type': SourceType.HTML, 'weight': 1.2},
    {'name': 'Sonic Perspectives', 'url': 'https://www.sonicperspectives.com/album-reviews/', 'source_type': SourceType.HTML, 'weight': 1.5},
    {'name': 'The Prog Report', 'url': 'https://progreport.com/category/progressive-rock-reviews/', 'source_type': SourceType.RSS, 'weight': 1.2},
    {'name': 'Heavy Music HQ', 'url': 'https://heavymusichq.com/category/album-reviews/', 'source_type': SourceType.RSS, 'weight': 1.2},
    {'name': 'Rock & Blues Muse', 'url': 'https://www.rockandbluesmuse.com/category/album-reviews/', 'source_type': SourceType.HTML, 'weight': 1.0},
]

with Session(engine) as session:
    for s in sources:
        source = Source(**s)
        session.add(source)
    session.commit()
    print('Sources seeded!')
"
```

### 7.3 Run Initial Ingestion

```bash
python -m src.music_scout.cli.ingest ingest
```

This will take 5-10 minutes to fetch all reviews with Spotify metadata.

---

## Step 8: Test Your Deployment

### 8.1 Visit Frontend

Open your frontend URL in a browser: `https://music-scout.onrender.com`

You should see:
- Recent albums list
- Top-rated albums
- Filters and sorting options

### 8.2 Test API Directly

Visit: `https://music-scout-api.onrender.com/api/reviews/latest`

Should return JSON array of recent reviews.

### 8.3 Check Logs

In each service dashboard:
1. Click "Logs" tab
2. Verify no errors
3. Look for "INFO" level messages

---

## Step 9: Monitoring & Maintenance

### Daily Ingestion

- Runs automatically at 3 AM UTC daily
- Check cron job logs: Go to `music-scout-ingestion` → Logs
- Last run status visible in dashboard

### Database Backups

**Important:** Free tier doesn't include automatic backups!

**Manual Backup (Recommended Weekly):**

1. Go to backend service shell
2. Run:
```bash
# Copy database to temporary location
cp /data/music_scout.db /tmp/backup.db

# Download via browser (if Render supports)
# OR use a backup script (see below)
```

**Automated Backup Script (TODO - Phase 5):**
- Add script to upload DB to GitHub/Dropbox/S3 weekly
- Run as another cron job

### Resource Limits

**Free Tier Limits:**
- Backend: 512 MB RAM, spins down after 15 min inactivity
- Frontend: Static site, always available
- Disk: 1 GB persistent storage
- Bandwidth: 100 GB/month

**Spin-down Impact:**
- First request after inactivity = 30-60 sec cold start
- Solution: Use a uptime monitor (e.g., UptimeRobot) to ping `/api/health` every 10 minutes

---

## Troubleshooting

### Backend won't start

**Check Logs:**
1. Look for errors in deploy logs
2. Common issues:
   - Missing environment variables
   - Disk not mounted properly
   - Port already in use

**Fix:**
- Verify all environment variables are set
- Check disk mount path is exactly `/data`
- Ensure `DATABASE_URL` uses `/data/music_scout.db`

### Frontend shows "Failed to fetch"

**CORS Error:**
- Check browser console (F12)
- If CORS error, verify `ALLOWED_ORIGINS` is set correctly
- Value should be exact frontend URL with `https://`

**API URL Wrong:**
- Check `VITE_API_URL` environment variable
- Must be full backend URL (not localhost!)

### Ingestion cron job fails

**Check:**
1. Cron job logs for specific error
2. Verify disk is shared with backend
3. Check Spotify credentials are set
4. Ensure schedule format is correct

**Common fixes:**
- Mount same disk as backend (`music-scout-data`)
- Add all required environment variables
- Check source URLs are still valid

### Database is empty

**Verify:**
1. Did you run seed script? (Step 7.2)
2. Did ingestion complete? (Step 7.3)
3. Check logs for errors

**Fix:**
- Re-run seed script
- Run ingestion manually
- Check disk permissions

---

## Cost Breakdown

| Service | Cost |
|---------|------|
| Backend (Web Service) | $0 (free tier) |
| Frontend (Static Site) | $0 (free tier) |
| Cron Job (Ingestion) | $0 (free tier) |
| Persistent Disk (1GB) | $0 (free tier) |
| **Total** | **$0/month** |

**Upgrade Path (if needed later):**
- Paid backend ($7/mo) → no spin-down, more RAM
- Larger disk → $0.25/GB/month
- PostgreSQL → $7/mo (not needed for your use case)

---

## Custom Domain (Optional)

Want `music-scout.yourdomain.com` instead of `.onrender.com`?

1. Buy domain (Namecheap, Google Domains, etc.)
2. In Render dashboard → Frontend service → Settings → Custom Domain
3. Add your domain
4. Update DNS records (Render provides instructions)
5. Update `ALLOWED_ORIGINS` to include new domain

---

## Next Steps

After successful deployment:

1. **Set up uptime monitoring** (prevents spin-down)
   - UptimeRobot.com (free)
   - Ping `https://music-scout-api.onrender.com/api/health` every 5 minutes

2. **Weekly backup routine**
   - Manual download of `/data/music_scout.db`
   - Store in cloud (Google Drive, Dropbox, etc.)

3. **Monitor ingestion**
   - Check cron job logs weekly
   - Verify new reviews are appearing

4. **Phase 4 implementation**
   - Spotify playlist creation
   - User authentication (OAuth)

---

## Support & Resources

- **Render Docs:** https://render.com/docs
- **Render Status:** https://status.render.com
- **Project Issues:** https://github.com/YOUR_USERNAME/personal-music-tracker/issues
- **Spotify API Docs:** https://developer.spotify.com/documentation/web-api

---

**Congratulations!** Your New Music Scout is now live and accessible from anywhere. 🎸🤘
