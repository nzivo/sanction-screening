# Ubuntu Linux Deployment Guide - Step by Step

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Ubuntu server (20.04 LTS or higher)
- [ ] Root or sudo access
- [ ] Internet connection
- [ ] SSH access (if deploying remotely)

---

## Step 1: Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

**What this does:** Updates package lists and upgrades installed packages to latest versions.

---

## Step 2: Install Python 3.11+

```bash
# Check current Python version
python3 --version

# If Python < 3.11, install Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Verify installation
python3.11 --version
```

**Expected output:** `Python 3.11.x` or higher

---

## Step 3: Install Node.js and npm

```bash
# Install Node.js 20.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Verify installation
node --version    # Should show v20.x.x
npm --version     # Should show 10.x.x or higher
```

**Expected output:**

- Node: `v20.x.x`
- npm: `10.x.x`

---

## Step 4: Install PostgreSQL Database

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify it's running
sudo systemctl status postgresql
```

**Expected output:** `active (running)` status in green

---

## Step 5: Configure PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql
```

**In the PostgreSQL prompt, run these commands:**

```sql
-- Create database
CREATE DATABASE sanctions_db;

-- Create user with password
CREATE USER sanctions_user WITH PASSWORD 'YourSecurePassword123!';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sanctions_db TO sanctions_user;

-- Grant schema permissions (PostgreSQL 15+)
\c sanctions_db
GRANT ALL ON SCHEMA public TO sanctions_user;

-- Exit PostgreSQL
\q
```

**Note:** Replace `YourSecurePassword123!` with a strong password. Save this password - you'll need it later.

---

## Step 6: Clone/Upload Your Project

### Option A: From GitHub (Recommended)

```bash
# Navigate to desired directory
cd /home/$USER

# Clone repository
git clone https://github.com/nzivo/sanction-screening.git
cd sanction-screening
```

### Option B: Upload Files via SCP

**From your local machine (Windows):**

```bash
# Using SCP (from Git Bash or PowerShell)
scp -r C:\Users\John Nzivo\Documents\PPs\sanction-screening username@server-ip:/home/username/

# Then SSH into server
ssh username@server-ip
cd /home/username/sanction-screening
```

---

## Step 7: Set Up Python Virtual Environment

```bash
# Ensure you're in project root
cd /home/$USER/sanction-screening

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

**Expected output:** Your terminal prompt will show `(venv)` prefix

---

## Step 8: Install Backend Dependencies

```bash
# Navigate to backend directory
cd backend

# Upgrade pip
pip install --upgrade pip

# Install all Python dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected output:** List of installed packages including fastapi, uvicorn, sqlalchemy, etc.

---

## Step 9: Configure Backend Environment

```bash
# Still in backend directory
nano .env
```

**Add this configuration (press Ctrl+O to save, Ctrl+X to exit):**

```env
DATABASE_URL=postgresql://sanctions_user:YourSecurePassword123!@localhost:5432/sanctions_db
OFAC_API_KEY=
UPDATE_INTERVAL_HOURS=24
FUZZY_MATCH_THRESHOLD=80
```

**Important:** Replace `YourSecurePassword123!` with the password you set in Step 5.

---

## Step 10: Initialize Database

```bash
# Still in backend directory with venv activated
python init_db.py
```

**Expected output:**

```
Database initialized successfully!
Tables created.
```

---

## Step 11: Test Backend

```bash
# Start backend server (test run)
python main.py
```

**Expected output:**

```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test in another terminal:**

```bash
curl http://localhost:8001/health
```

**Expected response:** `{"status":"healthy"}`

**Stop the test server:** Press `Ctrl+C`

---

## Step 12: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd /home/$USER/sanction-screening/frontend

# Install npm packages
npm install
```

**Expected output:** Progress bars and successful installation message

---

## Step 13: Build Frontend for Production

```bash
# Still in frontend directory
npm run build
```

**Expected output:**

```
vite v5.x.x building for production...
✓ built in Xs
```

A `dist/` folder will be created with production-ready files.

---

## Step 14: Install and Configure Nginx

