# Service Type Update Summary

**Date:** 2025-10-22
**Purpose:** Convert service_type names to simplified versions

---

## 🔄 CONVERSION MAPPING

```
EasyCredit   →  Fee
MBFG         →  Free
ungsanluong  →  Quota
```

---

## ✅ FILES UPDATED

### 1. Data File Created
```
/data/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv
```
- **Source:** recommendations_final_filtered.csv
- **Size:** 32 MB
- **Rows:** 214,504
- **Changes:** service_type column converted

**Distribution:**
- Fee: 137,644 (64.2%)
- Free: 46,582 (21.7%)
- Quota: 30,278 (14.1%)

---

### 2. Scripts Updated

#### A. sync_to_postgresql.py ✅
**File:** `/data/ut360/scripts/utils/sync_to_postgresql.py`

**Changes:**
```python
# Line 198: Changed input file
rec_file = OUTPUT_DIR / "recommendations" / "recommendations_final_filtered_typeupdate.csv"

# Line 90: Updated CHECK constraint
CONSTRAINT chk_service_type CHECK (service_type IN ('Fee', 'Free', 'Quota'))
```

**Impact:**
- PostgreSQL now accepts: Fee, Free, Quota
- Rejects: EasyCredit, MBFG, ungsanluong

---

#### B. sync_to_redis.py ✅
**File:** `/data/ut360/scripts/utils/sync_to_redis.py`

**Changes:**
```python
# Line 76: Changed input file (load_recommendations)
rec_file = OUTPUT_DIR / "recommendations" / "recommendations_final_filtered_typeupdate.csv"

# Line 270: Changed input file (create_indexes)
rec_file = OUTPUT_DIR / "recommendations" / "recommendations_final_filtered_typeupdate.csv"

# Line 334: Changed input file (create_metadata)
rec_file = OUTPUT_DIR / "recommendations" / "recommendations_final_filtered_typeupdate.csv"

# Lines 349-351: Updated metadata field names
'total_fee': str(len(df[df['service_type'] == 'Fee'])),
'total_free': str(len(df[df['service_type'] == 'Free'])),
'total_quota': str(len(df[df['service_type'] == 'Quota'])),
```

**Impact:**
- Redis indexes now use: Fee, Free, Quota
- Metadata stats renamed: total_fee, total_free, total_quota

**Redis Keys Affected:**
```
ut360:idx:service:Fee      (was ut360:idx:service:EasyCredit)
ut360:idx:service:Free     (was ut360:idx:service:MBFG)
ut360:idx:service:Quota    (was ut360:idx:service:ungsanluong)
```

---

#### C. Web Backend (FastAPI) ✅
**File:** `/data/web-ut360/backend/app.py`

**Changes:**
```python
# Multiple locations (lines 406, 950, 1000, 1074)
# Changed all references from:
recommendations_final_filtered.csv
# To:
recommendations_final_filtered_typeupdate.csv
```

**Impact:**
- Web API now reads from typeupdate file
- Subscribers list will show: Fee, Free, Quota
- Filters will work with new service_type values

---

### 3. Conversion Script Created
```
/data/ut360/scripts/utils/convert_service_type.py
```

**Purpose:** Convert service_type and create typeupdate file

**Usage:**
```bash
python3 /data/ut360/scripts/utils/convert_service_type.py
```

---

## 📊 REDIS DATA STRUCTURE CHANGES

### Before:
```redis
# Recommendation hash
HGET ut360:rec:++/hZFPrCDRre55vsZqqxQ== service_type
→ "EasyCredit"

# Index keys
ZCARD ut360:idx:service:EasyCredit  → 137644
ZCARD ut360:idx:service:MBFG        → 46582
ZCARD ut360:idx:service:ungsanluong → 30278

# Metadata
HGET ut360:meta:stats total_easycredit → "137644"
HGET ut360:meta:stats total_mbfg       → "46582"
HGET ut360:meta:stats total_ungsanluong → "30278"
```

### After:
```redis
# Recommendation hash
HGET ut360:rec:++/hZFPrCDRre55vsZqqxQ== service_type
→ "Fee"

# Index keys
ZCARD ut360:idx:service:Fee   → 137644
ZCARD ut360:idx:service:Free  → 46582
ZCARD ut360:idx:service:Quota → 30278

# Metadata
HGET ut360:meta:stats total_fee   → "137644"
HGET ut360:meta:stats total_free  → "46582"
HGET ut360:meta:stats total_quota → "30278"
```

---

## 📋 POSTGRESQL SCHEMA CHANGES

### Table: recommendations

**Column:** `service_type VARCHAR(50)`

**Before Constraint:**
```sql
CONSTRAINT chk_service_type CHECK (service_type IN ('EasyCredit', 'MBFG', 'ungsanluong'))
```

**After Constraint:**
```sql
CONSTRAINT chk_service_type CHECK (service_type IN ('Fee', 'Free', 'Quota'))
```

