# Redis & PostgreSQL Schema Design for UT360 Recommendations

**Date:** 2025-10-22
**Purpose:** Thiết kế schema tối ưu cho việc đồng bộ và truy vấn recommendation data

---

## 1. USE CASES - Các Trường Hợp Sử Dụng

### Use Case 1: Tra cứu theo ISDN (Phổ biến nhất)
```
Input: ISDN của thuê bao
Output: Thông tin recommendation đầy đủ (service, amount, revenue, risk, etc.)
```
**Frequency:** Rất cao - mỗi khi có request ứng tiền
**Performance Requirement:** < 10ms

### Use Case 2: Lấy danh sách theo Service Type
```
Input: Service type (EasyCredit, MBFG, ungsanluong)
Output: Danh sách tất cả recommendations cho service đó
```
**Frequency:** Trung bình - cho reporting/analytics
**Performance Requirement:** < 100ms

### Use Case 3: Lấy danh sách theo Risk Level
```
Input: Risk level (LOW, MEDIUM)
Output: Danh sách subscribers với risk level đó
```
**Frequency:** Thấp - cho risk management
**Performance Requirement:** < 500ms

### Use Case 4: Tìm kiếm theo Cluster/Segment
```
Input: Cluster ID
Output: Danh sách subscribers trong cluster đó
```
**Frequency:** Thấp - cho analysis
**Performance Requirement:** < 1s

### Use Case 5: Lấy 360 Profile
```
Input: ISDN
Output: Complete 360 profile (ARPU history, scores, metrics)
```
**Frequency:** Cao - cho Customer360-VNS modal
**Performance Requirement:** < 50ms

### Use Case 6: Bulk lookup cho campaign
```
Input: Danh sách ISDNs (1000-10000)
Output: Recommendations cho tất cả ISDNs
```
**Frequency:** Thấp - cho marketing campaigns
**Performance Requirement:** < 5s

---

## 2. REDIS DESIGN - Optimized for Speed

Redis được dùng cho **hot data** - data được truy cập thường xuyên, cần tốc độ cao.

### 2.1. Key Naming Convention

```
Pattern: {namespace}:{entity}:{identifier}
```

**Namespaces:**
- `ut360:rec` - Recommendations
- `ut360:profile` - 360 Profiles
- `ut360:idx` - Indexes (for quick lookup)
- `ut360:meta` - Metadata

### 2.2. Redis Data Structures

#### A. Recommendation by ISDN (Hash)
**Use Case:** Tra cứu nhanh recommendation theo ISDN

```redis
Key:   ut360:rec:{ISDN}
Type:  Hash
TTL:   7 days (refresh weekly)

Fields:
  isdn                    → Encrypted ISDN
  subscriber_type         → PRE/POS
  service_type            → EasyCredit/MBFG/ungsanluong
  advance_amount          → 25000
  revenue_per_advance     → 7500
  cluster_group           → 1
  bad_debt_risk           → LOW
  arpu_avg_6m            → 2757.50
  arpu_growth_rate       → -56.7
  arpu_trend             → Giảm
  customer_value_score   → 70
  advance_readiness_score → 90
  recommendation_date    → 2025-10-22
  priority               → HIGH/MEDIUM/LOW
```

**Example:**
```redis
HSET ut360:rec:++/hZFPrCDRre55vsZqqxQ== isdn "++/hZFPrCDRre55vsZqqxQ=="
HSET ut360:rec:++/hZFPrCDRre55vsZqqxQ== service_type "EasyCredit"
HSET ut360:rec:++/hZFPrCDRre55vsZqqxQ== advance_amount "25000"
...
```

**Query Example:**
```redis
# Get full recommendation
HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==

# Get specific field
HGET ut360:rec:++/hZFPrCDRre55vsZqqxQ== advance_amount
```

---

#### B. 360 Profile by ISDN (Hash + JSON)
**Use Case:** Lấy toàn bộ 360 profile cho modal