```bash
# Install Nginx
sudo apt install nginx -y

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Test Nginx is running
curl http://localhost
```

**Expected output:** HTML content from Nginx welcome page

---

## Step 15: Configure Nginx for Your Application

**Note:** This configuration uses **path-based routing** (`/sanctions`) to allow multiple services on the same server (port 80).

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/sanctions-screening
```

**Add this configuration:**

```nginx
# Upstream backend for better performance
upstream sanctions_backend {
    server localhost:8001;
}

server {
    listen 80;
    server_name 134.209.176.80;  # Replace with your actual IP or domain

    # Sanctions Screening Frontend - accessible at /sanctions
    location /sanctions {
        alias /home/YOUR_USERNAME/sanction-screening/frontend/dist;
        try_files $uri $uri/ /sanctions/index.html;
        index index.html;
    }

    # Sanctions Backend API - accessible at /sanctions/api
    location /sanctions/api/ {
        rewrite ^/sanctions/api/(.*) /$1 break;
        proxy_pass http://sanctions_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API Documentation - accessible at /sanctions/docs
    location /sanctions/docs {
        rewrite ^/sanctions/docs$ /docs break;
        proxy_pass http://sanctions_backend;
        proxy_set_header Host $host;
    }

    location /sanctions/redoc {
        rewrite ^/sanctions/redoc$ /redoc break;
        proxy_pass http://sanctions_backend;
        proxy_set_header Host $host;
    }

    location /sanctions/openapi.json {
        rewrite ^/sanctions/openapi.json$ /openapi.json break;
        proxy_pass http://sanctions_backend;
        proxy_set_header Host $host;
    }
}
```

**Important:**

- Replace `/home/YOUR_USERNAME/` with your actual username path
- Replace `134.209.176.80` with your server IP or domain name
- This allows you to run other services at `/cbk-gdi`, `/payment`, etc.

---

## Step 16: Enable Nginx Site

```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/sanctions-screening /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

**Expected output from nginx -t:**

```
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## Step 17: Create Systemd Service for Backend

```bash
# Create service file
sudo nano /etc/systemd/system/sanctions-backend.service
```

**Add this configuration:**

```ini
[Unit]
Description=Sanctions Screening Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/sanction-screening/backend
Environment="PATH=/home/YOUR_USERNAME/sanction-screening/venv/bin"
ExecStart=/home/YOUR_USERNAME/sanction-screening/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Important:** Replace `YOUR_USERNAME` with your actual Ubuntu username (check with `whoami` command).

---

## Step 18: Start Backend Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable sanctions-backend

# Start the service
sudo systemctl start sanctions-backend

# Check service status
sudo systemctl status sanctions-backend
```

**Expected output:** `active (running)` in green

---

## Step 19: Configure Firewall

```bash
# If ufw is not installed
sudo apt install ufw -y

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP on port 80 (standard port - path-based routing for multiple services)
sudo ufw allow 80/tcp

# Allow HTTPS (if you plan to add SSL later)
sudo ufw allow 443/tcp

# DO NOT open backend ports (8001, 8002, etc.) - they should only be accessible via Nginx proxy

# Enable firewall
sudo ufw enable

# Check firewall status
sudo ufw status
```

**Expected output:** Shows allowed ports (22, 80, 443)

---

## Step 20: Update Frontend API Configuration

If your frontend needs to know the backend URL, update it:

```bash
cd /home/$USER/sanction-screening/frontend/src/services
nano api.js
```

**Ensure the base URL is correct:**

```javascript
const API_BASE_URL = "/api"; // This works with Nginx proxy
```

**If you made changes, rebuild:**

```bash
cd /home/$USER/sanction-screening/frontend
npm run build
```

---

## Step 21: Verify Deployment

### Test Backend API:

```bash
# Health check
curl http://localhost:8001/health

# Or from outside
curl http://134.209.176.80/sanctions/api/health
```

### Test Frontend:

Open browser and visit:

- `http://134.209.176.80/sanctions` - Should show the React dashboard
- `http://134.209.176.80/sanctions/docs` - Should show API documentation

---

## Step 22: Initialize Sanctions Lists (First Time)

Access the dashboard at `http://134.209.176.80/sanctions` and:

1. Go to **Lists Management** section
2. Click "Update" buttons for each list:
   - Update OFAC List
   - Update UN List
   - Update EU List
   - Update UK List

Or via command line:

```bash
# Activate venv
cd /home/$USER/sanction-screening
source venv/bin/activate
cd backend

# Run update script
python -c "from list_downloaders import *; OFACDownloader().download()"
```

---

## Troubleshooting Commands

### Check Service Logs

```bash
# Backend logs
sudo journalctl -u sanctions-backend -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Restart Services

```bash
# Restart backend
sudo systemctl restart sanctions-backend

# Restart Nginx
sudo systemctl restart nginx

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Check Service Status

```bash
# Check backend
sudo systemctl status sanctions-backend

# Check Nginx
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql
```

### Database Connection Test

```bash
# Test database connection
psql -U sanctions_user -d sanctions_db -h localhost -W
# Enter password when prompted
# Type \q to exit
```

---

## Optional: SSL/HTTPS Setup

### Step A: Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Step B: Obtain SSL Certificate

**Requirements:** You need a domain name pointing to your server IP

```bash
# Replace with your actual domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Follow prompts:**

- Enter email address
- Agree to terms
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

### Step C: Test Auto-Renewal

```bash
# Dry run
sudo certbot renew --dry-run
```

**Expected output:** "Congratulations, all renewals succeeded"

---

## Performance Optimization (Optional)

### Enable Gzip Compression in Nginx

```bash
sudo nano /etc/nginx/nginx.conf
```

**Add in http block:**

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

```bash
sudo systemctl reload nginx
```

---

## Monitoring and Maintenance

### Set Up Log Rotation

Backend logs are automatically rotated by systemd/journald.

For custom logs:

```bash
sudo nano /etc/logrotate.d/sanctions-screening
```

**Add:**

```
/var/log/sanctions-screening/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 YOUR_USERNAME YOUR_USERNAME
}
```

---

## Backup Strategy

### Database Backup Script

```bash
# Create backup directory
mkdir -p /home/$USER/backups

