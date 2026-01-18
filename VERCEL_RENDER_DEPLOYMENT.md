# 🚀 FRONTEND (VERCEL) + BACKEND (RENDER) DEPLOYMENT

## Your Stack
- **Frontend**: React dashboard → **Vercel** ✅
- **Backend**: Flask Python API → **Render** ✅

---

## 📋 DEPLOYMENT CHECKLIST

| Step | Time | Status |
|------|------|--------|
| Setup backend on Render | 10 min | → Do this first |
| Setup frontend on Vercel | 5 min | → Then this |
| Connect frontend to backend API | 2 min | → Finally this |
| Test everything | 5 min | → Verify |
| **TOTAL** | **22 min** | **GO LIVE** |

---

## ⚡ STEP 1: DEPLOY BACKEND TO RENDER (10 minutes)

### 1.1 Create Render Account
```bash
# Go to: render.com
# Sign up with GitHub (easiest)
# Connect your repo
```

### 1.2 Create `.env.render` File

In root of project, create `.env.render`:
```bash
# Backend environment variables for Render

# API Keys
PORTKEY_API_KEY=your_portkey_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
COHERE_API_KEY=your_cohere_key_here

# Database (Render PostgreSQL)
DATABASE_URL=postgresql://user:password@your-render-db.onrender.com:5432/portkey_db

# Or use SQLite (simpler)
DATABASE_URL=sqlite:///./optimization.db

# Server config
ENVIRONMENT=production
DEBUG=false
FLASK_ENV=production
SECRET_KEY=generate_random_secret_key_here

# Vector DB
VECTOR_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384

# CORS - Allow Vercel frontend
CORS_ORIGINS=https://your-frontend.vercel.app

# Port (Render assigns this automatically)
PORT=10000
```

### 1.3 Create `render.yaml` in root

This tells Render how to deploy your backend:

```yaml
# render.yaml

services:
  - type: web
    name: portkey-backend
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:10000 backend.dashboard_api:app
    envVars:
      - key: PORTKEY_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: COHERE_API_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        sync: false
      - key: CORS_ORIGINS
        sync: false

databases:
  - name: portkey-db
    plan: free
    databaseName: portkey_db
    user: portkey_user
```

### 1.4 Update `requirements.txt`

Make sure you have gunicorn (for production):

```
flask==2.3.2
flask-cors==4.0.0
portkey-ai==1.0.0
sqlalchemy==2.0.0
sentence-transformers==2.2.2
numpy==1.24.0
python-dotenv==1.0.0
gunicorn==20.1.0
pytest==7.3.0
psycopg2-binary==2.9.0
```

### 1.5 Deploy to Render

```bash
# Option A: Auto-deploy (RECOMMENDED)
# Push to GitHub, Render auto-deploys on every push

git add .
git commit -m "Add Render deployment config"
git push origin main

# Option B: Deploy from Render dashboard
# 1. Go to render.com
# 2. Click "New" → "Web Service"
# 3. Connect GitHub repo
# 4. Select branch (main)
# 5. Choose render.yaml
# 6. Set environment variables
# 7. Click "Create Web Service"
```

### 1.6 Get Your Backend URL

```bash
# After deployment completes:
# Render gives you: https://portkey-backend-xxxx.onrender.com

# Test it:
curl https://portkey-backend-xxxx.onrender.com/api/evaluate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "user_id": "demo"}'

# Should return 200 with recommendation
```

**Save this URL!** You'll need it for frontend.

---

## 🎨 STEP 2: DEPLOY FRONTEND TO VERCEL (5 minutes)

### 2.1 Create Vercel Account
```bash
# Go to: vercel.com
# Sign up with GitHub
# Import your project
```

### 2.2 Update Frontend Config

In `dashboard/.env.production`:

```bash
# Vercel environment variables

# Point to your Render backend
REACT_APP_API_URL=https://portkey-backend-xxxx.onrender.com
REACT_APP_ENV=production
```

Or if using `next.config.js`:

```javascript
module.exports = {
  env: {
    REACT_APP_API_URL: process.env.REACT_APP_API_URL || 'https://portkey-backend-xxxx.onrender.com',
  },
}
```

### 2.3 Create `vercel.json` in root

