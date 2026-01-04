# Render Deployment Guide for PacasHomes

## 🚀 Quick Deploy Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - PacasHomes property aggregator"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Create Render Account
- Go to https://render.com
- Sign up with GitHub
- Connect your repository

### 3. Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repository
3. Configure settings:

**Basic Settings:**
- Name: `pacashomes`
- Region: Choose closest to UK (Frankfurt or London if available)
- Branch: `main`
- Root Directory: (leave empty)
- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn main:app`

**Instance Type:**
- Free tier (512MB RAM) - Good for testing
- Starter ($7/month) - Better for production

### 4. Environment Variables
Add these in Render Dashboard → Environment:

```
APIFY_TOKEN=apify_api_1a4jEwUXsMNvw5IK8lDrJM2GUFTOBQ2RQpmd
SCRAPER_API_KEY=ed074fcd19774200427ea44f1d5a8ede
BRIGHTDATA_KEY=29748bbec8f41b82e7680ae6dd43eb75d4c987e549851452e6e048ce48ea5e37
SCRAPINGBEE_KEY=SGSRKOR6HYW3VLFIS5SRIBCP5APNJRQP21CJBSSPGHIJMZTEZU0M4YGFQ99ZMTKNRNUUPA887FDB21B2
PROXY_SCRAPE_KEY=amym7uveh48xwo2doqrd

FLASK_HOST=0.0.0.0
FLASK_PORT=10000
FLASK_DEBUG=False
MAX_REQUESTS_PER_HOUR=100
SECRET_KEY=3f04953b05c4dbce6b330b144dc1065b7c917aab982e7ad9c8396b1d6cdbf71c

SMTP_SERVER=smtp.hostinger.com
SMTP_PORT=587
SENDER_EMAIL=verify@pacashomes.co.uk
SENDER_PASSWORD=Azim9090@!!
SENDER_NAME=PacasHomes
```

**⚠️ IMPORTANT:** Don't include the `.env` file in your git repo (add to .gitignore)

### 5. Database Consideration

**Current:** SQLite (properties.db) - Works but file-based, will reset on redeploys

**Render Free Tier Options:**
1. **Keep SQLite** - Simple but data resets on redeploy
2. **Upgrade to PostgreSQL** (Recommended for production):
   - Render provides free PostgreSQL (512MB, expires after 90 days)
   - Or use paid tier ($7/month persistent)

**To use PostgreSQL on Render:**
- Create PostgreSQL database in Render
- Install: `pip install psycopg2-binary`
- Update database connection in `utils/database.py`

### 6. Static Files & CORS

Already configured! ✅
- CORS enabled in main.py
- Static files served correctly
- All set for production

### 7. Domain Setup

**After deployment, Render gives you:**
- Free subdomain: `pacashomes.onrender.com`

**To use pacashomes.co.uk:**
1. Get SSL certificate (Render provides free)
2. In Hostinger DNS settings:
   - Add CNAME record: `www` → `pacashomes.onrender.com`
   - Add A record: `@` → Render's IP (they provide)
3. In Render → Settings → Custom Domains → Add `pacashomes.co.uk`

---

## 📋 Pre-Deploy Checklist

✅ Created: Procfile  
✅ Created: runtime.txt  
✅ Verified: requirements.txt has all packages  
✅ Gunicorn already in requirements.txt  
✅ SECRET_KEY is secure  
✅ Email SMTP configured  
✅ CORS enabled  
✅ Rate limiting active  

---

## 🧪 Testing After Deploy

1. Visit your Render URL
2. Test registration with email verification
3. Test property search
4. Test favorites
5. Check logs in Render Dashboard

---

## 💰 Costs

**Free Tier:**
- Web Service: Free (spins down after 15min inactive)
- PostgreSQL: Free (90 days, then $7/month)
- Custom Domain: Free SSL

**Paid Tier (Recommended for production):**
- Web Service: $7/month (always on, 512MB RAM)
- PostgreSQL: $7/month (persistent, 256MB storage)
- **Total: $14/month**

---

## 🔧 Troubleshooting

**If deploy fails:**
- Check Render logs
- Verify all packages in requirements.txt
- Ensure PORT env var not conflicting
- Check gunicorn is installed

**If emails don't send:**
- Verify SMTP settings in Render env vars
- Check Hostinger allows SMTP from external IPs
- Test with different SMTP provider if needed

---

## 🚀 Ready to Deploy?

1. Push code to GitHub
2. Connect to Render
3. Add environment variables
4. Deploy!

Your site will be live at: `https://pacashomes.onrender.com`