# Create backup script
nano /home/$USER/backup-sanctions-db.sh
```

**Add:**

```bash
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sanctions_db_$TIMESTAMP.sql"

pg_dump -U sanctions_user -h localhost sanctions_db > "$BACKUP_FILE"
gzip "$BACKUP_FILE"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

```bash
# Make executable
chmod +x /home/$USER/backup-sanctions-db.sh

# Test backup
./backup-sanctions-db.sh
```

### Schedule Daily Backups

```bash
# Edit crontab
crontab -e
```

**Add this line (runs daily at 2 AM):**

```
0 2 * * * /home/$USER/backup-sanctions-db.sh >> /home/$USER/backups/backup.log 2>&1
```

---

## Security Hardening (Recommended)

### Step 1: Configure PostgreSQL for Local Access Only

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```

**Find and modify:**

```
listen_addresses = 'localhost'
```

```bash
sudo systemctl restart postgresql
```

### Step 2: Set File Permissions

```bash
cd /home/$USER/sanction-screening

# Protect .env file
chmod 600 backend/.env

# Set proper ownership
sudo chown -R $USER:$USER /home/$USER/sanction-screening
```

### Step 3: Configure Fail2ban (Optional)

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Quick Reference Commands

### Start/Stop Services

```bash
# Backend
sudo systemctl start sanctions-backend
sudo systemctl stop sanctions-backend
sudo systemctl restart sanctions-backend

# Nginx
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
```

### View Logs

```bash
# Backend logs (live)
sudo journalctl -u sanctions-backend -f

# Backend logs (last 100 lines)
sudo journalctl -u sanctions-backend -n 100

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Update Application

```bash
# Stop backend
sudo systemctl stop sanctions-backend

# Navigate to project
cd /home/$USER/sanction-screening

# Pull latest changes
git pull origin main

# Update backend dependencies
source venv/bin/activate
cd backend
pip install -r requirements.txt

# Update and rebuild frontend
cd ../frontend
npm install
npm run build

# Restart backend
sudo systemctl start sanctions-backend

# Reload Nginx
sudo systemctl reload nginx
```

