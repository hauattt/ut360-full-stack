# UT360 Database Structure - Visual Guide

**Date:** 2025-10-22
**Purpose:** Hướng dẫn trực quan về cấu trúc Redis keys và PostgreSQL database

---

## 📊 TỔNG QUAN HỆ THỐNG

```
┌─────────────────────────────────────────────────────────────┐
│                    REDIS (Cache Layer)                       │
│                     ~1.2GB in memory                         │
│                                                              │
│  [ut360:rec:*]          214,504 hashes  (recommendations)   │
│  [ut360:profile:*]      214,504 hashes  (360 profiles)      │
│  [ut360:idx:service:*]  3 sorted sets   (EasyCredit, MBFG, ung) │
│  [ut360:idx:risk:*]     2 sets          (LOW, MEDIUM)       │
│  [ut360:idx:cluster:*]  4 sets          (cluster 0-3)       │
│  [ut360:meta:stats]     1 hash          (metadata)          │
│                                                              │
│  Total Keys: ~430,000                                        │
│  TTL: 7 days (auto-refresh)                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              POSTGRESQL (Source of Truth)                    │
│                     ~350MB on disk                           │
│                                                              │
│  [recommendations]           214,504 rows                    │
│  [subscriber_360_profiles]   214,504 rows                    │
│  [subscriber_monthly_arpu]   1,501,528 rows (7 months)       │
│                                                              │
│  Total Tables: 3                                             │
│  Total Rows: ~1.9M                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 REDIS KEY STRUCTURE

### Pattern 1: Recommendation by ISDN
```
Key Pattern:    ut360:rec:{ISDN}
Type:           Hash
Count:          214,504 keys
TTL:            7 days
Size per key:   ~1.5 KB
Total Size:     ~322 MB

Example Key:    ut360:rec:++/hZFPrCDRre55vsZqqxQ==
```

**Cấu trúc Hash:**
```redis
HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==

1)  "isdn"                      → "++/hZFPrCDRre55vsZqqxQ=="
2)  "subscriber_type"           → "PRE"
3)  "service_type"              → "EasyCredit"
4)  "advance_amount"            → "25000"
5)  "revenue_per_advance"       → "7500"
6)  "cluster_group"             → "1"
7)  "bad_debt_risk"             → "LOW"
8)  "arpu_avg_6m"              → "2757.50"
9)  "arpu_growth_rate"         → "-56.7"
10) "arpu_trend"                → "Giảm"
11) "customer_value_score"      → "70"
12) "advance_readiness_score"   → "90"
13) "priority_score"            → "63.00"
14) "user_type"                 → "Voice/SMS User"
15) "topup_frequency_class"     → "Trung bình"
16) "updated_at"                → "2025-10-22T10:30:00"
```

**Truy vấn:**
```bash
# Lấy toàn bộ thông tin
redis-cli HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==

# Lấy 1 field cụ thể
redis-cli HGET ut360:rec:++/hZFPrCDRre55vsZqqxQ== advance_amount

# Lấy nhiều fields
redis-cli HMGET ut360:rec:++/hZFPrCDRre55vsZqqxQ== \
  service_type advance_amount bad_debt_risk
```

---

### Pattern 2: 360 Profile by ISDN
```
Key Pattern:    ut360:profile:{ISDN}
Type:           Hash (with JSON fields)
Count:          214,504 keys
TTL:            7 days
Size per key:   ~4 KB
Total Size:     ~858 MB

Example Key:    ut360:profile:++/hZFPrCDRre55vsZqqxQ==
```

**Cấu trúc Hash:**
```redis
HGETALL ut360:profile:++/hZFPrCDRre55vsZqqxQ==

