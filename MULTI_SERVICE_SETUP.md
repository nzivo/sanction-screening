# Multi-Service Setup Guide

## Server: 134.209.176.80

This guide explains how to configure all three services on the same server with path-based routing.

---

## 🌐 Service URLs

After setup, your services will be accessible at:

| Service                 | URL                             | Backend Port            |
| ----------------------- | ------------------------------- | ----------------------- |
| **Sanctions Screening** | http://134.209.176.80/sanctions | 8001                    |
| **CBK GDI**             | http://134.209.176.80/cbk-gdi   | 8002 (adjust as needed) |
| **Payment Service**     | http://134.209.176.80/payment   | 8003 (adjust as needed) |
| **Landing Page**        | http://134.209.176.80/          | -                       |

---

## 📋 Quick Setup Steps

### Step 1: Deploy Sanctions Screening Service

```bash
# Navigate to project directory
cd /var/www/sanction-screening

# Run the deployment script
./deploy-ubuntu.sh
```

This will:

- Set up the backend on port 8001
- Build the frontend with `/sanctions` base path
- Configure Nginx with path-based routing

### Step 2: Configure Your Other Services

For **CBK GDI** and **Payment** services, you need to:

1. **Update their frontend build configuration** to use base paths:
   - CBK GDI: base path = `/cbk-gdi`
   - Payment: base path = `/payment`

2. **Update their API endpoints** to use the prefixed paths:
   - CBK GDI API: `/cbk-gdi/api`
   - Payment API: `/payment/api`

### Step 3: Update Nginx Configuration

```bash
# Edit the Nginx configuration
sudo nano /etc/nginx/sites-available/multi-service

# Use the provided nginx-multi-service.conf as reference
# Adjust the upstream ports and file paths to match your services

# Test configuration
sudo nginx -t

# If successful, enable and reload
sudo ln -sf /etc/nginx/sites-available/multi-service /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

---

## 🔧 Configuration for Each Service Type

### For React/Vue/Vite Projects (like Sanctions Screening)

**Vite config (vite.config.js):**

```javascript
export default defineConfig({
  base: "/your-service-name/", // e.g., "/sanctions/"
  // ... rest of config
});
```

**API endpoint (in service file):**

```javascript
const API_BASE_URL = import.meta.env.PROD
  ? "/your-service-name/api" // e.g., "/sanctions/api"
  : "/api";
```

### For React with create-react-app

**package.json:**

```json
{
  "homepage": "/your-service-name"
}
```

**Then rebuild:**

```bash
npm run build
```

### For Angular Projects

**angular.json:**

```json
{
  "projects": {
    "your-app": {
      "architect": {
        "build": {
          "options": {
            "baseHref": "/your-service-name/"
          }
        }
      }
    }
  }
}
```

---

## 🗂️ Directory Structure on Server

```
/var/www/
├── sanction-screening/
│   ├── backend/
│   ├── frontend/dist/
│   └── venv/
├── cbk-gdi/
│   ├── backend/
│   └── build/          # Frontend build
└── payment-service/
    ├── backend/
    └── build/          # Frontend build
```

---

## 🔥 Firewall Configuration

```bash
# Allow necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (for future SSL)

# DO NOT open backend ports (8001, 8002, 8003)
# They should only be accessible via Nginx proxy

sudo ufw enable
sudo ufw status
```

---

## 🚀 Backend Service Configuration

Each service should have its own systemd service file:

### Sanctions Backend

```bash
sudo nano /etc/systemd/system/sanctions-backend.service
```

Already configured by deploy-ubuntu.sh

### CBK GDI Backend (Example)

```bash
sudo nano /etc/systemd/system/cbk-gdi-backend.service
```

```ini
[Unit]
Description=CBK GDI Backend Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/var/www/cbk-gdi/backend
Environment="PATH=/var/www/cbk-gdi/venv/bin"
ExecStart=/var/www/cbk-gdi/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Payment Backend (Example)

```bash
sudo nano /etc/systemd/system/payment-backend.service
```

```ini
[Unit]
Description=Payment Service Backend
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/var/www/payment-service/backend
Environment="PATH=/var/www/payment-service/venv/bin"
ExecStart=/var/www/payment-service/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📊 Complete Nginx Configuration

The file `nginx-multi-service.conf` contains a complete configuration with:

✅ Path-based routing for all three services
✅ Upstream definitions for better performance
✅ Gzip compression
✅ Security headers
✅ CORS support
✅ Landing page showing all services
✅ WebSocket support
✅ SSL/HTTPS ready (commented out)

**To use it:**

```bash
# Copy to Nginx sites-available
sudo cp nginx-multi-service.conf /etc/nginx/sites-available/multi-service

