# Redis & PostgreSQL Quick Start Guide

**Date:** 2025-10-22
**Purpose:** Hướng dẫn nhanh setup và sử dụng Redis + PostgreSQL cho UT360

---

## 📋 Quick Summary

Hệ thống UT360 sử dụng **dual storage strategy**:
- **PostgreSQL**: Source of truth, complex queries, analytics
- **Redis**: High-speed cache, real-time lookups

**Data flow:**
```
Parquet Files → PostgreSQL (Source of Truth) → Redis (Cache) → API
```

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Redis & PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y redis-server postgresql postgresql-contrib

# Start services
sudo systemctl start redis-server
sudo systemctl start postgresql
sudo systemctl enable redis-server
sudo systemctl enable postgresql

# Verify
redis-cli ping  # Should return PONG
sudo -u postgres psql -c "SELECT version();"
```

### Step 2: Create PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE ut360;
CREATE USER ut360_user WITH PASSWORD 'ut360_password_2025';
GRANT ALL PRIVILEGES ON DATABASE ut360 TO ut360_user;
\q
EOF

# Verify
psql -U ut360_user -d ut360 -c "SELECT 'Connected successfully';"
```

### Step 3: Install Python Dependencies

```bash
pip install redis psycopg2-binary pandas numpy
```

### Step 4: Configure Sync Scripts

Edit PostgreSQL credentials in sync script:

```bash
# Edit /data/ut360/scripts/utils/sync_to_postgresql.py
nano /data/ut360/scripts/utils/sync_to_postgresql.py

# Change DB_CONFIG:
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ut360',
    'user': 'ut360_user',
    'password': 'ut360_password_2025'  # ← CHANGE THIS
}
```

### Step 5: Run Data Sync

```bash
cd /data/ut360

# Sync to PostgreSQL first (2-3 minutes)
python3 scripts/utils/sync_to_postgresql.py

# Then sync to Redis (1-2 minutes)
python3 scripts/utils/sync_to_redis.py
```

**Expected output:**
```
===========================================
UT360 - Sync Data to PostgreSQL
===========================================

✓ Connected to PostgreSQL
✓ Database schema created successfully

[1/3] Loading recommendations...
  Loaded 214504 recommendations from CSV
  ✓ Inserted/Updated 214504 recommendations

[2/3] Loading 360 profiles...
  Loaded 214504 profiles from parquet
  ✓ Inserted/Updated 214504 profiles

[3/3] Loading monthly ARPU...
  Loaded 1501528 monthly records from parquet
  ✓ Inserted 1501528 monthly ARPU records

===========================================
DATABASE STATISTICS
===========================================
Total Recommendations: 214,504
Total 360 Profiles: 214,504
Total Monthly ARPU Records: 1,501,528

✓ Data sync completed successfully!
```

---

## 🧪 Test Queries

### Test Redis

```bash
# Test Redis CLI
redis-cli

# Get metadata
HGETALL ut360:meta:stats

# Get recommendation
HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==

# Get top 10 EasyCredit
ZREVRANGE ut360:idx:service:EasyCredit 0 9 WITHSCORES

# Exit
exit
```

### Test PostgreSQL

```bash
# Test PostgreSQL
psql -U ut360_user -d ut360

# Get total count
SELECT COUNT(*) FROM recommendations;

# Get sample recommendation
SELECT isdn, service_type, advance_amount, customer_value_score
FROM recommendations
LIMIT 5;

# Get stats by service
SELECT service_type, COUNT(*) as count, SUM(advance_amount) as total_advance
FROM recommendations
GROUP BY service_type;

# Exit
\q
```

---

## 💻 Use in Your Application

### Python Example - Get Recommendation

```python
import redis
import psycopg2

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get recommendation by ISDN
isdn = "++/hZFPrCDRre55vsZqqxQ=="
rec = r.hgetall(f"ut360:rec:{isdn}")

if rec:
    print(f"ISDN: {rec['isdn']}")
    print(f"Service: {rec['service_type']}")
    print(f"Advance: {rec['advance_amount']} VND")
    print(f"Revenue: {rec['revenue_per_advance']} VND")
    print(f"Risk: {rec['bad_debt_risk']}")
    print(f"Customer Value Score: {rec['customer_value_score']}/100")
else:
    print("Recommendation not found")
```

### Python Example - Get 360 Profile

```python
import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

isdn = "++/hZFPrCDRre55vsZqqxQ=="
profile = r.hgetall(f"ut360:profile:{isdn}")

if profile:
    # Parse JSON fields
    basic = json.loads(profile['basic'])
    kpi_scores = json.loads(profile['kpi_scores'])
    monthly_arpu = json.loads(profile['monthly_arpu'])

    print(f"=== Customer360-VNS ===")
    print(f"ISDN: {basic['isdn']}")
    print(f"Service: {basic['service']}")
    print(f"Advance: {basic['advance']:,.0f} VND")
    print(f"Customer Value: {kpi_scores['customer_value']}/100")
    print(f"Advance Readiness: {kpi_scores['advance_readiness']}/100")
    print(f"Monthly Data: {len(monthly_arpu)} months")
```

### Python Example - Get Top 100 by Priority

```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get top 100 EasyCredit by priority
top_isdns = r.zrevrange('ut360:idx:service:EasyCredit', 0, 99, withscores=True)

print(f"Top 100 EasyCredit Recommendations:")
for idx, (isdn, priority) in enumerate(top_isdns, 1):
    rec = r.hgetall(f"ut360:rec:{isdn}")
    print(f"{idx:3d}. Priority: {priority:5.2f} | "
          f"Advance: {rec.get('advance_amount', '0'):>8} | "
          f"Value: {rec.get('customer_value_score', '0'):>3}/100")
```