1) "basic"              → '{"isdn":"...","type":"PRE","service":"EasyCredit","advance":25000,"revenue":7500}'
2) "arpu_stats"         → '{"avg":2757.5,"std":1234.5,"min":1000,"max":5000,"growth_rate":-56.7,"trend":"Giảm"}'
3) "revenue_breakdown"  → '{"call_pct":15.2,"sms_pct":8.5,"data_pct":76.3,"user_type":"Voice/SMS User"}'
4) "topup_behavior"     → '{"frequency":2.5,"avg_amount":50000,"ratio":0.02,"frequency_class":"Trung bình"}'
5) "risk_assessment"    → '{"level":"LOW","score":70,"factors":["Good payment history","Stable ARPU"]}'
6) "kpi_scores"         → '{"customer_value":70,"advance_readiness":90,"revenue_potential":7500}'
7) "monthly_arpu"       → '[{"month":"202503","arpu_total":3500},{"month":"202504","arpu_total":2800},...]'
8) "updated_at"         → "2025-10-22T10:30:00"
```

**Truy vấn:**
```python
import redis, json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
profile = r.hgetall('ut360:profile:++/hZFPrCDRre55vsZqqxQ==')

# Parse JSON fields
basic = json.loads(profile['basic'])
kpi_scores = json.loads(profile['kpi_scores'])
monthly_arpu = json.loads(profile['monthly_arpu'])

print(f"ISDN: {basic['isdn']}")
print(f"Customer Value: {kpi_scores['customer_value']}/100")
print(f"Monthly data: {len(monthly_arpu)} months")
```

---

### Pattern 3: Index by Service Type (Sorted Set)
```
Key Pattern:    ut360:idx:service:{service_type}
Type:           Sorted Set (sorted by priority_score)
Count:          3 keys
TTL:            30 days

Keys:
  - ut360:idx:service:EasyCredit      (~142,000 members)
  - ut360:idx:service:MBFG             (~45,000 members)
  - ut360:idx:service:ungsanluong      (~27,504 members)
```

**Cấu trúc Sorted Set:**
```redis
# Mỗi member là ISDN, score là priority_score
ZREVRANGE ut360:idx:service:EasyCredit 0 -1 WITHSCORES

Member: ++/hZFPrCDRre55vsZqqxQ==    Score: 63.00
Member: anotherISDN123==             Score: 81.00
Member: yetAnotherISDN==             Score: 72.50
...
```

**Truy vấn:**
```bash
# Lấy top 100 EasyCredit (highest priority)
redis-cli ZREVRANGE ut360:idx:service:EasyCredit 0 99 WITHSCORES

# Đếm số lượng
redis-cli ZCARD ut360:idx:service:EasyCredit

# Lấy rank của ISDN
redis-cli ZREVRANK ut360:idx:service:EasyCredit "++/hZFPrCDRre55vsZqqxQ=="

# Lấy subscribers có priority từ 70-100
redis-cli ZREVRANGEBYSCORE ut360:idx:service:EasyCredit 100 70 LIMIT 0 100
```

---

### Pattern 4: Index by Risk Level (Set)
```
Key Pattern:    ut360:idx:risk:{risk_level}
Type:           Set (unordered collection of ISDNs)
Count:          2 keys
TTL:            30 days

Keys:
  - ut360:idx:risk:LOW       (~180,000 members)
  - ut360:idx:risk:MEDIUM     (~34,504 members)
```

**Cấu trúc Set:**
```redis
# Set chứa danh sách ISDNs
SMEMBERS ut360:idx:risk:LOW

1) "++/hZFPrCDRre55vsZqqxQ=="
2) "anotherLowRiskISDN=="
3) "yetAnotherLowRiskISDN=="
...
```

**Truy vấn:**
```bash
# Đếm số lượng LOW risk
redis-cli SCARD ut360:idx:risk:LOW

# Check xem ISDN có phải LOW risk không
redis-cli SISMEMBER ut360:idx:risk:LOW "++/hZFPrCDRre55vsZqqxQ=="

# Lấy random 100 LOW risk subscribers
redis-cli SRANDMEMBER ut360:idx:risk:LOW 100

# Lấy tất cả LOW risk (chậm nếu nhiều)
redis-cli SMEMBERS ut360:idx:risk:LOW
```

---

### Pattern 5: Index by Cluster (Set)
```
Key Pattern:    ut360:idx:cluster:{cluster_id}
Type:           Set
Count:          4 keys (cluster 0-3)
TTL:            30 days

