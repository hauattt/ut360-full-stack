# UT360 Production Files List
**Created:** 2025-10-22
**Purpose:** Danh sách chính xác các file cần thiết để deploy lên production server

---

## 1. SCRIPTS - Core Pipeline (9 files)

### Phase 1: Data Loading
```
scripts/phase1_data/
└── 01_load_master_full.py                          [REQUIRED] Load & merge 9 data sources
```

### Phase 2: Feature Engineering
```
scripts/phase2_features/
└── feature_engineering.py                          [REQUIRED] Generate 50+ features
```

### Phase 3: Clustering & Recommendation
```
scripts/phase3_models/
├── 01_clustering_segmentation.py                   [REQUIRED] K-Means clustering
├── 03_recommendation_with_correct_arpu.py          [REQUIRED] Business rules recommendation
└── 04_apply_bad_debt_risk_filter.py                [REQUIRED] Bad debt risk filter
```

### Utils: Web Application Support
```
scripts/utils/
├── generate_subscriber_monthly_summary.py          [REQUIRED] Monthly ARPU for web UI
├── generate_subscriber_360_profile_parallel.py     [REQUIRED] 360 profile for web UI
└── generate_phase_summaries.py                     [REQUIRED] Phase summaries for web UI
```

**Total Scripts:** 9 files

---

## 2. OUTPUT FILES - Essential Results

### Core Pipeline Outputs (2.2GB)
```
output/
├── master_with_arpu_correct_202503-202509.parquet          2.1GB    [REQUIRED] Master data
├── subscribers_clustered_segmentation.parquet              51MB     [REQUIRED] Clustering results
├── subscriber_360_profile.parquet                          21MB     [REQUIRED] Web UI cache
├── subscriber_monthly_summary.parquet                      20MB     [REQUIRED] Web UI cache
└── recommendations/
    └── recommendations_final_filtered.csv                  33MB     [REQUIRED] Final recommendations
```

**Total Output:** 5 files (~2.2GB)

### Output Subdirectories Structure (Keep structure, backup old files)
```
output/
├── datasets/          [OPTIONAL] Intermediate datasets
├── models/            [OPTIONAL] Model artifacts
├── recommendations/   [REQUIRED] Final recommendations
├── summaries/         [OPTIONAL] Text summaries
└── visualizations/    [OPTIONAL] Charts/graphs
```

---

## 3. DATA - Sample Data for Testing

### Input Data (9 folders)
```
data/
├── N1/                [REQUIRED] ARPU data (100 rows sample)
├── N2/                [REQUIRED] TopUp data
├── N3/                [REQUIRED] Loan data
├── N4/                [REQUIRED] Bad debt data
├── N5/                [REQUIRED] Roaming data
├── N6/                [REQUIRED] Package data
├── N7/                [REQUIRED] Service data
├── N8/                [REQUIRED] Age data
└── N9/                [REQUIRED] Balance data
```

**Note:** Đây là sample data 100 rows/file cho testing. Production cần full data.

### data2 Folder (Package Info - Keep)
```
data2/
├── N1/ ... N8/        [REQUIRED] Package registration info
```

---

## 4. WEB APPLICATION - Active Version

### Backend
```
/data/web-ut360/backend/
├── app.py                                          [REQUIRED] FastAPI backend
├── requirements.txt                                [REQUIRED] Python dependencies
└── __init__.py                                     [OPTIONAL]
```

### Frontend
```
/data/web-ut360/frontend/
├── src/
│   ├── components/
│   │   ├── Profile360Modal.jsx                    [REQUIRED] Customer360-VNS modal
│   │   ├── Profile360Modal.css                    [REQUIRED] Modal styling
│   │   └── ... (other components)
│   ├── pages/
│   │   ├── Dashboard.jsx                          [REQUIRED]
│   │   ├── Subscribers.jsx                        [REQUIRED]
│   │   ├── PhaseResults.jsx                       [REQUIRED]
│   │   └── FileSelection.jsx                      [REQUIRED]
│   ├── App.jsx                                    [REQUIRED]
│   └── main.jsx                                   [REQUIRED]
├── public/
├── index.html                                     [REQUIRED]
├── package.json                                   [REQUIRED]
├── package-lock.json                              [REQUIRED]
└── vite.config.js                                 [REQUIRED]
```

