# Railway.app Deployment Guide - New Music Scout

Complete guide for deploying New Music Scout to Railway.app with persistent volumes and scheduled ingestion.

**Last Updated:** 2025-10-19

---

## Overview

This guide covers deploying New Music Scout to Railway.app, which offers a better free tier than Render for this use case.

**Architecture:**
- **Backend:** FastAPI (Python 3.13) with SQLite on persistent volume
- **Frontend:** React 19 static site
- **Database:** SQLite file on persistent volume (500MB free)
- **Scheduler:** Railway Cron Job for daily ingestion
- **Platform:** Railway.app

**What You'll Get:**
- Public HTTPS URLs for frontend and backend
- Automatic daily ingestion at 3 AM UTC
- Mobile-accessible from anywhere
- **$5 free credit per month** (enough for this app with room to spare)

---

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository (✓ already done)
2. **Railway Account** - Sign up at https://railway.app (free)
3. **Spotify API Credentials** - Get from https://developer.spotify.com/dashboard
   - Create an app
   - Copy Client ID and Client Secret

---

## Cost Breakdown

Railway uses a **usage-based pricing** model with **$5 free credit per month**:

| Resource | Usage | Estimated Cost |
|----------|-------|----------------|
| Backend (web service) | ~100 hours/mo (with sleep) | ~$2-3/mo |
| Frontend (static) | Minimal | ~$0.50/mo |
| Cron job | 1x/day @ 5 min | ~$0.10/mo |
| Persistent volume (1GB) | Storage | ~$0.10/mo |
| **Total** | | **~$3-4/mo** |
| **With $5 free credit** | | **$0/mo** |

**Stays free as long as usage < $5/month!**

---

## Step 1: Push Code to GitHub

Your code should already be pushed (we did this earlier), but let's verify:

```bash
git status
git push origin main
```

✓ Repository: `https://github.com/rafaeld17/new-music-scout`

---

## Step 2: Create Railway Account

1. Go to https://railway.app
2. Click "Start a New Project"
3. Sign up with GitHub (recommended for easy repo access)
4. Verify your email

---

## Step 3: Deploy Backend Service

### 3.1 Create New Project

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose `rafaeld17/new-music-scout`
4. Railway will detect the Dockerfile automatically

### 3.2 Configure Backend Service

1. Click on the deployed service
2. Go to **"Settings"** tab
3. Update these settings:

**Service Name:**
- Change to: `music-scout-backend`

**Root Directory:**
- Leave as `/` (project root)

**Build:**
- Builder: `Dockerfile`
- Dockerfile Path: `Dockerfile`

**Deploy:**
- Start Command: (leave default from railway.json)
- Watch Paths: `/` (rebuild on any change)

### 3.3 Add Environment Variables