Keys:
  - ut360:idx:cluster:0      (~50,000 members)
  - ut360:idx:cluster:1      (~60,000 members)
  - ut360:idx:cluster:2      (~55,000 members)
  - ut360:idx:cluster:3      (~49,504 members)
```

**Truy vấn:**
```bash
# Đếm subscribers trong cluster 1
redis-cli SCARD ut360:idx:cluster:1

# Lấy tất cả subscribers trong cluster 1
redis-cli SMEMBERS ut360:idx:cluster:1
```

---

### Pattern 6: Metadata (Hash)
```
Key:            ut360:meta:stats
Type:           Hash
Count:          1 key
TTL:            30 days
```

**Cấu trúc:**
```redis
HGETALL ut360:meta:stats

1)  "total_subscribers"         → "214504"
2)  "total_easycredit"         → "142000"
3)  "total_mbfg"               → "45000"
4)  "total_ungsanluong"        → "27504"
5)  "total_low_risk"           → "180000"
6)  "total_medium_risk"        → "34504"
7)  "avg_advance_amount"       → "28500.50"
8)  "total_revenue_potential"  → "1260000000.00"
9)  "last_updated"             → "2025-10-22T10:30:00"
10) "data_version"             → "v1.0"
```

---

## 🗄️ POSTGRESQL TABLE STRUCTURE

### Table 1: recommendations
```sql
Table:      recommendations
Rows:       214,504
Size:       ~43 MB
Indexes:    7 indexes (~20 MB)
```

**Cấu trúc:**
```
┌─────────────────────────────────────────────────────────────────┐
│ recommendations                                                  │
├──────────────────────┬──────────────┬──────────────────────────┤
│ Column               │ Type         │ Example                   │
├──────────────────────┼──────────────┼──────────────────────────┤
│ id                   │ BIGSERIAL PK │ 1                         │
│ isdn                 │ VARCHAR(255) │ ++/hZFPrCDRre55vsZqqxQ== │
│ subscriber_type      │ VARCHAR(10)  │ PRE                       │
│ service_type         │ VARCHAR(50)  │ EasyCredit                │
│ advance_amount       │ DECIMAL(12,2)│ 25000.00                  │
│ revenue_per_advance  │ DECIMAL(12,2)│ 7500.00                   │
│ cluster_group        │ INTEGER      │ 1                         │
│ bad_debt_risk        │ VARCHAR(20)  │ LOW                       │
│ arpu_avg_6m         │ DECIMAL(10,2)│ 2757.50                   │
│ arpu_std_6m         │ DECIMAL(10,2)│ 1234.50                   │
│ arpu_min_6m         │ DECIMAL(10,2)│ 1000.00                   │
│ arpu_max_6m         │ DECIMAL(10,2)│ 5000.00                   │
│ arpu_growth_rate    │ DECIMAL(10,2)│ -56.70                    │
│ arpu_trend          │ VARCHAR(20)  │ Giảm                      │
│ revenue_call_pct    │ DECIMAL(5,2) │ 15.20                     │
│ revenue_sms_pct     │ DECIMAL(5,2) │ 8.50                      │
│ revenue_data_pct    │ DECIMAL(5,2) │ 76.30                     │
│ user_type           │ VARCHAR(50)  │ Voice/SMS User            │
│ topup_frequency     │ DECIMAL(5,2) │ 2.50                      │
│ topup_avg_amount    │ DECIMAL(10,2)│ 50000.00                  │
│ topup_advance_ratio │ DECIMAL(10,4)│ 0.0200                    │
│ topup_frequency_class│VARCHAR(20)  │ Trung bình                │
│ customer_value_score │ DECIMAL(5,2)│ 70.00                     │
│ advance_readiness_score│DECIMAL(5,2)│90.00                     │
│ priority_score      │ DECIMAL(10,2)│ 63.00                     │
│ recommendation_date │ DATE         │ 2025-10-22                │
│ created_at          │ TIMESTAMP    │ 2025-10-22 10:30:00       │
│ updated_at          │ TIMESTAMP    │ 2025-10-22 10:30:00       │
└──────────────────────┴──────────────┴──────────────────────────┘

