# ✅ RECOMMENDATION SYSTEM - HOÀN TẤT

**Date:** 2025-10-18  
**Version:** 4.1 Business Rules + Bad Debt Risk Filter  
**Status:** ✅ PRODUCTION READY

---

## 🎯 KẾT QUẢ CUỐI CÙNG

### Tổng quan:
- **Ban đầu:** 273,312 subscribers (sau clustering)
- **Sau lọc bad debt risk:** **198,004 subscribers** (72.4% pass rate)
- **HIGH risk loại bỏ:** 75,308 (27.6%)
- **Revenue potential:** **1,214,404,200 VND** (~1.21 tỷ)
- **Avg revenue/subscriber:** 6,133 VND

---

## 📊 PHÂN LOẠI SERVICE TYPE

### Sau lọc bad debt risk:

| Service Type | Count | % | Avg ARPU | Avg Advance | Avg Revenue | Total Revenue | % Revenue |
|--------------|-------|---|----------|-------------|-------------|---------------|-----------|
| **EasyCredit** | 144,470 | 73.0% | 4,137 VND | 25,003 VND | 7,501 VND | 1,083,645,000 | **89.2%** |
| **MBFG** | 23,114 | 11.7% | 1,799 VND | 10,016 VND | 3,005 VND | 69,455,400 | 5.7% |
| **ungsanluong** | 30,420 | 15.4% | 2,137 VND | 10,076 VND | 2,015 VND | 61,303,800 | 5.0% |
| **TOTAL** | 198,004 | 100% | - | - | **6,133 VND** | **1,214,404,200** | 100% |

---

## 🔍 BAD DEBT RISK FILTER IMPACT

### Risk Distribution (Before filtering):

| Service | Initial | LOW | MEDIUM | HIGH | Pass Rate |
|---------|---------|-----|--------|------|-----------|
| **EasyCredit** | 144,470 | 144,312 (99.9%) | 158 (0.1%) | 0 (0%) | **100%** ✅ |
| **MBFG** | 76,724 | 22,913 (29.9%) | 201 (0.3%) | 53,610 (69.9%) | **30.1%** ⚠️ |
| **ungsanluong** | 52,118 | 30,397 (58.3%) | 23 (0.0%) | 21,698 (41.6%) | **58.4%** |

### Final (After filtering):
- **LOW risk:** 197,622 (99.8%)
- **MEDIUM risk:** 382 (0.2%)
- **HIGH risk removed:** 75,308

---

## 💡 KEY INSIGHTS

### 1. **EasyCredit là core business**
   - **Chiếm 73%** subscribers sau lọc
   - Mang lại **89.2% revenue**
   - **Pass rate 100%** - hầu như không có HIGH risk
   - Điều kiện: Nạp ≥50k/tháng, ổn định 2 tháng
   - **UNLIMITED usage** - lợi thế cạnh tranh lớn

### 2. **MBFG bị lọc rất nhiều**
   - Pass rate chỉ **30.1%** (23k/77k)
   - 70% MBFG là HIGH risk (không nạp tiền)
   - Chỉ giữ lại những MBFG thực sự nạp tiền thường xuyên
   - Revenue đóng góp giảm từ 16.2% → 5.7%

### 3. **ungsanluong còn 58%**
   - Pass rate trung bình (30k/52k)
   - Voice/SMS users có tendency nạp tiền hơn
   - Revenue đóng góp: 5.0%

### 4. **Revenue concentration cao**
   - EasyCredit: 89.2% revenue từ 73% subscribers
   - MBFG + ungsanluong: 10.8% revenue từ 27% subscribers
   - Focus vào EasyCredit để maximize revenue

---

## 🎯 BUSINESS RULES ÁP DỤNG

### 1. EasyCredit (Ứng có phí 30%)
**Classification:**
```python
IF voice_sms_pct <= 70% AND
   topup_count_last_1m >= 1 AND
   (topup_amount_last_1m >= 50,000 OR avg_topup_amount >= 50,000) AND
   topup_count_last_2m >= 1:
    → EasyCredit
```

**Characteristics:**
- Advance: 25,000 VND (default), 50,000 VND (ARPU > 100k)
- Usage time: **UNLIMITED** (until SIM locked)
- Revenue: **30% fee** = 7,501 VND avg
- Bad debt risk: **Rất thấp** (100% pass rate)

---

### 2. MBFG (Ứng không phí)
**Classification:**
```python
IF voice_sms_pct <= 70% AND
   topup_count_last_1m >= 2:
    → MBFG
```

**Characteristics:**
- Advance: min(max(arpu × 1.2, 10k), 50k)
- Usage time: 24-60 hours (from table)
- Revenue: Profit from unused = 3,005 VND avg
- Bad debt risk: **Cao** (70% HIGH risk nếu không nạp tiền)

---

### 3. ungsanluong (Ứng sản lượng)
**Classification:**
```python
IF voice_sms_pct > 70%:
    → ungsanluong
```

**Characteristics:**
- Advance: max(arpu × 0.8, 10k), capped 50k
- Usage time: 24-60 hours (from table)
- Revenue: 20% markup = 2,015 VND avg
- Bad debt risk: **Trung bình** (58% pass rate)

---

## 📁 FILES ĐẦU RA

### ✅ File chính (DÙNG FILE NÀY):
```
output/recommendations/recommendations_final_filtered.csv
```
**198,004 subscribers** - Đã lọc HIGH risk

### Files theo service type:
- `final_easycredit_filtered.csv` - 144,470 subs
- `final_mbfg_filtered.csv` - 23,114 subs
- `final_ungsanluong_filtered.csv` - 30,420 subs

### Files trung gian:
- `final_recommendations_with_business_rules.csv` - 273,312 subs (trước khi lọc)
- `recommendations_with_risk_full.csv` - 273,312 subs (có risk score)

### Summary files:
- `final_summary_with_risk.csv` - Thống kê tổng quan

---

## 🚀 CÁCH CHẠY

### Pipeline đầy đủ:

```bash
# Bước 1: Tạo recommendations với business rules
python3 scripts/phase3_models/03_recommendation_with_correct_arpu.py
# Output: 273,312 subscribers

# Bước 2: Lọc bad debt risk
python3 scripts/phase3_models/04_apply_bad_debt_risk_filter.py
# Output: 198,004 subscribers (72.4% pass rate)
```

**Total time:** ~2 phút

---

## ✅ VALIDATION

```bash
# Check file count
wc -l output/recommendations/recommendations_final_filtered.csv
# Expected: 198,005 (198,004 + header)

# Check revenue
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('output/recommendations/recommendations_final_filtered.csv')
print(f"Total subscribers: {len(df):,}")
print(f"Total revenue: {df['revenue_per_advance'].sum():,.0f} VND")
print(f"Avg revenue/sub: {df['revenue_per_advance'].mean():,.0f} VND")
print(f"\nService type distribution:")
print(df['service_type'].value_counts())
print(f"\nRisk distribution:")
print(df['bad_debt_risk'].value_counts())