```redis
Key:   ut360:profile:{ISDN}
Type:  Hash with JSON fields
TTL:   7 days

Fields:
  basic              → JSON: {isdn, type, service, advance, revenue}
  arpu_stats         → JSON: {avg, std, min, max, growth_rate, trend}
  revenue_breakdown  → JSON: {call_pct, sms_pct, data_pct, user_type}
  topup_behavior     → JSON: {frequency, avg_amount, ratio, frequency_class}
  risk_assessment    → JSON: {level, score, factors[]}
  kpi_scores         → JSON: {customer_value, advance_readiness, revenue_potential}
  monthly_arpu       → JSON: [{month, arpu_call, arpu_sms, arpu_data, arpu_total}, ...]
  insights           → JSON: {classification_reason, strengths[], recommendations[]}
  updated_at         → timestamp
```

**Example:**
```redis
HSET ut360:profile:++/hZFPrCDRre55vsZqqxQ== basic '{"isdn":"++/hZFPrCDRre55vsZqqxQ==","type":"PRE","service":"EasyCredit","advance":25000,"revenue":7500}'
HSET ut360:profile:++/hZFPrCDRre55vsZqqxQ== arpu_stats '{"avg":2757.5,"std":1234.5,"min":1000,"max":5000,"growth_rate":-56.7,"trend":"Giảm"}'
HSET ut360:profile:++/hZFPrCDRre55vsZqqxQ== monthly_arpu '[{"month":"202503","arpu_total":3500},{"month":"202504","arpu_total":2800}...]'
```

**Query Example:**
```redis
# Get full profile
HGETALL ut360:profile:++/hZFPrCDRre55vsZqqxQ==

# Get specific section
HGET ut360:profile:++/hZFPrCDRre55vsZqqxQ== kpi_scores
```

---

#### C. Index by Service Type (Sorted Set)
**Use Case:** Lấy danh sách subscribers theo service, sorted by priority

```redis
Key:   ut360:idx:service:{service_type}
Type:  Sorted Set
Score: Priority score (customer_value_score * advance_readiness_score / 10000)

Members: ISDN

Example:
  ut360:idx:service:EasyCredit
  ut360:idx:service:MBFG
  ut360:idx:service:ungsanluong
```

**Example:**
```redis
# Add to index (score = customer_value * advance_readiness / 10000)
ZADD ut360:idx:service:EasyCredit 6.3 "++/hZFPrCDRre55vsZqqxQ=="  # 70*90/10000
ZADD ut360:idx:service:EasyCredit 8.1 "another_isdn"

# Get top 100 by priority (descending)
ZREVRANGE ut360:idx:service:EasyCredit 0 99 WITHSCORES

# Get count
ZCARD ut360:idx:service:EasyCredit
```

---

#### D. Index by Risk Level (Set)
**Use Case:** Lấy danh sách subscribers theo risk level

```redis
Key:   ut360:idx:risk:{risk_level}
Type:  Set

Examples:
  ut360:idx:risk:LOW      → Set of ISDNs with LOW risk
  ut360:idx:risk:MEDIUM   → Set of ISDNs with MEDIUM risk
```

**Example:**
```redis
# Add to risk set
SADD ut360:idx:risk:LOW "++/hZFPrCDRre55vsZqqxQ=="

# Get all LOW risk subscribers
SMEMBERS ut360:idx:risk:LOW

# Get count
SCARD ut360:idx:risk:LOW

# Check if ISDN is in set
SISMEMBER ut360:idx:risk:LOW "++/hZFPrCDRre55vsZqqxQ=="
```

---

#### E. Index by Cluster (Set)
**Use Case:** Lấy subscribers trong cluster

```redis
Key:   ut360:idx:cluster:{cluster_id}
Type:  Set

Examples:
  ut360:idx:cluster:0
  ut360:idx:cluster:1
  ut360:idx:cluster:2
  ut360:idx:cluster:3
```

**Example:**
```redis
SADD ut360:idx:cluster:1 "++/hZFPrCDRre55vsZqqxQ=="
SMEMBERS ut360:idx:cluster:1
```