Indexes:
  - PRIMARY KEY (id)
  - UNIQUE (isdn)
  - idx_recommendations_service (service_type)
  - idx_recommendations_risk (bad_debt_risk)
  - idx_recommendations_cluster (cluster_group)
  - idx_recommendations_priority (priority_score DESC)
  - idx_service_risk (service_type, bad_debt_risk)
```

**Truy vấn mẫu:**
```sql
-- Lấy recommendation theo ISDN
SELECT * FROM recommendations
WHERE isdn = '++/hZFPrCDRre55vsZqqxQ==';

-- Top 100 EasyCredit theo priority
SELECT isdn, advance_amount, priority_score
FROM recommendations
WHERE service_type = 'EasyCredit'
ORDER BY priority_score DESC
LIMIT 100;

-- Thống kê theo service và risk
SELECT
    service_type,
    bad_debt_risk,
    COUNT(*) as count,
    SUM(advance_amount) as total_advance,
    AVG(customer_value_score) as avg_value
FROM recommendations
GROUP BY service_type, bad_debt_risk;
```

---

### Table 2: subscriber_360_profiles
```sql
Table:      subscriber_360_profiles
Rows:       214,504
Size:       ~107 MB
Indexes:    3 indexes (~15 MB)
```

**Cấu trúc:**
```
┌─────────────────────────────────────────────────────────────────┐
│ subscriber_360_profiles                                          │
├──────────────────────┬──────────────┬──────────────────────────┤
│ Column               │ Type         │ Example                   │
├──────────────────────┼──────────────┼──────────────────────────┤
│ id                   │ BIGSERIAL PK │ 1                         │
│ isdn                 │ VARCHAR(255) │ ++/hZFPrCDRre55vsZqqxQ== │
│ recommendation_id    │ BIGINT FK    │ 1                         │
│ subscriber_type      │ VARCHAR(10)  │ PRE                       │
│ service_type         │ VARCHAR(50)  │ EasyCredit                │
│ advance_amount       │ DECIMAL(12,2)│ 25000.00                  │
│ revenue_per_advance  │ DECIMAL(12,2)│ 7500.00                   │
│ arpu_avg_6m         │ DECIMAL(10,2)│ 2757.50                   │
│ arpu_std_6m         │ DECIMAL(10,2)│ 1234.50                   │
│ arpu_min_6m         │ DECIMAL(10,2)│ 1000.00                   │
│ arpu_max_6m         │ DECIMAL(10,2)│ 5000.00                   │
│ arpu_first_month    │ DECIMAL(10,2)│ 4000.00                   │
│ arpu_last_month     │ DECIMAL(10,2)│ 1500.00                   │
│ arpu_growth_rate    │ DECIMAL(10,2)│ -56.70                    │
│ arpu_trend          │ VARCHAR(20)  │ Giảm                      │
│ revenue_call_pct    │ DECIMAL(5,2) │ 15.20                     │
│ revenue_sms_pct     │ DECIMAL(5,2) │ 8.50                      │
│ revenue_data_pct    │ DECIMAL(5,2) │ 76.30                     │
│ user_type           │ VARCHAR(50)  │ Voice/SMS User            │
│ topup_frequency     │ DECIMAL(5,2) │ 2.50                      │
│ topup_avg_amount    │ DECIMAL(10,2)│ 50000.00                  │
│ topup_min_amount    │ DECIMAL(10,2)│ 20000.00                  │
│ topup_max_amount    │ DECIMAL(10,2)│ 100000.00                 │
│ topup_advance_ratio │ DECIMAL(10,4)│ 0.0200                    │
│ topup_frequency_class│VARCHAR(20)  │ Trung bình                │
│ bad_debt_risk       │ VARCHAR(20)  │ LOW                       │
│ risk_score          │ DECIMAL(5,2) │ 70.00                     │
│ risk_factors        │ JSONB        │ ["Good payment","Stable"] │
│ customer_value_score │ DECIMAL(5,2)│ 70.00                     │
│ advance_readiness_score│DECIMAL(5,2)│90.00                     │
│ revenue_potential   │ DECIMAL(12,2)│ 7500.00                   │
│ cluster_group       │ INTEGER      │ 1                         │
│ cluster_label       │ VARCHAR(100) │ High Value Prepaid        │
│ classification_reason│ TEXT        │ Voice/SMS user based...   │
│ strengths           │ JSONB        │ ["Loyal","Regular topup"] │
│ recommendations_text│ JSONB        │ ["EasyCredit suitable"]   │
│ profile_date        │ DATE         │ 2025-10-22                │
│ created_at          │ TIMESTAMP    │ 2025-10-22 10:30:00       │
│ updated_at          │ TIMESTAMP    │ 2025-10-22 10:30:00       │
└──────────────────────┴──────────────┴──────────────────────────┘

