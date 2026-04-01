# Smart Update Scheduling Guide

## Overview

The sanctions screening system now includes **intelligent update scheduling** that automatically determines when lists need updating based on:

1. **Time since last update** - Tracks when each list was last successfully updated
2. **Recommended intervals** - Different frequencies for each source
3. **Remote file modifications** - Checks if source files have changed (when possible)
4. **Minimum intervals** - Prevents excessive updates

## Update Frequencies

### Configured Intervals

| Source   | Interval           | Frequency | Typical Changes   |
| -------- | ------------------ | --------- | ----------------- |
| **OFAC** | 24 hours           | Daily     | 2-5 updates/week  |
| **UN**   | 168 hours (7 days) | Weekly    | Every 2-4 weeks   |
| **EU**   | 168 hours (7 days) | Weekly    | 1-3 updates/month |
| **UK**   | 168 hours (7 days) | Weekly    | 1-2 updates/month |

### Minimum Interval

- **6 hours** - Prevents any list from being updated more than once every 6 hours

## API Endpoints

### 1. Check Which Lists Need Updating

```bash
GET /lists/check-updates
```

**Response:**

```json
{
  "check_time": "2026-03-13T10:30:00",
  "sources": {
    "OFAC": {
      "should_update": true,
      "reason": "Scheduled update due (26.5h since last, interval: 24h)",
      "last_update": "2026-03-12T08:00:00",
      "hours_since_update": 26.5
    },
    "UN": {
      "should_update": false,
      "reason": "Update not due yet (156.2h remaining)",
      "last_update": "2026-03-11T22:00:00",
      "hours_since_update": 12.5,
      "hours_until_due": 155.5
    },
    "EU": {
      "should_update": true,
      "reason": "Remote list has been modified",
      "last_update": "2026-03-06T14:00:00",
      "hours_since_update": 164.5
    },
    "UK": {
      "should_update": true,
      "reason": "Scheduled update due (169.3h since last, interval: 168h)",
      "last_update": "2026-03-06T13:00:00",
      "hours_since_update": 169.3
    }
  },
  "summary": {
    "needs_update": ["OFAC", "EU", "UK"],
    "up_to_date": ["UN"]
  }
}
```

### 2. View Update Schedule Configuration

```bash
GET /lists/schedule
```

**Response:**

```json
{
  "schedule": {
    "OFAC": {
      "update_interval_hours": 24,
      "min_interval_hours": 6,
      "last_update": {
        "source": "OFAC",
        "list_type": "SDN",
        "status": "Success",
        "started": "2026-03-12T08:00:00",
        "completed": "2026-03-12T08:03:45",
        "records_added": 12,
        "records_updated": 18706
      },
      "should_update": true,
      "reason": "Scheduled update due"
    }
  },
  "recommendations": {
    "OFAC": "Daily (highly dynamic, 2-5 updates/week)",
    "UN": "Weekly (changes every 2-4 weeks)",
    "EU": "Weekly (1-3 updates/month)",
    "UK": "Weekly (1-2 updates/month)"
  }
}
```

### 3. Update with Smart Scheduling (Default)

```bash
POST /lists/update/ofac
POST /lists/update/un
POST /lists/update/eu
POST /lists/update/uk
POST /lists/update/all
```

**Behavior:**

- Checks if update is needed before downloading
- Skips update if not due yet
- Logs skip reason

**Example Response (when skipped):**

```json
{
  "message": "OFAC list update started in background",
  "source": "OFAC",
  "list_type": "SDN",
  "forced": false
}
```

**Console Output (when skipped):**

```
INFO:__main__:Skipping OFAC update: Updated 2.3 hours ago (min 6h)
```

### 4. Force Update (Override Schedule)

```bash
POST /lists/update/ofac?force=true
POST /lists/update/un?force=true
POST /lists/update/all?force=true
```

**Parameters:**

- `force=true` - Skip all schedule checks and update immediately

**Response:**

```json
{
  "message": "OFAC list update started in background",
  "source": "OFAC",
  "list_type": "SDN",
  "forced": true
}
```

## Usage Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Check which lists need updating
response = requests.get(f"{BASE_URL}/lists/check-updates")
check = response.json()

print(f"Lists needing update: {check['summary']['needs_update']}")

# Update only lists that need it
if "OFAC" in check['summary']['needs_update']:
    requests.post(f"{BASE_URL}/lists/update/ofac")
    print("OFAC update triggered")

if "UK" in check['summary']['needs_update']:
    requests.post(f"{BASE_URL}/lists/update/uk")
    print("UK update triggered")

# Force update all lists
response = requests.post(f"{BASE_URL}/lists/update/all?force=true")
print(response.json())

# View scheduled intervals
response = requests.get(f"{BASE_URL}/lists/schedule")
schedule = response.json()
for source, info in schedule['schedule'].items():
    print(f"{source}: Update every {info['update_interval_hours']} hours")
```

### cURL

```bash
# Check update status
curl http://localhost:8000/lists/check-updates

# Smart update (respects schedule)
curl -X POST http://localhost:8000/lists/update/all

