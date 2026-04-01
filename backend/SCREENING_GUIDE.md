# Screening API Guide

## Overview

The screening service searches **BOTH sanctions lists AND PEP lists** in a single API call using fuzzy matching (80% threshold by default).

## What Lists Are Searched?

### ✅ Sanctions Lists (when `include_sanctions: true`)

- **OFAC SDN** (Office of Foreign Assets Control - Specially Designated Nationals)
- **UN Consolidated** (United Nations Consolidated Sanctions List)
- **EU Sanctions** (European Union - if downloaded)
- **UK Sanctions** (United Kingdom - if downloaded)

### ✅ PEP Lists (when `include_pep: true`)

- **Kenya PEPs** (Politically Exposed Persons)
- Any other country PEP lists you upload via the `/pep/upload` endpoint

## Mandatory Parameters

### For Single Name Search (`POST /screen`)

**Only ONE parameter is mandatory:**

```json
{
  "name": "John Doe" // ✅ REQUIRED - The name to search
}
```

**All other parameters are OPTIONAL:**

```json
{
  "name": "John Doe", // ✅ REQUIRED
  "entity_type": "Individual", // ❌ Optional (Individual, Entity, Vessel)
  "country": "Kenya", // ❌ Optional (filters results by country)
  "date_of_birth": "1980-01-15", // ❌ Optional (additional matching)
  "client_reference": "REF-123", // ❌ Optional (your internal reference)
  "include_pep": true, // ❌ Optional (default: true)
  "include_sanctions": true // ❌ Optional (default: true)
}
```

### For Batch Search (`POST /screen/batch`)

**Only ONE parameter is mandatory:**

```json
{
  "names": ["John Doe", "Jane Smith"] // ✅ REQUIRED - Array of names
}
```

## Minimal API Examples

### 1. Simplest Search (Name Only)

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{"name": "SWALEH S ABUBAKAR"}'
```

### 2. Search with Country Filter

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SWALEH S ABUBAKAR",
    "country": "Kenya"
  }'
```

### 3. Search Only PEPs (Skip Sanctions)

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SWALEH S ABUBAKAR",
    "include_sanctions": false,
    "include_pep": true
  }'
```

### 4. Search Only Sanctions (Skip PEPs)

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Abdul Rahman",
    "include_sanctions": true,
    "include_pep": false
  }'
```

### 5. Batch Search (Multiple Names)

```bash
curl -X POST "http://localhost:8000/screen/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "names": [
      "SWALEH S ABUBAKAR",
      "William Ruto",
      "Abdul Rahman"
    ]
  }'
```

## Response Structure

```json
{
  "query_name": "SWALEH S ABUBAKAR",
  "query_type": null,
  "sanctions_matches": [
    {
      "match_id": 123,
      "match_score": 95.5,
      "match_type": "Fuzzy",
      "matched_name": "Swaleh Abubakar",
      "full_name": "SWALEH ABUBAKAR",
      "source": "OFAC",
      "list_type": "SDN",
      "entity_type": "Individual",
      "country": "Somalia",
      "programs": ["SDGT"],
      "remarks": "Terrorist designation"
    }
  ],
  "pep_matches": [
    {
      "match_id": 456,
      "match_score": 100,
      "match_type": "Exact",
      "matched_name": "SWALEH S ABUBAKAR",
      "full_name": "SWALEH S ABUBAKAR",
      "source": "PEP_Kenya",
      "country": "Kenya",
      "position": "Member of the National Assembly",
      "pep_type": "Direct",
      "status": "Active",
      "risk_level": "Medium"
    }
  ],
  "near_misses": [
    {
      "match_score": 78.2,
      "matched_name": "Swaleh Abdullahi",
      "comment": "Close match below 80% threshold"
    }
  ],
  "total_matches": 2,
  "highest_score": 100,
  "threshold_used": 80,
  "total_records_checked": 1523,
  "screening_date": "2026-03-13T10:30:00"
}
```

## Response Fields Explained

- **sanctions_matches[]**: Matches from OFAC, UN, EU, UK lists
- **pep_matches[]**: Matches from PEP lists (all countries)
- **near_misses[]**: Matches scoring 70-79% (helpful for debugging)
- **total_matches**: Count of matches >= 80%
- **highest_score**: Best match score found
- **threshold_used**: Fuzzy match threshold applied (80%)
- **total_records_checked**: Total database records examined

## How Country Parameter Works

### ⚠️ Important: Country filtering behavior

- **If country is provided AND valid** (e.g., "Kenya", "Somalia"):
  - Only searches records from that country
  - Useful for narrow, targeted searches
- **If country is empty, null, or placeholder** (e.g., "string", "test"):
  - Searches **ALL countries**
  - Recommended for comprehensive screening

### Example: Don't Use Placeholder Values

❌ **BAD** (limits search unnecessarily):

```json
{
  "name": "John Doe",
  "country": "string",
  "entity_type": "string"
}
```

✅ **GOOD** (searches everywhere):

```json
{
  "name": "John Doe"
}
```

✅ **ALSO GOOD** (specific country):

```json
{
  "name": "John Doe",
  "country": "Kenya"
}
```

## Fuzzy Matching

The system uses **RapidFuzz** with **token_sort_ratio** algorithm:

- **100%**: Exact match
- **90-99%**: Very similar (typos, different order)
- **80-89%**: Similar (additional words, abbreviations)
- **70-79%**: Somewhat similar (reported as near-miss)
- **< 70%**: Not matched

### Examples:

- "William Ruto" vs "WILLIAM RUTO" = **100%** (exact, case-insensitive)
- "William Ruto" vs "Ruto William" = **100%** (token sort handles order)
- "William S Ruto" vs "William Ruto" = **~95%** (extra middle initial)
- "Bill Ruto" vs "William Ruto" = **~75%** (nickname - near miss)

## Best Practices

1. **Use minimal parameters** - Only specify what you need
2. **Don't use placeholder values** - Leave optional fields empty
3. **Check near_misses** - Helps tune your search strategy
4. **Use batch endpoint** - For multiple names (more efficient)
5. **Monitor total_records_checked** - Ensures lists are loaded

## Common Issues

### ❓ "I get 0 results but the name exists"

**Solutions:**

1. Run `python check_pep_data.py` to verify data is in database
2. Check `near_misses[]` in response - might be scoring 70-79%
3. Remove country filter to search globally
4. Check `total_records_checked` - should be > 0

### ❓ "What if I don't have sanctions lists yet?"

No problem! The system works with:

- **Just PEPs**: Set `"include_sanctions": false`
- **Just Sanctions**: Set `"include_pep": false`
- Download lists: Use `/lists/update/ofac` and `/lists/update/un` endpoints

### ❓ "Can I adjust the 80% threshold?"

Yes! The threshold is configurable in `config.py`:

```python
fuzzy_match_threshold: int = 80  # Change to 70, 75, 85, etc.
```

Then restart the server.
