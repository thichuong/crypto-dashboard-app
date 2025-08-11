# Render Deployment Guide

## Deploy to Render

1. **Connect Repository**
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Choose "Web Service"

2. **Configuration**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT run:app`
   - **Environment**: Python 3

3. **Environment Variables**
   ```
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=production
   COINGECKO_API_KEY=your_coingecko_key
   TAAPI_SECRET=your_taapi_secret
   ENABLE_AUTO_REPORT_SCHEDULER=true
   ```

4. **Database Setup**
   - Add PostgreSQL addon
   - Set `POSTGRES_URL` environment variable

5. **Redis Setup** (Optional)
   - Add Redis addon for caching
   - Set `REDIS_URL` environment variable

## render.yaml (Alternative)
```yaml
services:
  - type: web
    name: crypto-dashboard
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT run:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: GEMINI_API_KEY
        sync: false
    
databases:
  - name: crypto-db
    databaseName: crypto_dashboard
    user: crypto_user