### Scripts & Config
```
/data/web-ut360/
├── start.sh                                       [REQUIRED] Startup script
├── stop.sh                                        [REQUIRED] Stop script
├── docker-compose.yml                             [OPTIONAL] For Docker deployment
└── database/                                      [REQUIRED] Pipeline execution DB
    └── pipeline_runs.db
```

---

## 5. CONFIGURATION

### Config Files
```
config/
└── (empty or minimal config)                      [OPTIONAL]
```

**Note:** Hiện tại chưa có config files, có thể thêm sau để configure:
- Data paths
- Model parameters
- Business rules thresholds

---

## 6. DOCUMENTATION

### Essential Docs
```
README.md                                          [REQUIRED] Project overview
COMPLETE_SUMMARY.md                                [OPTIONAL] Detailed summary
PIPELINE_FLOW_DOCUMENTATION.md                     [OPTIONAL] Pipeline documentation
QUICK_START.md                                     [OPTIONAL] Quick start guide
CLEANUP_ANALYSIS.md                                [REFERENCE] Cleanup analysis
PRODUCTION_FILES_LIST.md                           [REFERENCE] This file
```

---

## 7. FILES ALREADY BACKED UP (Not needed for production)

### Archived in /data/ut360/archive_20251022/
```
archive_20251022/
├── scripts_visualization/                         [BACKUP] Visualization scripts (5 files)
│   ├── advance_user_behavior_analysis.py
│   ├── bad_debt_risk_visualization.py
│   ├── cluster_map.py
│   ├── generate_subscriber_360_profile.py        (old version)
│   └── visualize_segmentation.py
├── output_duplicates/                             [BACKUP] Duplicate output files (10 files, 130MB)
│   ├── final_recommendations_with_business_rules.csv
│   ├── recommendations_with_risk_full.csv
│   ├── recommendations_easycredit.csv
│   ├── recommendations_mbfg.csv
│   ├── recommendations_ungsanluong.csv
│   ├── final_*_filtered.csv (5 files)
├── output_summaries/                              [BACKUP] Small summary CSVs (11 files, <1MB)
│   ├── advance_user_feature_importance.csv
│   ├── bad_debt_risk_summary*.csv
│   ├── clustering_summary.csv
│   ├── expansion_group2_*.csv (3 files)
│   └── business_rules_summary.csv
├── web_app_old/                                   [BACKUP] Old web app version
└── web-ut360_old/                                 [BACKUP] Older web app version
```

### Other Existing Archives
```
archive/                                           [OLD BACKUP] Oct 18 archive
backup_scripts_20251020/                           [OLD BACKUP] Scripts backup
```

---

## 8. DEPLOYMENT PACKAGE STRUCTURE

### Recommended deployment structure:
```
ut360-production/
├── scripts/                    (9 files)
│   ├── phase1_data/
│   ├── phase2_features/
│   ├── phase3_models/
│   └── utils/
├── output/                     (5 files, 2.2GB)
│   ├── *.parquet (4 files)
│   └── recommendations/
│       └── recommendations_final_filtered.csv
├── data/                       (9 folders - sample data)
│   └── N1/ ... N9/
├── data2/                      (8 folders - package info)
│   └── N1/ ... N8/
├── web-application/
│   ├── backend/
│   ├── frontend/
│   ├── database/
│   ├── start.sh
│   └── stop.sh
├── docs/
│   ├── README.md
│   └── QUICK_START.md
└── .gitignore
```

**Total Size:** ~2.3GB (mostly output files)

---

## 9. DEPLOYMENT CHECKLIST

### Pre-deployment
- [ ] Verify all required scripts present (9 files)
- [ ] Verify all output files present (5 files, 2.2GB)
- [ ] Verify web application files complete
- [ ] Test pipeline locally after cleanup
- [ ] Test web application locally after cleanup

