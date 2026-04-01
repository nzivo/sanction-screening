# Troubleshooting Guide

## Background Tasks Not Running

### Issue: EU and UK lists not updating when using "Update All"

**Symptoms:**

- Only OFAC and UN lists update
- No errors visible in logs
- EU and UK tasks appear to be skipped

**Root Cause:**
Database session handling in background tasks. FastAPI's `Depends(get_db)` provides a session tied to the request lifecycle, which closes before background tasks execute.

**Solution (Applied):**
Each background task now creates its own database session:

```python
def update_uk_list_background():
    db = next(get_db())
    try:
        # ... task logic ...
    finally:
        db.close()
```

## EU Sanctions List Issues

### Issue: 403 Forbidden Error

**Symptoms:**

```
ERROR:list_downloaders:Error downloading EU list: 403 Client Error: Forbidden
```

**Root Cause:**
The EU sanctions list API has changed and now requires authentication/API token.

**Solutions:**

1. **Alternative URL (Already Implemented):**
   The downloader now tries alternative public endpoints automatically.

2. **Manual Configuration:**
   If both automated methods fail, you need to:
   - Visit https://www.sanctionsmap.eu/
   - Register for API access
   - Add your token to `config.py`:
     ```python
     eu_sanctions_url: str = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=YOUR_TOKEN_HERE"
     ```

3. **Manual Download:**
   - Download the XML file from https://www.sanctionsmap.eu/
   - Import manually via database

### Issue: EU List Always Fails

**Check:**

1. Network connectivity
2. Firewall settings (EU endpoints may be blocked)
3. Alternative sources:
   - OpenSanctions.org (provides aggregated EU data)
   - Direct EEAS downloads

## UK Sanctions List Issues

### Issue: CSV Parsing Errors

**Symptoms:**

```
ERROR:list_downloaders:Error parsing UK CSV
```

**Possible Causes:**

1. UK changed CSV format
2. Encoding issues (BOM, character sets)
3. URL changed

**Solutions:**

1. **Check Official Source:**
   Visit: https://www.gov.uk/government/publications/financial-sanctions-consolidated-list-of-targets

2. **Update URL:**
   If the CSV location changed, update in `list_downloaders.py`:

   ```python
   url = "NEW_URL_HERE"
   ```

3. **Alternative Formats:**
   UK also provides:
   - XLSX format
   - JSON API
   - ODS format

### Issue: UK List Returns Empty

**Check:**

- URL accessibility
- CSV format changed (check column names)
- Network/proxy issues

## General List Update Issues

### Issue: All Lists Fail to Update

**Check:**

1. **Database Connection:**

   ```python
   python -c "from database import engine; engine.connect()"
   ```

2. **Network Connectivity:**

   ```bash
   curl -I https://www.treasury.gov/ofac/downloads/sdn.xml
   curl -I https://scsanctions.un.org/resources/xml/en/consolidated.xml
   curl -I https://ofsistorage.blob.core.windows.net/publishlive/2022format/ConList.csv
   ```

3. **Disk Space:**
   Lists can be large (10,000+ entries each)

4. **Memory:**
   XML parsing requires sufficient RAM

### Issue: Updates Are Slow

**Expected Times:**

- OFAC SDN: 1-3 minutes (18,000+ entries)
- UN Consolidated: 30-60 seconds (1,000+ entries)
- EU Sanctions: 1-2 minutes (if accessible)
- UK Consolidated: 1-2 minutes (19,000+ entries)

**Optimization:**

- Run updates during off-peak hours
- Use individual endpoint updates instead of "update all"
- Consider caching/scheduled updates

## Viewing Logs

### Enable Detailed Logging

In `main.py`, update:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check Background Task Errors

All background tasks now log with `exc_info=True`, providing full stack traces:

```
logger.error(f"Error updating UK list: {str(e)}", exc_info=True)
```

### Monitoring Updates

Use the status endpoint:

```bash
curl http://localhost:8000/lists/status
```

Check the logs table:

```sql
SELECT * FROM list_update_logs
ORDER BY update_started DESC
LIMIT 10;
```

## Testing Individual Components

### Test Downloaders

```python
from database import get_db
from list_downloaders import UKDownloader

db = next(get_db())
downloader = UKDownloader(db)
entities = downloader.download_sanctions_list()
print(f"Downloaded {len(entities)} entities")
```

### Test Database Connection

```python
from database import engine, SessionLocal
from models import SanctionsList

db = SessionLocal()
count = db.query(SanctionsList).filter(
    SanctionsList.source == 'UK'
).count()
print(f"UK entries in database: {count}")
db.close()
```

### Test API Endpoints

```bash
# Test individual updates
curl -X POST http://localhost:8000/lists/update/ofac
curl -X POST http://localhost:8000/lists/update/un
curl -X POST http://localhost:8000/lists/update/eu
curl -X POST http://localhost:8000/lists/update/uk

# Wait a few minutes, then check status
curl http://localhost:8000/lists/status
```

## Common Error Messages

### "No module named 'pandas'"

```bash
pip install pandas
```

### "psycopg2.OperationalError: could not connect"

Check PostgreSQL is running and DATABASE_URL is correct in `.env`

### "requests.exceptions.Timeout"

Increase timeout in downloaders or check network

### "xml.etree.ElementTree.ParseError"

Source XML format changed - update parser

### "UnicodeDecodeError"

CSV encoding issue - check encoding in CSV parser

## Performance Tuning

### Database Indexes

Add indexes for common queries:

```sql
CREATE INDEX idx_sanctions_source ON sanctions_lists(source);
CREATE INDEX idx_sanctions_name ON sanctions_lists(full_name);
CREATE INDEX idx_sanctions_search ON sanctions_lists USING gin(to_tsvector('english', search_text));
```

### Batch Processing

For large updates, consider batch commits:

```python
BATCH_SIZE = 1000
for i in range(0, len(entities), BATCH_SIZE):
    batch = entities[i:i+BATCH_SIZE]
    # Process batch
    db.commit()
```

## Getting Help

1. Check logs in terminal where server is running
2. Use `/lists/status` endpoint to see last update times
3. Test individual downloaders in isolation
4. Check source websites for API changes
5. Review database for partial updates

## Useful SQL Queries

```sql
-- Check records by source
SELECT source, COUNT(*)
FROM sanctions_lists
GROUP BY source;

-- Recent updates
SELECT source, list_type, status, update_completed, records_added, records_updated
FROM list_update_logs
ORDER BY update_started DESC
LIMIT 20;

-- Failed updates
SELECT * FROM list_update_logs
WHERE status = 'Failed'
ORDER BY update_started DESC;
```
