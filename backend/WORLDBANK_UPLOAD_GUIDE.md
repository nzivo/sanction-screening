# World Bank Debarred Entities Upload Guide

## Overview

The World Bank maintains a list of firms and individuals who are temporarily or permanently ineligible to be awarded a World Bank-financed contract. This guide shows you how to upload and manage these entities in the sanctions screening system.

## Uploading World Bank Lists

### Endpoint

```
POST /worldbank/upload
```

### Supported Formats

- **Excel**: `.xlsx`, `.xls`
- **CSV**: `.csv`

### Required Columns

The system will look for these columns (case-insensitive):

| Column Name                   | Alternative Names                  | Required       | Description                 |
| ----------------------------- | ---------------------------------- | -------------- | --------------------------- |
| **Firm Name**                 | Name, FIRM NAME, NAME, Entity Name | ✅ Yes         | Name of the debarred entity |
| **Country**                   | COUNTRY, Country of Origin         | ⚠️ Recommended | Country of the entity       |
| **Ineligibility Period From** | From Date, FROM DATE, Start Date   | ⚠️ Recommended | Start date of debarment     |

### Optional Columns

| Column Name                 | Alternative Names          | Description                                        |
| --------------------------- | -------------------------- | -------------------------------------------------- |
| **Ineligibility Period To** | To Date, TO DATE, End Date | End date of debarment                              |
| **Grounds**                 | GROUNDS, Reason, Basis     | Grounds for debarment                              |
| **Address**                 | ADDRESS                    | Address of the entity                              |
| **Entity Type**             | ENTITY TYPE, Type          | Type of entity (Firm, Individual, etc.)            |
| **ID**                      | -                          | Unique identifier (auto-generated if not provided) |

## World Bank Official Format

The World Bank publishes their debarment list at:
https://www.worldbank.org/en/projects-operations/procurement/debarred-firms

Their typical CSV format includes:

```csv
Firm Name,Country,Ineligibility Period From,Ineligibility Period To,Grounds,Address
"Acme Construction Ltd","Nigeria","01/15/2023","01/14/2028","Fraud and Corruption","123 Main St, Lagos"
"XYZ Consultants","Kenya","06/01/2024","12/31/9999","Fraudulent Practice","Nairobi, Kenya"
```

## Usage Examples

### Python

```python
import requests

# Upload World Bank list
with open('worldbank_debarment.xlsx', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/worldbank/upload',
        files=files,
        params={'update_if_exists': True}
    )

    result = response.json()
    print(f"Uploaded: {result['added']} new, {result['updated']} updated")
    print(f"Errors: {len(result['errors'])}")
```

### cURL

```bash
# Upload Excel file
curl -X POST "http://localhost:8000/worldbank/upload?update_if_exists=true" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@worldbank_debarment.xlsx"

# Upload CSV file
curl -X POST "http://localhost:8000/worldbank/upload" \
  -F "file=@worldbank_debarment.csv"
```

### Swagger UI

1. Go to `http://localhost:8000/docs`
2. Find **POST /worldbank/upload**
3. Click "Try it out"
4. Choose your file
5. Set `update_if_exists` (optional, default: true)
6. Click "Execute"

## Response Format

```json
{
  "total_records": 150,
  "added": 120,
  "updated": 25,
  "failed": 5,
  "errors": [
    "Row 45: Missing required field 'Firm Name'",
    "Row 78: Invalid date format"
  ],
  "message": "Successfully processed 145 entities (120 new, 25 updated, 5 failed)"
}
```

## API Endpoints

### 1. Upload Entities

```bash
POST /worldbank/upload
```

**Parameters:**

- `file`: Excel or CSV file (required)
- `update_if_exists`: Update existing entities (default: true)

### 2. List All Entities

```bash
GET /worldbank
```

**Query Parameters:**

- `name`: Filter by name (partial match)
- `country`: Filter by country
- `is_active`: Filter by active status (default: true)
- `limit`: Maximum results (default: 100)

**Example:**

