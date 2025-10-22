# 📚 UT360 Documentation Index

**Last Updated:** 2025-10-22
**Total Documents:** 21 files (~225KB)

---

## 🚀 START HERE - Quick Navigation

### For Immediate Deployment
1. **[READY_TO_DEPLOY.md](READY_TO_DEPLOY.md)** (6.5KB) ⭐ **READ THIS FIRST!**
   - 3-step deployment guide
   - Pre-configured for DB01 & WEB01
   - Complete checklist

2. **[DEPLOYMENT_SUMMARY.txt](DEPLOYMENT_SUMMARY.txt)** (4.2KB)
   - Quick visual summary
   - Files needed
   - Expected results

3. **[SIMPLE_SYNC_GUIDE.md](SIMPLE_SYNC_GUIDE.md)** (4.4KB)
   - Sync CSV to PostgreSQL & Redis
   - Simple instructions
   - Troubleshooting

---

## 📖 Documentation by Category

### 🎯 Deployment Guides (For Production Use)

| Document | Size | Purpose |
|----------|------|---------|
| **[READY_TO_DEPLOY.md](READY_TO_DEPLOY.md)** ⭐ | 6.5KB | **Main deployment guide - Start here** |
| [DEPLOYMENT_SUMMARY.txt](DEPLOYMENT_SUMMARY.txt) | 4.2KB | Visual deployment summary |
| [SIMPLE_SYNC_GUIDE.md](SIMPLE_SYNC_GUIDE.md) | 4.4KB | Simple CSV sync guide |
| [SYNC_TO_PRODUCTION_README.md](SYNC_TO_PRODUCTION_README.md) | 5.5KB | Production sync instructions |
| [DEPLOYMENT_TO_SERVER.md](DEPLOYMENT_TO_SERVER.md) | 12KB | Detailed server deployment |
| [FINAL_DEPLOYMENT_CHECKLIST.md](FINAL_DEPLOYMENT_CHECKLIST.md) | 7.9KB | Complete deployment checklist |

**Use Case:** Triển khai lên server production với DB01 (PostgreSQL) và WEB01 (Redis)

---

### 🗄️ Database & Redis Integration

| Document | Size | Purpose |
|----------|------|---------|
| **[REDIS_POSTGRES_SUMMARY.md](REDIS_POSTGRES_SUMMARY.md)** ⭐ | 15KB | **Complete Redis & PostgreSQL overview** |
| [REDIS_POSTGRES_DESIGN.md](REDIS_POSTGRES_DESIGN.md) | 22KB | Detailed schema design |
| [REDIS_POSTGRES_QUERY_EXAMPLES.md](REDIS_POSTGRES_QUERY_EXAMPLES.md) | 18KB | 50+ query examples |
| [REDIS_POSTGRES_QUICK_START.md](REDIS_POSTGRES_QUICK_START.md) | 11KB | Quick setup guide (20 min) |
| [REDIS_POSTGRES_DATA_EXAMPLES.md](REDIS_POSTGRES_DATA_EXAMPLES.md) | 20KB | Sample data and structures |
| [DATABASE_STRUCTURE_VISUAL.md](DATABASE_STRUCTURE_VISUAL.md) | 24KB | Visual database structure |

**Use Case:** Hiểu cấu trúc database, viết query, tối ưu performance

---

### 🔄 Service Type Conversion

| Document | Size | Purpose |
|----------|------|---------|
| **[SERVICE_TYPE_UPDATE_SUMMARY.md](SERVICE_TYPE_UPDATE_SUMMARY.md)** ⭐ | 8.3KB | **Service type conversion details** |

**Details:** EasyCredit → Fee, MBFG → Free, ungsanluong → Quota

---

### 🧹 Project Cleanup & Organization

| Document | Size | Purpose |
|----------|------|---------|
| [CLEANUP_ANALYSIS.md](CLEANUP_ANALYSIS.md) | 15KB | Analysis of files to keep/backup |
| [CLEANUP_REPORT.md](CLEANUP_REPORT.md) | 13KB | Cleanup execution report |
| [PRODUCTION_FILES_LIST.md](PRODUCTION_FILES_LIST.md) | 12KB | List of production files |
| [DEPLOYMENT_READY_SUMMARY.md](DEPLOYMENT_READY_SUMMARY.md) | 11KB | Deployment readiness summary |

**Use Case:** Hiểu cấu trúc project, files nào cần thiết cho production

---

### 📋 General Documentation

| Document | Size | Purpose |
|----------|------|---------|
| [README.md](README.md) | 6.3KB | Project overview |
| [QUICK_START.md](QUICK_START.md) | 1.9KB | Quick start guide |
| [PIPELINE_FLOW_DOCUMENTATION.md](PIPELINE_FLOW_DOCUMENTATION.md) | 8.7KB | Pipeline flow explanation |
| [COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md) | 5.4KB | Complete project summary |

---

## 🎯 Common Use Cases

### Use Case 1: Triển khai lên server lần đầu
**Path:** → **[READY_TO_DEPLOY.md](READY_TO_DEPLOY.md)** → [SIMPLE_SYNC_GUIDE.md](SIMPLE_SYNC_GUIDE.md)

**Time:** 5-6 minutes
**Steps:**
1. Copy 2 sync scripts to server
2. Install dependencies
3. Run sync commands

---

### Use Case 2: Hiểu schema để viết query
**Path:** → **[REDIS_POSTGRES_SUMMARY.md](REDIS_POSTGRES_SUMMARY.md)** → [REDIS_POSTGRES_QUERY_EXAMPLES.md](REDIS_POSTGRES_QUERY_EXAMPLES.md)

