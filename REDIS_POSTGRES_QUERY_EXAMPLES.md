# Redis & PostgreSQL Query Examples for UT360

**Date:** 2025-10-22
**Purpose:** Hướng dẫn chi tiết cách truy vấn data từ Redis và PostgreSQL

---

## Setup & Installation

### 1. Install Dependencies

```bash
# Python packages
pip install redis psycopg2-binary pandas numpy

# Redis (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis-server

# PostgreSQL (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. Create PostgreSQL Database

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE ut360;
CREATE USER ut360_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ut360 TO ut360_user;
\q
```

### 3. Run Sync Scripts

```bash
# Sync to PostgreSQL first (source of truth)
cd /data/ut360
python3 scripts/utils/sync_to_postgresql.py

# Then sync to Redis (cache layer)
python3 scripts/utils/sync_to_redis.py
```

---

## REDIS QUERY EXAMPLES

### Use Case 1: Get Recommendation by ISDN (Most Common)

#### Redis CLI:
```redis
# Get full recommendation
HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==

# Output:
# 1) "isdn"
# 2) "++/hZFPrCDRre55vsZqqxQ=="
# 3) "subscriber_type"
# 4) "PRE"
# 5) "service_type"
# 6) "EasyCredit"
# 7) "advance_amount"
# 8) "25000"
# ...

# Get specific field
HGET ut360:rec:++/hZFPrCDRre55vsZqqxQ== advance_amount
# Output: "25000"
```

#### Python:
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get full recommendation
isdn = "++/hZFPrCDRre55vsZqqxQ=="
rec = r.hgetall(f"ut360:rec:{isdn}")

print(f"ISDN: {rec.get('isdn')}")
print(f"Service: {rec.get('service_type')}")
print(f"Advance: {rec.get('advance_amount')} VND")
print(f"Revenue: {rec.get('revenue_per_advance')} VND")
print(f"Risk: {rec.get('bad_debt_risk')}")
print(f"Customer Value Score: {rec.get('customer_value_score')}")
```

**Performance:** ~2-5ms

---

### Use Case 2: Get 360 Profile for Customer360-VNS Modal

#### Python:
```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

isdn = "++/hZFPrCDRre55vsZqqxQ=="
profile = r.hgetall(f"ut360:profile:{isdn}")

# Parse JSON fields
basic = json.loads(profile.get('basic', '{}'))
arpu_stats = json.loads(profile.get('arpu_stats', '{}'))
revenue_breakdown = json.loads(profile.get('revenue_breakdown', '{}'))
topup_behavior = json.loads(profile.get('topup_behavior', '{}'))
risk_assessment = json.loads(profile.get('risk_assessment', '{}'))
kpi_scores = json.loads(profile.get('kpi_scores', '{}'))
monthly_arpu = json.loads(profile.get('monthly_arpu', '[]'))

# Display
print(f"=== Customer360-VNS ===")
print(f"ISDN: {basic.get('isdn')}")
print(f"Type: {basic.get('type')}")
print(f"Service: {basic.get('service')}")
print(f"Advance: {basic.get('advance'):,.0f} VND")
print(f"\nARPU Trend: {arpu_stats.get('trend')}")
print(f"ARPU Avg 6M: {arpu_stats.get('avg'):,.0f} VND")
print(f"Growth Rate: {arpu_stats.get('growth_rate'):.1f}%")
print(f"\nRisk: {risk_assessment.get('level')}")
print(f"Customer Value Score: {kpi_scores.get('customer_value')}/100")
print(f"Advance Readiness: {kpi_scores.get('advance_readiness')}/100")
print(f"\nMonthly ARPU: {len(monthly_arpu)} months")
```

**Performance:** ~5-10ms

---

### Use Case 3: Get Top 100 EasyCredit by Priority

#### Redis CLI:
```redis
# Get top 100 (highest priority first)
ZREVRANGE ut360:idx:service:EasyCredit 0 99 WITHSCORES