# Edit to match your actual paths and ports
sudo nano /etc/nginx/sites-available/multi-service

# Update these values:
# - Backend ports for CBK GDI and Payment
# - File paths for frontend builds
# - Server name (if you have a domain)

# Test and enable
sudo nginx -t
sudo ln -sf /etc/nginx/sites-available/multi-service /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default if exists
sudo systemctl reload nginx
```

---

## 🧪 Testing Each Service

### Test Sanctions Screening

```bash
# Test backend directly
curl http://localhost:8001/health

# Test through Nginx
curl http://134.209.176.80/sanctions/api/health

# Access in browser
http://134.209.176.80/sanctions
http://134.209.176.80/sanctions/docs
```

### Test CBK GDI

```bash
# Test backend (adjust port)
curl http://localhost:8002/health

# Test through Nginx
curl http://134.209.176.80/cbk-gdi/api/health
```

### Test Payment Service

```bash
# Test backend (adjust port)
curl http://localhost:8003/health

# Test through Nginx
curl http://134.209.176.80/payment/api/health
```

---

## 🐛 Troubleshooting

### Service not accessible

**Check Nginx logs:**

```bash
sudo tail -f /var/log/nginx/error.log
```

**Check backend is running:**

```bash
sudo systemctl status sanctions-backend
sudo systemctl status cbk-gdi-backend
sudo systemctl status payment-backend
```

**Check backend logs:**

```bash
sudo journalctl -u sanctions-backend -f
sudo journalctl -u cbk-gdi-backend -f
sudo journalctl -u payment-backend -f
```

### API calls failing

**Check if path rewriting is correct in Nginx:**

```bash
# View current Nginx config
sudo cat /etc/nginx/sites-enabled/multi-service

# Test Nginx configuration
sudo nginx -t
```

**Check CORS headers** (if frontend and backend are having issues):

- Ensure backend allows the correct origins
- Check browser console for CORS errors

### Frontend shows blank page

**Check base path configuration:**

- Vite: `base: "/service-name/"`
- Create-react-app: `"homepage": "/service-name"`
- Angular: `"baseHref": "/service-name/"`

**Rebuild frontend after changing base path:**

```bash
npm run build
```

**Check Nginx alias/root path:**

```bash
# Verify files exist
ls -la /var/www/sanction-screening/frontend/dist
ls -la /var/www/cbk-gdi/build
ls -la /var/www/payment-service/build
```

---

## 📝 Maintenance Commands

### Restart all services

```bash
sudo systemctl restart sanctions-backend
sudo systemctl restart cbk-gdi-backend
sudo systemctl restart payment-backend
sudo systemctl reload nginx
```

### View all logs

```bash
# Nginx access log
sudo tail -f /var/log/nginx/access.log

# Nginx error log
sudo tail -f /var/log/nginx/error.log

# All backend services
sudo journalctl -u sanctions-backend -u cbk-gdi-backend -u payment-backend -f
```

### Update a service

```bash
# Example for sanctions screening
cd /var/www/sanction-screening
git pull
source venv/bin/activate
cd backend && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
sudo systemctl restart sanctions-backend
sudo systemctl reload nginx
```

---

## 🔐 Adding SSL/HTTPS (Optional)

If you get a domain name, you can add free SSL with Let's Encrypt:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

---

## 📞 Need Help?

Common issues and solutions:

| Issue              | Solution                                             |
| ------------------ | ---------------------------------------------------- |
| 502 Bad Gateway    | Backend service not running - check systemctl status |
| 404 Not Found      | Check Nginx location blocks and file paths           |
| Blank page         | Check base path in frontend build config             |
| API CORS errors    | Update backend CORS settings                         |
| Assets not loading | Check base path and rebuild frontend                 |

---

## ✅ Setup Checklist

- [ ] Sanctions Screening deployed and accessible
- [ ] CBK GDI frontend built with correct base path
- [ ] CBK GDI backend configured with systemd
- [ ] Payment Service frontend built with correct base path
- [ ] Payment Service backend configured with systemd
- [ ] Nginx configuration updated for all services
- [ ] All backend services started and enabled
- [ ] Firewall configured (port 80/443 only)
- [ ] All services tested in browser
- [ ] Landing page shows all service links
- [ ] SSL certificate installed (optional)

---

## 🎯 Final Result

Visit http://134.209.176.80/ to see a landing page with links to all three services:

- **Sanctions Screening** → Modern sanctions and PEP screening
- **CBK GDI** → Central Bank system
- **Payment Service** → Payment processing

All services running on one server, one IP, one port (80), with clean path-based routing! 🚀
