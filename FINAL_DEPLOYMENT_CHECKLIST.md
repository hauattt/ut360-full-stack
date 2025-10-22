# UT360 Final Deployment Checklist

**Date:** 2025-10-22
**Status:** ✅ Ready for Production

---

## 📋 TÓM TẮT TOÀN BỘ THAY ĐỔI

### 1. Service Type Conversion ✅
```
EasyCredit   →  Fee      (137,644 subscribers)
MBFG         →  Free     (46,582 subscribers)
ungsanluong  →  Quota    (30,278 subscribers)
```

### 2. Files Đã Cập Nhật ✅
- ✅ `sync_to_postgresql.py` - Connection DB01 configured
- ✅ `sync_to_redis.py` - Connection WEB01 configured
- ✅ `web backend app.py` - Using typeupdate.csv
- ✅ `recommendations_final_filtered_typeupdate.csv` - Created (32MB)

### 3. Server Connections Configured ✅
- ✅ PostgreSQL DB01: 10.39.223.102:5432 (admin/Vns@2025)
- ✅ Redis WEB01: 10.39.223.70:6379 (redis/098poiA)

---

## 🚀 DEPLOYMENT STEPS CHO BẠN

### Bước 1: Copy Files Lên Server

**Files cần copy (chỉ 4 files nếu bạn đã có CSV):**

```bash
# 1. Sync scripts (2 files)
scp /data/ut360/scripts/utils/sync_to_postgresql.py user@server:/opt/ut360/scripts/utils/
scp /data/ut360/scripts/utils/sync_to_redis.py user@server:/opt/ut360/scripts/utils/

# 2. Data files (2 files parquet - nếu chưa có)
scp /data/ut360/output/subscriber_360_profile.parquet user@server:/opt/ut360/output/
scp /data/ut360/output/subscriber_monthly_summary.parquet user@server:/opt/ut360/output/

# 3. CSV file - CHỈ NẾU CHƯA CÓ (bạn nói đã có rồi)
# scp /data/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv \
#     user@server:/opt/ut360/output/recommendations/
```

### Bước 2: Cài Dependencies Trên Server

```bash
# SSH vào server
ssh user@server

# Install packages
pip3 install pandas numpy psycopg2-binary redis pyarrow
```

### Bước 3: Chạy Sync

```bash
# Sync to PostgreSQL (2-3 phút)
cd /opt/ut360
python3 scripts/utils/sync_to_postgresql.py

# Sync to Redis (1-2 phút)
python3 scripts/utils/sync_to_redis.py
```

**DONE!** 🎉

---

## 📊 KẾT QUẢ MONG ĐỢI

### PostgreSQL (DB01)
```
Database: ut360
Tables:
  - recommendations           214,504 rows
  - subscriber_360_profiles   214,504 rows
  - subscriber_monthly_arpu   1,501,528 rows

Service Distribution:
  - Fee:   137,644 (64.2%)
  - Free:   46,582 (21.7%)
  - Quota:  30,278 (14.1%)

Size: ~350MB
```

### Redis (WEB01)
```
Keys: ~430,000
Memory: ~1.2GB

Indexes:
  - ut360:idx:service:Fee     137,644 members
  - ut360:idx:service:Free     46,582 members
  - ut360:idx:service:Quota    30,278 members
  - ut360:idx:risk:LOW        180,000 members
  - ut360:idx:risk:MEDIUM      34,504 members

TTL: 7 days
```

---

## ✅ VERIFICATION COMMANDS

### Test PostgreSQL
```bash
psql -h 10.39.223.102 -U admin -d ut360 -c "SELECT service_type, COUNT(*) FROM recommendations GROUP BY service_type"
```

**Expected:**
```
service_type | count
-------------+--------
Fee          | 137644
Free         | 46582
Quota        | 30278
```

### Test Redis
```bash
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis HGETALL ut360:meta:stats
```

**Expected:**
```
1) "total_subscribers"
2) "214504"
3) "total_fee"
4) "137644"
5) "total_free"
6) "46582"
7) "total_quota"
8) "30278"
```

---

## 📁 CẤU TRÚC THƯ MỤC TRÊN SERVER

```
/opt/ut360/
├── scripts/
│   └── utils/
│       ├── sync_to_postgresql.py  ← Copy file này
│       └── sync_to_redis.py       ← Copy file này
└── output/
    ├── recommendations/
    │   └── recommendations_final_filtered_typeupdate.csv  ← Bạn đã có
    ├── subscriber_360_profile.parquet        ← Copy file này
    └── subscriber_monthly_summary.parquet    ← Copy file này
```

---

## 🔍 QUERY EXAMPLES SAU KHI SYNC

### PostgreSQL Queries

