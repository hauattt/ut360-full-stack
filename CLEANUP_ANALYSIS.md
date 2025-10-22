# UT360 Project Cleanup Analysis
**Date:** 2025-10-22

## Mục tiêu
- Giữ lại chỉ những file cần thiết cho production
- Backup những file không dùng hoặc trùng lặp
- Giảm kích thước project để deploy lên server

---

## 1. SCRIPTS - Phân tích Python Scripts

### ✅ Scripts CẦN GIỮ (Core Pipeline)

#### Phase 1: Data Loading
```
/data/ut360/scripts/phase1_data/01_load_master_full.py
```
- **Mục đích:** Load và merge 9 data sources (N1-N9)
- **Output:** master_with_arpu_correct_202503-202509.parquet (2.1GB)
- **Trạng thái:** CẦN GIỮ - Script chính của Phase 1

#### Phase 2: Feature Engineering
```
/data/ut360/scripts/phase2_features/feature_engineering.py
```
- **Mục đích:** Tạo 50+ features cho clustering
- **Input:** master file
- **Output:** Thêm features vào master file
- **Trạng thái:** CẦN GIỮ - Script chính của Phase 2

#### Phase 3: Clustering & Recommendations
```
/data/ut360/scripts/phase3_models/01_clustering_segmentation.py
```
- **Mục đích:** K-Means clustering (4 clusters)
- **Output:** subscribers_clustered_segmentation.parquet (51MB)
- **Trạng thái:** CẦN GIỮ - Script chính của Phase 3a

```
/data/ut360/scripts/phase3_models/03_recommendation_with_correct_arpu.py
```
- **Mục đích:** Business rules recommendation (EasyCredit, MBFG, ungsanluong)
- **Output:** recommendations_final_filtered.csv (33MB)
- **Trạng thái:** CẦN GIỮ - Script chính của Phase 3b

#### Phase 4: Bad Debt Risk Filter
```
/data/ut360/scripts/phase3_models/04_apply_bad_debt_risk_filter.py
```
- **Mục đích:** Apply bad debt risk filter
- **Output:** recommendations_with_risk_full.csv (41MB)
- **Trạng thái:** CẦN GIỮ - Script chính của Phase 4

#### Utils - Web Application Support
```
/data/ut360/scripts/utils/generate_subscriber_monthly_summary.py
```
- **Mục đích:** Tạo monthly ARPU summary cho web UI
- **Output:** subscriber_monthly_summary.parquet (20MB)
- **Trạng thái:** CẦN GIỮ - Cần cho web app (ARPU trend chart)

```
/data/ut360/scripts/utils/generate_subscriber_360_profile_parallel.py
```
- **Mục đích:** Tạo 360 profile với scores và metrics
- **Output:** subscriber_360_profile.parquet (21MB)
- **Trạng thái:** CẦN GIỮ - Cần cho web app (Customer360-VNS modal)

```
/data/ut360/scripts/utils/generate_phase_summaries.py
```
- **Mục đích:** Generate summary reports cho mỗi phase
- **Output:** Text summaries
- **Trạng thái:** CẦN GIỮ - Cần cho web app (Phase Results page)

---

### ❌ Scripts CÓ THỂ BACKUP (Visualization/Analysis)

```
/data/ut360/scripts/visualizations/advance_user_behavior_analysis.py
/data/ut360/scripts/visualizations/bad_debt_risk_visualization.py
/data/ut360/scripts/visualizations/cluster_map.py
/data/ut360/scripts/visualize_segmentation.py
```
- **Mục đích:** Tạo charts và visualizations cho analysis
- **Output:** PNG/HTML files trong output/visualizations/
- **Trạng thái:** CÓ THỂ BACKUP - Chỉ dùng để phân tích, không cần cho pipeline chính

```
/data/ut360/scripts/utils/generate_subscriber_360_profile.py
```
- **Mục đích:** Version cũ của 360 profile generator (không dùng vectorized operations)
- **Trạng thái:** CÓ THỂ BACKUP - Đã thay thế bằng version _parallel.py

---

## 2. OUTPUT FILES - Phân tích File Outputs

### ✅ Files CẦN GIỮ cho Production

#### Core Pipeline Outputs (Large files - cần cho pipeline)
```
/data/ut360/output/master_with_arpu_correct_202503-202509.parquet        2.1GB
/data/ut360/output/subscribers_clustered_segmentation.parquet            51MB
```
- **Lý do:** Cần cho pipeline chính, input cho các phase sau

#### Web Application Files (Small files - cần cho web UI)
```
/data/ut360/output/subscriber_360_profile.parquet                        21MB
/data/ut360/output/subscriber_monthly_summary.parquet                    20MB
```
- **Lý do:** Web app load trực tiếp từ các file này (cached in-memory)

#### Final Recommendations (Cần 1 file duy nhất)
```
/data/ut360/output/recommendations/recommendations_final_filtered.csv    33MB
```
- **Lý do:** File chính được web app sử dụng (có trong app.py)
- **Note:** Web app dùng file này để list subscribers và filter