### Server Requirements
- [ ] Python 3.8+
- [ ] Node.js 16+
- [ ] RAM: 512GB (for full data processing)
- [ ] CPU: 256 cores (for parallel processing)
- [ ] Disk: 5GB+ free space
- [ ] Dependencies: pandas, numpy, scikit-learn, fastapi, uvicorn, react, vite

### Deployment Steps
1. [ ] Tar/zip production files
2. [ ] Upload to server
3. [ ] Extract files
4. [ ] Install Python dependencies: `pip install -r requirements.txt`
5. [ ] Install Node dependencies: `cd frontend && npm install`
6. [ ] Configure data paths if needed
7. [ ] Run pipeline to verify: `python scripts/phase1_data/01_load_master_full.py`
8. [ ] Start web application: `./start.sh`
9. [ ] Test web UI: http://server:3000
10. [ ] Verify Customer360-VNS modal works

### Post-deployment
- [ ] Monitor logs for errors
- [ ] Test with production data
- [ ] Set up automated backups
- [ ] Document any custom configurations

---

## 10. EXCLUSIONS (DO NOT DEPLOY)

### Directories to exclude:
```
.git/                          (Git repository - 不需要)
.claude/                       (Claude AI config - 不需要)
archive/                       (Old backups - 不需要)
archive_20251022/              (New backups - 不需要)
backup_scripts_*/              (Script backups - 不需要)
output/visualizations/         (Charts/graphs - 不需要)
output/summaries/              (Text summaries - 可选)
```

### Files to exclude:
```
*.log                          (Log files)
*.pyc, __pycache__/            (Python cache)
node_modules/                  (Will reinstall on server)
.DS_Store, Thumbs.db           (OS files)
*.tmp, *.bak                   (Temporary files)
```

---

## 11. QUICK DEPLOYMENT COMMANDS

### Create deployment package:
```bash
cd /data/ut360
tar -czf ut360-production-$(date +%Y%m%d).tar.gz \
  --exclude='.git' \
  --exclude='.claude' \
  --exclude='archive*' \
  --exclude='backup_*' \
  --exclude='*.log' \
  --exclude='__pycache__' \
  --exclude='node_modules' \
  --exclude='output/visualizations' \
  scripts/phase1_data/ \
  scripts/phase2_features/ \
  scripts/phase3_models/ \
  scripts/utils/ \
  output/*.parquet \
  output/recommendations/recommendations_final_filtered.csv \
  data/ \
  data2/ \
  README.md \
  QUICK_START.md

cd /data/web-ut360
tar -czf web-ut360-$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='*.log' \
  --exclude='.vite' \
  --exclude='dist' \
  backend/ \
  frontend/ \
  database/ \
  start.sh \
  stop.sh \
  docker-compose.yml
```

### Upload to server:
```bash
scp ut360-production-20251022.tar.gz user@server:/path/to/deployment/
scp web-ut360-20251022.tar.gz user@server:/path/to/deployment/
```

### Extract on server:
```bash
ssh user@server
cd /path/to/deployment/
tar -xzf ut360-production-20251022.tar.gz
tar -xzf web-ut360-20251022.tar.gz
```

---

## 12. FILE SIZE SUMMARY

| Category | Files | Size | Status |
|----------|-------|------|--------|
| Scripts | 9 | <1MB | ✅ Required |
| Output Files | 5 | 2.2GB | ✅ Required |
| Sample Data | 18 folders | <10MB | ✅ Required |
| Web Backend | ~5 files | <1MB | ✅ Required |
| Web Frontend | ~30 files | <5MB | ✅ Required |
| Documentation | 4 files | <1MB | ✅ Recommended |
| **TOTAL** | **~60 files** | **~2.3GB** | |

---

## 13. NOTES

- ⚠️ Output files (2.2GB) chiếm phần lớn dung lượng
- ⚠️ Sample data chỉ có 100 rows/file, production cần full data
- ⚠️ Web app cần install dependencies (node_modules ~500MB, không bao gồm trong package)
- ✅ Đã backup tất cả files không cần thiết vào archive_20251022/
- ✅ Cấu trúc sạch, chỉ giữ files production cần thiết
- ✅ Có thể restore từ backup nếu cần

---

**Last Updated:** 2025-10-22
**Maintained By:** UT360 Team