---

## 🔧 Configuration Files

### Create Redis Configuration (Optional)

```bash
# Create custom redis.conf
sudo nano /etc/redis/redis.conf

# Important settings:
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Create PostgreSQL Connection Pool (Optional)

```python
# connection_pool.py
import psycopg2
from psycopg2 import pool

# Create connection pool
pg_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min=1, max=20 connections
    host='localhost',
    database='ut360',
    user='ut360_user',
    password='ut360_password_2025'
)

def get_db_connection():
    """Get connection from pool"""
    return pg_pool.getconn()

def return_db_connection(conn):
    """Return connection to pool"""
    pg_pool.putconn(conn)

# Usage
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM recommendations")
count = cursor.fetchone()[0]
print(f"Total: {count}")
conn.close()
return_db_connection(conn)
```

---

## 📊 Monitoring

### Redis Memory Usage

```bash
# Check memory
redis-cli INFO memory | grep used_memory_human

# Check keys count
redis-cli DBSIZE

# Monitor commands in real-time
redis-cli MONITOR
```

### PostgreSQL Table Sizes

```sql
-- Connect
psql -U ut360_user -d ut360

-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 🔄 Data Refresh Strategy

### Daily Refresh (Recommended)

Create cron job:

```bash
# Edit crontab
crontab -e

# Add daily refresh at 2 AM
0 2 * * * cd /data/ut360 && python3 scripts/utils/sync_to_postgresql.py && python3 scripts/utils/sync_to_redis.py >> /var/log/ut360_sync.log 2>&1
```

### Manual Refresh

```bash
cd /data/ut360

# Refresh PostgreSQL
python3 scripts/utils/sync_to_postgresql.py

# Refresh Redis
python3 scripts/utils/sync_to_redis.py
```

---

## 🚨 Troubleshooting

### Redis not starting

```bash
# Check status
sudo systemctl status redis-server

# Check logs
sudo tail -f /var/log/redis/redis-server.log

# Restart
sudo systemctl restart redis-server
```

### PostgreSQL not starting

```bash
# Check status
sudo systemctl status postgresql

# Check logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Restart
sudo systemctl restart postgresql
```

### Cannot connect to PostgreSQL

```bash
# Check if listening
sudo netstat -plnt | grep 5432

# Edit pg_hba.conf to allow connections
sudo nano /etc/postgresql/*/main/pg_hba.conf

# Add line:
# local   all   ut360_user   md5

# Restart
sudo systemctl restart postgresql
```

### Redis out of memory

```bash
# Check memory usage
redis-cli INFO memory

# Clear all data
redis-cli FLUSHDB

# Or increase maxmemory in redis.conf
sudo nano /etc/redis/redis.conf
# maxmemory 4gb

sudo systemctl restart redis-server
```

---

## 📈 Performance Benchmarks

After setup, test performance:

```bash
# Test Redis performance
redis-cli --intrinsic-latency 100

# Expected: < 1ms average

# Test PostgreSQL performance
time psql -U ut360_user -d ut360 -c "SELECT COUNT(*) FROM recommendations"

# Expected: < 0.1s
```

---

## 🎯 Next Steps

1. ✅ Setup complete
2. ⏳ Integrate with FastAPI backend
3. ⏳ Update web application to use Redis/PostgreSQL
4. ⏳ Set up monitoring and alerts
5. ⏳ Configure backup strategy

---

## 📚 Documentation Links

- [Redis Schema Design](REDIS_POSTGRES_DESIGN.md) - Complete schema design
- [Query Examples](REDIS_POSTGRES_QUERY_EXAMPLES.md) - Comprehensive query examples
- [Production Files List](PRODUCTION_FILES_LIST.md) - Deployment files

---

## 💡 Tips

### Redis Tips:
- ✅ Keep hot data only (7-day TTL)
- ✅ Use pipeline for bulk operations
- ✅ Monitor memory usage regularly
- ✅ Set maxmemory-policy to allkeys-lru

### PostgreSQL Tips:
- ✅ Create indexes on frequently queried columns
- ✅ Run ANALYZE after bulk inserts
- ✅ Use connection pooling for high traffic
- ✅ Regular backups with pg_dump

### General Tips:
- ✅ Redis for reads (cache layer)
- ✅ PostgreSQL for writes (source of truth)
- ✅ Sync Redis from PostgreSQL daily
- ✅ Monitor both systems

---

## ✅ Checklist

- [ ] Redis installed and running
- [ ] PostgreSQL installed and running
- [ ] Database `ut360` created
- [ ] User `ut360_user` created with password
- [ ] Python packages installed (redis, psycopg2-binary)
- [ ] Sync scripts configured (DB_CONFIG updated)
- [ ] Data synced to PostgreSQL (214K recommendations)
- [ ] Data synced to Redis (cache populated)
- [ ] Test queries working in both systems
- [ ] Monitoring set up
- [ ] Backup strategy configured

---

**Setup Time:** ~10-15 minutes
**Data Sync Time:** ~5 minutes
**Total Time:** ~20 minutes

**Redis Memory Used:** ~1.2 GB
**PostgreSQL Disk Used:** ~350 MB

---

**Created By:** Claude AI
**Date:** 2025-10-22
**Status:** Ready for Production
