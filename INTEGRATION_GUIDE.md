# Integration Guide: CBK GDI + Sanctions Screening

## Server: 134.209.176.80

Based on your existing CBK GDI setup, here's how to integrate it with the Sanctions Screening service.

---

## 📊 Current Setup Analysis

From your command history, I can see:

**CBK GDI (Already Running):**

- Location: `/var/www/cbk-gdi/`
- Service: `fastapi-app` (systemd)
- Nginx config: `/etc/nginx/sites-available/fastapi-app`
- Database: PostgreSQL (cbkgdi database)
- Currently accessible at: `http://134.209.176.80/` (root path)

**Sanctions Screening (To Deploy):**

- Location: `/var/www/sanction-screening/`
- Service: `sanctions-backend` (systemd)
- Will be accessible at: `http://134.209.176.80/sanctions/`

---

## 🎯 Integration Strategy

We'll use **path-based routing** so both services work on port 80:

| Service             | URL                                | Backend Port |
| ------------------- | ---------------------------------- | ------------ |
| CBK GDI (existing)  | http://134.209.176.80/ or /cbk-gdi | Current port |
| Sanctions Screening | http://134.209.176.80/sanctions    | 8001         |

---

## 📝 Step-by-Step Integration

### Step 1: Check Current CBK GDI Configuration

```bash
# View current Nginx config
sudo cat /etc/nginx/sites-available/fastapi-app

# Check what port CBK GDI backend is running on
sudo cat /etc/systemd/system/fastapi-app.service | grep ExecStart

# Check if it's running
sudo systemctl status fastapi-app
```

**Note the backend port** - it's likely something like 8000, 5000, or 8080.

---

### Step 2: Deploy Sanctions Screening Service

```bash
# Navigate to deployment location
cd /var/www

# Clone the repository (if not already there)
git clone https://github.com/nzivo/sanction-screening.git
cd sanction-screening

# Pull latest changes
git pull origin main

# Make script executable
chmod +x deploy-ubuntu.sh

# Run as non-root user (create one if needed)
# If you're root, switch to a regular user first
./deploy-ubuntu.sh
```

The script will:

- Set up Python virtual environment
- Install backend dependencies
- Build frontend with `/sanctions` base path
- Create systemd service for sanctions-backend (port 8001)

---

### Step 3: Create Unified Nginx Configuration

**Option A: Single Configuration File (Recommended)**

Create a new Nginx config that handles both services:

```bash
# Create new combined configuration
sudo nano /etc/nginx/sites-available/multi-service
```

**Add this configuration:**

```nginx
# Backend upstreams
upstream cbk_gdi_backend {
    server localhost:YOUR_CBK_PORT;  # Replace with actual CBK port (check Step 1)
}

upstream sanctions_backend {
    server localhost:8001;
}

server {
    listen 80;
    server_name 134.209.176.80;

    # Increase buffer sizes
    client_max_body_size 100M;

    # ============================================
    # CBK GDI Service (Root Path and /cbk-gdi)
    # ============================================

    # Root path - serves CBK GDI
    location / {
        proxy_pass http://cbk_gdi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Alternative path for CBK GDI
    location /cbk-gdi {
        proxy_pass http://cbk_gdi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ============================================
    # Sanctions Screening Service
    # ============================================

    # Frontend - serve built React app
    location /sanctions {
        alias /var/www/sanction-screening/frontend/dist;
        try_files $uri $uri/ /sanctions/index.html;
        index index.html;
    }

    # Backend API
    location /sanctions/api/ {
        rewrite ^/sanctions/api/(.*) /$1 break;
        proxy_pass http://sanctions_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # API Documentation
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

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

**Important:** Replace `YOUR_CBK_PORT` with the actual port from Step 1.

---

### Step 4: Enable New Configuration

```bash
# Disable old CBK GDI config
sudo rm /etc/nginx/sites-enabled/fastapi-app

# Enable new combined config
sudo ln -s /etc/nginx/sites-available/multi-service /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

---

### Step 5: Start Sanctions Backend Service

```bash
# Enable and start the sanctions backend
sudo systemctl enable sanctions-backend
sudo systemctl start sanctions-backend

# Check status
sudo systemctl status sanctions-backend
```

---

### Step 6: Verify Both Services

```bash
# Test CBK GDI (should still work at root)
curl http://localhost/

# Test Sanctions (health check)
curl http://localhost/sanctions/api/health

# Check both services are running
sudo systemctl status fastapi-app
sudo systemctl status sanctions-backend
```

---

## 🌐 Access URLs After Integration

| Service            | URL                                  | Status               |
| ------------------ | ------------------------------------ | -------------------- |
| **CBK GDI**        | http://134.209.176.80/               | Existing (unchanged) |
| **CBK GDI**        | http://134.209.176.80/cbk-gdi        | Alternative path     |
| **Sanctions**      | http://134.209.176.80/sanctions      | New                  |
| **Sanctions API**  | http://134.209.176.80/sanctions/api  | New                  |
| **Sanctions Docs** | http://134.209.176.80/sanctions/docs | New                  |