# Get count
ZCARD ut360:idx:service:EasyCredit
```

#### Python:
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get top 100 ISDNs with scores
top_isdns = r.zrevrange('ut360:idx:service:EasyCredit', 0, 99, withscores=True)

print(f"Top 100 EasyCredit Recommendations:")
for idx, (isdn, score) in enumerate(top_isdns, 1):
    # Get full recommendation
    rec = r.hgetall(f"ut360:rec:{isdn}")
    print(f"{idx}. {isdn[:20]}... | "
          f"Advance: {rec.get('advance_amount')} | "
          f"Priority: {score:.2f}")
```

**Performance:** ~20-50ms (including fetching details)

---

### Use Case 4: Get All LOW Risk Subscribers

#### Redis CLI:
```redis
# Get all LOW risk ISDNs
SMEMBERS ut360:idx:risk:LOW

# Get count
SCARD ut360:idx:risk:LOW

# Check if ISDN is in set
SISMEMBER ut360:idx:risk:LOW "++/hZFPrCDRre55vsZqqxQ=="
```

#### Python:
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get count of LOW risk
low_risk_count = r.scard('ut360:idx:risk:LOW')
print(f"Total LOW risk subscribers: {low_risk_count:,}")

# Check if specific ISDN is LOW risk
isdn = "++/hZFPrCDRre55vsZqqxQ=="
is_low_risk = r.sismember('ut360:idx:risk:LOW', isdn)
print(f"{isdn} is LOW risk: {is_low_risk}")

# Get first 100 LOW risk subscribers
low_risk_isdns = list(r.sscan_iter('ut360:idx:risk:LOW', count=100))
print(f"\nFirst 100 LOW risk subscribers:")
for isdn in low_risk_isdns[:100]:
    print(f"  {isdn}")
```

**Performance:** ~10-20ms

---

### Use Case 5: Get Subscribers in Cluster 1

#### Python:
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get all subscribers in cluster 1
cluster_isdns = list(r.smembers('ut360:idx:cluster:1'))
print(f"Cluster 1 has {len(cluster_isdns):,} subscribers")

# Get details for first 10
for isdn in cluster_isdns[:10]:
    rec = r.hgetall(f"ut360:rec:{isdn}")
    print(f"  {isdn[:20]}... | Service: {rec.get('service_type')} | "
          f"Advance: {rec.get('advance_amount')}")
```

---

### Use Case 6: Get Metadata/Statistics

#### Redis CLI:
```redis
HGETALL ut360:meta:stats
```

#### Python:
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

stats = r.hgetall('ut360:meta:stats')

print("=== UT360 Statistics ===")
print(f"Total Subscribers: {stats.get('total_subscribers'):,}")
print(f"EasyCredit: {stats.get('total_easycredit'):,}")
print(f"MBFG: {stats.get('total_mbfg'):,}")
print(f"ungsanluong: {stats.get('total_ungsanluong'):,}")
print(f"LOW Risk: {stats.get('total_low_risk'):,}")
print(f"MEDIUM Risk: {stats.get('total_medium_risk'):,}")
print(f"Avg Advance: {float(stats.get('avg_advance_amount', 0)):,.0f} VND")
print(f"Total Revenue Potential: {float(stats.get('total_revenue_potential', 0)):,.0f} VND")
print(f"Last Updated: {stats.get('last_updated')}")
```

---

### Use Case 7: Bulk Lookup (1000 ISDNs)

#### Python with Pipeline:
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# List of ISDNs to lookup
isdns = ["isdn1", "isdn2", "isdn3", ...]  # 1000 ISDNs

# Use pipeline for batch operations
pipe = r.pipeline()

for isdn in isdns:
    pipe.hgetall(f"ut360:rec:{isdn}")

# Execute all at once
results = pipe.execute()

# Process results
for isdn, rec in zip(isdns, results):
    if rec:
        print(f"{isdn}: {rec.get('service_type')} - {rec.get('advance_amount')} VND")
```