Indexes:
  - PRIMARY KEY (id)
  - UNIQUE (isdn)
  - idx_360_recommendation (recommendation_id)
```

**Truy vấn mẫu:**
```sql
-- Lấy full 360 profile
SELECT * FROM subscriber_360_profiles
WHERE isdn = '++/hZFPrCDRre55vsZqqxQ==';

-- Lấy 360 profile với monthly ARPU
SELECT
    p.*,
    json_agg(
        json_build_object(
            'month', m.data_month,
            'arpu_total', m.arpu_total
        ) ORDER BY m.data_month
    ) as monthly_arpu
FROM subscriber_360_profiles p
LEFT JOIN subscriber_monthly_arpu m ON p.isdn = m.isdn
WHERE p.isdn = '++/hZFPrCDRre55vsZqqxQ=='
GROUP BY p.id;
```

---

### Table 3: subscriber_monthly_arpu
```sql
Table:      subscriber_monthly_arpu
Rows:       1,501,528 (214,504 x 7 months)
Size:       ~75 MB
Indexes:    3 indexes (~35 MB)
```

**Cấu trúc:**
```
┌─────────────────────────────────────────────────────────────────┐
│ subscriber_monthly_arpu                                          │
├──────────────────────┬──────────────┬──────────────────────────┤
│ Column               │ Type         │ Example                   │
├──────────────────────┼──────────────┼──────────────────────────┤
│ id                   │ BIGSERIAL PK │ 1                         │
│ isdn                 │ VARCHAR(255) │ ++/hZFPrCDRre55vsZqqxQ== │
│ data_month           │ VARCHAR(6)   │ 202503                    │
│ arpu_call            │ DECIMAL(10,2)│ 450.50                    │
│ arpu_sms             │ DECIMAL(10,2)│ 230.20                    │
│ arpu_data            │ DECIMAL(10,2)│ 2800.00                   │
│ arpu_total           │ DECIMAL(10,2)│ 3480.70                   │
│ created_at           │ TIMESTAMP    │ 2025-10-22 10:30:00       │
└──────────────────────┴──────────────┴──────────────────────────┘

Indexes:
  - PRIMARY KEY (id)
  - UNIQUE (isdn, data_month)
  - idx_monthly_isdn (isdn)
  - idx_monthly_month (data_month)
```

**Truy vấn mẫu:**
```sql
-- Lấy monthly ARPU của 1 subscriber
SELECT data_month, arpu_call, arpu_sms, arpu_data, arpu_total
FROM subscriber_monthly_arpu
WHERE isdn = '++/hZFPrCDRre55vsZqqxQ=='
ORDER BY data_month;

-- ARPU trung bình theo tháng (all subscribers)
SELECT
    data_month,
    AVG(arpu_total) as avg_arpu,
    COUNT(*) as subscriber_count
FROM subscriber_monthly_arpu
GROUP BY data_month
ORDER BY data_month;
```

---

## 🔍 QUERY PATTERNS - Các Pattern Tra Cứu Phổ Biến

### Pattern 1: Tra cứu khi mời ứng tiền (Real-time)

**Redis (FAST - 2-5ms):**
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
isdn = "++/hZFPrCDRre55vsZqqxQ=="

# Get recommendation
rec = r.hgetall(f"ut360:rec:{isdn}")

if rec and rec.get('bad_debt_risk') == 'LOW':
    print(f"✓ Recommend advance: {rec.get('advance_amount')} VND")
    print(f"  Service: {rec.get('service_type')}")
    print(f"  Expected revenue: {rec.get('revenue_per_advance')} VND")
else:
    print("✗ Not eligible for advance")
```