---

### ⚠️ Files TRÙNG LẶP - Chọn 1 giữ, còn lại backup

#### Recommendation Files (Nhiều versions)
```
recommendations_final_filtered.csv                                       33MB  ← WEB APP DÙNG
final_recommendations_with_business_rules.csv                            38MB
recommendations_with_risk_full.csv                                       41MB
```
- **Phân tích:**
  - `recommendations_final_filtered.csv` - Web app đang dùng (trong app.py)
  - `final_recommendations_with_business_rules.csv` - Version có business rules
  - `recommendations_with_risk_full.csv` - Version có bad debt risk
- **Quyết định:** GIỮ `recommendations_final_filtered.csv`, backup 2 files kia

#### Service-Specific Recommendations (Tách theo service)
```
recommendations_easycredit.csv                                           21MB
recommendations_mbfg.csv                                                 11MB
recommendations_ungsanluong.csv                                          6.7MB
final_easycredit_filtered.csv                                            22MB
final_fee_filtered.csv                                                   22MB
final_mbfg_filtered.csv                                                  6.7MB
final_free_filtered.csv                                                  3.3MB
final_ungsanluong_filtered.csv                                           4.3MB
```
- **Phân tích:** Các file này là subset của file chính, tách theo service_type
- **Quyết định:** CÓ THỂ BACKUP - Web app có thể filter từ file chính

---

### ❌ Files CÓ THỂ BACKUP (Analysis/Reports)

#### Expansion Group Files (Old approach)
```
expansion_group2_all_targets.csv                                         12MB
expansion_group2_medium_priority.csv                                     5.6MB
expansion_group2_similar_high_priority.csv                               5.8MB
```
- **Lý do:** Approach cũ, không dùng trong pipeline hiện tại

#### Summary/Report CSV Files
```
advance_user_feature_importance.csv                                      757B
advance_vs_nonadvance_comparison.csv                                     1.6K
bad_debt_risk_summary.csv                                                228B
bad_debt_risk_summary_final.csv                                          301B
clustering_summary.csv                                                   206B
business_rules_summary.csv                                               265B
final_summary_with_risk.csv                                              314B
```
- **Lý do:** Small analysis files, có thể regenerate bất cứ lúc nào

#### Clustering Features
```
clustering_features.txt
```
- **Lý do:** Text file liệt kê features, có thể tạo lại

#### Visualization Outputs
```
/data/ut360/output/visualizations/*.png
/data/ut360/output/visualizations/*.html
```
- **Lý do:** Charts/graphs cho analysis, không cần cho production

---

## 3. WEB APPLICATION - Phân tích Web Code

### ✅ CẦN GIỮ - /data/web-ut360/ (Active version)
```
/data/web-ut360/
├── backend/
│   └── app.py                     ← FastAPI backend (đã update)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Profile360Modal.jsx      ← Customer360-VNS modal
│   │   │   └── Profile360Modal.css      ← Modal styling
│   │   └── pages/
│   │       ├── Dashboard.jsx
│   │       ├── Subscribers.jsx          ← Subscriber list + 360 modal
│   │       ├── PhaseResults.jsx
│   │       └── FileSelection.jsx
│   └── package.json
├── start.sh                       ← Startup script
├── stop.sh                        ← Stop script
└── database/                      ← Pipeline execution database
```
- **Trạng thái:** ACTIVE - Đang chạy production
- **Đặc điểm:**
  - Backend đã update để dùng subscriber_360_profile.parquet
  - Frontend có Profile360Modal component mới
  - Server-side pagination
  - Fast loading với cached data

### ❌ CÓ THỂ XÓA HOÀN TOÀN

#### /data/ut360/web-ut360/ (Symlink duplicate)
```
/data/ut360/web-ut360/ -> Actually contains full copy
```
- **Trạng thái:** TRÙNG LẶP - Copy cũ của web app
- **Quyết định:** XÓA - Đã có /data/web-ut360/ là active version

#### /data/ut360/web_app/ (Old version)
```
/data/ut360/web_app/
├── backend/
├── frontend/
├── pipeline.db
└── docker-compose.yml
```
- **Trạng thái:** CŨ - Version cũ trước khi refactor
- **Đặc điểm:**
  - Không có Profile360Modal
  - Không có server-side pagination
  - Backend chậm (không có caching)
- **Quyết định:** BACKUP - Giữ trong archive nếu cần reference

---

## 4. THƯMỤC ARCHIVE/BACKUP HIỆN CÓ

### Đã có sẵn
```
/data/ut360/archive/                    ← Archive cũ (Oct 18)
/data/ut360/backup_scripts_20251020/    ← Backup scripts
/data/ut360/scripts/backup_scripts_20251020_094732/  ← Backup scripts trong scripts/
```

### Thư mục data trùng lặp
```
/data/ut360/data/     ← 100 rows sample data (for testing)
/data/ut360/data2/    ← Duplicate? Cần check
```

---

## 5. RECOMMENDED CLEANUP ACTIONS

