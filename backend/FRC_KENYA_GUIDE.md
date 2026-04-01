# FRC Kenya Domestic Sanctions List Guide

This guide covers the integration of the **Financial Reporting Centre (FRC) Kenya** domestic sanctions list into your sanctions screening system.

## Overview

The FRC Kenya maintains a **Domestic List** of designated persons and entities under **UNSCR 1373 (2001)** related to terrorism financing and counter-terrorism measures. This is a domestic list specific to Kenya, maintained by the Financial Reporting Centre.

**Source**: https://www.frc.go.ke/targeted-financial-sanctions/

### Key Information

| Field                | Details                                                                   |
| -------------------- | ------------------------------------------------------------------------- |
| **List Name**        | FRC Kenya Domestic TFS List                                               |
| **Maintained By**    | Financial Reporting Centre - Kenya                                        |
| **Legal Basis**      | UNSCR 1373 (2001), POCAMLA 2009                                           |
| **Update Frequency** | Irregular (via TFS Notices)                                               |
| **Format**           | Excel (.xlsx)                                                             |
| **Current URL**      | https://www.frc.go.ke/wp-content/uploads/2026/02/Domestic-List_Kenya.xlsx |

## What's Included

The FRC Kenya list includes:

### Individuals

- Full name
- Date of birth
- Nationality
- Passport/ID numbers
- Address
- Designation date
- Grounds for designation

### Entities/Organizations

- Organization name
- Country/Location
- Address
- Designation date
- Grounds for designation

## Integration Methods

### 1. Automated Download (Recommended)

The system can automatically download and update the FRC Kenya list from the official URL.

#### Update FRC Kenya List

```bash
POST /lists/update/frc-kenya
POST /lists/update/frc-kenya?force=true  # Force update
```

**Using cURL:**

```bash
curl -X POST "http://localhost:8000/lists/update/frc-kenya"
```

**Using Python:**

```python
import requests

response = requests.post("http://localhost:8000/lists/update/frc-kenya")
print(response.json())
# {
#   "message": "FRC Kenya list update started in background",
#   "source": "FRC_Kenya",
#   "list_type": "Domestic TFS Kenya",
#   "forced": false
# }
```

### 2. Manual Upload

If the FRC Kenya URL changes or you want to upload a specific version of the list, use the manual upload endpoint.

#### Upload FRC Kenya List Manually

```bash
POST /frc-kenya/upload
```

**Using cURL:**

```bash
curl -X POST "http://localhost:8000/frc-kenya/upload" \
  -F "file=@Domestic-List_Kenya.xlsx" \
  -F "update_if_exists=true"
```

**Using Python:**

```python
import requests

with open("Domestic-List_Kenya.xlsx", "rb") as f:
    files = {"file": f}
    data = {"update_if_exists": True}

    response = requests.post(
        "http://localhost:8000/frc-kenya/upload",
        files=files,
        data=data
    )

    print(response.json())
```

**Using Swagger UI:**

1. Go to http://localhost:8000/docs
2. Find `/frc-kenya/upload` endpoint
3. Click "Try it out"
4. Upload your Excel file
5. Set `update_if_exists` to true
6. Execute

#### Expected File Format

The Excel file should contain these columns (flexible column name detection):

| Column Name Variations                  | Description            | Required |
| --------------------------------------- | ---------------------- | -------- |
| Name, Full Name, Individual/Entity Name | Person or entity name  | ✓        |
| Type, Entity Type, Individual/Entity    | Individual or Entity   | Optional |
| Nationality, Country                    | Nationality/Country    | Optional |
| Passport, Passport No, ID Number        | Identification number  | Optional |
| Date of Birth, DOB                      | Birth date             | Optional |
| Address, Location                       | Physical address       | Optional |
| Designation Date, Date Listed           | When designated        | Optional |
| Reason, Grounds                         | Reason for designation | Optional |
| Reference, Ref No                       | Reference number       | Optional |

**Example:**

| Name             | Type       | Nationality | Passport | Date of Birth | Address | Designation Date | Reason              |
| ---------------- | ---------- | ----------- | -------- | ------------- | ------- | ---------------- | ------------------- |
| John Doe         | Individual | Kenyan      | A123456  | 1980-01-15    | Nairobi | 2025-02-04       | UNSCR 1373 criteria |
| ABC Organization | Entity     | Kenya       | -        | -             | Mombasa | 2025-02-04       | Financing terrorism |

## Viewing FRC Kenya Entities

### List All Entities