---

#### F. Metadata (Hash)
**Use Case:** Lưu metadata về dataset

```redis
Key:   ut360:meta:stats
Type:  Hash

Fields:
  total_subscribers       → 214504
  total_easycredit       → 142000
  total_mbfg             → 45000
  total_ungsanluong      → 27504
  total_low_risk         → 180000
  total_medium_risk      → 34504
  avg_advance_amount     → 28500
  total_revenue_potential → 1260000000
  last_updated           → 2025-10-22T10:30:00
  data_version           → v1.0
```

---

#### G. Bulk Lookup Cache (String - JSON Array)
**Use Case:** Cache kết quả bulk lookup

```redis
Key:   ut360:bulk:{hash_of_isdn_list}
Type:  String (JSON array)
TTL:   1 hour

Value: JSON array of recommendations
```

---

### 2.3. Redis Memory Estimation

**Per Recommendation (Hash):**
- Key: ~50 bytes
- Fields: ~15 fields * 100 bytes = 1,500 bytes
- **Total per rec:** ~1.5 KB

**Per 360 Profile (Hash with JSON):**
- Key: ~50 bytes
- Fields: ~8 JSON fields * 500 bytes = 4,000 bytes
- **Total per profile:** ~4 KB

**Total for 214,504 subscribers:**
- Recommendations: 214,504 * 1.5 KB = ~322 MB
- 360 Profiles: 214,504 * 4 KB = ~858 MB
- Indexes: ~50 MB
- **Total:** ~1.2 GB RAM

**Recommendation:** Use 2GB Redis instance với maxmemory-policy: allkeys-lru

---

## 3. POSTGRESQL DESIGN - Optimized for Complex Queries

PostgreSQL được dùng cho **cold storage** và complex analytics.

### 3.1. Database Schema

#### Table 1: recommendations
**Purpose:** Main recommendations table

```sql
CREATE TABLE recommendations (
    id BIGSERIAL PRIMARY KEY,

    -- Subscriber Info
    isdn VARCHAR(255) NOT NULL UNIQUE,
    subscriber_type VARCHAR(10) NOT NULL,  -- PRE/POS

    -- Recommendation
    service_type VARCHAR(50) NOT NULL,     -- EasyCredit, MBFG, ungsanluong
    advance_amount DECIMAL(12,2) NOT NULL,
    revenue_per_advance DECIMAL(12,2) NOT NULL,

    -- Clustering
    cluster_group INTEGER,

    -- Risk
    bad_debt_risk VARCHAR(20) NOT NULL,    -- LOW, MEDIUM, HIGH

    -- ARPU Stats
    arpu_avg_6m DECIMAL(10,2),
    arpu_std_6m DECIMAL(10,2),
    arpu_min_6m DECIMAL(10,2),
    arpu_max_6m DECIMAL(10,2),
    arpu_growth_rate DECIMAL(10,2),
    arpu_trend VARCHAR(20),                -- Tăng trưởng, Ổn định, Giảm

    -- Revenue Breakdown
    revenue_call_pct DECIMAL(5,2),
    revenue_sms_pct DECIMAL(5,2),
    revenue_data_pct DECIMAL(5,2),
    user_type VARCHAR(50),                 -- Heavy Data User, Voice/SMS User, Balanced

    -- Topup Behavior
    topup_frequency DECIMAL(5,2),
    topup_avg_amount DECIMAL(10,2),
    topup_advance_ratio DECIMAL(10,4),
    topup_frequency_class VARCHAR(20),     -- Cao, Trung bình, Thấp

    -- Scores
    customer_value_score DECIMAL(5,2),
    advance_readiness_score DECIMAL(5,2),

    -- Priority
    priority_score DECIMAL(10,2),          -- customer_value * advance_readiness / 100

    -- Metadata
    recommendation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT chk_subscriber_type CHECK (subscriber_type IN ('PRE', 'POS')),
    CONSTRAINT chk_service_type CHECK (service_type IN ('EasyCredit', 'MBFG', 'ungsanluong')),
    CONSTRAINT chk_risk CHECK (bad_debt_risk IN ('LOW', 'MEDIUM', 'HIGH'))
);

-- Indexes for fast queries
CREATE INDEX idx_recommendations_isdn ON recommendations(isdn);
CREATE INDEX idx_recommendations_service ON recommendations(service_type);
CREATE INDEX idx_recommendations_risk ON recommendations(bad_debt_risk);
CREATE INDEX idx_recommendations_cluster ON recommendations(cluster_group);
CREATE INDEX idx_recommendations_priority ON recommendations(priority_score DESC);
CREATE INDEX idx_recommendations_subscriber_type ON recommendations(subscriber_type);
CREATE INDEX idx_recommendations_date ON recommendations(recommendation_date);

-- Composite index for common queries
CREATE INDEX idx_service_risk ON recommendations(service_type, bad_debt_risk);
CREATE INDEX idx_service_priority ON recommendations(service_type, priority_score DESC);
```