```json
{
  "version": 2,
  "builds": [
    {
      "src": "dashboard/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "dashboard/$1"
    }
  ],
  "env": {
    "REACT_APP_API_URL": "@react_app_api_url"
  }
}
```

### 2.4 Deploy to Vercel

```bash
# Option A: From command line (easiest)
npm i -g vercel

cd dashboard

vercel --prod \
  --env REACT_APP_API_URL=https://portkey-backend-xxxx.onrender.com

# Option B: From Vercel dashboard
# 1. Go to vercel.com
# 2. Click "Add New" → "Project"
# 3. Import GitHub repo
# 4. Select Root Directory: "dashboard"
# 5. Add environment variables
# 6. Click "Deploy"
```

### 2.5 Get Your Frontend URL

```bash
# After deployment:
# Vercel gives you: https://portkey-dashboard-xyz.vercel.app

# Test it in browser:
# https://portkey-dashboard-xyz.vercel.app

# Should load React dashboard
```

---

## 🔗 STEP 3: CONNECT FRONTEND TO BACKEND

### 3.1 Update Frontend API Calls

In `dashboard/src/api.js` (or similar):

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const evaluatePrompt = async (prompt, userId) => {
  const response = await fetch(`${API_BASE_URL}/api/evaluate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: prompt,
      user_id: userId,
    }),
  });

  if (!response.ok) {
    throw new Error('API request failed');
  }

  return response.json();
};
```

### 3.2 Update Backend CORS

In `backend/dashboard_api.py`:

```python
from flask_cors import CORS
import os

app = Flask(__name__)

# Get CORS origins from environment
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')

CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Set environment variable in Render
CORS_ORIGINS=https://portkey-dashboard-xyz.vercel.app
```

### 3.3 Test Connection

```bash
# 1. Go to: https://portkey-dashboard-xyz.vercel.app
# 2. Open browser DevTools (F12)
# 3. Enter a test prompt
# 4. Check Console tab - should see successful API call
# 5. Should see recommendation from backend
```

---

## ✅ VERIFICATION CHECKLIST

### Backend (Render) ✅
- [ ] `render.yaml` created
- [ ] `requirements.txt` has gunicorn
- [ ] Environment variables set in Render dashboard
- [ ] Backend URL is: `https://portkey-backend-xxxx.onrender.com`
- [ ] Test API endpoint works:
  ```bash
  curl https://portkey-backend-xxxx.onrender.com/api/evaluate \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test", "user_id": "demo"}'
  ```

### Frontend (Vercel) ✅
- [ ] `vercel.json` created
- [ ] `.env.production` updated with backend URL
- [ ] Frontend URL is: `https://portkey-dashboard-xyz.vercel.app`
- [ ] Can load React app in browser
- [ ] Can see all UI components

### Connection ✅
- [ ] Update `CORS_ORIGINS` in Render to match Vercel URL
- [ ] Update `REACT_APP_API_URL` in Vercel to match Render URL
- [ ] Test prompt submission works
- [ ] See recommendation in dashboard
- [ ] No CORS errors in browser console

---

## 📊 PRODUCTION ENVIRONMENT SETUP

### Render Dashboard - Set Environment Variables

1. Go to Render dashboard
2. Select your web service
3. Go to "Environment" tab
4. Add each variable:

```
PORTKEY_API_KEY = [your key]
OPENAI_API_KEY = [your key]
ANTHROPIC_API_KEY = [your key]
COHERE_API_KEY = [your key]
DATABASE_URL = [sqlite or postgres]
FLASK_ENV = production
SECRET_KEY = [generate random: python -c "import secrets; print(secrets.token_urlsafe(32))"]
CORS_ORIGINS = https://portkey-dashboard-xyz.vercel.app
```

### Vercel Dashboard - Set Environment Variables

1. Go to Vercel dashboard
2. Select your project
3. Go to "Settings" → "Environment Variables"
4. Add:

```
REACT_APP_API_URL = https://portkey-backend-xxxx.onrender.com
REACT_APP_ENV = production
```

---

## 🔄 DEPLOYMENT FLOW

### Every time you push code:

```bash
# 1. Make changes
vim backend/dashboard_api.py

# 2. Test locally
pytest backend/

# 3. Push to GitHub
git add .
git commit -m "Update API logic"
git push origin main

# 4. AUTO-DEPLOY happens:
#    - Render pulls latest
#    - Runs buildCommand
#    - Starts app with startCommand
#    - Live in ~2 minutes

# 5. Check status
# Render: render.com → Your service → Logs
# Vercel: vercel.com → Your project → Deployments
```

---

## 📈 PRODUCTION URLS

| Component | URL | Provider |
|-----------|-----|----------|
| Frontend | `https://portkey-dashboard-xyz.vercel.app` | Vercel |
| Backend API | `https://portkey-backend-xxxx.onrender.com` | Render |
| Backend Health | `https://portkey-backend-xxxx.onrender.com/health` | Render |

**Share with judges:**
```
Frontend: https://portkey-dashboard-xyz.vercel.app
Try it now! (No installation needed)
```

---

## 💰 MONTHLY COSTS

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Free tier | $0 |
| Render | Free tier | $0 (will spin down after 15 min inactivity) |
| **Total** | | **$0** |

**For production (paid tier):**

| Service | Plan | Cost |
|---------|------|------|
| Vercel | Pro | $20/month |
| Render | Standard | $7/month (web) + $15/month (DB) |
| **Total** | | **$42/month** |

---

## 🆘 TROUBLESHOOTING

### Frontend shows "Cannot reach API"

**Fix**: Update CORS_ORIGINS in Render

```bash
# Render dashboard → Environment
CORS_ORIGINS = https://portkey-dashboard-xyz.vercel.app

# Then redeploy:
# Click "Manual Redeploy" in Render
```

### API returns 500 error

**Fix**: Check Render logs

```bash
# Render → Logs tab
# Look for Python errors
# Common: Missing environment variable

# Check environment variables are set:
# Render → Environment → Check all keys
```

### Frontend keeps redeploying

**Fix**: This is normal! Vercel auto-deploys on every push to GitHub.

```bash
# To prevent auto-deploy:
# Vercel → Settings → Git → Toggle "Auto-deploy" off
```

### "ModuleNotFoundError" in Render logs

**Fix**: Update requirements.txt

```bash
# Add missing package
pip freeze > requirements.txt

# Commit and push
git add requirements.txt
git commit -m "Update dependencies"
git push origin main

# Render auto-redeploys
```

---

## 🎯 FINAL CHECKLIST

### Before Demo to Judges

- [ ] Frontend loads at Vercel URL
- [ ] Can submit prompt in dashboard
- [ ] Get recommendation from backend
- [ ] Cost, quality, model comparison shown
- [ ] No errors in browser console
- [ ] No CORS errors
- [ ] API responses in <2 seconds
- [ ] Numbers match your documentation

### Share with Judges

```
🚀 LIVE DEMO
Frontend: https://portkey-dashboard-xyz.vercel.app
Backend API: https://portkey-backend-xxxx.onrender.com/api/evaluate

Try it:
1. Go to frontend URL
2. Enter: "How to optimize Python?"
3. See AI model comparison
4. See cost savings recommendation

All Track 4 requirements met:
✅ Replay historical data
✅ Evaluate across models & guardrails
✅ Measure cost, quality, refusal
✅ Recommend trade-offs
```

---

## 🚀 QUICK START COMMANDS

```bash
# 1. Prepare backend
# Create render.yaml ✅
# Update requirements.txt ✅
# Set environment variables in Render ✅

# 2. Prepare frontend
# Create vercel.json ✅
# Update .env.production ✅
# Set environment variables in Vercel ✅

# 3. Deploy
git add .
git commit -m "Production deployment config"
git push origin main

# 4. Wait for auto-deploy
# Render: 2-3 minutes
# Vercel: 2-3 minutes

# 5. Test
# Frontend: https://your-frontend.vercel.app
# Backend: https://your-backend.onrender.com/api/evaluate

# 6. Share with judges
echo "Production URLs ready!"
```

---

## ✨ YOU'RE PRODUCTION READY!

**Timeline**:
- ⏱️ 10 min: Backend on Render
- ⏱️ 5 min: Frontend on Vercel
- ⏱️ 2 min: Connect them
- ⏱️ 5 min: Test everything
- **Total: 22 minutes**

**Result**: 
- Live production app
- Show judges real URL
- Get real-time recommendations
- All Track 4 requirements working
- Professional deployment

🏆 **YOU'RE READY TO WIN!**
