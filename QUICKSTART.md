# 🚀 Quick Start Guide

## Project Overview

Your sanctions screening system has been reorganized with:

- ✅ **Backend**: All Python/FastAPI code in `backend/` folder
- ✅ **Frontend**: Modern React + Tailwind dashboard in `frontend/` folder
- ✅ **Startup Scripts**: Easy launch scripts for both Windows and Unix

## 📁 Project Structure

```
sanction-screening/
├── backend/                    # FastAPI Backend
│   ├── main.py                # API endpoints
│   ├── models.py              # Database models
│   ├── schemas.py             # Request/Response schemas
│   ├── list_downloaders.py    # Sanctions downloaders
│   ├── screening_service.py   # Screening logic
│   ├── requirements.txt       # Python dependencies
│   └── *.md                   # Documentation
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Dashboard components
│   │   ├── services/          # API integration
│   │   ├── App.jsx           # Main application
│   │   └── index.css         # Styles
│   ├── package.json
│   └── README.md
├── venv/                      # Python virtual environment (shared)
├── start.bat                  # Windows startup script
├── start.sh                   # Unix/Mac startup script
└── README.md                  # Main documentation
```

## 🎯 Quick Start

### Option 1: Use Startup Script (Recommended)

**Windows:**

```bash
start.bat
```

**Unix/Mac/Linux:**

```bash
./start.sh
```

This will:

1. Start the backend API on `http://localhost:8001`
2. Start the frontend dashboard on `http://localhost:3001`
3. Open both in separate terminal windows

### Option 2: Manual Start

**Terminal 1 - Backend:**

```bash
cd backend
../venv/Scripts/activate  # Windows
source ../venv/bin/activate  # Unix/Mac
python main.py
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm install  # First time only
npm run dev
```

## 🌐 Access Points

Once running, you can access:

- **Frontend Dashboard**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **API Alternative Docs**: http://localhost:8001/redoc

## 📱 Dashboard Features

### 1. Dashboard (Home)

- Real-time statistics for all sanctions lists
- Quick update buttons for each list
- System status monitoring
- Entity counts across all sources

### 2. Screening

- Screen individuals or entities by name
- Optional filters (DOB, nationality)
- Fuzzy matching with 80% threshold
- Detailed match results with scores
- View aliases and remarks

### 3. Lists Management

- Update individual lists (OFAC, UN, EU, UK, FRC Kenya)
- Update all lists at once
- View update schedules and intervals
- Monitor last update times
- Check if updates are needed

### 4. PEP Management

- Upload PEP (Politically Exposed Persons) lists
- Search PEP records
- View statistics
- Excel/CSV support

### 5. World Bank

- Upload World Bank debarred entities
- Search debarred entities
- View statistics
- Excel/CSV support

### 6. FRC Kenya

- Upload Kenya domestic sanctions
- Search FRC Kenya entities
- View statistics
- Excel format support

## 🔧 First Time Setup

### Backend Setup

1. **Database** (if not already done):

```bash
cd backend
python init_db.py
```

2. **Environment Variables** (optional):
   Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost/sanctions_db
```

3. **Initial Data Load**:

```bash
# Update all sanctions lists
curl -X POST http://localhost:8001/lists/update/all
```

### Frontend Setup

No additional setup needed! Dependencies install automatically on first run.

## 📚 API Usage Examples

### Screen a Name

```bash
curl -X POST "http://localhost:8001/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "entity_type": "Individual"
  }'
```

### Update OFAC List

```bash
curl -X POST "http://localhost:8001/lists/update/OFAC?force=true"
```

### Check All Lists Status

```bash
curl "http://localhost:8001/lists/check-updates"
```

### Search PEP

```bash
curl "http://localhost:8001/pep/search?name=John&limit=10"
```

## 🎨 Dashboard Screenshots

The dashboard includes:

- **Modern UI**: Clean, professional design with Tailwind CSS
- **Responsive**: Works on desktop, tablet, and mobile
- **Dark Sidebar**: Easy navigation with icons
- **Real-time Stats**: Live data updates
- **Color-coded Alerts**: Red for high matches, yellow for medium, blue for low
- **Interactive Tables**: Sortable and searchable
- **File Upload**: Drag & drop support

## 🔄 Update Schedules

The system automatically updates lists based on these intervals:

- **OFAC**: Every 24 hours (daily)
- **UN**: Every 168 hours (weekly)
- **EU**: Every 168 hours (weekly)
- **UK**: Every 168 hours (weekly)
- **FRC Kenya**: Every 168 hours (weekly)
- **World Bank**: Manual upload only
- **PEP Lists**: Manual upload only

## 📖 Documentation

Detailed guides available in `backend/`:

- `QUICKSTART.md` - Quick start guide
- `SCREENING_GUIDE.md` - How to use screening
- `EU_UK_LISTS_GUIDE.md` - EU & UK integration
- `FRC_KENYA_GUIDE.md` - Kenya sanctions
- `WORLDBANK_UPLOAD_GUIDE.md` - World Bank entities
- `PEP_UPLOAD_GUIDE.md` - PEP management
- `SMART_UPDATES_GUIDE.md` - Update scheduling
- `TROUBLESHOOTING.md` - Common issues

## 🐛 Troubleshooting

### Backend won't start

```bash
cd backend
pip install -r requirements.txt
python init_db.py
```

### Frontend won't start

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Port already in use

- Backend (8000): Change in `backend/main.py`
- Frontend (3000): Change in `frontend/vite.config.js`

### CORS errors

Make sure backend CORS is configured for `http://localhost:3001`

## 🚀 Production Deployment

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Frontend

```bash
cd frontend
npm run build
# Serve dist/ folder with nginx or any static server
```

## 📝 Next Steps

1. ✅ Start both servers
2. ✅ Access dashboard at http://localhost:3000
3. ✅ Update all sanctions lists from Lists Management
4. ✅ Try screening a name
5. ✅ Upload PEP lists if available
6. ✅ Explore all features

## 🎉 You're All Set!

Your sanctions screening system is ready to use. The frontend provides an intuitive interface for all backend functionality.

### Need Help?

- Check API docs: http://localhost:8000/docs
- Review documentation in `backend/*.md` files
- Check troubleshooting guide
- Review the main README.md

Happy Screening! 🔍