---

#### Table 2: subscriber_360_profiles
**Purpose:** Complete 360 profile data

```sql
CREATE TABLE subscriber_360_profiles (
    id BIGSERIAL PRIMARY KEY,
    isdn VARCHAR(255) NOT NULL UNIQUE,

    -- Link to recommendation
    recommendation_id BIGINT REFERENCES recommendations(id),

    -- Basic Info
    subscriber_type VARCHAR(10) NOT NULL,
    service_type VARCHAR(50),
    advance_amount DECIMAL(12,2),
    revenue_per_advance DECIMAL(12,2),

    -- ARPU Statistics (detailed)
    arpu_avg_6m DECIMAL(10,2),
    arpu_std_6m DECIMAL(10,2),
    arpu_min_6m DECIMAL(10,2),
    arpu_max_6m DECIMAL(10,2),
    arpu_first_month DECIMAL(10,2),
    arpu_last_month DECIMAL(10,2),
    arpu_growth_rate DECIMAL(10,2),
    arpu_trend VARCHAR(20),

    -- Revenue Breakdown
    revenue_call_pct DECIMAL(5,2),
    revenue_sms_pct DECIMAL(5,2),
    revenue_data_pct DECIMAL(5,2),
    user_type VARCHAR(50),

    -- Topup Behavior
    topup_frequency DECIMAL(5,2),
    topup_avg_amount DECIMAL(10,2),
    topup_min_amount DECIMAL(10,2),
    topup_max_amount DECIMAL(10,2),
    topup_advance_ratio DECIMAL(10,4),
    topup_frequency_class VARCHAR(20),

    -- Risk Assessment
    bad_debt_risk VARCHAR(20),
    risk_score DECIMAL(5,2),
    risk_factors JSONB,                    -- Array of risk factors

    -- KPI Scores
    customer_value_score DECIMAL(5,2),
    advance_readiness_score DECIMAL(5,2),
    revenue_potential DECIMAL(12,2),

    -- Clustering
    cluster_group INTEGER,
    cluster_label VARCHAR(100),

    -- Insights (stored as JSON)
    classification_reason TEXT,
    strengths JSONB,                       -- Array of strengths
    recommendations_text JSONB,            -- Array of recommendations

    -- Metadata
    profile_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_360_isdn ON subscriber_360_profiles(isdn);
CREATE INDEX idx_360_recommendation ON subscriber_360_profiles(recommendation_id);
CREATE INDEX idx_360_cluster ON subscriber_360_profiles(cluster_group);
```

---

#### Table 3: subscriber_monthly_arpu
**Purpose:** Monthly ARPU history for trend analysis

