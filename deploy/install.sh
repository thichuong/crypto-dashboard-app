#!/bin/bash

# VPS Deployment Script for Crypto Dashboard
# Supports Ubuntu 20.04/22.04, Debian 11/12, CentOS 8/9

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="crypto-dashboard"
APP_DIR="/opt/$APP_NAME"
DOMAIN=""
EMAIL=""
USER="crypto"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        log_error "Cannot detect OS"
        exit 1
    fi
    log_info "Detected OS: $OS $VER"
}

# Install Docker
install_docker() {
    log_info "Installing Docker..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        centos|rhel)
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            systemctl start docker
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
    
    systemctl enable docker
    log_success "Docker installed successfully"
}

# Setup user
setup_user() {
    log_info "Setting up application user..."
    
    if ! id "$USER" &>/dev/null; then
        useradd -m -s /bin/bash $USER
        usermod -aG docker $USER
        log_success "User $USER created"
    else
        log_info "User $USER already exists"
    fi
}

# Setup application directory
setup_app_dir() {
    log_info "Setting up application directory..."
    
    mkdir -p $APP_DIR
    chown $USER:$USER $APP_DIR
    
    # Create environment file template
    cat > $APP_DIR/.env << EOF
# Flask Configuration
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production

# Database Configuration
POSTGRES_PASSWORD=$(openssl rand -hex 16)

# API Keys (fill these in)
GEMINI_API_KEY=your_gemini_api_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here
TAAPI_SECRET=your_taapi_secret_here

# Auto Report Configuration
ENABLE_AUTO_REPORT_SCHEDULER=true
AUTO_REPORT_INTERVAL_HOURS=3
AUTO_UPDATE_SECRET_KEY=$(openssl rand -hex 32)

# Optional
MAX_REPORT_ATTEMPTS=3
USE_FALLBACK_ON_500=true
THINKING_BUDGET=32768
EOF
    
    chown $USER:$USER $APP_DIR/.env
    chmod 600 $APP_DIR/.env
    
    log_success "Application directory setup complete"
}

# Install SSL certificate with Certbot
setup_ssl() {
    if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
        log_warning "Domain or email not provided. Skipping SSL setup."
        log_warning "To setup SSL later, run: certbot --nginx -d yourdomain.com"
        return
    fi
    
    log_info "Installing SSL certificate for $DOMAIN..."
    
    case $OS in
        ubuntu|debian)
            apt-get install -y certbot python3-certbot-nginx
            ;;
        centos|rhel)
            yum install -y certbot python3-certbot-nginx
            ;;
    esac
    
    certbot certonly --webroot -w /var/www/html -d $DOMAIN --email $EMAIL --agree-tos --non-interactive
    
    # Setup auto-renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    log_success "SSL certificate installed for $DOMAIN"
}

# Setup firewall
setup_firewall() {
    log_info "Configuring firewall..."
    
    case $OS in
        ubuntu|debian)
            ufw --force enable
            ufw allow ssh
            ufw allow 80/tcp
            ufw allow 443/tcp
            ;;
        centos|rhel)
            systemctl enable firewalld
            systemctl start firewalld
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --reload
            ;;
    esac
    
    log_success "Firewall configured"
}

# Create systemd service
create_service() {
    log_info "Creating systemd service..."
    
    cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Crypto Dashboard Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable $APP_NAME
    
    log_success "Systemd service created"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up basic monitoring..."
    
    # Create log rotation
    cat > /etc/logrotate.d/$APP_NAME << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF
    
    # Create monitoring script
    cat > $APP_DIR/monitor.sh << 'EOF'
#!/bin/bash
# Basic health check script

APP_URL="http://localhost:8080"
LOG_FILE="/var/log/crypto-dashboard-monitor.log"

if curl -f -s $APP_URL > /dev/null; then
    echo "$(date): Application is healthy" >> $LOG_FILE
else
    echo "$(date): Application is down, restarting..." >> $LOG_FILE
    systemctl restart crypto-dashboard
    
    # Send notification (configure webhook URL)
    # curl -X POST -H 'Content-type: application/json' \
    #   --data '{"text":"Crypto Dashboard is down and has been restarted"}' \
    #   YOUR_WEBHOOK_URL
fi
EOF
    
    chmod +x $APP_DIR/monitor.sh
    chown $USER:$USER $APP_DIR/monitor.sh
    
    # Add to crontab
    (crontab -u $USER -l 2>/dev/null; echo "*/5 * * * * $APP_DIR/monitor.sh") | crontab -u $USER -
    
    log_success "Monitoring setup complete"
}

# Performance optimization
optimize_system() {
    log_info "Optimizing system performance..."
    
    # Increase file limits
    cat >> /etc/security/limits.conf << EOF
$USER soft nofile 65536
$USER hard nofile 65536
EOF
    
    # Optimize sysctl
    cat >> /etc/sysctl.conf << EOF
# Network optimization
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 12582912 16777216
net.ipv4.tcp_wmem = 4096 12582912 16777216
net.core.netdev_max_backlog = 5000
EOF
    
    sysctl -p
    
    log_success "System optimization complete"
}

# Main deployment function
main() {
    log_info "Starting Crypto Dashboard deployment..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        log_error "Please run as root (use sudo)"
        exit 1
    fi
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [-d domain] [-e email]"
                echo "  -d, --domain    Domain name for SSL certificate"
                echo "  -e, --email     Email for Let's Encrypt notifications"
                exit 0
                ;;
            *)
                log_error "Unknown option $1"
                exit 1
                ;;
        esac
    done
    
    detect_os
    install_docker
    setup_user
    setup_app_dir
    setup_firewall
    create_service
    setup_monitoring
    optimize_system
    
    if [ -n "$DOMAIN" ] && [ -n "$EMAIL" ]; then
        setup_ssl
    fi
    
    log_success "Deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Copy your application code to $APP_DIR"
    echo "2. Edit $APP_DIR/.env with your API keys"
    echo "3. Run: cd $APP_DIR && docker compose up -d"
    echo "4. Check status: systemctl status $APP_NAME"
    echo ""
    echo "Your application will be available at:"
    if [ -n "$DOMAIN" ]; then
        echo "  https://$DOMAIN"
    else
        echo "  http://$(curl -s ipinfo.io/ip)"
    fi
    echo ""
    echo "Logs: docker compose logs -f"
    echo "Monitor: tail -f /var/log/crypto-dashboard-monitor.log"
}

# Run main function
main "$@"
