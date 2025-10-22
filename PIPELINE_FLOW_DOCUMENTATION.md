# UT360 PIPELINE FLOW DOCUMENTATION

**Generated:** 2025-10-20
**Status:** ✅ VERIFIED & PRODUCTION READY

---

## OVERVIEW

Pipeline gồm **4 phases** xử lý tuần tự để tạo advance recommendations với bad debt risk filtering.

```
Data Sources (N1-N10) → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Final Recommendations
```

---

## DATA SOURCES

### Input Files (CSV format):
- **N1** (ARPU): `/data/ut360/data/N1/N1_*.csv` - ARPU data by package
- **N2** (Package): `/data/ut360/data/N2/N2_*.csv` - Package subscriptions
- **N3** (Usage): `/data/ut360/data/N3/N3_*.csv` - Usage records
- **N4** (Advance): `/data/ut360/data/N4/N4_*.csv` - Advance transactions
- **N5** (Topup): `/data/ut360/data/N5/N5_*.csv` - Topup transactions
- **N10** (Subscriber): `/data/ut360/data/N10/N10_*.csv` - Subscriber information

### Time Range:
- **Production**: 202503-202508 (6 months)
- File naming: `{source}_mhtt_{YYYYMM}.csv`

---

## PHASE 1: DATA LOADING & AGGREGATION

### Script:
```
/data/ut360/scripts/phase1_data/01_load_master_full.py
```

### Input:
- N10 (Subscriber Info)
- N4 (Advance Data)
- N5 (Topup Data)
- N2 (Package Data)
- N3 (Usage Data)

### Processing Logic:

#### 1. Load & Filter
- Load CSV files từ 6 tháng (202503-202508)
- Parallel loading với 128 workers

#### 2. N4 Aggregation (CRITICAL LOGIC):
```python
# BEFORE aggregation: Apply service-type-specific correction
df_n4['advance_amount_corrected'] = np.where(
    df_n4['advance_service_type'].isin(['EasyCredit', 'ungdata247']),
    df_n4['advance_amount'] / 10,  # Divide by 10
    df_n4['advance_amount']  # Keep original for MBFG, UT_SPLUS, etc.
)

# THEN aggregate by (isdn, data_month)
df_n4_agg = df_n4.groupby(['isdn', 'data_month']).agg({
    'advance_amount_corrected': ['count', 'sum', 'mean', 'max'],
    'repayment_amount_corrected': 'sum'
})
```

**Service Type Rules:**
- **EasyCredit** → Chia 10
- **ungdata247** → Chia 10
- **MBFG** → Không chia (SUM)
- **UT_SPLUS** → Không chia (SUM)

#### 3. Other Aggregations:
- **N5**: Simple aggregation by (isdn, month) - topup count, sum, mean
- **N2**: Package count và renewal info
- **N3**: Usage record count
- **N10**: Base subscriber info (no aggregation needed)

#### 4. Merge All:
- Start with N10 as base
- LEFT JOIN all other sources
- Fill missing values with 0 (numeric) or 'Unknown' (categorical)

### Output:
```
/data/ut360/output/datasets/master_full_202503-202508.parquet
```

**Structure:**
- **Records**: 50,972,112
- **Columns**: 30 base columns
- **Unique Subscribers**: 1,006,534

**Columns:**
1. isdn, subscriber_type, subscriber_status, status_detail
2. activation_date, expire_date, data_month
3. **Advance (N4)**: advance_count, total_advance_amount, avg_advance_amount, max_advance_amount, total_repayment_amount, avg_repayment_rate, outstanding_debt, most_used_advance_service, has_advance_in_month
4. **Topup (N5)**: topup_count, total_topup_amount, avg_topup_amount, std_topup_amount, max_topup_amount, most_used_topup_channel
5. **Package (N2)**: num_packages, total_package_value, avg_package_price, max_package_price, avg_package_cycle, num_active_packages, num_renewed_packages
6. **Usage (N3)**: n3_record_count

---

## PHASE 2: FEATURE ENGINEERING

### Script:
```
/data/ut360/scripts/phase2_features/feature_engineering.py
```

### Input:
```
/data/ut360/output/datasets/master_full_202503-202508.parquet
```

### Processing:
1. Load master file with 30 base columns
2. Create 45 engineered features:
   - Time-based features (lag features, rolling averages)
   - Behavioral features (advance frequency, topup patterns)
   - Financial features (ARPU ratios, repayment rates)
   - Risk indicators

### Output:
```
/data/ut360/output/datasets/dataset_with_features_202503-202508_CORRECTED.parquet
```

**Structure:**
- **Records**: 50,972,112
- **Columns**: 75 (30 base + 45 features)
- **File Size**: ~292 MB (compressed)

---

## PHASE 3A: CLUSTERING & SEGMENTATION

### Script:
```
/data/ut360/scripts/phase3_models/01_clustering_segmentation.py
```

### Input:
```
/data/ut360/output/datasets/dataset_with_features_202503-202508_CORRECTED.parquet
```

### Processing:
1. Select relevant features for clustering
2. Apply K-Means clustering (n_clusters=3)
3. Assign cluster labels to subscribers

