# ✅ SẴN SÀNG TRIỂN KHAI - READY TO DEPLOY

**Date:** 2025-10-22
**Status:** 🟢 **HOÀN TẤT - ALL READY**

---

## 📦 FILES CẦN COPY LÊN SERVER

### Option 1: Nếu đã có CSV trên server (CHỈ 2 FILES)
```bash
1. scripts/utils/sync_to_postgresql.py    (9KB)
2. scripts/utils/sync_to_redis.py         (12KB)
```

### Option 2: Nếu chưa có CSV trên server (3 FILES)
```bash
1. scripts/utils/sync_to_postgresql.py    (9KB)
2. scripts/utils/sync_to_redis.py         (12KB)
3. output/recommendations/recommendations_final_filtered_typeupdate.csv  (32MB)
```

---

## 🎯 ĐÃ CẤU HÌNH SẴN

### ✅ PostgreSQL (DB01)
```
Host:     10.39.223.102
Port:     5432
Database: ut360
User:     admin
Password: Vns@2025
```

### ✅ Redis (WEB01)
```
Host:     10.39.223.70
Port:     6379
Username: redis
Password: 098poiA
```

### ✅ Service Types Converted
```
EasyCredit   →  Fee     (137,644 rows)
MBFG         →  Free    (46,582 rows)
ungsanluong  →  Quota   (30,278 rows)
                        ──────────────
                Total:  214,504 rows
```

**→ KHÔNG CẦN SỬA GÌ TRONG CODE!** Tất cả đã được cấu hình sẵn!

---

## 🚀 TRIỂN KHAI - 3 BƯỚC ĐƠN GIẢN

### Bước 1: Copy Files Lên Server

```bash
# Từ máy local
scp /data/ut360/scripts/utils/sync_to_postgresql.py user@server:/path/to/ut360/scripts/utils/
scp /data/ut360/scripts/utils/sync_to_redis.py user@server:/path/to/ut360/scripts/utils/

# Nếu chưa có CSV trên server
scp /data/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv \
    user@server:/path/to/ut360/output/recommendations/
```

### Bước 2: Cài Dependencies (1 lần)

```bash
# SSH vào server
ssh user@server

# Install packages
pip3 install pandas psycopg2-binary redis
```

### Bước 3: Chạy Sync

```bash
cd /path/to/ut360   # Thư mục chứa scripts/ và output/

# Sync to PostgreSQL (1-2 phút)
python3 scripts/utils/sync_to_postgresql.py

# Sync to Redis (1 phút)
python3 scripts/utils/sync_to_redis.py
```

**DONE!** 🎉

---

## 📊 KẾT QUẢ SAU KHI CHẠY

### PostgreSQL
```sql
-- Table: recommendations (214,504 rows)
SELECT service_type, COUNT(*)
FROM recommendations
GROUP BY service_type;

-- Kết quả mong đợi:
-- Fee    | 137644
-- Free   | 46582
-- Quota  | 30278
```

### Redis
```bash
# Tổng số subscribers
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis \
  HGET ut360:meta:stats total_subscribers

# Kết quả mong đợi: "214504"
```

---

## 🔍 CẤU TRÚC THư MỤC YÊU CẦU

**QUAN TRỌNG:** Scripts mong đợi cấu trúc như sau:

```
/path/to/ut360/                           ← BASE_DIR (chạy từ đây)
├── scripts/
│   └── utils/
│       ├── sync_to_postgresql.py         ← Script 1
│       └── sync_to_redis.py              ← Script 2
└── output/
    └── recommendations/
        └── recommendations_final_filtered_typeupdate.csv  ← Data file
```

**Ví dụ cụ thể:**
```bash
# Nếu scripts ở: /opt/ut360/scripts/utils/sync_to_postgresql.py
# Thì CSV phải ở: /opt/ut360/output/recommendations/recommendations_final_filtered_typeupdate.csv
# Và chạy từ:    cd /opt/ut360
```

---

## ✅ VERIFY CONNECTION TRƯỚC KHI SYNC

Có thể test connection trước:

```bash
# Test PostgreSQL
psql -h 10.39.223.102 -U admin -d ut360 -c "SELECT version();"

# Test Redis
redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis PING
```

---