```bash
curl "http://localhost:8000/worldbank?country=Nigeria&limit=50"
```

### 3. Get Specific Entity

```bash
GET /worldbank/{entity_id}
```

**Example:**

```bash
curl http://localhost:8000/worldbank/123
```

### 4. Get Statistics

```bash
GET /worldbank/stats
```

**Response:**

```json
{
  "total_active": 1250,
  "total_inactive": 45,
  "top_countries": [
    { "country": "India", "count": 234 },
    { "country": "China", "count": 189 },
    { "country": "Nigeria", "count": 156 }
  ]
}
```

### 5. Deactivate Entity

```bash
POST /worldbank/{entity_id}/deactivate
```

Marks an entity as inactive (soft delete).

### 6. Delete Entity

```bash
DELETE /worldbank/{entity_id}
```

Permanently deletes an entity.

## Example CSV Template

Create a CSV file with this structure:

```csv
Firm Name,Country,Ineligibility Period From,Ineligibility Period To,Grounds,Address
"ABC Construction Ltd","Kenya","2023-01-15","2028-01-14","Fraudulent Practice","Nairobi, Kenya"
"XYZ Trading Co","Nigeria","2024-06-01","9999-12-31","Corruption and Fraud","Lagos, Nigeria"
"Acme Consultants","India","2022-03-10","2027-03-09","Collusive Practice","Mumbai, India"
"Beta Engineering","South Africa","2023-11-20","2025-11-19","Obstructive Practice","Johannesburg"
```

Save as `worldbank_template.csv` and upload.

## Example Excel Template

**Sheet Name:** Debarment List

| Firm Name            | Country | Ineligibility Period From | Ineligibility Period To | Grounds              | Address        |
| -------------------- | ------- | ------------------------- | ----------------------- | -------------------- | -------------- |
| ABC Construction Ltd | Kenya   | 01/15/2023                | 01/14/2028              | Fraudulent Practice  | Nairobi, Kenya |
| XYZ Trading Co       | Nigeria | 06/01/2024                | 12/31/9999              | Corruption and Fraud | Lagos, Nigeria |
| Acme Consultants     | India   | 03/10/2022                | 03/09/2027              | Collusive Practice   | Mumbai, India  |

## Screening Against World Bank List

Once uploaded, World Bank entities are automatically included in sanctions screening:

```python
import requests

response = requests.post(
    'http://localhost:8000/screen',
    json={
        'name': 'ABC Construction',
        'entity_type': 'Entity',
        'include_sanctions': True
    }
)

result = response.json()

# Check for World Bank matches
for match in result['sanctions_matches']:
    if match['source'] == 'WorldBank':
        print(f"Found World Bank debarment: {match['matched_name']}")
        print(f"Match score: {match['match_score']}%")
        print(f"Details: {match['remarks']}")
```

## Data Storage

World Bank entities are stored in the `sanctions_lists` table:

- **source**: "WorldBank"
- **list_type**: "Debarred"
- **entity_type**: Usually "Entity" for firms
- **remarks**: Contains debarment dates and grounds

## Update Strategy

### Manual Updates

The World Bank list changes periodically as:

- New firms are debarred
- Debarment periods expire
- Appeals are processed

**Recommended:** Check monthly for updates.

### Update Process

1. Download latest list from World Bank website
2. Upload via `/worldbank/upload` with `update_if_exists=true`
3. System will:
   - Add new entries
   - Update existing entries
   - Preserve entities not in the new file

### Replace All Data

To completely replace the list:

```python
# 1. Clear existing data (be careful!)
# This would require admin access or direct database access

# 2. Upload new file
response = requests.post(
    'http://localhost:8000/worldbank/upload',
    files={'file': open('latest_worldbank.xlsx', 'rb')},
    params={'update_if_exists': True}
)
```

## Best Practices

### 1. **Data Validation**

Before uploading:

- Check for required columns
- Validate date formats
- Remove duplicate entries
- Verify country names

### 2. **Regular Updates**