```bash
GET /frc-kenya?limit=100
```

### Search by Name

```bash
GET /frc-kenya?name=john&limit=50
```

### Filter by Country

```bash
GET /frc-kenya?country=Kenya&limit=100
```

### Filter by Entity Type

```bash
GET /frc-kenya?entity_type=Individual&limit=100
```

**Example Response:**

```json
[
  {
    "id": 1,
    "entity_number": "FRC-KE-0001",
    "full_name": "John Doe",
    "entity_type": "Individual",
    "nationality": "Kenyan",
    "country": "Kenya",
    "date_of_birth": "1980-01-15",
    "passport_number": "A123456",
    "address": "Nairobi, Kenya",
    "remarks": "Designated under UNSCR 1373 criteria",
    "designation_date": "2025-02-04",
    "list_updated_date": "2026-03-13T10:30:00"
  }
]
```

## Statistics

Get statistics about the FRC Kenya list:

```bash
GET /frc-kenya/stats
```

**Response:**

```json
{
  "total": 45,
  "by_type": [
    { "type": "Individual", "count": 32 },
    { "type": "Entity", "count": 13 }
  ],
  "top_countries": [
    { "country": "Kenya", "count": 40 },
    { "country": "Somalia", "count": 5 }
  ]
}
```

## Smart Update Scheduling

FRC Kenya updates are managed by the smart scheduler with the following settings:

- **Recommended Interval**: 168 hours (weekly)
- **Minimum Interval**: 6 hours (prevents excessive updates)
- **Update Check**: System checks if update is needed before downloading

### Check Update Status

```bash
GET /lists/check-updates
```

**Response includes FRC Kenya status:**

```json
{
  "sources": {
    "FRC_Kenya": {
      "should_update": false,
      "reason": "Last update was 48 hours ago. Recommended interval is 168 hours",
      "last_update": "2026-03-11T10:00:00",
      "hours_since_update": 48,
      "recommended_interval": 168
    }
  }
}
```

### Force Update

To bypass the smart scheduler and force an update:

```bash
POST /lists/update/frc-kenya?force=true
```

## Screening with FRC Kenya Data

FRC Kenya entities are automatically included in all screening operations. The system performs fuzzy matching (80% threshold) against FRC Kenya entries.

### Screen a Name

```bash
POST /screen
```

```json
{
  "name": "John Doe",
  "entity_type": "Individual",
  "include_sanctions": true
}
```

**Response includes FRC Kenya matches:**

```json
{
  "query": {
    "name": "John Doe",
    "entity_type": "Individual"
  },
  "sanctions_matches": [
    {
      "match_score": 95,
      "source": "FRC_Kenya",
      "list_type": "Domestic TFS Kenya",
      "entity_type": "Individual",
      "full_name": "John Doe",
      "nationality": "Kenyan",
      "date_of_birth": "1980-01-15",
      "remarks": "Designated under UNSCR 1373 criteria"
    }
  ],
  "has_sanctions_match": true,
  "risk_level": "High"
}
```

## Update All Lists

FRC Kenya is included when updating all lists:

```bash
POST /lists/update/all
POST /lists/update/all?force=true
```

This updates:

- OFAC SDN
- UN Consolidated
- EU Sanctions
- UK Consolidated
- **FRC Kenya Domestic**

## Monitoring Updates

### View Update Log

Check the database `list_update_logs` table for FRC Kenya update history:

```sql
SELECT * FROM list_update_logs
WHERE source = 'FRC_Kenya'
ORDER BY update_started DESC
LIMIT 10;
```

### Update Log Fields

- `update_started`: When update began
- `update_completed`: When update finished
- `status`: Success/Failed
- `records_added`: New entities added
- `records_updated`: Existing entities updated
- `error_message`: Error details if failed

## Downloading the Latest List

To manually download the latest FRC Kenya list:

1. Visit: https://www.frc.go.ke/targeted-financial-sanctions/
2. Look for "Domestic List Kenya" link
3. Download the Excel file
4. Upload via `/frc-kenya/upload` endpoint

## TFS Notices

FRC Kenya publishes Targeted Financial Sanctions (TFS) Notices when the list changes:

- **Notice Format**: "Targeted Financial Sanctions Notice No. X of YEAR"
- **Types**: New listings, amendments, delistings
- **Check for notices**: https://www.frc.go.ke/ (Recent Posts section)

### Subscribing to Updates

To receive TFS notices automatically, subscribe to the FRC Kenya mailing list:

**Email**: tfs@frc.go.ke  
**Subject**: Subscribe  
**Body**: Include your name, organization name, and official email address

## Troubleshooting

### Issue: Download Failed

**Error**: "Error downloading FRC Kenya list"

**Solutions**:

1. Check internet connectivity
2. Verify the FRC Kenya website is accessible: https://www.frc.go.ke/
3. Check if the URL has changed (FRC may update the URL in TFS notices)
4. Use manual upload as fallback

### Issue: Excel Parse Error

**Error**: "Error parsing FRC Kenya Excel"

**Solutions**:

1. Verify file format is .xlsx or .xls
2. Check that the file has the expected columns
3. Ensure the file is not corrupted
4. Try downloading a fresh copy from FRC Kenya website

### Issue: No Entities Found

**Error**: "No valid entities found in the uploaded file"

**Solutions**:

1. Check that the Name column exists
2. Ensure rows are not empty
3. Verify the file structure matches the expected format
4. Check server logs for specific parsing errors

### Issue: URL Changed

FRC Kenya may update the download URL when publishing new lists.

**Solution**:

1. Check latest TFS notice for new URL
2. Download the file manually
3. Upload via `/frc-kenya/upload` endpoint
4. Contact FRC Kenya if URL is unclear: info@frc.go.ke

## Database Storage

FRC Kenya entities are stored in the `sanctions_lists` table with:

- `source`: "FRC_Kenya"
- `list_type`: "Domestic TFS Kenya"
- `entity_type`: "Individual", "Entity", or "Unknown"
- `entity_number`: Auto-generated (FRC-KE-0001, FRC-KE-0002, etc.)

### Query FRC Kenya Entities

```sql
SELECT
  entity_number,
  full_name,
  entity_type,
  nationality,
  date_of_birth,
  designation_date,
  remarks
FROM sanctions_lists
WHERE source = 'FRC_Kenya'
  AND is_active = true
ORDER BY list_updated_date DESC;
```

## Best Practices

1. **Regular Updates**: Run weekly updates via `POST /lists/update/frc-kenya`
2. **Monitor TFS Notices**: Subscribe to FRC Kenya mailing list for timely updates
3. **Manual Verification**: For high-risk matches, verify against official FRC Kenya notices
4. **Backup Lists**: Keep copies of downloaded lists for compliance records
5. **Alert on Matches**: Configure alerts when FRC Kenya matches are found
6. **Document Matches**: Record all FRC Kenya matches in screening history
7. **Compliance**: Ensure compliance with POCAMLA 2009 and related regulations

## Legal Considerations

- **POCAMLA 2009**: Proceeds of Crime and Anti-Money Laundering Act
- **UNSCR 1373**: UN Security Council Resolution on counter-terrorism
- **Asset Freezing**: FRC Kenya designations require immediate asset freezing
- **Reporting**: Reporting institutions must report matches to FRC Kenya
- **Penalties**: Non-compliance may result in penalties under POCAMLA

## Integration with Other Lists

FRC Kenya works alongside:

- **OFAC SDN**: US Treasury sanctions
- **UN Consolidated**: UN Security Council sanctions
- **EU Sanctions**: European Union sanctions
- **UK Consolidated**: UK HM Treasury sanctions
- **World Bank**: Debarred entities
- **PEP Lists**: Politically Exposed Persons

All lists are checked together during screening operations for comprehensive coverage.

## API Summary

| Endpoint                  | Method | Description                          |
| ------------------------- | ------ | ------------------------------------ |
| `/lists/update/frc-kenya` | POST   | Update FRC Kenya list automatically  |
| `/frc-kenya/upload`       | POST   | Upload FRC Kenya list manually       |
| `/frc-kenya`              | GET    | List/search FRC Kenya entities       |
| `/frc-kenya/stats`        | GET    | Get FRC Kenya statistics             |
| `/lists/update/all`       | POST   | Update all lists including FRC Kenya |
| `/lists/check-updates`    | GET    | Check if FRC Kenya needs updating    |
| `/screen`                 | POST   | Screen names (includes FRC Kenya)    |

## Support and Resources

- **FRC Kenya Website**: https://www.frc.go.ke/
- **TFS Page**: https://www.frc.go.ke/targeted-financial-sanctions/
- **Email**: info@frc.go.ke
- **Phone**: +254 709 858000
- **Address**: Old Mutual Tower, 13th Floor, Upper Hill Road, Nairobi, Kenya

For technical issues with the integration, check the application logs and refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