### Action 1: Backup unused scripts
```bash
mkdir -p /data/ut360/archive_20251022/scripts_visualization
mv /data/ut360/scripts/visualizations/*.py /data/ut360/archive_20251022/scripts_visualization/
mv /data/ut360/scripts/visualize_segmentation.py /data/ut360/archive_20251022/scripts_visualization/
mv /data/ut360/scripts/utils/generate_subscriber_360_profile.py /data/ut360/archive_20251022/scripts_visualization/
```

### Action 2: Backup duplicate output files
```bash
mkdir -p /data/ut360/archive_20251022/output_duplicates

# Backup duplicate recommendation versions
mv /data/ut360/output/recommendations/final_recommendations_with_business_rules.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/recommendations_with_risk_full.csv /data/ut360/archive_20251022/output_duplicates/

# Backup service-specific splits (can filter from main file)
mv /data/ut360/output/recommendations/recommendations_easycredit.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/recommendations_mbfg.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/recommendations_ungsanluong.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/final_easycredit_filtered.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/final_fee_filtered.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/final_mbfg_filtered.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/final_free_filtered.csv /data/ut360/archive_20251022/output_duplicates/
mv /data/ut360/output/recommendations/final_ungsanluong_filtered.csv /data/ut360/archive_20251022/output_duplicates/

# Backup expansion group files (old approach)
mv /data/ut360/output/expansion_*.csv /data/ut360/archive_20251022/output_duplicates/
```

### Action 3: Backup small summary files
```bash
mkdir -p /data/ut360/archive_20251022/output_summaries
mv /data/ut360/output/*.csv /data/ut360/archive_20251022/output_summaries/
mv /data/ut360/output/recommendations/*.csv /data/ut360/archive_20251022/output_summaries/ 2>/dev/null
# Keep only recommendations_final_filtered.csv
cp /data/ut360/archive_20251022/output_summaries/recommendations_final_filtered.csv /data/ut360/output/recommendations/
```

### Action 4: Remove old web app versions
```bash
mv /data/ut360/web_app /data/ut360/archive_20251022/web_app_old
rm -rf /data/ut360/web-ut360  # If it's duplicate
```

### Action 5: Check and remove duplicate data folders
```bash
# First check if data2 is duplicate
ls -lh /data/ut360/data/N1/ | head -3
ls -lh /data/ut360/data2/N1/ | head -3
# If duplicate:
# mv /data/ut360/data2 /data/ut360/archive_20251022/data2_duplicate
```

---

## 6. FILES TO KEEP - FINAL PRODUCTION LIST

### Scripts (9 files)
```
scripts/
├── phase1_data/
│   └── 01_load_master_full.py
├── phase2_features/
│   └── feature_engineering.py
├── phase3_models/
│   ├── 01_clustering_segmentation.py
│   ├── 03_recommendation_with_correct_arpu.py
│   └── 04_apply_bad_debt_risk_filter.py
└── utils/
    ├── generate_subscriber_monthly_summary.py
    ├── generate_subscriber_360_profile_parallel.py
    └── generate_phase_summaries.py
```

### Output Files (5 files - 2.2GB total)
```
output/
├── master_with_arpu_correct_202503-202509.parquet          (2.1GB)
├── subscribers_clustered_segmentation.parquet              (51MB)
├── subscriber_360_profile.parquet                          (21MB)
├── subscriber_monthly_summary.parquet                      (20MB)
└── recommendations/
    └── recommendations_final_filtered.csv                  (33MB)
```

### Data (9 folders - sample data)
```
data/
├── N1/ ... N9/  (100 rows each for testing)
```

### Web Application (1 directory)
```
/data/web-ut360/
├── backend/app.py
├── frontend/
├── start.sh
├── stop.sh
└── database/
```

### Documentation
```
README.md
COMPLETE_SUMMARY.md
PIPELINE_FLOW_DOCUMENTATION.md
QUICK_START.md
```

---

## 7. SIZE REDUCTION ESTIMATE

### Current Size:
```
Scripts: ~50 files
Output: ~30 files (2.5GB+)
Web apps: 3 copies
Total: ~3GB+
```

### After Cleanup:
```
Scripts: 9 core files
Output: 5 essential files (2.2GB)
Web app: 1 active version
Total: ~2.3GB
```

**Reduction:** ~30% size reduction, 90% file count reduction

---

## 8. NEXT STEPS

1. **Review this analysis** - Xác nhận danh sách files cần giữ
2. **Create backup** - Chạy các lệnh backup ở Section 5
3. **Test after cleanup** - Verify pipeline và web app vẫn chạy đúng
4. **Create deployment package** - Tar/zip các files cần thiết để deploy lên server
5. **Document final structure** - Update documentation với structure mới

---

## NOTES

- ⚠️ **QUAN TRỌNG:** Trước khi xóa bất cứ file nào, nên backup toàn bộ project
- ⚠️ Kiểm tra kỹ các file được web app reference trong app.py
- ⚠️ Test pipeline sau khi cleanup để đảm bảo không thiếu dependencies
- ✅ Các file được backup vẫn có thể restore nếu cần