### Pattern 2: Hiển thị Customer360-VNS Modal

**Redis (FAST - 5-10ms):**
```python
import redis, json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)
isdn = "++/hZFPrCDRre55vsZqqxQ=="

profile = r.hgetall(f"ut360:profile:{isdn}")

# Parse JSON
basic = json.loads(profile['basic'])
kpi_scores = json.loads(profile['kpi_scores'])
monthly_arpu = json.loads(profile['monthly_arpu'])

return {
    'isdn': basic['isdn'],
    'service': basic['service'],
    'advance': basic['advance'],
    'customer_value': kpi_scores['customer_value'],
    'monthly_chart': monthly_arpu  # For ARPU trend chart
}
```

### Pattern 3: Lấy top subscribers cho campaign

**Redis (FAST - 20-50ms):**
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Get top 1000 EasyCredit by priority
top_isdns = r.zrevrange('ut360:idx:service:EasyCredit', 0, 999, withscores=True)

campaign_list = []
for isdn, priority in top_isdns:
    rec = r.hgetall(f"ut360:rec:{isdn}")
    if rec.get('bad_debt_risk') == 'LOW':  # Only LOW risk
        campaign_list.append({
            'isdn': isdn,
            'advance': rec.get('advance_amount'),
            'priority': priority
        })

print(f"Campaign list: {len(campaign_list)} subscribers")
```

### Pattern 4: Analytics & Reporting

**PostgreSQL (POWERFUL - 100-500ms):**
```sql
-- Revenue analysis by service and risk
SELECT
    service_type,
    bad_debt_risk,
    COUNT(*) as subscriber_count,
    SUM(advance_amount) as total_advance,
    SUM(revenue_per_advance) as total_revenue_potential,
    AVG(customer_value_score) as avg_customer_value,
    AVG(advance_readiness_score) as avg_readiness
FROM recommendations
GROUP BY service_type, bad_debt_risk
ORDER BY total_revenue_potential DESC;
```

---

## 📊 MEMORY & STORAGE SUMMARY

### Redis Memory Usage
```
Recommendations:        214,504 × 1.5 KB  = 322 MB
360 Profiles:           214,504 × 4 KB    = 858 MB
Service Indexes:        3 sorted sets     = 30 MB
Risk Indexes:           2 sets            = 10 MB
Cluster Indexes:        4 sets            = 10 MB
Metadata:               1 hash            = <1 MB
──────────────────────────────────────────────────
Total:                                      ~1.2 GB

Recommended: 2GB Redis instance with allkeys-lru policy
```

### PostgreSQL Disk Usage
```
recommendations:           43 MB data + 20 MB indexes  = 63 MB
subscriber_360_profiles:  107 MB data + 15 MB indexes  = 122 MB
subscriber_monthly_arpu:   75 MB data + 35 MB indexes  = 110 MB
──────────────────────────────────────────────────────────────
Total:                                                  ~295 MB

Plus system tables + WAL:                               ~55 MB
──────────────────────────────────────────────────────────────
Total Database Size:                                    ~350 MB
```

---

## 🎯 KEY TAKEAWAYS

### Redis:
- **430,000 keys total**
- **~1.2GB memory**
- **<10ms** query time
- **7-day TTL** auto-refresh
- **Perfect for:** Real-time lookups

### PostgreSQL:
- **3 tables**
- **~1.9M rows**
- **~350MB disk**
- **<50ms** complex queries
- **Perfect for:** Analytics, reporting

### Strategy:
```
Read Path:  Check Redis → If miss, query PostgreSQL → Cache in Redis
Write Path: Update PostgreSQL → Sync to Redis daily
```

---

**Created By:** Claude AI
**Date:** 2025-10-22
**Last Updated:** 2025-10-22
