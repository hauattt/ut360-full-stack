# Simple Sync Guide - Chỉ File typeupdate.csv

**Purpose:** Đồng bộ file `recommendations_final_filtered_typeupdate.csv` vào PostgreSQL và Redis

---

## 📦 FILES CẦN COPY (CHỈ 3 FILES)

```bash
1. scripts/utils/sync_to_postgresql.py  (script sync PostgreSQL)
2. scripts/utils/sync_to_redis.py       (script sync Redis)
3. output/recommendations/recommendations_final_filtered_typeupdate.csv  (data file - 32MB)
```

**Note:** Bạn nói đã có CSV trên server rồi → Chỉ cần copy 2 scripts!

---

## 🚀 DEPLOYMENT ĐƠN GIẢN

### Bước 1: Copy 2 Scripts Lên Server

```bash
# Từ máy local
scp /data/ut360/scripts/utils/sync_to_postgresql.py user@server:/path/to/ut360/scripts/utils/
scp /data/ut360/scripts/utils/sync_to_redis.py user@server:/path/to/ut360/scripts/utils/
```

### Bước 2: Cài Dependencies (1 lần)

```bash
# SSH vào server
ssh user@server

# Install packages
pip3 install pandas psycopg2-binary redis
```

### Bước 3: Chạy Sync

**⚠️ QUAN TRỌNG:** Scripts mong đợi file CSV ở đường dẫn:
```
BASE_DIR/output/recommendations/recommendations_final_filtered_typeupdate.csv
```

Trong đó `BASE_DIR` = thư mục cha của thư mục `scripts/`

**Ví dụ cấu trúc:**
```
/opt/ut360/                                          ← BASE_DIR
├── scripts/
│   └── utils/
│       ├── sync_to_postgresql.py                   ← Script ở đây
│       └── sync_to_redis.py
└── output/
    └── recommendations/
        └── recommendations_final_filtered_typeupdate.csv  ← CSV ở đây
```

**Chạy sync:**
```bash
cd /opt/ut360   # Hoặc thư mục BASE_DIR của bạn

# Sync to PostgreSQL (1-2 phút)
python3 scripts/utils/sync_to_postgresql.py

# Sync to Redis (1 phút)
python3 scripts/utils/sync_to_redis.py
```

**DONE!** 🎉

---

## 📊 SCRIPTS CHỈ DÙNG FILE CSV

### sync_to_postgresql.py
```python
# Chỉ đọc file CSV này:
rec_file = "output/recommendations/recommendations_final_filtered_typeupdate.csv"

# Tạo 1 table:
- recommendations  (214,504 rows với service_type: Fee/Free/Quota)
```

### sync_to_redis.py
```python
# Chỉ đọc file CSV này:
rec_file = "output/recommendations/recommendations_final_filtered_typeupdate.csv"

# Tạo Redis keys:
- ut360:rec:{ISDN}              (214,504 hashes)
- ut360:idx:service:Fee         (sorted set)
- ut360:idx:service:Free        (sorted set)
- ut360:idx:service:Quota       (sorted set)
- ut360:idx:risk:LOW            (set)
- ut360:idx:risk:MEDIUM         (set)
- ut360:meta:stats              (hash)
```

---

## ⚠️ LƯU Ý

### Script Đã Configure Sẵn:

**PostgreSQL (DB01):**
```python
host='10.39.223.102'
port=5432
database='ut360'
user='admin'
password='Vns@2025'
```

**Redis (WEB01):**
```python
host='10.39.223.70'
port=6379
username='redis'
password='098poiA'
```

**→ KHÔNG CẦN SỬA GÌ!** Chỉ cần chạy!

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

## 🎯 TÓM TẮT

Bạn đã có CSV trên server → Chỉ cần:

1. **Copy 2 scripts** lên server
2. **Install 3 packages:** `pip3 install pandas psycopg2-binary redis`
3. **Chạy 2 lệnh:**
   - `python3 scripts/utils/sync_to_postgresql.py`
   - `python3 scripts/utils/sync_to_redis.py`

**Thời gian:** 2-3 phút
**Kết quả:** 214,504 recommendations với service_type mới (Fee/Free/Quota) trong PostgreSQL và Redis

---

## ❓ TROUBLESHOOTING

### Nếu script báo "File not found":

Script tìm file ở: `BASE_DIR/output/recommendations/recommendations_final_filtered_typeupdate.csv`

Trong đó `BASE_DIR` = `scripts/` ở 2 cấp trên.

**Giải pháp:**
1. Đặt CSV đúng vị trí theo cấu trúc trên
2. Hoặc chạy script từ đúng thư mục BASE_DIR

**Ví dụ:**
```bash
# Nếu script ở: /opt/ut360/scripts/utils/sync_to_postgresql.py
# Thì CSV phải ở: /opt/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv
# Và chạy từ: cd /opt/ut360
```

---

**That's it!** Đơn giản vậy thôi 😊
