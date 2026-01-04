# Google Analytics Setup Guide

## ✅ Analytics Added to Your Site!

I've added Google Analytics 4 tracking code to track:
- **Page views** - How many people visit
- **Search queries** - What locations people search for
- **User registrations** - Sign-up tracking
- **Favorites** - When users save properties

---

## 🔧 How to Set It Up (5 Minutes)

### Step 1: Create Google Analytics Account
1. Go to https://analytics.google.com
2. Click "Start measuring"
3. Create Account:
   - Account Name: `PacasHomes`
   - Check all data sharing options (recommended)
   - Click Next

### Step 2: Create Property
1. Property Name: `PacasHomes Website`
2. Time Zone: `United Kingdom`
3. Currency: `British Pound (£)`
4. Click Next

### Step 3: Business Details
1. Industry: `Real Estate`
2. Business Size: `Small`
3. How you plan to use Analytics: Check all that apply
4. Click Create

### Step 4: Get Your Tracking ID
1. Choose Platform: **Web**
2. Set up data stream:
   - Website URL: `https://pacashomes.co.uk`
   - Stream name: `PacasHomes Main Site`
3. Click "Create stream"
4. **Copy your Measurement ID** (looks like `G-XXXXXXXXXX`)

### Step 5: Add ID to Your Code
1. Open `templates/index.html`
2. Find line with: `G-XXXXXXXXXX` (appears twice)
3. Replace BOTH instances with your real Measurement ID
4. Example: Change `G-XXXXXXXXXX` to `G-ABC1234DEF`

### Step 6: Deploy & Test
```bash
git add .
git commit -m "Add Google Analytics tracking"
git push origin main
```

Then in Google Analytics:
- Go to Reports → Realtime
- Visit your website
- You should see yourself as active user!

---

## 📊 What You Can Track

### Automatic Tracking:
- ✅ **Page Views** - Every page load
- ✅ **Session Duration** - How long users stay
- ✅ **Bounce Rate** - % who leave immediately
- ✅ **Device Type** - Mobile vs Desktop
- ✅ **Location** - Where visitors are from
- ✅ **Traffic Sources** - Google, direct, social media

### Custom Event Tracking (Already Added):
- ✅ **Property Searches** - `trackSearch(location)`
- ✅ **User Registrations** - `trackRegistration()`
- ✅ **Favorites Added** - `trackFavorite(propertyId)`

---

## 🎯 Key Metrics to Watch

**First Week:**
- **Users** - How many unique visitors
- **Sessions** - Number of visits
- **Engagement Rate** - % who interact

**First Month:**
- **Top Search Locations** - Popular areas
- **Conversion Rate** - Visits → Registrations
- **Traffic Sources** - Where users come from

**Ongoing:**
- **Growth Trends** - Week over week
- **User Retention** - Do they come back?
- **Popular Features** - What do they use most?

---

## 🔍 How to View Your Data

### Real-time Reports:
**Analytics → Reports → Realtime**
- See active users right now
- What pages they're on
- What they're searching for

### Traffic Reports:
**Analytics → Reports → Acquisition**
- Where users come from (Google, social, direct)
- Best performing channels

### User Behavior:
**Analytics → Reports → Engagement**
- Most viewed pages
- Average engagement time
- Events (searches, registrations)

### Conversions:
**Analytics → Reports → Monetization** (for tracking goals)
- Set up goal: User Registration
- Track conversion funnel

---

## 🎨 Custom Dashboards (Advanced)

Create custom reports to track:
1. **Registration funnel:**
   - Visits → Sign Up Click → Email Sent → Verified → Active User

2. **Search effectiveness:**
   - Search → Results Shown → Favorite Added → Contact Made

3. **Popular locations:**
   - Top 10 searched cities
   - Regional interest over time

---

## 🔒 Privacy Compliance

Already configured:
- ✅ **IP Anonymization** - User IPs masked
- ✅ **Cookie flags** - Secure & SameSite
- ✅ **No PII** - No personal data collected

**Add to Privacy Policy:**
"We use Google Analytics to understand how visitors use our site. This helps us improve your experience. Analytics uses cookies to collect anonymous data."

---

## 📈 Expected Timeline

- **Week 1:** Basic traffic data, understand baseline
- **Week 2-4:** Identify traffic patterns, peak times
- **Month 2-3:** See SEO efforts paying off
- **Month 6+:** Predict trends, optimize based on data

---

## 🚀 Pro Tips

1. **Set up Goals:**
   - Track user registrations as conversions
   - Monitor property favorites

2. **Link to Search Console:**
   - See what keywords bring traffic
   - Identify SEO opportunities

3. **Enable Enhanced Measurement:**
   - Already on by default in GA4
   - Tracks scrolls, clicks, downloads automatically

4. **Create Alerts:**
   - Get notified of traffic spikes
   - Alert on conversion drops

---

## 📱 Google Analytics App

Download mobile app to check stats on the go:
- iOS: https://apps.apple.com/app/google-analytics/id881599038
- Android: https://play.google.com/store/apps/details?id=com.google.android.apps.giant

---

## ✅ Next Steps

1. **Create Analytics account** (5 min)
2. **Get Measurement ID** (looks like G-XXXXXXXXXX)
3. **Replace in index.html** (find both instances)
4. **Push to GitHub & deploy**
5. **Test** - Visit site, check Realtime reports
6. **Share** - Start driving traffic to see data!

Your analytics is ready to go! 🎉
