#!/bin/bash

# Sanctions Screening - Ubuntu Deployment Script
# This script automates the deployment process on Ubuntu Linux

set -e  # Exit on error

echo "=========================================="
echo "  Sanctions Screening Ubuntu Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}Error: This script is for Linux only${NC}"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_error "Don't run this script as root. It will use sudo when needed."
    exit 1
fi

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."

# Check Python
if command -v python3.11 &> /dev/null; then
    PYTHON_VERSION=$(python3.11 --version)
    print_status "Python found: $PYTHON_VERSION"
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
        print_status "Python found: Python $PYTHON_VERSION"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.11+ required. Current: $PYTHON_VERSION"
        echo "Install with: sudo apt install python3.11 python3.11-venv -y"
        exit 1
    fi
else
    print_error "Python 3.11+ not found"
    echo "Install with: sudo apt install python3.11 python3.11-venv -y"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found"
    echo "Install with: curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install nodejs -y"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_status "npm found: $NPM_VERSION"
else
    print_error "npm not found"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    print_status "PostgreSQL found"
else
    print_warning "PostgreSQL not found. Install with: sudo apt install postgresql postgresql-contrib -y"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""

# Step 2: Create virtual environment
echo "Step 2: Setting up Python virtual environment..."

if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate
print_status "Virtual environment activated"

echo ""

# Step 3: Install backend dependencies
echo "Step 3: Installing backend dependencies..."

cd backend
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_status "Backend dependencies installed"

cd ..
echo ""

# Step 4: Check database configuration
echo "Step 4: Checking database configuration..."

if [ ! -f "backend/.env" ]; then
    print_warning "No .env file found. Creating template..."
    cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://sanctions_user:YourSecurePassword123!@localhost:5432/sanctions_db
OFAC_API_KEY=
UPDATE_INTERVAL_HOURS=24
FUZZY_MATCH_THRESHOLD=80
EOF
    print_warning "IMPORTANT: Edit backend/.env with your actual database credentials"
    read -p "Press Enter after updating .env file..." 
else
    print_status ".env file found"
fi

echo ""

# Step 5: Initialize database
echo "Step 5: Initializing database..."

read -p "Run database initialization? This will create tables. (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd backend
    python init_db.py
    if [ $? -eq 0 ]; then
        print_status "Database initialized successfully"
    else
        print_error "Database initialization failed. Check your credentials in .env"
        exit 1
    fi
    cd ..
else
    print_warning "Skipped database initialization"
fi

echo ""

# Step 6: Install frontend dependencies
echo "Step 6: Installing frontend dependencies..."

cd frontend
if [ ! -d "node_modules" ]; then
    npm install
    print_status "Frontend dependencies installed"
else
    print_status "Frontend dependencies already installed"
fi

echo ""

# Step 7: Build frontend
echo "Step 7: Building frontend for production..."

npm run build
if [ -d "dist" ]; then
    print_status "Frontend built successfully (dist/ folder created)"
else
    print_error "Frontend build failed"
    exit 1
fi

cd ..
echo ""

# Step 8: Create systemd service
echo "Step 8: Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/sanctions-backend.service"

if [ -f "$SERVICE_FILE" ]; then
    print_status "Systemd service already exists"
    read -p "Recreate service file? (y/n) " -n 1 -r
    echo
    CREATE_SERVICE=$REPLY
else
    CREATE_SERVICE="y"
fi

if [[ $CREATE_SERVICE =~ ^[Yy]$ ]]; then
    sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Sanctions Screening Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$SCRIPT_DIR/backend
Environment="PATH=$SCRIPT_DIR/venv/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    print_status "Systemd service file created"
    
    sudo systemctl daemon-reload
    sudo systemctl enable sanctions-backend
    print_status "Service enabled"
fi

echo ""

# Step 9: Configure Nginx
echo "Step 9: Configuring Nginx..."

if command -v nginx &> /dev/null; then
    print_status "Nginx is installed"
    
    NGINX_CONF="/etc/nginx/sites-available/sanctions-screening"
    
    if [ -f "$NGINX_CONF" ]; then
        print_status "Nginx configuration already exists"
        read -p "Recreate Nginx configuration? (y/n) " -n 1 -r
        echo
        CREATE_NGINX=$REPLY
    else
        CREATE_NGINX="y"
    fi
    
    if [[ $CREATE_NGINX =~ ^[Yy]$ ]]; then
        sudo tee $NGINX_CONF > /dev/null << EOF
server {
    listen 80;
    server_name _;

    # Frontend - serve built React app
    location / {
        root $SCRIPT_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

    # Backend API - proxy to FastAPI
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API Documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host \$host;
    }

    location /redoc {
        proxy_pass http://localhost:8000/redoc;
        proxy_set_header Host \$host;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_set_header Host \$host;
    }
}
EOF
        print_status "Nginx configuration created"
        
        # Enable site
        sudo ln -sf /etc/nginx/sites-available/sanctions-screening /etc/nginx/sites-enabled/
        
        # Test configuration
        if sudo nginx -t; then
            print_status "Nginx configuration is valid"
            sudo systemctl reload nginx
            print_status "Nginx reloaded"
        else
            print_error "Nginx configuration has errors"
        fi
    fi
else
    print_warning "Nginx not installed. Install with: sudo apt install nginx -y"
fi

echo ""

# Step 10: Start services
echo "Step 10: Starting services..."

sudo systemctl start sanctions-backend
if sudo systemctl is-active --quiet sanctions-backend; then
    print_status "Backend service started"
else
    print_error "Backend service failed to start"
    echo "Check logs with: sudo journalctl -u sanctions-backend -n 50"
fi

echo ""

# Final summary
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Your application should now be accessible at:"
echo ""
echo "  Frontend:     http://$(hostname -I | awk '{print $1}')"
echo "  API:          http://$(hostname -I | awk '{print $1}')/api"
echo "  API Docs:     http://$(hostname -I | awk '{print $1}')/docs"
echo ""
echo "Useful commands:"
echo "  View backend logs:    sudo journalctl -u sanctions-backend -f"
echo "  Restart backend:      sudo systemctl restart sanctions-backend"
echo "  Stop backend:         sudo systemctl stop sanctions-backend"
echo "  Reload Nginx:         sudo systemctl reload nginx"
echo ""
echo "Next steps:"
echo "  1. Access the dashboard in your browser"
echo "  2. Go to 'Lists Management' and update sanctions lists"
echo "  3. Upload PEP and World Bank data if needed"
echo ""
