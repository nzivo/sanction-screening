# Sanctions Screening System

A comprehensive FastAPI-based sanctions screening system that integrates with OFAC, UN, EU, UK, and other sanctions lists, along with Politically Exposed Persons (PEP) lists.

## Features

- **Multi-Source Sanctions Screening**: Integrates with OFAC SDN, UN Consolidated, EU Financial Sanctions, UK HM Treasury, FRC Kenya Domestic, World Bank Debarment, and other major sanctions lists
- **PEP Screening**: Manage and screen against Politically Exposed Persons lists (starting with Kenya)
- **FRC Kenya Integration**: Automated download and manual upload of Kenya's domestic Targeted Financial Sanctions (TFS) list
- **World Bank Integration**: Manual upload and management of World Bank debarred entities (firms/individuals)
- **Smart Update Scheduling**: Intelligent list updates based on recommended frequencies and remote file modifications
- **Fuzzy Matching**: 80% threshold fuzzy matching using RapidFuzz for accurate name matching
- **PostgreSQL Storage**: All lists and screening results stored locally for fast querying
- **RESTful API**: Complete FastAPI-based REST API for all operations
- **Automated Updates**: Background tasks for updating sanctions lists with skip logic
- **Screening History**: Track all screening queries and results
- **Alias Support**: Handles alternative names and aliases for comprehensive matching

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+

### Setup

1. **Clone or navigate to the project directory**

```bash
cd sanction-screening
```

2. **Create a virtual environment**

```bash
python -m venv venv
```

3. **Activate virtual environment**

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Setup PostgreSQL Database**

Create a PostgreSQL database:

```sql
CREATE DATABASE sanctions_db;
CREATE USER sanctions_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sanctions_db TO sanctions_user;
```

