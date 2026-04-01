# Quick Start Guide

## 🚀 Fast Setup (5 minutes)

### Step 1: Start PostgreSQL Database

Using Docker (Recommended):

```bash
docker-compose up -d
```

Or install PostgreSQL manually and create database:

```sql
CREATE DATABASE sanctions_db;
CREATE USER sanctions_user WITH PASSWORD 'sanctions_password';
GRANT ALL PRIVILEGES ON DATABASE sanctions_db TO sanctions_user;
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy example env file
cp .env.example .env
```

Edit `.env` if needed (default values work with Docker setup):

```
DATABASE_URL=postgresql://sanctions_user:sanctions_password@localhost:5432/sanctions_db
FUZZY_MATCH_THRESHOLD=80
```

### Step 4: Initialize Database

```bash
python init_db.py
```

This will:

- Create all database tables
- Load Kenya PEP list (16 entries)

### Step 5: Start the API

```bash
python main.py
```

Or with auto-reload for development:

```bash
uvicorn main:app --reload
```

### Step 6: Test the API

Open your browser:

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

Or run the test script:

```bash
python test_api.py
```

### Step 7: Download Sanctions Lists

Download OFAC and UN lists (this may take a few minutes):

```bash
curl -X POST http://localhost:8000/lists/update/all
```

Wait a few minutes for the lists to download and process.

## 🎯 First Screening

Screen a name:

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "William Ruto",
    "country": "Kenya",
    "include_pep": true,
    "include_sanctions": true
  }'
```

Expected response:

```json
{
  "query_name": "William Ruto",
  "total_matches": 1,
  "highest_score": 100,
  "pep_matches": [
    {
      "matched_name": "William Samoei Ruto",
      "match_score": 100,
      "position": "President of the Republic of Kenya",
      "risk_level": "High"
    }
  ],
  "sanctions_matches": []
}
```

## 📊 Check System Status

View lists status:

```bash
curl http://localhost:8000/lists/status
```

View Kenya PEPs:

```bash
curl http://localhost:8000/pep/country/Kenya
```

## 🔄 Regular Maintenance

### Update Lists Daily

Add to cron (Linux/Mac):

```bash
0 2 * * * curl -X POST http://localhost:8000/lists/update/all
```

Or use Windows Task Scheduler to run:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/lists/update/all" -Method Post
```

### Backup Database

```bash
# Using Docker
docker exec sanctions_db pg_dump -U sanctions_user sanctions_db > backup_$(date +%Y%m%d).sql

# Direct PostgreSQL
pg_dump -U sanctions_user sanctions_db > backup_$(date +%Y%m%d).sql
```

## 🛠️ Common Issues

### Port 5432 already in use

```bash
# Stop existing PostgreSQL
# Windows: services.msc
# Linux: sudo systemctl stop postgresql
```

### Database connection error

- Check PostgreSQL is running: `docker ps` or `pg_isready`
- Verify credentials in `.env`
- Test connection: `psql -U sanctions_user -d sanctions_db -h localhost`

### No matches found

- Make sure lists are downloaded: `curl http://localhost:8000/lists/status`
- Initialize Kenya PEPs: `curl -X POST http://localhost:8000/pep/initialize/kenya`

## 📱 Integration Examples

### Python Client

```python
import requests

def screen_person(name, country=None):
    response = requests.post(
        "http://localhost:8000/screen",
        json={
            "name": name,
            "country": country,
            "include_pep": True,
            "include_sanctions": True
        }
    )
    return response.json()

# Use it
result = screen_person("John Doe", "Kenya")
if result['total_matches'] > 0:
    print(f"⚠️ Found {result['total_matches']} matches!")
else:
    print("✅ No matches found")
```

### JavaScript/Node.js

```javascript
async function screenPerson(name, country) {
  const response = await fetch("http://localhost:8000/screen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: name,
      country: country,
      include_pep: true,
      include_sanctions: true,
    }),
  });
  return await response.json();
}

// Use it
const result = await screenPerson("John Doe", "Kenya");
console.log(`Matches: ${result.total_matches}`);
```

## 🎓 Next Steps

1. **Add More PEPs**: Create lists for other countries
2. **Customize Threshold**: Adjust fuzzy match threshold in `.env`
3. **Add Authentication**: Implement JWT or API keys
4. **Set Up Monitoring**: Add logging and alerting
5. **Scale**: Use connection pooling and caching

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

## 🆘 Support

- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