**Performance:** ~100-200ms for 1000 ISDNs (vs ~2-5 seconds if done sequentially)

---

## POSTGRESQL QUERY EXAMPLES

### Use Case 1: Get Recommendation by ISDN

```sql
SELECT * FROM recommendations
WHERE isdn = '++/hZFPrCDRre55vsZqqxQ==';
```

#### Python:
```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='ut360',
    user='ut360_user',
    password='your_password'
)

cursor = conn.cursor()

isdn = "++/hZFPrCDRre55vsZqqxQ=="
cursor.execute("SELECT * FROM recommendations WHERE isdn = %s", (isdn,))

row = cursor.fetchone()
if row:
    print(f"Service: {row[3]}")
    print(f"Advance: {row[4]}")
    print(f"Revenue: {row[5]}")

conn.close()
```

**Performance:** ~5-10ms (with index)

---

### Use Case 2: Get 360 Profile with Monthly ARPU

```sql
SELECT
    p.*,
    json_agg(
        json_build_object(
            'month', m.data_month,
            'arpu_call', m.arpu_call,
            'arpu_sms', m.arpu_sms,
            'arpu_data', m.arpu_data,
            'arpu_total', m.arpu_total
        ) ORDER BY m.data_month
    ) as monthly_arpu
FROM subscriber_360_profiles p
LEFT JOIN subscriber_monthly_arpu m ON p.isdn = m.isdn
WHERE p.isdn = '++/hZFPrCDRre55vsZqqxQ=='
GROUP BY p.id;
```

**Performance:** ~20-50ms

---

### Use Case 3: Get Top 100 by Priority for EasyCredit

```sql
SELECT isdn, subscriber_type, advance_amount, revenue_per_advance,
       customer_value_score, advance_readiness_score, priority_score
FROM recommendations
WHERE service_type = 'EasyCredit'
ORDER BY priority_score DESC
LIMIT 100;
```

---

### Use Case 4: Analytics - Revenue by Service and Risk

```sql
SELECT
    service_type,
    bad_debt_risk,
    COUNT(*) as subscriber_count,
    SUM(advance_amount) as total_advance,
    SUM(revenue_per_advance) as total_revenue,
    AVG(customer_value_score) as avg_customer_value,
    AVG(advance_readiness_score) as avg_readiness
FROM recommendations
GROUP BY service_type, bad_debt_risk
ORDER BY service_type, bad_debt_risk;
```

**Output:**
```
service_type  | bad_debt_risk | subscriber_count | total_advance | total_revenue | avg_value | avg_readiness
--------------+---------------+------------------+---------------+---------------+-----------+--------------
EasyCredit    | LOW           | 120000           | 3000000000    | 900000000     | 65.5      | 85.2
EasyCredit    | MEDIUM        | 22000            | 550000000     | 165000000     | 55.3      | 70.1
MBFG          | LOW           | 40000            | 0             | 0             | 60.2      | 80.5
MBFG          | MEDIUM        | 5000             | 0             | 0             | 50.1      | 65.3
...
```

---

### Use Case 5: Find High-Value, Low-Risk Subscribers

```sql
SELECT isdn, service_type, advance_amount, revenue_per_advance,
       customer_value_score, advance_readiness_score
FROM recommendations
WHERE bad_debt_risk = 'LOW'
  AND customer_value_score >= 70
  AND advance_readiness_score >= 80
ORDER BY priority_score DESC
LIMIT 1000;
```

---

### Use Case 6: ARPU Trend Analysis

```sql
SELECT
    r.service_type,
    r.arpu_trend,
    COUNT(*) as count,
    AVG(r.arpu_avg_6m) as avg_arpu,
    AVG(r.arpu_growth_rate) as avg_growth_rate
FROM recommendations r
GROUP BY r.service_type, r.arpu_trend
ORDER BY r.service_type, r.arpu_trend;
```

---

### Use Case 7: User Type Distribution