6. **Configure Environment**

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
```

Edit `.env`:

```
DATABASE_URL=postgresql://sanctions_user:your_password@localhost:5432/sanctions_db
FUZZY_MATCH_THRESHOLD=80
UPDATE_INTERVAL_HOURS=24
```

7. **Initialize Database**

```bash
python -c "from database import engine, Base; Base.metadata.create_all(bind=engine)"
```

## Running the Application

### Start the API Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## API Endpoints

### Screening

#### Screen a Single Name

```bash
POST /screen
```

Request body:

```json
{
  "name": "John Doe",
  "entity_type": "Individual",
  "country": "Kenya",
  "date_of_birth": "1970-01-01",
  "client_reference": "REF123",
  "include_pep": true,
  "include_sanctions": true
}
```

#### Batch Screen Multiple Names

```bash
POST /screen/batch
```

Request body:

```json
{
  "names": ["John Doe", "Jane Smith", "Acme Corporation"],
  "include_pep": true,
  "include_sanctions": true
}
```

#### Get Screening History

```bash
POST /screen/history
```

Request body:

```json
{
  "query_name": "John",
  "client_reference": "REF123",
  "min_score": 80,
  "limit": 100
}
```

### PEP Management

#### Add a PEP

```bash
POST /pep
```

Request body:

```json
{
  "country": "Kenya",
  "full_name": "William Ruto",
  "position": "President",
  "position_level": "National",
  "organization": "Office of the President",
  "pep_type": "Direct",
  "status": "Active",
  "risk_level": "High"
}
```

#### Get PEP by ID

```bash
GET /pep/{pep_id}
```

#### Update PEP

```bash
PUT /pep/{pep_id}
```

#### Deactivate PEP

```bash
DELETE /pep/{pep_id}
```

#### Get PEPs by Country

```bash
GET /pep/country/Kenya
```

#### Search PEPs

```bash
GET /pep/search/?name=William&country=Kenya&status=Active
```

#### Initialize Kenya PEP List

```bash
POST /pep/initialize/kenya
```

### World Bank Management

#### Upload World Bank Debarred Entities

```bash
POST /worldbank/upload
```

Upload Excel (.xlsx) or CSV file with World Bank debarment list. The endpoint accepts flexible column names:

- **Firm Name** or **Name**: Entity name
- **Country**: Country of the entity
- **Ineligibility Period From**: Start date (YYYY-MM-DD or DD/MM/YYYY)
- **Ineligibility Period To**: End date
- **Grounds**: Reason for debarment
- **Address**: Entity address

Returns upload statistics including records added, updated, and any errors.

#### List World Bank Entities

```bash
GET /worldbank?skip=0&limit=100&country=Kenya&search=ABC Company
```

#### Get World Bank Entity by ID

```bash
GET /worldbank/{entity_id}
```

#### Get World Bank Statistics

```bash
GET /worldbank/stats
```

Returns total count, active/inactive counts, and country breakdown.

#### Delete World Bank Entity

```bash
DELETE /worldbank/{entity_id}
```

#### Deactivate World Bank Entity

```bash
POST /worldbank/{entity_id}/deactivate
```

See [WORLDBANK_UPLOAD_GUIDE.md](WORLDBANK_UPLOAD_GUIDE.md) for detailed instructions.

### FRC Kenya Management

#### Update FRC Kenya List Automatically

```bash
POST /lists/update/frc-kenya
POST /lists/update/frc-kenya?force=true
```

Downloads and updates the FRC Kenya domestic sanctions list from the official source.

#### Upload FRC Kenya List Manually

```bash
POST /frc-kenya/upload
```

Upload Excel file with FRC Kenya domestic list. Useful when the official URL changes or for uploading historical versions.

#### List FRC Kenya Entities

```bash
GET /frc-kenya?limit=100
GET /frc-kenya?name=search&country=Kenya&entity_type=Individual
```

#### Get FRC Kenya Statistics

```bash
GET /frc-kenya/stats
```

Returns total count, entity type breakdown, and country distribution.

See [FRC_KENYA_GUIDE.md](FRC_KENYA_GUIDE.md) for detailed instructions.

### Sanctions List Management

#### Check Which Lists Need Updating

```bash
GET /lists/check-updates
```

Returns which lists need updating based on schedule and last update time.

#### View Update Schedule

```bash
GET /lists/schedule
```

Shows configured update intervals and recommended frequencies.

#### Update OFAC List

```bash
POST /lists/update/ofac
POST /lists/update/ofac?force=true  # Force update
```

#### Update UN List

```bash
POST /lists/update/un
POST /lists/update/un?force=true
```

#### Update EU List

```bash
POST /lists/update/eu
POST /lists/update/eu?force=true
```

#### Update UK List

```bash
POST /lists/update/uk
POST /lists/update/uk?force=true
```

#### Update FRC Kenya Domestic List

```bash
POST /lists/update/frc-kenya
POST /lists/update/frc-kenya?force=true
```

#### Update All Lists

```bash
POST /lists/update/all
POST /lists/update/all?force=true  # Force all updates
```

By default, updates respect the smart schedule and skip unnecessary updates. Use `force=true` to override.

**Note**: "Update All" now includes OFAC, UN, EU, UK, and FRC Kenya lists.

#### Get Lists Status

```bash
GET /lists/status
```

## Usage Examples

### Python Example

```python
import requests

# Screen a name
response = requests.post(
    "http://localhost:8000/screen",
    json={
        "name": "John Doe",
        "entity_type": "Individual",
        "include_pep": True,
        "include_sanctions": True
    }
)

result = response.json()
print(f"Total matches: {result['total_matches']}")
print(f"Highest score: {result['highest_score']}")
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "William Ruto",
    "entity_type": "Individual",
    "country": "Kenya",
    "include_pep": true,
    "include_sanctions": true
  }'
