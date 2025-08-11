# Railway Deployment Guide

## Quick Deploy to Railway

1. **Connect Repository**
   ```bash
   railway login
   railway link
   ```

2. **Set Environment Variables**
   ```bash
   railway variables set GEMINI_API_KEY=your_key
   railway variables set SECRET_KEY=$(openssl rand -hex 32)
   railway variables set FLASK_ENV=production
   ```

3. **Deploy**
   ```bash
   railway up
   ```

## Configuration

Add these files to your project root:

### `Procfile`
```
web: gunicorn --bind 0.0.0.0:$PORT run:app
```

### `railway.json` (optional)
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

## Environment Variables to Set:

- `GEMINI_API_KEY` - Your Google Gemini API key
- `SECRET_KEY` - Flask secret key 
- `FLASK_ENV` - Set to 'production'
- `COINGECKO_API_KEY` - (Optional) CoinGecko API key
- `TAAPI_SECRET` - (Optional) TAAPI.io secret key
- `ENABLE_AUTO_REPORT_SCHEDULER` - Set to 'true'

Railway automatically provides PostgreSQL and Redis via plugins.