**Sample Data:**
```sql
SELECT service_type, COUNT(*) FROM recommendations GROUP BY service_type;

service_type | count
-------------|--------
Fee          | 137644
Free         |  46582
Quota        |  30278
```

---

## 🌐 WEB APPLICATION CHANGES

### Frontend Display
**Before:**
- Service badges showed: "EasyCredit", "MBFG", "ungsanluong"

**After:**
- Service badges will show: "Fee", "Free", "Quota"

### API Responses
**Before:**
```json
{
  "isdn": "++/hZFPrCDRre55vsZqqxQ==",
  "service_type": "EasyCredit",
  "advance_amount": 25000
}
```

**After:**
```json
{
  "isdn": "++/hZFPrCDRre55vsZqqxQ==",
  "service_type": "Fee",
  "advance_amount": 25000
}
```

---

## 🔍 QUERY EXAMPLES

### Redis Queries

#### Get top 100 Fee service by priority:
```bash
# OLD:
redis-cli ZREVRANGE ut360:idx:service:EasyCredit 0 99 WITHSCORES

# NEW:
redis-cli ZREVRANGE ut360:idx:service:Fee 0 99 WITHSCORES
```

#### Get recommendation:
```python
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

rec = r.hgetall('ut360:rec:++/hZFPrCDRre55vsZqqxQ==')
print(rec['service_type'])  # Output: "Fee" (was "EasyCredit")
```

---

### PostgreSQL Queries

#### Filter by service type:
```sql
-- OLD:
SELECT * FROM recommendations WHERE service_type = 'EasyCredit';

-- NEW:
SELECT * FROM recommendations WHERE service_type = 'Fee';
```

#### Service distribution:
```sql
SELECT service_type, COUNT(*) as count
FROM recommendations
GROUP BY service_type;

-- Output:
-- Fee    137644
-- Free    46582
-- Quota   30278
```

---

## 🚀 DEPLOYMENT STEPS

### Step 1: File Already Created ✅
```bash
# File exists:
ls -lh /data/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv
# Output: 32M
```

### Step 2: Restart Web Application
```bash
cd /data/web-ut360
./stop.sh
./start.sh
```

**Expected:** Web UI will now show Fee/Free/Quota

### Step 3: Sync to PostgreSQL (When Ready)
```bash
python3 /data/ut360/scripts/utils/sync_to_postgresql.py
```

**Expected:**
- Creates tables with new CHECK constraint
- Loads 214,504 recommendations with Fee/Free/Quota

### Step 4: Sync to Redis (When Ready)
```bash
python3 /data/ut360/scripts/utils/sync_to_redis.py
```

**Expected:**
- Creates indexes: ut360:idx:service:Fee, Free, Quota
- Metadata uses: total_fee, total_free, total_quota

---

## ⚠️ MIGRATION NOTES

### Breaking Changes:
1. **Old Redis keys invalid:**
   - `ut360:idx:service:EasyCredit` → will not exist
   - Must use `ut360:idx:service:Fee`

2. **PostgreSQL constraint:**
   - Inserting 'EasyCredit' will fail
   - Must use 'Fee'

3. **API filters:**
   - `?service_type=EasyCredit` → will return 0 results
   - Must use `?service_type=Fee`

### Backward Compatibility:
❌ **Not backward compatible**
- Old code expecting EasyCredit/MBFG/ungsanluong will fail
- All systems must use new names: Fee/Free/Quota

---

## 📝 UPDATE CHECKLIST

- [x] Created conversion script
- [x] Generated typeupdate.csv file
- [x] Updated sync_to_postgresql.py
- [x] Updated sync_to_redis.py
- [x] Updated web backend (app.py)
- [ ] Restart web application
- [ ] Test web UI with new service_type
- [ ] Sync to PostgreSQL (optional)
- [ ] Sync to Redis (optional)
- [ ] Update documentation

---

## 🎯 BENEFITS

### Simplified Names:
- **Fee** - Clear indication of paid service (was EasyCredit)
- **Free** - Clear indication of free service (was MBFG)
- **Quota** - Clear indication of quota-based service (was ungsanluong)

### Consistency:
- Shorter, easier to type
- English names (no Vietnamese)
- Clear meaning at a glance

### API/UI:
- Cleaner display in frontend
- Easier to understand in API responses
- Better for international users

---

## 🔄 ROLLBACK (If Needed)

To rollback to old service_type names:

### Step 1: Revert scripts
```bash
# In sync_to_postgresql.py, sync_to_redis.py, app.py
# Change back to:
recommendations_final_filtered.csv
```

### Step 2: Revert PostgreSQL constraint
```sql
ALTER TABLE recommendations DROP CONSTRAINT chk_service_type;
ALTER TABLE recommendations ADD CONSTRAINT chk_service_type
  CHECK (service_type IN ('EasyCredit', 'MBFG', 'ungsanluong'));
```

### Step 3: Restart services
```bash
cd /data/web-ut360
./stop.sh
./start.sh
```

---

**Created By:** Claude AI
**Date:** 2025-10-22
**Status:** ✅ All files updated, ready for deployment