# Force update (ignores schedule)
curl -X POST "http://localhost:8000/lists/update/all?force=true"

# View schedule configuration
curl http://localhost:8000/lists/schedule
```

### Automated Script

```bash
#!/bin/bash
# Daily cron job that only updates when needed

# Check which lists need updating
NEEDS_UPDATE=$(curl -s http://localhost:8000/lists/check-updates | jq -r '.summary.needs_update[]')

# Update only those that need it
for source in $NEEDS_UPDATE; do
    echo "Updating $source..."
    curl -X POST http://localhost:8000/lists/update/$(echo $source | tr '[:upper:]' '[:lower:]')
done

echo "Updates completed"
```

## How It Works

### 1. Schedule Check

When an update is requested (without `force=true`):

```python
scheduler = UpdateScheduler(db)
check = scheduler.should_update("OFAC", force=False)

if not check["should_update"]:
    logger.info(f"Skipping OFAC update: {check['reason']}")
    return {"skipped": True, "reason": check["reason"]}

# Proceed with update...
```

### 2. Decision Logic

The scheduler checks (in order):

1. **Force flag** - If `force=true`, update immediately
2. **Never updated** - If no successful update exists, update now
3. **Minimum interval** - If updated within 6 hours, skip
4. **Recommended interval** - If interval has passed, update
5. **Remote modification** - If source file changed, update
6. **Otherwise** - Skip and report time until next update

### 3. Remote Modification Check

For sources that support it (OFAC, UN, UK), the system checks HTTP headers:

```python
response = requests.head(url, timeout=10)
last_modified = response.headers.get('Last-Modified')

if last_modified > last_update_time:
    return True  # Update needed
```

## Benefits

### 1. **Cost Savings**

- Reduces unnecessary API calls and bandwidth
- Minimizes database operations
- Saves processing time

### 2. **Performance**

- Prevents duplicate updates running simultaneously
- Reduces server load during peak times
- Improves API response times

### 3. **Reliability**

- Avoids rate limiting from source websites
- Prevents database locks from concurrent updates
- Better error recovery

### 4. **Transparency**

- Clear logging of why updates are/aren't running
- Audit trail in database
- Easy monitoring and troubleshooting

## Configuration

### Customizing Update Intervals

Edit `update_scheduler.py`:

```python
UPDATE_INTERVALS = {
    "OFAC": 12,      # Every 12 hours (more frequent)
    "UN": 336,       # Every 2 weeks (less frequent)
    "EU": 168,       # Weekly (unchanged)
    "UK": 84,        # Twice weekly
}
```

### Adjusting Minimum Interval

```python
MIN_UPDATE_INTERVAL = 3  # Allow updates every 3 hours
```

## Monitoring

### Check Last Update Times

```sql
SELECT
    source,
    status,
    update_started,
    update_completed,
    records_added,
    records_updated
FROM list_update_logs
ORDER BY update_started DESC
LIMIT 20;
```

### View Update History

```bash
# Get recent update logs
curl http://localhost:8000/lists/status
```

### Monitor Skipped Updates

Check application logs:

```
INFO:__main__:Skipping OFAC update: Updated 2.3 hours ago (min 6h)
INFO:__main__:Skipping UN update: Update not due yet (143.2h remaining)
INFO:__main__:Starting UK list update: Scheduled update due (169.5h since last)
```

## Best Practices

### 1. Daily Automated Updates

```bash
# Crontab: Run daily at 2 AM
0 2 * * * curl -X POST http://localhost:8000/lists/update/all
```

The smart scheduler will determine which lists actually need updating.

### 2. Force Updates After Manual Changes

If you manually modify the database, force an update:

```bash
curl -X POST "http://localhost:8000/lists/update/ofac?force=true"
```

### 3. Check Before Critical Operations

Before important screening:

```python
# Ensure lists are current
check = requests.get(f"{BASE_URL}/lists/check-updates").json()
if check['summary']['needs_update']:
    print("Warning: Some lists may be outdated")
    # Optionally trigger update
```

### 4. Monitor Update Failures

Check for failed updates regularly:

```sql
SELECT * FROM list_update_logs
WHERE status = 'Failed'
ORDER BY update_started DESC;
```

## Troubleshooting

### Updates Always Skipped

Check minimum interval:

```python
# In update_scheduler.py
MIN_UPDATE_INTERVAL = 6  # Must be at least this many hours
```

### Updates Never Run

Check recommended intervals:

```python
# Ensure reasonable intervals
UPDATE_INTERVALS = {
    "OFAC": 24,  # Not 240000!
}
```

### Remote Check Not Working

Some servers don't provide `Last-Modified` headers. Fallback to time-based scheduling.

### Force Updates Not Working

Ensure parameter is passed correctly:

```bash
curl -X POST "http://localhost:8000/lists/update/ofac?force=true"
# Not: force=1 or force=True
```

## Migration from Old System

If upgrading from non-scheduled updates:

1. Existing list data is preserved
2. First run will see "Never updated before"
3. All lists will update on first scheduled run
4. Subsequent runs will follow schedule

No database migration needed - uses existing `list_update_logs` table.
