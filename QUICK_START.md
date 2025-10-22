# 🚀 QUICK START GUIDE

**Version:** 4.1 Final
**Date:** 2025-10-18

---

## 📁 FILE CHÍNH

```
output/recommendations/recommendations_final_filtered.csv
```

**Thông tin:**
- **198,004 subscribers** (đã lọc bad debt risk)
- **3 service types:** fee, free, ungsanluong
- **Revenue potential:** 1.21 tỷ VND

---

## 🏃 CHẠY PIPELINE

### Bước 1: Tạo recommendations
```bash
python3 scripts/phase3_models/03_recommendation_with_correct_arpu.py
```
**Output:** 273,312 subscribers với business rules

### Bước 2: Lọc bad debt risk
```bash
python3 scripts/phase3_models/04_apply_bad_debt_risk_filter.py
```
**Output:** 198,004 subscribers (72.4% pass rate)

**Thời gian:** ~2 phút total

---

## 📊 KẾT QUẢ

| Service | Count | % | Revenue/Sub | Total Revenue | % Revenue |
|---------|-------|---|-------------|---------------|-----------|
| **fee** | 144,470 | 73.0% | 7,501 VND | 1,083.6M | **89.2%** |
| **free** | 23,114 | 11.7% | 3,005 VND | 69.5M | 5.7% |
| **ungsanluong** | 30,420 | 15.4% | 2,015 VND | 61.3M | 5.0% |

---

## 🎯 BUSINESS RULES

### 1. fee (Ứng có phí 30%)
- Điều kiện: Nạp ≥50k/tháng, 2 tháng liên tiếp
- Advance: 25k (default)
- Usage time: **UNLIMITED**
- Revenue: 30% phí

### 2. free (Ứng không phí)
- Điều kiện: Nạp ≥2 lần/tháng
- Advance: 10k (default)
- Usage time: 24-60h
- Revenue: Profit từ unused

### 3. ungsanluong (Ứng sản lượng)
- Điều kiện: voice_sms_pct > 70%
- Advance: 10k
- Usage time: 24-60h
- Revenue: 20% markup

---

## 📚 TÀI LIỆU

- [README.md](README.md) - Overview đầy đủ
- [COMPLETE_SUMMARY.md](COMPLETE_SUMMARY.md) - Chi tiết kết quả
- [docs/BUSINESS_RULES_LOGIC.md](docs/BUSINESS_RULES_LOGIC.md) - Business rules

---

## 📦 FILES CŨ

Các file cũ đã được move vào `archive/` folder.

---

**Status:** ✅ PRODUCTION READY