```sql
-- Get recommendation by ISDN
SELECT * FROM recommendations
WHERE isdn = '++/hZFPrCDRre55vsZqqxQ==';

-- Top 100 Fee service
SELECT isdn, advance_amount, customer_value_score
FROM recommendations
WHERE service_type = 'Fee'
ORDER BY priority_score DESC
LIMIT 100;

-- Analytics by service and risk
SELECT service_type, bad_debt_risk, COUNT(*), SUM(advance_amount)
FROM recommendations
GROUP BY service_type, bad_debt_risk;
```

### Redis Queries

```bash
# Get recommendation
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis \
  HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==

# Top 10 Fee by priority
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis \
  ZREVRANGE ut360:idx:service:Fee 0 9 WITHSCORES

# Get 360 profile
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis \
  HGETALL ut360:profile:++/hZFPrCDRre55vsZqqxQ==
```

---

## 📚 TÀI LIỆU THAM KHẢO

| Document | Purpose | Path |
|----------|---------|------|
| **DEPLOYMENT_TO_SERVER.md** | Chi tiết deployment steps | [Link](/data/ut360/DEPLOYMENT_TO_SERVER.md) |
| **SERVICE_TYPE_UPDATE_SUMMARY.md** | Service type conversion details | [Link](/data/ut360/SERVICE_TYPE_UPDATE_SUMMARY.md) |
| **DATABASE_STRUCTURE_VISUAL.md** | Redis/PostgreSQL structure | [Link](/data/ut360/DATABASE_STRUCTURE_VISUAL.md) |
| **REDIS_POSTGRES_QUERY_EXAMPLES.md** | Query examples | [Link](/data/ut360/REDIS_POSTGRES_QUERY_EXAMPLES.md) |
| **REDIS_POSTGRES_DATA_EXAMPLES.md** | Sample data | [Link](/data/ut360/REDIS_POSTGRES_DATA_EXAMPLES.md) |

---

## 🎯 QUICK START (TL;DR)

Nếu bạn đã có CSV trên server:

```bash
# 1. Copy 4 files
scp sync_to_postgresql.py sync_to_redis.py user@server:/opt/ut360/scripts/utils/
scp subscriber_360_profile.parquet subscriber_monthly_summary.parquet user@server:/opt/ut360/output/

# 2. SSH và install
ssh user@server
pip3 install pandas numpy psycopg2-binary redis pyarrow

# 3. Chạy sync
cd /opt/ut360
python3 scripts/utils/sync_to_postgresql.py
python3 scripts/utils/sync_to_redis.py

# 4. Verify
psql -h 10.39.223.102 -U admin -d ut360 -c "SELECT COUNT(*) FROM recommendations"
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis DBSIZE
```

**Done! 5-10 phút tổng cộng**

---

## ⚠️ LƯU Ý QUAN TRỌNG

1. **Firewall:** Đảm bảo server của bạn có thể connect tới:
   - 10.39.223.102:5432 (PostgreSQL)
   - 10.39.223.70:6379 (Redis)

2. **File CSV:** Bạn nói đã có file `recommendations_final_filtered_typeupdate.csv` trên server
   - Verify path: `/opt/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv`
   - Size: ~32MB
   - Rows: 214,504

3. **Credentials:** Scripts đã config sẵn:
   - PostgreSQL: admin/Vns@2025
   - Redis: redis/098poiA
   - **KHÔNG CẦN** sửa gì trong scripts

4. **Service Types:** Phải dùng service_type mới:
   - ✅ Fee, Free, Quota
   - ❌ EasyCredit, MBFG, ungsanluong (old, không dùng nữa)

---

## 📞 TROUBLESHOOTING

### Nếu PostgreSQL connection failed:
```bash
# Test connection
telnet 10.39.223.102 5432

# Check credentials
psql -h 10.39.223.102 -U admin -d postgres
```

### Nếu Redis connection failed:
```bash
# Test connection
telnet 10.39.223.70 6379

# Test auth
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis PING
```

### Nếu file not found:
```bash
# Verify files
ls -lh /opt/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv
ls -lh /opt/ut360/output/subscriber_360_profile.parquet
ls -lh /opt/ut360/output/subscriber_monthly_summary.parquet
```

---

## ✅ FINAL CHECKLIST

**Trước khi chạy:**
- [ ] Đã copy 2 sync scripts lên server
- [ ] Đã copy 2 parquet files lên server (hoặc verify CSV đã có)
- [ ] Đã install dependencies (pandas, numpy, psycopg2-binary, redis, pyarrow)
- [ ] Đã test connection tới PostgreSQL
- [ ] Đã test connection tới Redis

**Sau khi chạy:**
- [ ] PostgreSQL có 3 tables với đúng số rows
- [ ] Redis có ~430K keys
- [ ] Service types hiển thị: Fee, Free, Quota
- [ ] Test queries hoạt động đúng

---

**Status:** 🟢 **READY TO DEPLOY**

**Estimated Time:** 5-10 minutes total

**Next Step:** Copy files và chạy sync scripts!

---

**Created By:** Claude AI
**Date:** 2025-10-22
**For:** Production Deployment to DB01 & WEB01