---

## 🔧 Alternative: Keep Separate Nginx Configs

If you prefer to keep configs separate, you can add just the sanctions locations to your existing config:

```bash
# Edit existing CBK GDI config
sudo nano /etc/nginx/sites-available/fastapi-app
```

**Add these location blocks inside the existing `server` block:**

```nginx
    # Sanctions Screening Service
    location /sanctions {
        alias /var/www/sanction-screening/frontend/dist;
        try_files $uri $uri/ /sanctions/index.html;
        index index.html;
    }

    location /sanctions/api/ {
        rewrite ^/sanctions/api/(.*) /$1 break;
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }

    location /sanctions/docs {
        rewrite ^/sanctions/docs$ /docs break;
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
    }

    location /sanctions/redoc {
        rewrite ^/sanctions/redoc$ /redoc break;
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
    }
```

Then reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🧪 Testing Checklist

- [ ] CBK GDI accessible at http://134.209.176.80/
- [ ] CBK GDI functions work (test login, database access)
- [ ] Sanctions accessible at http://134.209.176.80/sanctions
- [ ] Sanctions API responds at http://134.209.176.80/sanctions/api/health
- [ ] Sanctions documentation at http://134.209.176.80/sanctions/docs
- [ ] Both systemd services running
- [ ] No Nginx errors in logs

---

## 🐛 Troubleshooting

### CBK GDI Stops Working

```bash
# Check if service is running
sudo systemctl status fastapi-app

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Restart if needed
sudo systemctl restart fastapi-app
sudo systemctl reload nginx
```

### Sanctions Service Not Accessible

```bash
# Check backend is running
sudo systemctl status sanctions-backend

# Check logs
sudo journalctl -u sanctions-backend -f

# Verify files exist
ls -la /var/www/sanction-screening/frontend/dist

# Check Nginx config
sudo nginx -t
```

### Port Conflicts

```bash
# Check what's running on each port
sudo lsof -i :8000
sudo lsof -i :8001

# If CBK GDI is on 8001, change sanctions to 8002
# Edit: /var/www/sanction-screening/backend/main.py
# Change: uvicorn.run(app, host="0.0.0.0", port=8002)
```

### Both Services Show Same Content

This means Nginx location blocks are conflicting. Make sure:

- Sanctions uses `/sanctions` prefix
- CBK GDI uses `/` or `/cbk-gdi`
- More specific paths come first in Nginx config

---

## 📊 Service Management Commands

```bash
# View all service statuses
sudo systemctl status fastapi-app sanctions-backend nginx

# View all logs
sudo journalctl -u fastapi-app -u sanctions-backend -f

# Restart everything
sudo systemctl restart fastapi-app
sudo systemctl restart sanctions-backend
sudo systemctl reload nginx

# Check which ports are in use
sudo ss -tlnp | grep -E ':(80|443|8000|8001)'
```

---

## 🔐 Firewall Check

Your current UFW rules should work fine:

```bash
# Check current rules
sudo ufw status

# Should show:
# - 22/tcp (SSH) - ALLOW
# - Nginx HTTP - ALLOW
# - Nginx Full - ALLOW
```

No additional firewall changes needed since both services use port 80 through Nginx.

---

## 📦 Database Configuration

Your databases:

- **CBK GDI**: PostgreSQL database `cbkgdi` (already configured)
- **Sanctions**: PostgreSQL database `sanctions_db` (configured by deploy script)

Both can coexist on the same PostgreSQL instance.

---

## 🚀 Quick Summary

```bash
# 1. Check CBK GDI port
sudo cat /etc/systemd/system/fastapi-app.service | grep ExecStart

# 2. Deploy sanctions service
cd /var/www/sanction-screening
./deploy-ubuntu.sh

# 3. Create unified Nginx config (or update existing)
sudo nano /etc/nginx/sites-available/multi-service
# (Use config from Step 3)

# 4. Switch to new config
sudo rm /etc/nginx/sites-enabled/fastapi-app
sudo ln -s /etc/nginx/sites-available/multi-service /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 5. Start sanctions backend
sudo systemctl start sanctions-backend

# 6. Test both services
curl http://localhost/
curl http://localhost/sanctions/api/health
```

---

## 💡 Best Practice Recommendation

For cleaner URLs, consider:

1. **CBK GDI** at `/` (root) - since it's your main service
2. **Sanctions** at `/sanctions` - clearly identified
3. **Payment** (when ready) at `/payment` - clearly identified

This keeps your existing CBK GDI URLs working while adding new services with clear paths!

---

## ✅ Final Result

After integration, your server will serve:

- **http://134.209.176.80/** → CBK GDI System (unchanged)
- **http://134.209.176.80/sanctions** → Sanctions Screening
- **http://134.209.176.80/payment** → Payment Service (when ready)

All on one server, one IP, one port (80), with clean path-based routing! 🎉