**Coverage:**
- Redis key patterns (5 types)
- PostgreSQL tables (3 tables)
- 50+ query examples
- Performance benchmarks

---

### Use Case 3: Troubleshooting deployment issues
**Path:** → [READY_TO_DEPLOY.md](READY_TO_DEPLOY.md) (Troubleshooting section) → [SYNC_TO_PRODUCTION_README.md](SYNC_TO_PRODUCTION_README.md)

**Common Issues:**
- File not found
- Connection refused
- Permission denied
- Wrong directory structure

---

### Use Case 4: Hiểu chuyển đổi service_type
**Path:** → **[SERVICE_TYPE_UPDATE_SUMMARY.md](SERVICE_TYPE_UPDATE_SUMMARY.md)**

**Details:**
- Mapping: EasyCredit/MBFG/ungsanluong → Fee/Free/Quota
- Distribution: 214,504 rows
- Files updated: 4 scripts + backend

---

### Use Case 5: Setup database từ đầu
**Path:** → [REDIS_POSTGRES_QUICK_START.md](REDIS_POSTGRES_QUICK_START.md) → [DATABASE_STRUCTURE_VISUAL.md](DATABASE_STRUCTURE_VISUAL.md)

**Time:** 20 minutes
**Steps:**
1. Install Redis & PostgreSQL
2. Create database and user
3. Run sync scripts
4. Verify data

---

## 📊 Data Summary

### Recommendations Data
```
Total: 214,504 rows (32MB CSV)
├── Fee:   137,644 (64%)  - EasyCredit
├── Free:   46,582 (22%)  - MBFG
└── Quota:  30,278 (14%)  - ungsanluong
```

### PostgreSQL
```
Tables: 3
Rows:   214,504 (recommendations only)
Size:   ~50MB (with indexes)
```

### Redis
```
Keys:   ~220K
Memory: ~600MB
TTL:    7 days (recommendations)
```

---

## 🔧 Key Scripts

### Sync Scripts
```
scripts/utils/
├── sync_to_postgresql.py    (9KB)  - Sync CSV → PostgreSQL
├── sync_to_redis.py         (12KB) - Sync CSV → Redis
└── convert_service_type.py  (1.7KB) - Convert service types
```

### Configuration
```
PostgreSQL (DB01):
  Host: 10.39.223.102:5432
  DB:   ut360
  User: admin / Vns@2025

Redis (WEB01):
  Host: 10.39.223.70:6379
  User: redis / 098poiA
```

---

## ✅ Quick Checklist

### Pre-deployment
- [ ] Read [READY_TO_DEPLOY.md](READY_TO_DEPLOY.md)
- [ ] Verify CSV file exists on server
- [ ] Test PostgreSQL connection
- [ ] Test Redis connection

### Deployment
- [ ] Copy 2 sync scripts to server
- [ ] Install dependencies: `pip3 install pandas psycopg2-binary redis`
- [ ] Verify directory structure
- [ ] Run `sync_to_postgresql.py`
- [ ] Run `sync_to_redis.py`

### Post-deployment
- [ ] Verify PostgreSQL row count (214,504)
- [ ] Verify Redis key count (~220K)
- [ ] Test sample queries
- [ ] Check performance (<10ms Redis, <50ms PostgreSQL)

---

## 📞 Support

### Troubleshooting Resources
1. [READY_TO_DEPLOY.md](READY_TO_DEPLOY.md) - Troubleshooting section
2. [SIMPLE_SYNC_GUIDE.md](SIMPLE_SYNC_GUIDE.md) - Common errors
3. [SYNC_TO_PRODUCTION_README.md](SYNC_TO_PRODUCTION_README.md) - Detailed fixes

### Common Questions

**Q: Tôi chỉ cần sync CSV, dùng file nào?**
A: → [SIMPLE_SYNC_GUIDE.md](SIMPLE_SYNC_GUIDE.md)

**Q: Làm sao biết đã sync thành công?**
A: → [READY_TO_DEPLOY.md](READY_TO_DEPLOY.md) (Verify section)

**Q: Query như thế nào để lấy recommendation theo ISDN?**
A: → [REDIS_POSTGRES_QUERY_EXAMPLES.md](REDIS_POSTGRES_QUERY_EXAMPLES.md)

**Q: Service type Fee/Free/Quota là gì?**
A: → [SERVICE_TYPE_UPDATE_SUMMARY.md](SERVICE_TYPE_UPDATE_SUMMARY.md)

---

## 🎯 Summary

### For Quick Deployment (Most Users)
Start with: **[READY_TO_DEPLOY.md](READY_TO_DEPLOY.md)** → [SIMPLE_SYNC_GUIDE.md](SIMPLE_SYNC_GUIDE.md)

### For Technical Details
Start with: **[REDIS_POSTGRES_SUMMARY.md](REDIS_POSTGRES_SUMMARY.md)** → other Redis/Postgres docs

### For Understanding Project Structure
Start with: [CLEANUP_ANALYSIS.md](CLEANUP_ANALYSIS.md) → [PRODUCTION_FILES_LIST.md](PRODUCTION_FILES_LIST.md)

---

**Total Documentation Size:** ~225KB
**Total Scripts:** 3 Python files
**Total Data:** 1 CSV file (32MB)
**Deployment Time:** 5-6 minutes
**Status:** ✅ **READY FOR PRODUCTION**

---

**Created By:** Claude AI
**Date:** 2025-10-22
**Version:** Final Production Release