Click **"Variables"** tab and add:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `sqlite:////data/music_scout.db` |
| `DEBUG` | `false` |
| `LOG_LEVEL` | `INFO` |
| `SPOTIFY_CLIENT_ID` | (your Spotify client ID) |
| `SPOTIFY_CLIENT_SECRET` | (your Spotify client secret) |
| `ALLOWED_ORIGINS` | (leave blank for now, we'll update after frontend deploys) |

**Important:** Railway automatically provides `PORT` variable - don't set it manually.

### 3.4 Add Persistent Volume

1. Click **"Settings"** tab
2. Scroll to **"Volumes"** section
3. Click **"+ New Volume"**
4. Configure:
   - **Mount Path:** `/data`
   - Click "Add"

Railway will create a persistent volume and mount it at `/data`.

### 3.5 Generate Public URL

1. Click **"Settings"** tab
2. Scroll to **"Networking"**
3. Click **"Generate Domain"**
4. Note your backend URL (e.g., `music-scout-backend-production.up.railway.app`)

### 3.6 Wait for Deployment

- Check the **"Deployments"** tab
- Wait for build to complete (~3-5 minutes)
- Status should show "Success" with green checkmark

### 3.7 Verify Backend

Visit: `https://your-backend-url.up.railway.app/api/health`

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

### 4.1 Add Service to Same Project

1. In your Railway project, click **"+ New"**
2. Select **"GitHub Repo"**
3. Choose the **same repository**: `rafaeld17/new-music-scout`
4. Railway will create a second service

### 4.2 Configure Frontend Service

1. Click on the new service
2. Go to **"Settings"** tab

**Service Name:**
- Change to: `music-scout-frontend`

**Root Directory:**
- Change to: `frontend`

**Build:**
- Builder: `Dockerfile`
- Dockerfile Path: `frontend/Dockerfile`

### 4.3 Add Environment Variables

Click **"Variables"** tab and add:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://your-backend-url.up.railway.app` |

(Use your actual backend URL from Step 3.5)

### 4.4 Generate Public URL

1. Click **"Settings"** tab
2. Scroll to **"Networking"**
3. Click **"Generate Domain"**
4. Note your frontend URL (e.g., `music-scout-frontend-production.up.railway.app`)

### 4.5 Wait for Deployment

- Check **"Deployments"** tab
- Wait for build (~2-3 minutes)
- Status should show "Success"

---

## Step 5: Update Backend CORS

Now that you have the frontend URL, update the backend:

1. Go to **backend service** (`music-scout-backend`)
2. Click **"Variables"** tab
3. Add/update:

| Variable | Value |
|----------|-------|
| `ALLOWED_ORIGINS` | `https://your-frontend-url.up.railway.app` |

(Use your actual frontend URL from Step 4.4)

4. Service will auto-redeploy (~1 minute)

---

## Step 6: Set Up Scheduled Ingestion

Railway supports cron jobs natively!

### 6.1 Add Cron Job Service

1. In your project, click **"+ New"**
2. Select **"Cron Job"**
3. Choose **"From GitHub Repo"**
4. Select the same repository

### 6.2 Configure Cron Service

1. Click on the cron service
2. Go to **"Settings"** tab

**Service Name:**
- Change to: `music-scout-ingestion`

**Schedule:**
- Cron Expression: `0 3 * * *` (daily at 3 AM UTC)

**Build:**
- Builder: `Dockerfile`
- Dockerfile Path: `Dockerfile`

**Run Command:**
```bash
python -m src.music_scout.cli.ingest ingest
```

### 6.3 Add Environment Variables

Click **"Variables"** tab and add:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `sqlite:////data/music_scout.db` |
| `SPOTIFY_CLIENT_ID` | (your Spotify client ID) |
| `SPOTIFY_CLIENT_SECRET` | (your Spotify client secret) |
| `LOG_LEVEL` | `INFO` |

### 6.4 Mount Same Volume (CRITICAL!)

**Important:** The cron job needs access to the same database as the backend.

1. Click **"Settings"** tab
2. Scroll to **"Volumes"** section
3. Click **"+ Mount Volume"**
4. Select the **existing volume** you created for the backend
5. Mount path: `/data`

### 6.5 Test Manually

Before waiting for the scheduled run:

1. Click **"Deployments"** tab
2. Click **"Deploy"** to trigger a manual run
3. Check logs to verify ingestion works

---

## Step 7: Initial Data Setup

Since the database starts empty, you need to seed it.

### 7.1 Access Backend Shell

**Option A: Using Railway CLI (recommended)**

1. Install Railway CLI:
```bash
npm i -g @railway/cli
# or
curl -fsSL https://railway.app/install.sh | sh
```

2. Login and connect:
```bash
railway login
railway link
```

3. Open shell to backend service:
```bash
railway shell music-scout-backend
```

**Option B: Using Web Shell**

1. Go to backend service
2. Click **"..." menu** (top right)
3. Select **"Shell"**

### 7.2 Seed Sources

Run this Python script in the shell:

```bash
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
    print('✓ Sources seeded!')
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

Open your frontend URL in a browser:
`https://your-frontend-url.up.railway.app`

You should see:
- Recent albums list
- Top-rated albums
- Filters and sorting

### 8.2 Test API

Visit: `https://your-backend-url.up.railway.app/api/reviews/latest`

Should return JSON array of recent reviews.

### 8.3 Check Logs

For each service:
1. Click on the service
2. Go to **"Logs"** tab
3. Verify no errors

---

## Step 9: Monitoring & Maintenance

### Daily Ingestion

- Runs automatically at 3 AM UTC daily
- Check cron job logs in Railway dashboard
- View last run in "Deployments" tab

### Database Backups

Railway doesn't include automatic volume backups on free tier.

**Manual Backup (Recommended Weekly):**

1. Use Railway shell:
```bash
railway shell music-scout-backend
```

2. Download database:
```bash
# In shell
cat /data/music_scout.db | base64
# Copy output and decode locally
```

**Automated Backup (Better):**

Add a weekly backup script that uploads to GitHub or cloud storage (TODO for Phase 5).

### Monitor Usage & Costs

1. Go to project **"Settings"**
2. Click **"Usage"**
3. Monitor to ensure you stay under $5/month
4. Set up usage alerts if available

### Optimize to Stay Free

**Sleep Configuration:**
- Backend can sleep after 10 min inactivity (saves money)
- First request will take ~30 sec to wake up
- Frontend (static) stays awake

To enable sleep:
1. Backend service → Settings → Sleep
2. Enable with 10 minute timeout

---

## Troubleshooting

### Backend won't start

**Check Build Logs:**
1. Go to service → Deployments
2. Click on failed deployment
3. Check build/deploy logs

**Common issues:**
- Missing environment variables
- Volume not mounted
- Python dependencies failed

**Fix:**
- Verify all env vars are set
- Check volume mount path is `/data`
- Check Dockerfile for errors

### Frontend shows "Failed to fetch"

**CORS Error:**
- Check browser console (F12)
- Verify `ALLOWED_ORIGINS` on backend
- Must be exact frontend URL with `https://`

**Wrong API URL:**
- Check `VITE_API_URL` on frontend service
- Must be full backend URL

### Cron job fails

**Check:**
1. Cron service logs for errors
2. Verify volume is mounted
3. Check Spotify credentials
4. Ensure schedule format is correct

**Fix:**
- Mount same volume as backend (`/data`)
- Add all required env vars
- Test with manual deploy first

### Database is empty

**Verify:**
1. Did you run seed script?
2. Did ingestion complete?
3. Is volume properly mounted?

**Fix:**
- Re-run seed script
- Run ingestion manually
- Check volume mount in Settings

### Exceeding $5/month free tier

**Reduce Usage:**
- Enable sleep mode on backend (10 min)
- Reduce cron frequency (weekly instead of daily)
- Optimize Docker image size

**Check Usage:**
- Project → Settings → Usage
- Identify which service uses most resources

---

## Railway vs Render Comparison

| Feature | Railway | Render Free |
|---------|---------|-------------|
| **Persistent Volumes** | ✅ 500MB free | ❌ Not on free tier |
| **Cron Jobs** | ✅ Included | ❌ Not on free tier |
| **Free Credit** | $5/month | None |
| **Spin-down** | Optional | Mandatory (15 min) |
| **Build Time** | Fast | Fast |
| **Custom Domains** | ✅ Free | ✅ Free |
| **GitHub Integration** | ✅ Excellent | ✅ Excellent |
| **Best For** | Apps needing storage + cron | Simple stateless apps |

**Winner for this project:** Railway (due to volume + cron support)

---

## Custom Domain (Optional)

Want `music-scout.yourdomain.com`?

1. Buy domain (Namecheap, Google Domains, etc.)
2. In Railway:
   - Service → Settings → Networking
   - Add custom domain
   - Update DNS records per instructions
3. Update `ALLOWED_ORIGINS` on backend

---

## Next Steps

After successful deployment:

1. **Monitor usage** - Keep it under $5/month to stay free
2. **Set up local backup routine** - Weekly download of database
3. **Test scheduled ingestion** - Wait 24 hours, verify cron runs
4. **Optional: Add uptime monitoring** - UptimeRobot.com
5. **Phase 4:** Implement Spotify playlist features

---

## Support & Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Railway Status:** https://status.railway.app
- **Project Issues:** https://github.com/rafaeld17/new-music-scout/issues
- **Spotify API Docs:** https://developer.spotify.com/documentation/web-api

---

## Summary

**What you deployed:**
- ✅ FastAPI backend with SQLite on persistent volume
- ✅ React frontend (static site)
- ✅ Daily cron job for automated ingestion
- ✅ All running on Railway's free tier ($5 credit/month)

**Total deployment time:** ~30-40 minutes

**Monthly cost:** $0 (usage < free credit)

**Access from anywhere:** ✅ HTTPS URLs work on mobile/desktop

---

**Congratulations!** Your New Music Scout is now live on Railway! 🎸🤘