## 📚 TÀI LIỆU THAM KHẢO

### Deployment Guides
1. **[SIMPLE_SYNC_GUIDE.md](SIMPLE_SYNC_GUIDE.md)** - Hướng dẫn chi tiết sync CSV
2. **[SYNC_TO_PRODUCTION_README.md](SYNC_TO_PRODUCTION_README.md)** - Hướng dẫn sync production
3. **[REDIS_POSTGRES_SUMMARY.md](REDIS_POSTGRES_SUMMARY.md)** - Tổng quan Redis & PostgreSQL

### Technical Documentation
4. **[REDIS_POSTGRES_DESIGN.md](REDIS_POSTGRES_DESIGN.md)** - Chi tiết schema design
5. **[REDIS_POSTGRES_QUERY_EXAMPLES.md](REDIS_POSTGRES_QUERY_EXAMPLES.md)** - Ví dụ query
6. **[DATABASE_STRUCTURE_VISUAL.md](DATABASE_STRUCTURE_VISUAL.md)** - Cấu trúc database

### Service Type Update
7. **[SERVICE_TYPE_UPDATE_SUMMARY.md](SERVICE_TYPE_UPDATE_SUMMARY.md)** - Chi tiết chuyển đổi service_type

---

## ⚠️ TROUBLESHOOTING

### Lỗi: "File not found"
```
Nguyên nhân: Script tìm file ở BASE_DIR/output/recommendations/
Giải pháp:
  1. Đặt CSV đúng vị trí theo cấu trúc trên
  2. Chạy script từ đúng thư mục BASE_DIR (cd /path/to/ut360)
```

### Lỗi: "Connection refused" (PostgreSQL)
```
Nguyên nhân: Không kết nối được DB01
Giải pháp:
  1. Kiểm tra IP có đúng: 10.39.223.102
  2. Kiểm tra firewall/security group
  3. Test: psql -h 10.39.223.102 -U admin -d ut360
```

### Lỗi: "Connection refused" (Redis)
```
Nguyên nhân: Không kết nối được WEB01
Giải pháp:
  1. Kiểm tra IP có đúng: 10.39.223.70
  2. Kiểm tra Redis đang chạy
  3. Test: redis-cli -h 10.39.223.70 -p 6379 -a 098poiA --user redis PING
```

### Lỗi: "Permission denied"
```
Nguyên nhân: User không có quyền ghi
Giải pháp:
  PostgreSQL: Kiểm tra user 'admin' có quyền CREATE TABLE
  Redis: Kiểm tra user 'redis' có quyền ghi
```

---

## 🎯 THỜI GIAN DỰ KIẾN

| Bước | Thời gian |
|------|-----------|
| Copy files lên server | 1 phút |
| Install dependencies | 2 phút |
| Sync to PostgreSQL | 1-2 phút |
| Sync to Redis | 1 phút |
| **TỔNG** | **5-6 phút** |

---

## 📝 CHECKLIST

- [ ] Copy 2 scripts lên server
- [ ] Copy CSV file lên server (nếu chưa có)
- [ ] Verify cấu trúc thư mục đúng
- [ ] Install dependencies: `pip3 install pandas psycopg2-binary redis`
- [ ] Test connection PostgreSQL
- [ ] Test connection Redis
- [ ] Chạy `python3 scripts/utils/sync_to_postgresql.py`
- [ ] Chạy `python3 scripts/utils/sync_to_redis.py`
- [ ] Verify PostgreSQL: `SELECT COUNT(*) FROM recommendations`
- [ ] Verify Redis: `HGET ut360:meta:stats total_subscribers`

---

## 🎉 KẾT QUẢ CUỐI CÙNG

Sau khi hoàn thành:
- ✅ PostgreSQL có 214,504 recommendations với service_type mới (Fee/Free/Quota)
- ✅ Redis có 214,504 keys để tra cứu nhanh (<10ms)
- ✅ Sẵn sàng cho hệ thống Customer360-VNS tra cứu khi cần mời ứng tiền

---

**Status:** 🟢 **HOÀN TOÀN SẴN SÀNG TRIỂN KHAI**

**Prepared By:** Claude AI
**Date:** 2025-10-22
**Version:** Final - Production Ready