```sql
CREATE TABLE subscriber_monthly_arpu (
    id BIGSERIAL PRIMARY KEY,
    isdn VARCHAR(255) NOT NULL,
    data_month VARCHAR(6) NOT NULL,        -- YYYYMM format

    arpu_call DECIMAL(10,2),
    arpu_sms DECIMAL(10,2),
    arpu_data DECIMAL(10,2),
    arpu_total DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(isdn, data_month)
);

CREATE INDEX idx_monthly_isdn ON subscriber_monthly_arpu(isdn);
CREATE INDEX idx_monthly_month ON subscriber_monthly_arpu(data_month);
CREATE INDEX idx_monthly_isdn_month ON subscriber_monthly_arpu(isdn, data_month);
```

---

#### Table 4: recommendation_stats
**Purpose:** Aggregated statistics by service/risk/cluster

```sql
CREATE TABLE recommendation_stats (
    id SERIAL PRIMARY KEY,

    -- Dimension
    dimension_type VARCHAR(50) NOT NULL,   -- service, risk, cluster, date
    dimension_value VARCHAR(100) NOT NULL,

    -- Metrics
    total_count INTEGER,
    total_advance_amount DECIMAL(15,2),
    total_revenue_potential DECIMAL(15,2),
    avg_customer_value_score DECIMAL(5,2),
    avg_advance_readiness_score DECIMAL(5,2),

    -- Date
    stats_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(dimension_type, dimension_value, stats_date)
);

CREATE INDEX idx_stats_dimension ON recommendation_stats(dimension_type, dimension_value);
CREATE INDEX idx_stats_date ON recommendation_stats(stats_date);
```

---

### 3.2. PostgreSQL Storage Estimation

**recommendations table:**
- ~200 bytes per row
- 214,504 rows
- **Total:** ~43 MB

**subscriber_360_profiles table:**
- ~500 bytes per row
- 214,504 rows
- **Total:** ~107 MB

**subscriber_monthly_arpu table:**
- ~50 bytes per row
- 214,504 * 7 months = 1,501,528 rows
- **Total:** ~75 MB

**recommendation_stats table:**
- ~100 bytes per row
- ~50 rows (aggregated)
- **Total:** <1 MB

**Total Database Size:** ~250 MB (+ indexes ~100 MB) = **~350 MB**

---

## 4. DATA SYNC STRATEGY

### Strategy 1: Redis as Cache Layer (Recommended)

```
PostgreSQL (Source of Truth)
     ↓
  Redis (Cache)
     ↓
  API (Read from Redis, fallback to PostgreSQL)
```

**Workflow:**
1. Load data into PostgreSQL first
2. Populate Redis from PostgreSQL
3. API reads from Redis (fast)
4. If Redis misses, query PostgreSQL and cache result
5. Periodic refresh (daily/weekly)

---

### Strategy 2: Dual Write

```
Data Source
     ↓
  ┌──────┬──────┐
  ↓      ↓      ↓
Redis  PostgreSQL
```

**Workflow:**
1. Write to both Redis and PostgreSQL simultaneously
2. Redis for fast reads
3. PostgreSQL for analytics and backup

---

## 5. QUERY PATTERNS

### Pattern 1: Get recommendation by ISDN (Redis)
```redis
HGETALL ut360:rec:++/hZFPrCDRre55vsZqqxQ==
```
**Performance:** <5ms

### Pattern 2: Get recommendation by ISDN (PostgreSQL)
```sql
SELECT * FROM recommendations WHERE isdn = '++/hZFPrCDRre55vsZqqxQ==';
```
**Performance:** <10ms (with index)

### Pattern 3: Get top 100 EasyCredit by priority (Redis)
```redis
ZREVRANGE ut360:idx:service:EasyCredit 0 99
# Then get details for each ISDN
```
**Performance:** <20ms

### Pattern 4: Get top 100 EasyCredit by priority (PostgreSQL)
```sql
SELECT * FROM recommendations
WHERE service_type = 'EasyCredit'
ORDER BY priority_score DESC
LIMIT 100;
```
**Performance:** <50ms

### Pattern 5: Get 360 profile (Redis)
```redis
HGETALL ut360:profile:++/hZFPrCDRre55vsZqqxQ==
```
**Performance:** <10ms