```bash
# Monthly cron job
0 0 1 * * /path/to/update_worldbank.sh
```

Script content:

```bash
#!/bin/bash
# Download latest from World Bank
wget https://www.worldbank.org/debarred_firms.xlsx -O /tmp/wb.xlsx

# Upload to system
curl -X POST "http://localhost:8000/worldbank/upload" \
  -F "file=@/tmp/wb.xlsx" \
  --silent

# Cleanup
rm /tmp/wb.xlsx
```

### 3. **Monitor Upload Results**

```python
def upload_and_monitor(filepath):
    with open(filepath, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/worldbank/upload',
            files={'file': f}
        )

    result = response.json()

    # Alert if high failure rate
    if result['failed'] > result['added'] * 0.1:
        send_alert(f"High failure rate: {result['failed']} failures")

    # Log results
    logging.info(f"World Bank upload: {result['message']}")
```

### 4. **Backup Before Major Updates**

```sql
-- PostgreSQL backup
pg_dump -U user -t sanctions_lists -W sanctions_db > worldbank_backup.sql

-- Or backup specific source
COPY (SELECT * FROM sanctions_lists WHERE source = 'WorldBank')
TO '/path/to/worldbank_backup.csv' WITH CSV HEADER;
```

## Troubleshooting

### Issue: "Could not find name column"

**Solution:** Ensure your file has one of these columns:

- Firm Name
- Name
- Entity Name

### Issue: "No valid World Bank entities found"

**Causes:**

- Empty name column
- All rows have blank names
- File format not recognized

**Solution:**

1. Open file in Excel/LibreOffice
2. Verify data exists
3. Check column headers match expected names

### Issue: High number of failed records

**Check:**

1. Review `errors` array in response
2. Common issues:
   - Missing required fields
   - Invalid data types
   - Extremely long text fields

### Issue: Duplicates being created

**Solution:** Use `update_if_exists=true` parameter:

```bash
curl -X POST "http://localhost:8000/worldbank/upload?update_if_exists=true" \
  -F "file=@worldbank.xlsx"
```

## Database Queries

### Check uploaded count

```sql
SELECT COUNT(*) FROM sanctions_lists
WHERE source = 'WorldBank' AND is_active = true;
```

### View recent uploads

```sql
SELECT * FROM list_update_logs
WHERE source = 'WorldBank'
ORDER BY update_started DESC LIMIT 5;
```

### Find specific entity

```sql
SELECT full_name, country, remarks
FROM sanctions_lists
WHERE source = 'WorldBank'
  AND full_name ILIKE '%construction%';
```

### Top countries

```sql
SELECT country, COUNT(*) as count
FROM sanctions_lists
WHERE source = 'WorldBank' AND is_active = true
GROUP BY country
ORDER BY count DESC
LIMIT 10;
```

## Integration with Screening

World Bank entities are automatically included in screening:

```bash
# Screen a company name
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ABC Construction",
    "entity_type": "Entity",
    "include_sanctions": true
  }'
```

Response will include World Bank matches:

```json
{
  "sanctions_matches": [
    {
      "source": "WorldBank",
      "list_type": "Debarred",
      "matched_name": "ABC Construction Ltd",
      "match_score": 95.5,
      "country": "Kenya",
      "remarks": "From: 01/15/2023; To: 01/14/2028; Grounds: Fraudulent Practice"
    }
  ]
}
```

## Resources

- **World Bank Debarment List**: https://www.worldbank.org/en/projects-operations/procurement/debarred-firms
- **API Documentation**: http://localhost:8000/docs#/worldbank
- **Support**: Check TROUBLESHOOTING.md for common issues

## Summary

✅ Upload Excel/CSV files with debarred entities  
✅ Automatic duplicate detection and updates  
✅ Integrated with sanctions screening  
✅ Search and filter by name, country  
✅ Track upload statistics and errors  
✅ Export and backup capabilities

The World Bank list integration provides comprehensive coverage of procurement-related debarments alongside traditional sanctions lists!
