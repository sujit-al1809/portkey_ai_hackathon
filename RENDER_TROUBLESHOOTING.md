# 🔧 RENDER BACKEND - TROUBLESHOOTING

## Problem: "Backend not working on Render"

---

## ⚡ QUICK FIXES (Try in order)

### Fix 1: Check Render Logs (Do this first!)

1. Go to **render.com**
2. Select your **portkey-backend** service
3. Click **"Logs"** tab
4. Look for errors

**Common errors you'll see:**

#### Error: "ModuleNotFoundError: No module named..."
```
Solution: requirements.txt missing package

# Add to requirements.txt:
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push origin main

# Render auto-redeploys
```

#### Error: "gunicorn: command not found"
```
Solution: gunicorn not in requirements.txt

# Add to requirements.txt:
gunicorn==20.1.0
flask==2.3.2
flask-cors==4.0.0

# Push to GitHub:
git add requirements.txt
git commit -m "Add gunicorn"
git push origin main
```

#### Error: "Port 10000 not available"
```
Solution: Change port in render.yaml

# In render.yaml, change:
startCommand: gunicorn -w 4 -b 0.0.0.0:8000 backend.dashboard_api:app

# Port doesn't matter (Render assigns it)
# But code must use: os.getenv('PORT', '8000')
```

---

### Fix 2: Check Environment Variables

1. Go to **render.com**
2. Select **portkey-backend**
3. Click **"Environment"**
4. Verify these are set:

```
PORTKEY_API_KEY=xxxx          ✅ Must exist
OPENAI_API_KEY=xxxx           ✅ Must exist
ANTHROPIC_API_KEY=xxxx        ✅ Must exist
COHERE_API_KEY=xxxx           ✅ Must exist
DATABASE_URL=sqlite:///optimization.db
FLASK_ENV=production
SECRET_KEY=some_random_key
CORS_ORIGINS=https://your-vercel-url.vercel.app
```

**If any are missing**: Add them now, then click "Manual Redeploy"

---

### Fix 3: Check render.yaml

Must be in **root** of project (same level as backend/ folder)

Create file: `render.yaml`

```yaml
services:
  - type: web
    name: portkey-backend
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python -m flask run --host=0.0.0.0 --port=8000
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
```

Then push:
```bash
git add render.yaml
git commit -m "Fix Render configuration"
git push origin main
```

---

### Fix 4: Test Backend Code Locally First

Before deploying, make sure it works locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
$env:FLASK_ENV = "production"
$env:DATABASE_URL = "sqlite:///./optimization.db"
$env:PORTKEY_API_KEY = "your_key"
$env:OPENAI_API_KEY = "your_key"

# Run tests
pytest backend/

# Run backend
python backend/dashboard_api.py

# Test in browser
# http://localhost:5000/api/evaluate
```

If it fails locally, fix it before pushing to Render!

---

### Fix 5: Update requirements.txt to have ALL dependencies

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
requests==2.31.0
```

Then:
```bash
git add requirements.txt
git commit -m "Complete requirements"
git push origin main
```

---

### Fix 6: Check Code - Startup Issues

Make sure `backend/dashboard_api.py` has:

```python
import os
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# Enable CORS
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "OPTIONS"]
    }
})

# Routes
@app.route('/api/health', methods=['GET'])
def health():
    return {"status": "ok"}

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    # Your code here
    pass

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

Key points:
- ✅ `CORS` enabled
- ✅ `PORT` from environment
- ✅ `host='0.0.0.0'` (listens on all interfaces)
- ✅ `debug=False` (production)

---

## 🎯 COMPLETE TROUBLESHOOTING FLOW

### Step 1: Check Render Logs
```
render.com → portkey-backend → Logs
↓
Look for red errors
↓
Note the error type
```

### Step 2: Based on Error Type

| Error | Solution |
|-------|----------|
| ModuleNotFoundError | Add to requirements.txt + push |
| gunicorn: command not found | Add gunicorn to requirements.txt + push |
| Port not available | Change port in render.yaml + push |
| Connection refused | Missing environment variables |
| 500 error | Check code has no syntax errors |
| "cannot import module" | Check backend/ folder structure |

### Step 3: After Fix
```
git add .
git commit -m "Fix Render deployment"
git push origin main
↓
Wait 2-3 minutes
↓
Render auto-redeploys
↓
Check logs again
```

### Step 4: Verify It Works
```bash
# Get Render URL from dashboard
# It looks like: https://portkey-backend-xxxx.onrender.com

# Test health endpoint
curl https://portkey-backend-xxxx.onrender.com/api/health

# Should return:
# {"status": "ok"}

# Then test API
curl https://portkey-backend-xxxx.onrender.com/api/evaluate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "user_id": "demo"}'
```

---

## 🚨 MOST COMMON ISSUES

### Issue 1: "Build failed"
**Cause**: Python syntax error in code
**Fix**: 
```bash
python -m py_compile backend/dashboard_api.py
```
If it shows error, fix it before pushing.

### Issue 2: "Deployment spinning indefinitely"
**Cause**: App not listening on correct port
**Fix**: Make sure code has:
```python
port = int(os.getenv('PORT', 8000))
app.run(host='0.0.0.0', port=port)
```

### Issue 3: "Cannot find API key"
**Cause**: Environment variable not set
**Fix**:
```
Render → portkey-backend → Environment
Add: PORTKEY_API_KEY = your_key
Click: Manual Redeploy
```

### Issue 4: "502 Bad Gateway"
**Cause**: Backend crashed or not responding
**Fix**:
```bash
# Check logs for errors
# Render → Logs tab
# Look for Python stack trace
# Fix error locally, push to Render
```

### Issue 5: "CORS error"
**Cause**: Frontend URL not in CORS_ORIGINS
**Fix**:
```
Render → Environment
Update: CORS_ORIGINS = https://your-vercel-url.vercel.app
Click: Manual Redeploy
```

---

## ✅ DEBUGGING CHECKLIST

- [ ] Render logs checked (any errors?)
- [ ] requirements.txt has gunicorn
- [ ] All environment variables set in Render
- [ ] render.yaml is in root folder
- [ ] Backend code runs locally without errors
- [ ] Port set to 8000 or from environment
- [ ] CORS enabled in Flask app
- [ ] No hardcoded API keys (use environment variables)
- [ ] Flask app uses `host='0.0.0.0'`
- [ ] No syntax errors in Python files

---

## 🆘 IF STILL NOT WORKING

### Send me these:
1. **Screenshot of Render logs** (the error message)
2. **Your render.yaml** (show me the file)
3. **Your requirements.txt** (show me dependencies)
4. **Test result:**
   ```bash
   python -m py_compile backend/dashboard_api.py
   ```

### Then I can:
- [ ] Fix the specific error
- [ ] Update your code
- [ ] Push to GitHub
- [ ] Verify it works

---

## 🚀 QUICK DEPLOY COMMAND

Once everything works:

```bash
# 1. Test locally
pytest backend/
python backend/dashboard_api.py

# 2. Push to GitHub
git add .
git commit -m "Backend fix"
git push origin main

# 3. Wait for Render redeploy (2-3 min)

# 4. Test production
curl https://your-backend.onrender.com/api/health
```

**That's it!** Render auto-deploys on every push. 🎉

---

## 📞 NEED HELP?

Tell me:
1. **What error do you see?** (screenshot or paste error)
2. **Where do you see it?** (Render logs, browser, etc.)
3. **What did you try?** (any fixes attempted)

Then I can give exact solution! ✅
