# Sync to Production - Quick Guide

**Server:** DB01 (PostgreSQL) & WEB01 (Redis)
**Date:** 2025-10-22
**Status:** ✅ Ready to Deploy

---

## 🎯 MỤC ĐÍCH

Đồng bộ 214,504 recommendations vào:
- **PostgreSQL (DB01):** 10.39.223.102:5432 - Lưu trữ dài hạn, queries phức tạp
- **Redis (WEB01):** 10.39.223.70:6379 - Cache tốc độ cao cho tra cứu nhanh

---

## 📦 FILES CẦN COPY

### 1. Scripts (3 files)
```bash
scripts/utils/sync_to_postgresql.py
scripts/utils/sync_to_redis.py
scripts/utils/test_connections.py
```

### 2. Data Files (3 files)
```bash
output/recommendations/recommendations_final_filtered_typeupdate.csv  (32MB)
output/subscriber_360_profile.parquet                                 (21MB)
output/subscriber_monthly_summary.parquet                             (20MB)
```

**Note:** Bạn đã có CSV, chỉ cần 2 parquet files

---

## 🚀 DEPLOYMENT (3 BƯỚC)

### Bước 1: Copy Files
```bash
# Tạo thư mục
ssh user@server "mkdir -p /opt/ut360/scripts/utils /opt/ut360/output/recommendations"

# Copy scripts (3 files)
cd /data/ut360
scp scripts/utils/sync_to_postgresql.py user@server:/opt/ut360/scripts/utils/
scp scripts/utils/sync_to_redis.py user@server:/opt/ut360/scripts/utils/
scp scripts/utils/test_connections.py user@server:/opt/ut360/scripts/utils/

# Copy data files (2 parquet - bạn đã có CSV)
scp output/subscriber_360_profile.parquet user@server:/opt/ut360/output/
scp output/subscriber_monthly_summary.parquet user@server:/opt/ut360/output/
```

### Bước 2: Setup Dependencies
```bash
# SSH vào server
ssh user@server

# Install packages
pip3 install pandas numpy psycopg2-binary redis pyarrow

# Test connections
cd /opt/ut360
python3 scripts/utils/test_connections.py
```

**Expected output:**
```
============================================================
UT360 - Connection Test
============================================================

[1/2] Testing PostgreSQL connection to DB01...
      ✓ Connected successfully!

[2/2] Testing Redis connection to WEB01...
      ✓ Connected successfully!

[3/3] Checking data files...
      ✓ CSV: 31.70 MB
      ✓ 360 Profile: 21.00 MB
      ✓ Monthly ARPU: 19.50 MB

✓ You are ready to run sync scripts!
```

### Bước 3: Chạy Sync
```bash
# Sync to PostgreSQL (2-3 phút)
python3 scripts/utils/sync_to_postgresql.py

# Sync to Redis (1-2 phút)
python3 scripts/utils/sync_to_redis.py
```

**DONE!** 🎉

---

## ✅ VERIFY

### PostgreSQL
```bash
psql -h 10.39.223.102 -U admin -d ut360 -c \
  "SELECT service_type, COUNT(*) FROM recommendations GROUP BY service_type"
```

**Expected:**
```
service_type | count
-------------+--------
Fee          | 137644
Free         | 46582
Quota        | 30278
```

### Redis
```bash
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis \
  HGET ut360:meta:stats total_subscribers
```

**Expected:**
```
"214504"
```

---

## 📊 KẾT QUẢ

### PostgreSQL (DB01)
- ✅ 214,504 recommendations
- ✅ 214,504 360 profiles
- ✅ 1,501,528 monthly ARPU records
- 📦 Size: ~350MB
- ⏱️ Time: 2-3 minutes

### Redis (WEB01)
- ✅ ~430,000 keys
- ✅ 3 service indexes (Fee/Free/Quota)
- ✅ 2 risk indexes (LOW/MEDIUM)
- 💾 Memory: ~1.2GB
- ⏱️ Time: 1-2 minutes

---

## 🔍 QUERY EXAMPLES

### PostgreSQL - Lấy recommendation
```sql
SELECT isdn, service_type, advance_amount, bad_debt_risk
FROM recommendations
WHERE isdn = '++/hZFPrCDRre55vsZqqxQ==';
```

### Redis - Tra cứu nhanh khi mời ứng
```bash
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis \
  HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==
```

**Output:**
```
service_type     → "Fee"
advance_amount   → "25000"
bad_debt_risk    → "LOW"
customer_value   → "70"
```

---

## ⚠️ TROUBLESHOOTING

### Connection Failed?
```bash
# Test PostgreSQL
telnet 10.39.223.102 5432

# Test Redis
telnet 10.39.223.70 6379

# Re-run test
python3 scripts/utils/test_connections.py
```

### File Not Found?
```bash
# Verify structure
ls -lh /opt/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv
ls -lh /opt/ut360/output/subscriber_360_profile.parquet
ls -lh /opt/ut360/output/subscriber_monthly_summary.parquet
```

### Package Missing?
```bash
pip3 install --upgrade pandas numpy psycopg2-binary redis pyarrow
```

---

## 📞 QUICK REFERENCE

| Item | Value |
|------|-------|
| **PostgreSQL Host** | 10.39.223.102:5432 |
| **PostgreSQL User** | admin |
| **PostgreSQL Pass** | Vns@2025 |
| **Redis Host** | 10.39.223.70:6379 |
| **Redis User** | redis |
| **Redis Pass** | 098poiA |
| **Service Types** | Fee, Free, Quota |
| **Total Records** | 214,504 |

---

## 📚 FULL DOCUMENTATION

- [DEPLOYMENT_TO_SERVER.md](DEPLOYMENT_TO_SERVER.md) - Chi tiết deployment
- [FINAL_DEPLOYMENT_CHECKLIST.md](FINAL_DEPLOYMENT_CHECKLIST.md) - Checklist đầy đủ
- [DATABASE_STRUCTURE_VISUAL.md](DATABASE_STRUCTURE_VISUAL.md) - Cấu trúc database
- [REDIS_POSTGRES_QUERY_EXAMPLES.md](REDIS_POSTGRES_QUERY_EXAMPLES.md) - Query examples

---

## ⏰ SCHEDULE (OPTIONAL)

Setup cron job để sync tự động hàng ngày:

```bash
crontab -e

# Add:
0 2 * * * cd /opt/ut360 && python3 scripts/utils/sync_to_postgresql.py >> /var/log/ut360_pg.log 2>&1
30 2 * * * cd /opt/ut360 && python3 scripts/utils/sync_to_redis.py >> /var/log/ut360_redis.log 2>&1
```

---

**Tổng thời gian:** 5-10 phút
**Complexity:** Low (chỉ copy files và chạy scripts)
**Risk:** Low (không ảnh hưởng hệ thống hiện tại)

✅ **Ready to deploy!**

---

**Created:** 2025-10-22
**For:** Production deployment to DB01 & WEB01
