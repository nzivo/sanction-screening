# Entity Type Guide for Sanctions Screening

## Understanding Entity Types in OFAC/UN Lists

Sanctions lists classify entries by **entity type**. This is crucial for accurate screening.

## Valid Entity Types

### For OFAC SDN List:

- **`individual`** - Natural persons (people)
- **`entity`** - Organizations, companies, groups
- **`vessel`** - Ships, boats
- **`aircraft`** - Planes, helicopters

### For UN Consolidated List:

- **`individual`** - Natural persons
- **`entity`** - Organizations, groups

## How to Use Entity Type Parameter

### ❌ DON'T Use Placeholder Values

**This won't work:**

```json
{
  "name": "ADEM YILMAZ",
  "entity_type": "string" // ❌ Placeholder - will be ignored
}
```

### ✅ DO Use Valid Values or Leave Empty

**Option 1: Search ALL entity types (Recommended for first search)**

```json
{
  "name": "ADEM YILMAZ"
  // No entity_type - searches individuals, entities, vessels
}
```

**Option 2: Search ONLY individuals**

```json
{
  "name": "ADEM YILMAZ",
  "entity_type": "individual" // Case-insensitive
}
```

**Option 3: Search ONLY entities/organizations**

```json
{
  "name": "ABC Company",
  "entity_type": "entity"
}
```

**Option 4: Search ONLY vessels**

```json
{
  "name": "Ship Name",
  "entity_type": "vessel"
}
```

## Complete Examples

### Example 1: Person (Natural Person)

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ADEM YILMAZ",
    "entity_type": "individual"
  }'
```

### Example 2: Company/Organization

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "entity_type": "entity"
  }'
```

### Example 3: Unknown Type - Search All

```bash
curl -X POST "http://localhost:8000/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Unknown Name"
  }'
```

## How Entity Type Affects Results

### Without entity_type (searches all):

- ✅ Searches individuals
- ✅ Searches entities
- ✅ Searches vessels
- ✅ Searches aircraft
- **Result:** Maximum coverage, may return more matches

### With entity_type="individual":

- ✅ Searches only individuals
- ❌ Skips entities
- ❌ Skips vessels
- ❌ Skips aircraft
- **Result:** Faster, more targeted

## Response Shows Entity Type

The response includes the entity type of each match:

```json
{
  "sanctions_matches": [
    {
      "match_score": 100,
      "full_name": "ADEM YILMAZ",
      "entity_type": "individual", // ← Shows what type it is
      "source": "OFAC",
      "country": "Turkey"
    }
  ],
  "query_type": "individual" // ← Shows what you searched for
}
```

## Common Issues

### Issue: "I know the name is in OFAC but get 0 results"

**Solutions:**

1. **Don't specify entity_type first** - Search all types:

   ```json
   {
     "name": "ADEM YILMAZ"
   }
   ```

2. **Check if data is downloaded:**

   ```bash
   python check_ofac_data.py
   ```

3. **Download OFAC list if missing:**

   ```bash
   curl -X POST http://localhost:8000/lists/update/ofac
   ```

4. **Check server logs** - Look for:
   ```
   INFO:screening_service:Filtering sanctions by entity_type: individual
   INFO:screening_service:Screening against 12345 sanctions entries
   ```

### Issue: "Wrong entity_type specified"

If you're not sure whether someone is an "individual" or "entity":

1. **First search:** Leave `entity_type` empty (searches all)
2. **Check response:** See what `entity_type` the match has
3. **Refine:** Use that entity_type for future searches

## Case Sensitivity

Entity type matching is **case-insensitive**:

- `"individual"` ✅
- `"Individual"` ✅
- `"INDIVIDUAL"` ✅
- All work the same!

## Validation

The system automatically:

- ✅ Ignores placeholder values: "string", "test", "example"
- ✅ Converts to case-insensitive matching
- ✅ Logs when filtering is applied
- ✅ Shows "All Types" in response if no valid entity_type provided

## Best Practice Workflow

1. **Initial Search - Cast wide net:**

   ```json
   {
     "name": "ADEM YILMAZ"
   }
   ```

2. **Review Results** - Check `entity_type` in matches

3. **Refined Search - If needed:**
   ```json
   {
     "name": "ADEM YILMAZ",
     "entity_type": "individual",
     "country": "Turkey"
   }
   ```

## Quick Reference

| Parameter           | Required | Valid Values                                          | Default Behavior       |
| ------------------- | -------- | ----------------------------------------------------- | ---------------------- |
| `name`              | ✅ Yes   | Any string                                            | N/A                    |
| `entity_type`       | ❌ No    | `individual`, `entity`, `vessel`, `aircraft` or empty | Searches all types     |
| `country`           | ❌ No    | Country name or empty                                 | Searches all countries |
| `include_sanctions` | ❌ No    | `true`/`false`                                        | `true`                 |
| `include_pep`       | ❌ No    | `true`/`false`                                        | `true`                 |

## Testing Your Setup

Run this to verify entity types in your database:

```bash
python check_ofac_data.py
```

This shows:

- Total records by source (OFAC, UN)
- Entity type distribution
- Sample records with their entity types
- Fuzzy match scores for test names
