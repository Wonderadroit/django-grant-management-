#!/bin/bash
# Production Deployment Script for Django Grant Management System
# Run as: ./deploy_production.sh

set -e  # Exit on any error

echo "🚀 Starting Django Grant Management System Production Deployment"
echo "================================================================"

# Configuration
PROJECT_NAME="djf_grant_system"
PROJECT_USER="djf"
PROJECT_DIR="/var/www/djf_grant_system"
VENV_DIR="/var/www/djf_grant_system/venv"
LOG_DIR="/var/log/djf"
BACKUP_DIR="/var/backups/djf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run this script as root"
    exit 1
fi

print_status "Step 1: Creating system user and directories"
# Create project user
if ! id "$PROJECT_USER" &>/dev/null; then
    useradd -r -s /bin/bash -d $PROJECT_DIR $PROJECT_USER
    print_status "Created user: $PROJECT_USER"
else
    print_warning "User $PROJECT_USER already exists"
fi

# Create directories
mkdir -p $PROJECT_DIR
mkdir -p $LOG_DIR
mkdir -p $BACKUP_DIR
mkdir -p /var/run/djf

# Set ownership
chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR
chown -R $PROJECT_USER:$PROJECT_USER $LOG_DIR
chown -R $PROJECT_USER:$PROJECT_USER $BACKUP_DIR
chown -R $PROJECT_USER:$PROJECT_USER /var/run/djf

print_status "Step 2: Installing system dependencies"
# Update system packages
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    supervisor \
    git \
    curl \
    wget \
    certbot \
    python3-certbot-nginx \
    logrotate \
    fail2ban

print_status "Step 3: Setting up PostgreSQL database"
# Start PostgreSQL service
systemctl start postgresql
systemctl enable postgresql

# Create database and user (if not exists)
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'djf_grants_prod'" | grep -q 1 || \
sudo -u postgres createdb djf_grants_prod

sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = 'djf_user'" | grep -q 1 || \
sudo -u postgres createuser djf_user

# Set password (you'll need to update this)
sudo -u postgres psql -c "ALTER USER djf_user PASSWORD 'your-secure-database-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE djf_grants_prod TO djf_user;"

print_status "Step 4: Setting up Redis"
systemctl start redis-server
systemctl enable redis-server

print_status "Step 5: Setting up Python virtual environment"
# Switch to project user for Python setup
sudo -u $PROJECT_USER bash << EOF
cd $PROJECT_DIR

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

print_status "Virtual environment created successfully"
EOF

print_status "Step 6: Cloning/copying project files"
# Note: You'll need to adjust this based on your deployment method
# For now, we'll assume files are already in place

print_status "Step 7: Installing Python dependencies"
sudo -u $PROJECT_USER bash << EOF
cd $PROJECT_DIR
source venv/bin/activate
pip install -r requirements.production.txt
EOF

print_status "Step 8: Configuring environment variables"
# Copy environment template
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp $PROJECT_DIR/.env.production.example $PROJECT_DIR/.env
    chown $PROJECT_USER:$PROJECT_USER $PROJECT_DIR/.env
    chmod 600 $PROJECT_DIR/.env
    print_warning "Environment file created. Please update $PROJECT_DIR/.env with your configuration!"
fi

print_status "Step 9: Running Django setup commands"
sudo -u $PROJECT_USER bash << EOF
cd $PROJECT_DIR
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=core.settings_production

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser if needed
# python manage.py setup_admin

print_status "Django setup completed"
EOF

print_status "Step 10: Setting up Nginx"
cat > /etc/nginx/sites-available/djf_grant_system << 'NGINX_EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Security Headers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Static files
    location /static/ {
        alias /var/www/djf_grant_system/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/djf_grant_system/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Rate limiting
        limit_req zone=login burst=5 nodelay;
    }
    
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    # Error pages
    error_page 404 /static/404.html;
    error_page 500 502 503 504 /static/50x.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
NGINX_EOF

# Enable site
ln -sf /etc/nginx/sites-available/djf_grant_system /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t
systemctl restart nginx
systemctl enable nginx

print_status "Step 11: Setting up Supervisor (Process Management)"
cat > /etc/supervisor/conf.d/djf_grant_system.conf << 'SUPERVISOR_EOF'
[program:djf_grant_system]
command=/var/www/djf_grant_system/venv/bin/gunicorn core.wsgi:application -c /var/www/djf_grant_system/gunicorn.conf.py
directory=/var/www/djf_grant_system
user=djf
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/djf/gunicorn-supervisor.log
stderr_logfile=/var/log/djf/gunicorn-supervisor-error.log
environment=DJANGO_SETTINGS_MODULE="core.settings_production"
SUPERVISOR_EOF

# Restart supervisor
systemctl restart supervisor
systemctl enable supervisor
supervisorctl reread
supervisorctl update

print_status "Step 12: Setting up log rotation"
cat > /etc/logrotate.d/djf_grant_system << 'LOGROTATE_EOF'
/var/log/djf/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 djf djf
    postrotate
        systemctl reload nginx
        supervisorctl restart djf_grant_system
    endscript
}
LOGROTATE_EOF

print_status "Step 13: Setting up fail2ban"
cat > /etc/fail2ban/jail.d/nginx-djf.conf << 'FAIL2BAN_EOF'
[nginx-djf]
enabled = true
port = http,https
filter = nginx-djf
logpath = /var/log/nginx/access.log
maxretry = 5
bantime = 3600
findtime = 600
FAIL2BAN_EOF

systemctl restart fail2ban
systemctl enable fail2ban

print_status "Step 14: Setting up SSL with Let's Encrypt"
print_warning "You need to update the domain name and run: certbot --nginx -d yourdomain.com -d www.yourdomain.com"

print_status "Step 15: Final security setup"
# Set proper file permissions
chmod 755 $PROJECT_DIR
chmod -R 644 $PROJECT_DIR/core/templates/
chmod -R 644 $PROJECT_DIR/core/static/
chmod 600 $PROJECT_DIR/.env
chmod +x $PROJECT_DIR/manage.py

# Set up firewall
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'

print_status "✅ Production deployment completed successfully!"
echo "================================================================"
print_warning "IMPORTANT: Please complete these manual steps:"
echo "1. Update $PROJECT_DIR/.env with your actual configuration"
echo "2. Run: certbot --nginx -d yourdomain.com -d www.yourdomain.com"
echo "3. Update Nginx server_name with your actual domain"
echo "4. Test the application: https://yourdomain.com"
echo "5. Create admin user: cd $PROJECT_DIR && source venv/bin/activate && python manage.py setup_admin"
echo ""
print_status "System Status:"
echo "- Nginx: $(systemctl is-active nginx)"
echo "- PostgreSQL: $(systemctl is-active postgresql)"
echo "- Redis: $(systemctl is-active redis-server)"
echo "- Supervisor: $(systemctl is-active supervisor)"
echo "- Application: $(supervisorctl status djf_grant_system | awk '{print $2}')"
echo ""
print_status "Log files location: $LOG_DIR"
print_status "Backup location: $BACKUP_DIR"
echo "================================================================"