---

## Complete Deployment Checklist

- [ ] Step 1: System packages updated
- [ ] Step 2: Python 3.11+ installed
- [ ] Step 3: Node.js 20+ installed
- [ ] Step 4: PostgreSQL installed
- [ ] Step 5: Database created and configured
- [ ] Step 6: Project files uploaded
- [ ] Step 7: Virtual environment created
- [ ] Step 8: Backend dependencies installed
- [ ] Step 9: Backend .env file configured
- [ ] Step 10: Database initialized
- [ ] Step 11: Backend tested
- [ ] Step 12: Frontend dependencies installed
- [ ] Step 13: Frontend built
- [ ] Step 14: Nginx installed
- [ ] Step 15: Nginx configured for app
- [ ] Step 16: Nginx site enabled
- [ ] Step 17: Systemd service created
- [ ] Step 18: Backend service started
- [ ] Step 19: Firewall configured
- [ ] Step 20: Frontend API config verified
- [ ] Step 21: Deployment verified in browser
- [ ] Step 22: Sanctions lists initialized

---

## Access Your Application

After completing all steps:

- **Frontend Dashboard:** `http://134.209.176.80/sanctions`
- **Backend API:** `http://134.209.176.80/sanctions/api`
- **API Documentation:** `http://134.209.176.80/sanctions/docs`
- **Alternative API Docs:** `http://134.209.176.80/sanctions/redoc`

**Note:** This path-based routing (`/sanctions`) allows you to run other services on the same server:

- CBK GDI at `/cbk-gdi`
- Payment Service at `/payment`

See [MULTI_SERVICE_SETUP.md](MULTI_SERVICE_SETUP.md) for complete multi-service configuration.

---

## Common Issues and Solutions

### Issue 1: Backend won't start

**Check logs:**

```bash
sudo journalctl -u sanctions-backend -n 50
```

**Common causes:**

- Database connection error → Check .env file and PostgreSQL credentials
- Port already in use → Kill process on port 8001: `sudo lsof -ti:8001 | xargs kill -9`
- Missing dependencies → Reinstall: `pip install -r requirements.txt`

### Issue 2: Frontend shows blank page

**Check:**

- Nginx is running: `sudo systemctl status nginx`
- Files exist: `ls -la /home/$USER/sanction-screening/frontend/dist`
- Rebuild if needed: `cd frontend && npm run build`

### Issue 3: API calls fail from frontend

**Check Nginx proxy configuration:**

```bash
sudo nginx -t
sudo systemctl reload nginx
```

**Check backend is running:**

```bash
sudo systemctl status sanctions-backend
curl http://localhost:8001/health
```

### Issue 4: Database connection errors

**Verify PostgreSQL is running:**

```bash
sudo systemctl status postgresql
```

**Test connection:**

```bash
psql -U sanctions_user -d sanctions_db -h localhost -W
```

**If login fails, reset password:**

```bash
sudo -u postgres psql
ALTER USER sanctions_user WITH PASSWORD 'NewPassword123!';
\q
```

Then update `backend/.env` with new password.

### Issue 5: Permission denied errors

**Fix ownership:**

```bash
sudo chown -R $USER:$USER /home/$USER/sanction-screening
chmod +x start.sh
```

---

## Production Checklist

Before going live:

- [ ] Database password is strong and secured
- [ ] `.env` file has correct permissions (600)
- [ ] Firewall is configured and enabled
- [ ] SSL certificate installed (if using domain)
- [ ] Backup script set up and tested
- [ ] Log rotation configured
- [ ] Services set to start on boot
- [ ] Application tested end-to-end
- [ ] Monitoring set up

---

## Need Help?

Check these log files if something goes wrong:

1. Backend API logs: `sudo journalctl -u sanctions-backend -f`
2. Nginx errors: `sudo tail -f /var/log/nginx/error.log`
3. PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`

Remember to keep your system updated:

```bash
sudo apt update && sudo apt upgrade -y
```
