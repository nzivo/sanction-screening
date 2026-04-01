# Sanctions Screening System

A comprehensive sanctions screening system with FastAPI backend and React frontend.

## Project Structure

```
sanction-screening/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main API application
│   ├── models.py           # Database models
│   ├── schemas.py          # Pydantic schemas
│   ├── database.py         # Database configuration
│   ├── config.py           # Application configuration
│   ├── list_downloaders.py # Sanctions list downloaders
│   ├── screening_service.py # Screening logic
│   ├── pep_manager.py      # PEP management
│   ├── worldbank_manager.py # World Bank management
│   ├── update_scheduler.py  # Smart update scheduling
│   └── requirements.txt     # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   └── App.jsx        # Main app
│   ├── package.json
│   └── README.md
└── venv/                  # Python virtual environment
```

## Features

### Backend (FastAPI)

- **Sanctions Lists**: OFAC, UN, EU, UK, FRC Kenya, World Bank
- **Smart Scheduling**: Automatic list updates based on change frequency
- **Fuzzy Matching**: RapidFuzz for accurate name matching (80% threshold)
- **PEP Management**: Upload and manage Politically Exposed Persons
- **Comprehensive API**: RESTful API with OpenAPI documentation

### Frontend (React + Tailwind)

- **Modern Dashboard**: Real-time statistics and status monitoring
- **Sanctions Screening**: Interactive screening interface
- **List Management**: Update and manage all sanctions lists
- **File Uploads**: Easy upload for PEP, World Bank, and FRC Kenya lists
- **Search Functionality**: Search across all databases
- **Responsive Design**: Works on desktop and mobile

## Quick Start

### Backend Setup

```bash
# Navigate to backend
cd backend

# Activate virtual environment
# Windows:
..\venv\Scripts\activate
# Unix/Mac:
source ../venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Initialize database
python init_db.py

# Start backend server
python main.py
```

Backend will run on `http://localhost:8001`

API Documentation: `http://localhost:8001/docs`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on `http://localhost:3001`

## Configuration

### Backend Configuration

Edit `backend/config.py` or create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost/sanctions_db
SECRET_KEY=your-secret-key
```

### Frontend Configuration

The frontend is pre-configured to work with the backend. No additional configuration needed.

## API Endpoints

### Sanctions Lists

- `POST /lists/update/{source}` - Update specific list
- `POST /lists/update/all` - Update all lists
- `GET /lists/check-updates` - Check update status
- `GET /lists/schedule` - View update schedule
- `GET /lists/status` - Get all lists status

### Screening

- `POST /screen` - Screen a name
- `GET /screening/history` - View screening history

### PEP Management

- `POST /pep/upload` - Upload PEP list
- `GET /pep/search` - Search PEP records
- `GET /pep/stats` - Get PEP statistics

### World Bank

- `POST /worldbank/upload` - Upload World Bank list
- `GET /worldbank/search` - Search entities
- `GET /worldbank/stats` - Get statistics

### FRC Kenya

- `POST /frc-kenya/upload` - Upload FRC Kenya list
- `GET /frc-kenya` - Search entities
- `GET /frc-kenya/stats` - Get statistics

## Sanctions Sources

1. **OFAC** (Office of Foreign Assets Control) - US sanctions
2. **UN** (United Nations) - UN sanctions
3. **EU** (European Union) - EU financial sanctions
4. **UK** (United Kingdom) - UK sanctions
5. **World Bank** - Debarred entities (manual upload)
6. **FRC Kenya** - Kenya domestic sanctions (manual upload)

## Update Intervals

- **OFAC**: 24 hours (daily)
- **UN**: 168 hours (weekly)
- **EU**: 168 hours (weekly)
- **UK**: 168 hours (weekly)
- **FRC Kenya**: 168 hours (weekly)
- **World Bank**: Manual upload only

## Development

### Backend Development

```bash
cd backend

# Run tests
python test_api.py

# Check database
python check_pep_data.py

# Debug OFAC downloads
python debug_ofac.py
```

### Frontend Development

```bash
cd frontend

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Production Deployment

### Backend

```bash
cd backend

# Install production dependencies
pip install -r requirements.txt

# Run with uvicorn (production)
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# Serve the dist/ folder with nginx, Apache, or any static server
```

## Documentation

- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)
- [Entity Type Guide](backend/ENTITY_TYPE_GUIDE.md)
- [PEP Upload Guide](backend/PEP_UPLOAD_GUIDE.md)
- [EU/UK Lists Guide](backend/EU_UK_LISTS_GUIDE.md)
- [FRC Kenya Guide](backend/FRC_KENYA_GUIDE.md)
- [World Bank Guide](backend/WORLDBANK_UPLOAD_GUIDE.md)
- [Smart Updates Guide](backend/SMART_UPDATES_GUIDE.md)
- [Screening Guide](backend/SCREENING_GUIDE.md)
- [Troubleshooting](backend/TROUBLESHOOTING.md)

## Database

PostgreSQL 12+ required.

### Database Schema

- `sanctions_lists` - All sanctions entities
- `pep_lists` - Politically Exposed Persons
- `screening_results` - Screening history
- `list_update_logs` - Update history

## Security

- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM
- CORS configured for frontend
- Environment variables for sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions:

- Review documentation in `backend/*.md` files
- Check API docs at `http://localhost:8001/docs`
- Refer to troubleshooting guide

## Version

Current Version: 1.0.0