### Output:
```
/data/ut360/output/datasets/subscribers_clustered_segmentation.parquet
```

---

## PHASE 3B: BUSINESS RULES & RECOMMENDATIONS

### Script:
```
/data/ut360/scripts/phase3_models/03_recommendation_with_correct_arpu.py
```

### Input:
- Clustered segmentation file
- Features dataset

### Processing:
1. Apply business rules per service type:
   - **ungsanluong**: Voice/SMS dominant users
   - **EasyCredit**: Moderate topup users
   - **MBFG**: High-value subscribers

2. Calculate recommended advance amounts based on:
   - ARPU
   - Topup history
   - Usage patterns
   - Cluster membership

### Output:
```
/data/ut360/output/recommendations/final_recommendations_with_business_rules.csv
```

---

## PHASE 4: BAD DEBT RISK FILTERING

### Script:
```
/data/ut360/scripts/phase3_models/04_apply_bad_debt_risk_filter.py
```

### Input:
```
/data/ut360/output/recommendations/final_recommendations_with_business_rules.csv
```

### Processing:
1. Calculate bad debt risk score based on:
   - `topup_advance_ratio_weight` (40%)
   - `topup_frequency_weight` (20%)
   - `arpu_stability_weight` (20%)
   - `avg_topup_weight` (20%)

2. Classify risk levels:
   - **LOW** (< 30): Approve
   - **MEDIUM** (30-60): Approve with monitoring
   - **HIGH** (> 60): Reject

3. Filter out HIGH risk subscribers

### Output:
```
/data/ut360/output/recommendations/recommendations_final_filtered.csv
```

**Final Output:**
- Only LOW and MEDIUM risk subscribers
- Ready for deployment

---

## WEBAPP CONFIGURATION

### Backend API:
```
/data/web-ut360/backend/app.py
```

### Phase Scripts Mapping:
```python
phase_scripts = {
    "phase1": "scripts/phase1_data/01_load_master_full.py",
    "phase2": "scripts/phase2_features/feature_engineering.py",
    "phase3a": "scripts/phase3_models/01_clustering_segmentation.py",
    "phase3b": "scripts/phase3_models/03_recommendation_with_correct_arpu.py",
    "phase4": "scripts/phase3_models/04_apply_bad_debt_risk_filter.py"
}
```

### Output Paths:
```python
if phase == "phase1":
    output_path = "output/datasets/master_full_202503-202508.parquet"
elif phase == "phase2":
    output_path = "output/datasets/dataset_with_features_202503-202508_CORRECTED.parquet"
elif phase == "phase3b":
    output_path = "output/recommendations/final_recommendations_with_business_rules.csv"
elif phase == "phase4":
    output_path = "output/recommendations/recommendations_final_filtered.csv"
```

---

## VERIFICATION RESULTS

### Phase 1 Logic Verification:
- **Test Sample**: 10 subscribers
- **advance_count**: 10/10 MATCH (100%)
- **total_advance_amount**: 10/10 MATCH (100%)
- **Logic**: Service-type-specific DIV10 per-record VERIFIED ✅

### Data Quality:
- All aggregations tested and verified
- No data loss during pipeline
- File integrity maintained

---

## CRITICAL NOTES

### ⚠️ IMPORTANT:
1. **N4 Logic**: MUST apply DIV10 correction PER-RECORD before aggregation for EasyCredit & ungdata247
2. **Month Range**: MUST use 202503-202508 (6 months only)
3. **File Paths**: All paths are FIXED in webapp config
4. **Backup**: Old scripts backed up to `/data/ut360/backup_scripts_20251020/`

### File Naming Convention:
- Master file: `master_full_202503-202508.parquet`
- Features file: `dataset_with_features_202503-202508_CORRECTED.parquet`
- Use `_CORRECTED` suffix to indicate verified logic

---

## EXECUTION

### Via Webapp:
```bash
cd /data/web-ut360
./start.sh
# Access: http://localhost:8000
```

### Manual Execution:
```bash
cd /data/ut360

# Phase 1
python3 scripts/phase1_data/01_load_master_full.py

# Phase 2
python3 scripts/phase2_features/feature_engineering.py

# Phase 3a
python3 scripts/phase3_models/01_clustering_segmentation.py

# Phase 3b
python3 scripts/phase3_models/03_recommendation_with_correct_arpu.py

# Phase 4
python3 scripts/phase3_models/04_apply_bad_debt_risk_filter.py
```

---

## BACKUP & RECOVERY

### Code Backups:
- **Location**: `/data/ut360/backup_scripts_20251020/`
- **Contents**: Old Phase 1 scripts, test scripts

### Data Backups:
- **Location**: `/data/ut360/output/datasets/backup_20251020_094512/`
- **Contents**:
  - `dataset_with_features_202503-202508_CORRECTED.parquet` (old version)
  - `master_full_202503-202509.parquet` (7 months - incorrect)

---

## CONTACT & SUPPORT

For questions or issues:
1. Check this documentation first
2. Review webapp logs: `/data/web-ut360/backend/logs/`
3. Check pipeline logs in webapp UI

**Document Version**: 1.0
**Last Updated**: 2025-10-20
**Status**: ✅ Production Ready