### Pattern 6: Get 360 profile (PostgreSQL)
```sql
SELECT p.*,
       json_agg(m ORDER BY m.data_month) as monthly_arpu
FROM subscriber_360_profiles p
LEFT JOIN subscriber_monthly_arpu m ON p.isdn = m.isdn
WHERE p.isdn = '++/hZFPrCDRre55vsZqqxQ=='
GROUP BY p.id;
```
**Performance:** <30ms

### Pattern 7: Analytics - Revenue by service
```sql
SELECT
    service_type,
    COUNT(*) as total_count,
    SUM(advance_amount) as total_advance,
    SUM(revenue_per_advance) as total_revenue,
    AVG(customer_value_score) as avg_value_score
FROM recommendations
GROUP BY service_type;
```

### Pattern 8: Risk distribution
```sql
SELECT
    service_type,
    bad_debt_risk,
    COUNT(*) as count,
    AVG(advance_amount) as avg_advance
FROM recommendations
GROUP BY service_type, bad_debt_risk
ORDER BY service_type, bad_debt_risk;
```

---

## 6. RECOMMENDED ARCHITECTURE

```
┌─────────────────────────────────────────────────────────┐
│                    Data Pipeline                         │
│  (Parquet files → CSV → Python scripts)                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL (Source of Truth)                │
│  - recommendations (214K rows)                           │
│  - subscriber_360_profiles (214K rows)                   │
│  - subscriber_monthly_arpu (1.5M rows)                   │
│  - recommendation_stats (aggregate)                      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ (Sync every 6 hours or daily)
┌─────────────────────────────────────────────────────────┐
│              Redis (Hot Cache - 2GB)                     │
│  - ut360:rec:{ISDN} - Recommendations (322MB)            │
│  - ut360:profile:{ISDN} - 360 Profiles (858MB)           │
│  - ut360:idx:service:{type} - Service indexes            │
│  - ut360:idx:risk:{level} - Risk indexes                 │
│  - ut360:idx:cluster:{id} - Cluster indexes              │
│  - TTL: 7 days, refresh weekly                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  - Check Redis first (fast path)                         │
│  - Fallback to PostgreSQL (if cache miss)                │
│  - Update Redis on cache miss                            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│              Frontend (React)                            │
│  - Customer360-VNS modal                                 │
│  - Subscriber list with pagination                       │
│  - Analytics dashboards                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 7. ADVANTAGES OF THIS DESIGN

### Redis Advantages:
✅ **Ultra-fast lookups** - <10ms for ISDN lookup
✅ **Efficient indexing** - Sorted sets for priority, Sets for categories
✅ **Low latency** - Perfect for real-time recommendation serving
✅ **Built-in TTL** - Auto-expire old data
✅ **Atomic operations** - HGETALL returns full record in one call

### PostgreSQL Advantages:
✅ **ACID compliance** - Data integrity guaranteed
✅ **Complex queries** - JOIN, GROUP BY, aggregations
✅ **Analytics** - Generate reports and statistics
✅ **Backup & Recovery** - Full backup capabilities
✅ **Historical data** - Store monthly ARPU trends
✅ **JSONB support** - Flexible schema for insights/recommendations

### Combined:
✅ **Best of both worlds** - Speed + Reliability
✅ **Scalable** - Redis for reads, PostgreSQL for writes
✅ **Cost-effective** - Only cache hot data in Redis
✅ **Maintainable** - Clear separation of concerns

---

## 8. NEXT STEPS

1. ✅ Review this design
2. ⏳ Create PostgreSQL schema (DDL scripts)
3. ⏳ Create data sync script (Parquet → PostgreSQL)
4. ⏳ Create Redis sync script (PostgreSQL → Redis)
5. ⏳ Update FastAPI to use Redis + PostgreSQL
6. ⏳ Test performance benchmarks
7. ⏳ Document query examples

---

**Designed By:** Claude AI
**Date:** 2025-10-22
**Status:** Design Complete - Ready for Implementation
