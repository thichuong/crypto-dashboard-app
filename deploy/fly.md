# Fly.io Deployment Guide

## Deploy to Fly.io

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and Initialize**
   ```bash
   fly auth login
   fly launch --no-deploy
   ```

3. **Configure fly.toml** (generated automatically)

4. **Set Secrets**
   ```bash
   fly secrets set GEMINI_API_KEY=your_key
   fly secrets set SECRET_KEY=$(openssl rand -hex 32)
   fly secrets set FLASK_ENV=production
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

## Dockerfile for Fly.io
Already provided in `/deploy/Dockerfile`

## fly.toml Example
```toml
app = "crypto-dashboard"

[build]
  dockerfile = "deploy/Dockerfile"

[env]
  FLASK_ENV = "production"
  PORT = "8080"

[[services]]
  http_checks = []
  internal_port = 8080
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

[mounts]
  source = "crypto_data"
  destination = "/app/instance"
```
