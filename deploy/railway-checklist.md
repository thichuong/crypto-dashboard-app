# 📋 Railway Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Repository Setup
- [ ] Code được push lên GitHub
- [ ] File `Procfile` có sẵn
- [ ] File `requirements.txt` đầy đủ dependencies  
- [ ] File `railway.json` được tạo (optional)
- [ ] `.env` file không được commit (chỉ local)

### 2. Railway Account Setup
- [ ] Tạo tài khoản Railway (https://railway.app)
- [ ] Verify email
- [ ] Connect GitHub account

## 🚀 Deployment Steps

### 3. Create Railway Project
- [ ] New Project → Deploy from GitHub
- [ ] Authorize Railway access to repo
- [ ] Select `crypto-dashboard-app` repository
- [ ] Wait for initial deployment

### 4. Add PostgreSQL Database
- [ ] Click "Add Service" → Database → PostgreSQL
- [ ] Wait for provision complete
- [ ] Note: `DATABASE_URL` auto-generated

### 5. Add Redis Cache  
- [ ] Click "Add Service" → Database → Redis
- [ ] Wait for provision complete
- [ ] Note: `REDIS_URL` auto-generated

### 6. Configure Environment Variables
Go to App service → Variables tab:

- [ ] `FLASK_ENV=production`
- [ ] `PORT=8080`
- [ ] `SECRET_KEY=` (generate new key)
- [ ] `GEMINI_API_KEY=AIzaSyCWU8kvuv9w2kGh5YDwpF8DLOGL2T37tiA`
- [ ] `TAAPI_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- [ ] `AUTO_UPDATE_SECRET_KEY=railway_production_key`
- [ ] `ENABLE_AUTO_REPORT_SCHEDULER=true`
- [ ] `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- [ ] `REDIS_URL=${{Redis.REDIS_URL}}`

### 7. Generate SECRET_KEY
```bash
# Run locally
python3 deploy/generate_secret.py
```
- [ ] Copy generated key to Railway variables

## ✅ Post-Deployment Verification

### 8. Check Deployment Status
- [ ] App service shows "Active" status
- [ ] No errors in deployment logs
- [ ] App accessible via Railway URL

### 9. Verify Database Connections
Check app logs for:
- [ ] `INFO: Running in production mode`
- [ ] `INFO: Connecting to Postgres database`
- [ ] `INFO: Connecting to Redis for caching`

### 10. Test Application
- [ ] Homepage loads: `https://your-app.railway.app/`
- [ ] API endpoints work: `/api/crypto/bitcoin`
- [ ] Database queries working
- [ ] Redis caching functional

### 11. Monitor Performance
- [ ] Check CPU/Memory usage in Railway dashboard
- [ ] Monitor database connections
- [ ] Verify Redis cache hit rates

## 🔧 Troubleshooting

### Common Issues:
- [ ] **Build fails**: Check `requirements.txt` dependencies
- [ ] **Database error**: Verify `DATABASE_URL` format
- [ ] **Redis error**: Check `REDIS_URL` connection
- [ ] **Environment vars**: Ensure all required vars set
- [ ] **Port binding**: Verify `PORT` env var and Procfile

### Debug Commands:
```bash
# Check app logs
railway logs

# Test database connection
railway shell
python3 -c "import psycopg2; print('DB OK')"

# Test Redis connection  
python3 -c "import redis; print('Redis OK')"
```

## 🌐 Optional: Custom Domain

### 12. Domain Setup (if needed)
- [ ] Go to App service → Settings → Domains
- [ ] Add custom domain
- [ ] Update DNS records (CNAME)
- [ ] Verify SSL certificate

## 📊 Production Monitoring

### 13. Setup Monitoring
- [ ] Enable Railway monitoring dashboard
- [ ] Set up error alerting (if available)
- [ ] Monitor resource usage trends
- [ ] Track application performance metrics

## 💰 Cost Management

### 14. Resource Optimization
- [ ] Monitor monthly usage in Railway dashboard
- [ ] Optimize database queries for performance
- [ ] Maximize Redis caching to reduce DB load
- [ ] Review and adjust resource limits if needed

---

## 📞 Support Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **PostgreSQL Docs**: https://docs.railway.app/databases/postgresql
- **Redis Docs**: https://docs.railway.app/databases/redis

---

## ✅ Deployment Complete!

Once all items are checked, your crypto dashboard should be running on Railway with:
- ✅ Flask app deployed and accessible
- ✅ PostgreSQL database connected
- ✅ Redis caching enabled  
- ✅ All environment variables configured
- ✅ Production-ready configuration
