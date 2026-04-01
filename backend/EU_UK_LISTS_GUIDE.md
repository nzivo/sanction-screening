# EU and UK Sanctions Lists Integration Guide

This guide covers the newly integrated EU and UK sanctions lists.

## Overview

The system now supports **four major sanctions sources**:

1. **OFAC** (US Office of Foreign Assets Control) - SDN List
2. **UN** (United Nations) - Consolidated Sanctions List
3. **EU** (European Union) - Financial Sanctions List ✨ NEW
4. **UK** (United Kingdom) - HM Treasury Consolidated List ✨ NEW

## What's New

### EU Financial Sanctions List

- **Source**: European Union
- **Format**: XML
- **Coverage**: EU-specific sanctions, asset freezes, travel bans
- **Updates**: Download from EU Commission's Financial Sanctions Database
- **Entity Types**: Individuals and Entities
- **Includes**: Names, aliases, birth dates, addresses, nationalities

### UK HM Treasury Consolidated List

- **Source**: UK Office of Financial Sanctions Implementation (OFSI)
- **Format**: CSV
- **Coverage**: UK financial sanctions under various regimes
- **Updates**: Download from UK Government's official source
- **Entity Types**: Individuals and Entities
- **Includes**: Names, aliases, DOB, addresses, nationalities, regimes

## API Endpoints

### Update EU List

```bash
POST /lists/update/eu
```

**Response:**

```json
{
  "message": "EU list update started in background",
  "source": "EU",
  "list_type": "EU Sanctions"
}
```

### Update UK List

```bash
POST /lists/update/uk
```

**Response:**

```json
{
  "message": "UK list update started in background",
  "source": "UK",
  "list_type": "UK Consolidated"
}
```

### Update All Lists (Now includes EU & UK)

```bash
POST /lists/update/all
```

**Response:**

```json
{
  "message": "All lists update started in background",
  "lists": ["OFAC SDN", "UN Consolidated", "EU Sanctions", "UK Consolidated"]
}
```

## Usage Examples

### Python

```python
import requests

base_url = "http://localhost:8000"

# Update EU list
response = requests.post(f"{base_url}/lists/update/eu")
print(response.json())

# Update UK list
response = requests.post(f"{base_url}/lists/update/uk")
print(response.json())

# Update all lists including EU and UK
response = requests.post(f"{base_url}/lists/update/all")
print(response.json())

# Screen a name against all sources
response = requests.post(
    f"{base_url}/screen",
    json={
        "name": "John Smith",
        "entity_type": "Individual",
        "include_sanctions": True
    }
)

result = response.json()
print(f"Total matches: {result['total_matches']}")
print(f"Highest score: {result['highest_score']}")

# Check which source matched
for match in result['sanctions_matches']:
    print(f"Source: {match['source']}, Score: {match['match_score']}")
```

### cURL

```bash
# Update EU list
curl -X POST "http://localhost:8000/lists/update/eu"

# Update UK list
curl -X POST "http://localhost:8000/lists/update/uk"

# Update all lists
curl -X POST "http://localhost:8000/lists/update/all"

# Check list status
curl -X GET "http://localhost:8000/lists/status"
```

## Screening Results

When you screen a name, results will now include matches from EU and UK lists:

```json
{
  "query_name": "Vladimir Putin",
  "sanctions_matches": [
    {
      "source": "OFAC",
      "list_type": "SDN",
      "match_score": 100,
      "matched_name": "Vladimir PUTIN"
    },
    {
      "source": "EU",
      "list_type": "EU Sanctions",
      "match_score": 100,
      "matched_name": "Vladimir Vladimirovich PUTIN"
    },
    {
      "source": "UK",
      "list_type": "UK Consolidated",
      "match_score": 100,
      "matched_name": "Vladimir Vladimirovich PUTIN"
    },
    {
      "source": "UN",
      "list_type": "Consolidated",
      "match_score": 95,
      "matched_name": "Vladimir V. PUTIN"
    }
  ],
  "total_matches": 4,
  "highest_score": 100
}
```

## Database Storage

All EU and UK sanctions data is stored in the same `sanctions_lists` table with:

- **source**: "EU" or "UK"
- **list_type**: "EU Sanctions" or "UK Consolidated"
- **entity_type**: "Individual" or "Entity"
- All standard fields: names, aliases, dates, addresses, etc.

## Data Fields

### EU List Fields

- Entity Number (EU Reference)
- Full Name
- Aliases
- Date of Birth
- Place of Birth
- Nationality
- Address
- Remarks

### UK List Fields

- Entity Number (Group ID)
- Full Name
- Aliases (multiple name fields)
- Date of Birth
- Town/Country of Birth
- Nationality
- Address (multiple fields)
- Postal Code
- Regime
- Listed Date
- Other Information

## Update Frequency

Recommended update schedule:

- **OFAC**: Daily (highly dynamic)
- **UN**: Weekly
- **EU**: Weekly
- **UK**: Weekly

You can automate updates using cron jobs or scheduled tasks:

```bash
# Linux/Mac crontab example
0 2 * * * curl -X POST http://localhost:8000/lists/update/all

# Windows Task Scheduler PowerShell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/lists/update/all"
```

## Troubleshooting

### EU List Issues

If EU list download fails:

- URL may require authentication token (currently blank in config)
- Check: https://www.sanctionsmap.eu/
- Alternative: https://webgate.ec.europa.eu/fsd/fsf

### UK List Issues

The UK CSV URL used:

```
https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv
```

If this fails:

- Check official source: https://www.gov.uk/government/publications/financial-sanctions-consolidated-list-of-targets
- UK also provides XLSX format

### General Tips

1. **Check logs**: Monitor terminal output for download errors
2. **Verify list status**: Use `/lists/status` endpoint
3. **Database space**: EU and UK lists add ~10,000+ entries each
4. **First run**: Initial download may take 1-2 minutes per list

## Implementation Details

### Code Structure

**list_downloaders.py**:

- `EUDownloader`: Handles EU XML parsing with namespaces
- `UKDownloader`: Handles UK CSV parsing with multiple name fields

**main.py**:

- `update_eu_list_background()`: Background task
- `update_uk_list_background()`: Background task
- API endpoints for user-triggered updates

## Configuration

Update URLs in `config.py` if needed:

```python
eu_sanctions_url: str = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token="
uk_sanctions_url: str = "https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv"
```

## Benefits

✅ **Comprehensive Coverage**: Screen against major international sanctions  
✅ **Regional Compliance**: Meet EU and UK regulatory requirements  
✅ **Multi-Source Validation**: Cross-reference matches across jurisdictions  
✅ **Unified API**: Same screening endpoint works for all sources  
✅ **Automatic Deduplication**: System handles overlapping entries

## Next Steps

Consider adding:

- Australia DFAT sanctions
- Canada OSFI sanctions
- Japan METI sanctions
- World Bank debarred entities
- INTERPOL red notices

See the main README for information on extending the system with additional sources.
