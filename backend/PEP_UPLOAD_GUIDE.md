# PEP List Upload Guide

## Installation

First, install the required packages:

```bash
pip install pandas==2.2.0 openpyxl==3.1.2
```

Then restart your FastAPI server.

## Endpoint

**POST** `/pep/upload`

Upload a PEP list from an Excel (.xlsx) file.

## Parameters

- **file** (required): Excel file (.xlsx format)
- **country** (optional, default: "Kenya"): Country for the PEP list
- **source** (optional, default: "Excel Upload"): Source identifier
- **update_if_exists** (optional, default: true): Update existing PEPs or skip them

## Excel File Format

Your Excel file should have these columns:

### Required Columns:

- **NAME**: Full name of the PEP (e.g., "Aaron Cheruiyot")
- **ENTITY DESCRIPTION**: Position/role (e.g., "Member of the National Assembly")

### Optional Columns:

- **ENTITY SOURCE**: Source type (defaults to "PEP")
- **ORGANIZATION**: Organization name
- **POSITION_LEVEL**: Level of position (e.g., "National", "County")
- **RISK_LEVEL**: Risk assessment ("High", "Medium", "Low")
- **STATUS**: Current status ("Active", "Former")
- **PEP_TYPE**: Type of PEP ("Direct", "RCA", "Close Associate")
- **NATIONALITY**: Nationality
- **DATE_OF_BIRTH**: Date of birth
- **PLACE_OF_BIRTH**: Place of birth
- **NOTES**: Additional notes

### Example Excel Format:

| NAME            | ENTITY SOURCE | ENTITY DESCRIPTION                    |
| --------------- | ------------- | ------------------------------------- |
| Aaron Cheruiyot | PEP           | Member of the National Assembly       |
| Ababu Namwamba  | PEP           | Principal Secretary - Foreign Affairs |

## Usage Examples

### Using cURL:

```bash
curl -X POST "http://localhost:8000/pep/upload?country=Kenya&update_if_exists=true" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@pep_list.xlsx"
```

### Using Python requests:

```python
import requests

url = "http://localhost:8000/pep/upload"
params = {
    "country": "Kenya",
    "source": "Official Government List",
    "update_if_exists": True
}

with open("pep_list.xlsx", "rb") as f:
    files = {"file": ("pep_list.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = requests.post(url, params=params, files=files)

print(response.json())
```

### Using the Swagger UI:

1. Navigate to http://localhost:8000/docs
2. Find the `/pep/upload` endpoint
3. Click "Try it out"
4. Upload your Excel file
5. Set parameters (country, source, update_if_exists)
6. Click "Execute"

## Response

The endpoint returns a response with:

```json
{
  "total_records": 100,
  "added": 85,
  "updated": 10,
  "failed": 5,
  "errors": ["Row 23: Invalid data format", "Row 45: Missing required field"],
  "message": "Successfully processed 95 PEPs (85 new, 10 updated, 5 failed)"
}
```

## Notes

- Empty rows (rows where NAME is blank) are automatically skipped
- If `update_if_exists=true`, existing PEPs (matched by country + full_name) will be updated
- If `update_if_exists=false`, existing PEPs will be skipped
- The endpoint returns up to 10 error messages for failed rows
- All processing is done in a single transaction for data integrity
