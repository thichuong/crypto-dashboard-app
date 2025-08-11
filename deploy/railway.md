# 🚂 Railway Deployment Guide - Crypto Dashboard với Redis & PostgreSQL

## 💰 Pricing Railway
- **Starter Plan**: $5/tháng cho 500 execution hours
- **PostgreSQL & Redis**: Miễn phí trong giới hạn
- **Custom domains**: Miễn phí

## 🚀 Quick Deploy to Railway

### 1. Setup Railway CLI (Optional - có thể dùng Web UI)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link project (nếu đã tạo project)
railway link
```

### 2. Deploy via Web UI (Recommended)

#### 2.1 Tạo Project
1. Truy cập: https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Authorize Railway và chọn `crypto-dashboard-app`
4. Railway sẽ auto-detect Flask app

#### 2.2 Add PostgreSQL Database
1. Trong project dashboard, click "Add Service"
2. Chọn "Database" → "PostgreSQL"
3. Railway tự động tạo database và generate connection vars

#### 2.3 Add Redis Cache
1. Click "Add Service" → "Database" → "Redis"  
2. Railway tự động provision Redis instance

## ⚙️ Environment Variables Configuration

### 3.1 Auto-Generated Variables (Railway tự tạo)
```bash
# Database connection (auto-linked)
DATABASE_URL=${{Postgres.DATABASE_URL}}
POSTGRES_URL=${{Postgres.DATABASE_URL}}

# Redis connection (auto-linked)
REDIS_URL=${{Redis.REDIS_URL}}
```

### 3.2 Manual Variables (cần thêm vào app service)
Vào app service → "Variables" tab:

```bash
# Production config
FLASK_ENV=production
PORT=8080

# API Keys
GEMINI_API_KEY=AIzaSyCWU8kvuv9w2kGh5YDwpF8DLOGL2T37tiA
TAAPI_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbHVlIjoiNjg4MDdhYmY4MDZmZjE2NTFlMjc4MDNkIiwiaWF0IjoxNzUzMjUwNDk1LCJleHAiOjMzMjU3NzE0NDk1fQ.LVqPJ1Pla0genBQEAm3l3BoNqp-DJjnKf6g_o1iH0Yg

# App config
SECRET_KEY=your_generated_secret_key_here
AUTO_UPDATE_SECRET_KEY=railway_production_key
ENABLE_AUTO_REPORT_SCHEDULER=true
```

### 3.3 Generate SECRET_KEY
```bash
# Local terminal - generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 📁 Required Files (đã có sẵn)

### `Procfile` ✅
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app
```

### `requirements.txt` ✅  
```pip-requirements
Flask
Flask-SQLAlchemy
Flask-Caching
redis
psycopg2-binary
# ... other dependencies
```

### `railway.json` (optional - thêm để optimize)
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

## 🔄 Deployment Process

### 4.1 Auto-Deploy
1. Push code lên GitHub
2. Railway tự động detect changes và deploy
3. Monitor deployment logs trong Railway dashboard

### 4.2 Manual Deploy (CLI)
```bash
# Deploy current code
railway up

# Set environment variables via CLI
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

## ✅ Verify Deployment

### 5.1 Check App Logs
Trong Railway dashboard → App service → "Logs":
```
INFO: Running in production mode
INFO: Connecting to Postgres database  
INFO: Connecting to Redis for caching
```

### 5.2 Test Endpoints
```bash
# Get app URL từ Railway dashboard
curl https://your-app.railway.app/
curl https://your-app.railway.app/api/crypto/bitcoin
```

### 5.3 Database Check
1. Vào PostgreSQL service → "Data" tab
2. Verify tables được tạo
3. Test connection:
```bash
# Connect via psql (nếu có)
psql $DATABASE_URL
\dt  # List tables
```

## 🗄️ Database Management

### PostgreSQL Features:
- **Auto-backups**: Railway tự động backup daily
- **Connection pooling**: Built-in connection pooling
- **SSL enabled**: Secure connections
- **Monitoring**: CPU, memory, storage metrics

### Redis Features:
- **Persistence**: RDB + AOF persistence
- **Memory optimization**: Automatic memory management
- **Monitoring**: Hit rate, memory usage
- **SSL/TLS**: Secure connections

## 🌐 Custom Domain Setup

### 6.1 Add Custom Domain
1. Vào app service → "Settings" → "Domains"
2. Click "Add Domain" 
3. Nhập domain: `crypto-dashboard.yourdomain.com`
4. Update DNS records:
```
Type: CNAME
Name: crypto-dashboard
Value: your-app.railway.app
```

## 📊 Monitoring & Performance

### 7.1 Railway Dashboard Metrics
- **CPU/Memory usage**: Real-time monitoring
- **Request metrics**: Response times, error rates  
- **Database performance**: Query times, connections
- **Redis performance**: Cache hit rates

### 7.2 Application Logs
```bash
# View logs
railway logs

# Follow logs
railway logs --follow
```

## 🔧 Troubleshooting Common Issues

### Database Connection Issues:
```bash
# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/dbname

# Test connection
railway run python3 -c "import psycopg2; print('DB OK')"
```

### Redis Connection Issues:
```bash
# Check REDIS_URL
echo $REDIS_URL
# Should be: redis://default:pass@host:port

# Test Redis
railway run python3 -c "import redis; r=redis.from_url('$REDIS_URL'); print('Redis OK')"
```

### Memory/Performance Issues:
- Monitor resource usage trong Railway dashboard
- Scale up service nếu cần thiết
- Optimize database queries và Redis caching

## 💡 Best Practices

1. **Environment Variables**: Dùng Railway variable references `${{Service.VARIABLE}}`
2. **Database Indexing**: Index các queries thường dùng
3. **Redis Caching**: Cache expensive operations
4. **Connection Pooling**: Sử dụng SQLAlchemy connection pooling
5. **Health Checks**: Implement `/health` endpoint
6. **Logging**: Structured logging cho easy debugging

## 💰 Cost Optimization

- **Resource Monitoring**: Track CPU/memory usage
- **Database Optimization**: Optimize queries, use indices
- **Caching Strategy**: Maximize Redis usage
- **Auto-scaling**: Railway tự động scale theo demand
- **Sleep Mode**: Railway có thể sleep inactive apps

## 🔗 Useful Commands

```bash
# Railway CLI commands
railway status           # Check project status
railway logs             # View application logs  
railway shell            # Open shell in deployment
railway variables        # List environment variables
railway run python manage.py migrate  # Run migrations

# Database commands
railway connect postgres # Connect to PostgreSQL
railway connect redis    # Connect to Redis
```

## 📚 References

- **Railway Docs**: https://docs.railway.app
- **PostgreSQL Guide**: https://docs.railway.app/databases/postgresql  
- **Redis Guide**: https://docs.railway.app/databases/redis
- **Flask Deployment**: https://docs.railway.app/guides/flask