```

## Database Schema

### Tables

- **sanctions_lists**: Stores all sanctions entries from various sources
- **pep_lists**: Stores Politically Exposed Persons
- **screening_results**: Stores all screening queries and matches
- **list_update_logs**: Tracks list update history

## Matching Logic

The system uses RapidFuzz's `token_sort_ratio` algorithm with an 80% threshold:

1. **Name Matching**: Fuzzy matching against full names
2. **Alias Matching**: Checks all known aliases
3. **Additional Verification**: Date of birth, country matching
4. **Scoring**: Returns match percentage (0-100)

## Adding More Countries

To add PEPs for another country, create a list similar to `KENYA_PEPS` in `pep_manager.py`:

```python
COUNTRY_PEPS = [
    {
        "country": "CountryName",
        "full_name": "Person Name",
        "position": "Title",
        "position_level": "National",
        "pep_type": "Direct",
        "status": "Active",
        "risk_level": "High"
    },
    # ... more entries
]
```

Then add an initialization function similar to `initialize_kenya_peps()`.

## Maintenance

### Update Sanctions Lists

It's recommended to update sanctions lists regularly:

```bash
# Daily cron job
0 2 * * * curl -X POST http://localhost:8000/lists/update/all
```

### Database Backups

Regular PostgreSQL backups:

```bash
pg_dump -U sanctions_user sanctions_db > backup_$(date +%Y%m%d).sql
```

## Security Considerations

1. **Database Credentials**: Never commit `.env` file
2. **API Authentication**: Consider adding JWT or API key authentication
3. **Rate Limiting**: Implement rate limiting for production
4. **HTTPS**: Use HTTPS in production environments
5. **Input Validation**: All inputs are validated via Pydantic schemas

## Performance Optimization

- Database indexes on frequently queried fields
- Background tasks for list updates
- Batch screening for multiple names
- PostgreSQL full-text search for large datasets

## Troubleshooting

### Database Connection Issues

Check PostgreSQL is running:

```bash
# Windows
services.msc

# Linux
sudo systemctl status postgresql
```

### XML Parsing Errors

If list downloads fail, check:

- Internet connectivity
- Sanctions list URLs (may change over time)
- XML format compatibility

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting steps.

## Documentation

Additional guides are available:

- [QUICKSTART.md](QUICKSTART.md) - Quick start guide for getting up and running
- [SCREENING_GUIDE.md](SCREENING_GUIDE.md) - Detailed screening workflow and usage
- [PEP_UPLOAD_GUIDE.md](PEP_UPLOAD_GUIDE.md) - Bulk upload PEP lists
- [WORLDBANK_UPLOAD_GUIDE.md](WORLDBANK_UPLOAD_GUIDE.md) - Upload World Bank debarred entities
- [FRC_KENYA_GUIDE.md](FRC_KENYA_GUIDE.md) - FRC Kenya domestic sanctions list integration
- [EU_UK_LISTS_GUIDE.md](EU_UK_LISTS_GUIDE.md) - EU and UK sanctions list integration
- [SMART_UPDATES_GUIDE.md](SMART_UPDATES_GUIDE.md) - Smart update scheduling system
- [ENTITY_TYPE_GUIDE.md](ENTITY_TYPE_GUIDE.md) - Entity types and classification
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

## License

This project is for compliance and regulatory purposes. Ensure compliance with local laws and regulations when using sanctions data.

## Support

For issues and questions, please refer to the API documentation at `/docs` endpoint.

## Contributing

To add more sanctions sources:

1. Create a downloader class in `list_downloaders.py`
2. Implement XML/JSON parsing
3. Add update endpoint in `main.py`
4. Update documentation

## Roadmap

- [x] EU Sanctions List integration
- [x] UK Sanctions List integration
- [x] FRC Kenya Domestic TFS List integration
- [x] World Bank Debarred Entities (manual upload)
- [ ] Automated World Bank list updates
- [ ] Vessel screening
- [ ] Real-time API webhooks
- [ ] Machine learning for improved matching
- [ ] Multi-language support
- [ ] Advanced reporting and analytics