```sql
SELECT
    user_type,
    COUNT(*) as count,
    AVG(customer_value_score) as avg_value_score,
    AVG(revenue_call_pct) as avg_call_pct,
    AVG(revenue_sms_pct) as avg_sms_pct,
    AVG(revenue_data_pct) as avg_data_pct
FROM recommendations
WHERE user_type IS NOT NULL
GROUP BY user_type
ORDER BY count DESC;
```

---

### Use Case 8: Cluster Analysis

```sql
SELECT
    cluster_group,
    COUNT(*) as subscriber_count,
    AVG(customer_value_score) as avg_value,
    AVG(arpu_avg_6m) as avg_arpu,
    COUNT(CASE WHEN bad_debt_risk = 'LOW' THEN 1 END) as low_risk_count,
    COUNT(CASE WHEN bad_debt_risk = 'MEDIUM' THEN 1 END) as medium_risk_count
FROM recommendations
GROUP BY cluster_group
ORDER BY cluster_group;
```

---

### Use Case 9: Monthly ARPU Trend for Subscriber

```sql
SELECT data_month, arpu_call, arpu_sms, arpu_data, arpu_total
FROM subscriber_monthly_arpu
WHERE isdn = '++/hZFPrCDRre55vsZqqxQ=='
ORDER BY data_month;
```

---

### Use Case 10: Bulk Insert/Update (For Campaign Results)

```sql
-- Create temp table for campaign results
CREATE TEMP TABLE campaign_results (
    isdn VARCHAR(255),
    accepted BOOLEAN,
    accepted_date DATE
);

-- Bulk insert campaign results
COPY campaign_results FROM '/path/to/campaign_results.csv' CSV HEADER;

-- Update recommendations with campaign results
UPDATE recommendations r
SET updated_at = NOW()
FROM campaign_results c
WHERE r.isdn = c.isdn AND c.accepted = true;
```

---

## COMBINED REDIS + POSTGRESQL PATTERN

### Pattern 1: Read from Redis, Fallback to PostgreSQL

```python
import redis
import psycopg2

def get_recommendation(isdn):
    """Get recommendation from Redis, fallback to PostgreSQL"""

    # Try Redis first (fast)
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    rec = r.hgetall(f"ut360:rec:{isdn}")

    if rec:
        print("✓ Found in Redis (cache hit)")
        return rec

    # Fallback to PostgreSQL
    print("✗ Not in Redis, querying PostgreSQL...")
    conn = psycopg2.connect(
        host='localhost',
        database='ut360',
        user='ut360_user',
        password='your_password'
    )

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recommendations WHERE isdn = %s", (isdn,))
    row = cursor.fetchone()

    if row:
        # Cache in Redis for future requests
        rec_dict = {
            'isdn': row[1],
            'service_type': row[3],
            'advance_amount': str(row[4]),
            # ... map other fields
        }
        r.hset(f"ut360:rec:{isdn}", mapping=rec_dict)
        r.expire(f"ut360:rec:{isdn}", 7 * 24 * 60 * 60)  # 7 days
        print("✓ Cached in Redis")
        return rec_dict

    conn.close()
    return None

# Usage
isdn = "++/hZFPrCDRre55vsZqqxQ=="
rec = get_recommendation(isdn)
if rec:
    print(f"Service: {rec.get('service_type')}")
    print(f"Advance: {rec.get('advance_amount')}")
```

---

### Pattern 2: Analytics from PostgreSQL, Cache Results in Redis

