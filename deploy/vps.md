# VPS Deployment Guide

## Automatic Installation

### 1. Download and Run Install Script
```bash
# Download
curl -O https://raw.githubusercontent.com/your-repo/crypto-dashboard-app/main/deploy/install.sh

# Make executable
chmod +x install.sh

# Run with domain and email for SSL
sudo ./install.sh -d yourdomain.com -e your@email.com

# Or run without SSL
sudo ./install.sh
```

### 2. Manual Setup Steps

**Deploy your code:**
```bash
# Clone repository
git clone https://github.com/your-repo/crypto-dashboard-app.git
sudo cp -r crypto-dashboard-app/* /opt/crypto-dashboard/

# Set permissions
sudo chown -R crypto:crypto /opt/crypto-dashboard
```

**Configure environment:**
```bash
sudo nano /opt/crypto-dashboard/.env
# Fill in your API keys
```

**Start services:**
```bash
cd /opt/crypto-dashboard
sudo docker compose up -d
sudo systemctl start crypto-dashboard
```

## Supported VPS Providers

### 1. Contabo (Recommended)
- **Price**: €3.99/month (4GB RAM, 2 vCPU, 50GB SSD)
- **Locations**: Germany, USA, Singapore
- **Sign up**: [contabo.com](https://contabo.com)

### 2. Hetzner Cloud
- **Price**: €3.29/month (2GB RAM, 1 vCPU, 20GB SSD)
- **Locations**: Germany, Finland, USA
- **Sign up**: [hetzner.com](https://hetzner.com)

### 3. Vultr
- **Price**: $2.50/month (512MB RAM, 1 vCPU, 10GB SSD)
- **Locations**: 25+ worldwide
- **Sign up**: [vultr.com](https://vultr.com)

### 4. DigitalOcean
- **Price**: $4/month (1GB RAM, 1 vCPU, 25GB SSD)
- **Locations**: 14 datacenters
- **Sign up**: [digitalocean.com](https://digitalocean.com)

### 5. Linode
- **Price**: $5/month (1GB RAM, 1 vCPU, 25GB SSD)
- **Locations**: 11 datacenters
- **Sign up**: [linode.com](https://linode.com)

## Manual Installation

### Prerequisites
- Ubuntu 20.04/22.04 or Debian 11/12
- Root access
- 1GB+ RAM recommended

### Step-by-step

1. **Update system**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

3. **Create application user**
```bash
sudo useradd -m -s /bin/bash crypto
sudo usermod -aG docker crypto
```

4. **Setup application**
```bash
sudo mkdir -p /opt/crypto-dashboard
sudo chown crypto:crypto /opt/crypto-dashboard
```

5. **Copy deployment files**
```bash
# Copy docker-compose.yml, Dockerfile, nginx.conf
# Copy your application code
```

6. **Configure environment**
```bash
sudo nano /opt/crypto-dashboard/.env
# Add your API keys and configuration
```

7. **Start services**
```bash
cd /opt/crypto-dashboard
sudo docker compose up -d
```

## SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## Monitoring and Maintenance

### View logs
```bash
docker compose logs -f
```

### Update application
```bash
git pull origin main
docker compose build --no-cache
docker compose up -d
```

### Backup database
```bash
docker compose exec postgres pg_dump -U crypto_user crypto_db > backup.sql
```

### Restore database
```bash
docker compose exec -T postgres psql -U crypto_user crypto_db < backup.sql
```

## Troubleshooting

### Check container status
```bash
docker compose ps
```

### Restart services
```bash
docker compose restart
```

### View system resources
```bash
docker stats
```

### Check firewall
```bash
sudo ufw status
sudo firewall-cmd --list-all  # CentOS/RHEL
```