```python
import redis
import psycopg2
import json

def get_service_stats(service_type):
    """Get service statistics, cache for 1 hour"""

    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    cache_key = f"ut360:stats:service:{service_type}"

    # Check cache
    cached = r.get(cache_key)
    if cached:
        print("✓ Using cached stats")
        return json.loads(cached)

    # Query PostgreSQL
    print("✗ Cache miss, querying PostgreSQL...")
    conn = psycopg2.connect(
        host='localhost',
        database='ut360',
        user='ut360_user',
        password='your_password'
    )

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(advance_amount) as total_advance,
            SUM(revenue_per_advance) as total_revenue,
            AVG(customer_value_score) as avg_value
        FROM recommendations
        WHERE service_type = %s
    """, (service_type,))

    row = cursor.fetchone()
    stats = {
        'total': row[0],
        'total_advance': float(row[1]),
        'total_revenue': float(row[2]),
        'avg_value': float(row[3])
    }

    # Cache for 1 hour
    r.setex(cache_key, 3600, json.dumps(stats))
    print("✓ Cached stats for 1 hour")

    conn.close()
    return stats

# Usage
stats = get_service_stats('EasyCredit')
print(f"Total: {stats['total']:,}")
print(f"Total Advance: {stats['total_advance']:,.0f} VND")
print(f"Total Revenue: {stats['total_revenue']:,.0f} VND")
```

---

## PERFORMANCE COMPARISON

| Operation | Redis | PostgreSQL | Notes |
|-----------|-------|------------|-------|
| Get by ISDN | 2-5ms | 5-10ms | Redis ~2x faster |
| Get 360 Profile | 5-10ms | 20-50ms | Redis ~4x faster |
| Top 100 by Priority | 20-50ms | 50-100ms | Redis ~2x faster |
| Bulk 1000 ISDNs | 100-200ms | 500-1000ms | Redis ~5x faster |
| Complex Analytics | N/A | 100-500ms | PostgreSQL only |
| Aggregations | Limited | Full SQL | PostgreSQL better |

---

## WHEN TO USE REDIS VS POSTGRESQL

### Use Redis When:
✅ Need ultra-fast lookups (<10ms)
✅ Serving real-time recommendation requests
✅ High read frequency (1000+ req/s)
✅ Simple key-value or index lookups
✅ Data can fit in memory (< 2GB recommended)

### Use PostgreSQL When:
✅ Need complex queries (JOIN, GROUP BY, aggregations)
✅ Generating reports and analytics
✅ Need ACID transactions
✅ Need to store historical data long-term
✅ Data size > available Redis memory

### Use Both When:
✅ Redis for hot data (cache layer)
✅ PostgreSQL for cold storage (source of truth)
✅ Redis for reads, PostgreSQL for writes
✅ Best performance + reliability

---

## MONITORING & MAINTENANCE

### Redis Monitoring

```redis
# Check memory usage
INFO memory

# Check number of keys
DBSIZE

# Check connected clients
INFO clients

# Monitor commands in real-time
MONITOR
```

### PostgreSQL Monitoring

```sql
-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## TROUBLESHOOTING

### Redis Issues

**Problem:** Connection refused
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Start Redis
sudo systemctl start redis-server
```

**Problem:** Out of memory
```bash
# Check memory usage
redis-cli INFO memory

# Clear old data
redis-cli FLUSHDB

# Increase maxmemory in redis.conf
# maxmemory 2gb
# maxmemory-policy allkeys-lru
```

### PostgreSQL Issues

**Problem:** Connection refused
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

**Problem:** Slow queries
```sql
-- Create missing indexes
CREATE INDEX idx_name ON table(column);

-- Analyze query performance
EXPLAIN ANALYZE SELECT ...;

-- Update statistics
ANALYZE table_name;
```

---

## BACKUP & RECOVERY

### Redis Backup

```bash
# Create snapshot
redis-cli SAVE

# Backup RDB file
cp /var/lib/redis/dump.rdb /backup/dump.rdb

# Restore
cp /backup/dump.rdb /var/lib/redis/dump.rdb
sudo systemctl restart redis-server
```

### PostgreSQL Backup

```bash
# Backup database
pg_dump -U ut360_user ut360 > ut360_backup.sql

# Backup specific table
pg_dump -U ut360_user -t recommendations ut360 > recommendations_backup.sql

# Restore
psql -U ut360_user ut360 < ut360_backup.sql
```

---

**Created By:** Claude AI
**Date:** 2025-10-22
**Version:** 1.0
