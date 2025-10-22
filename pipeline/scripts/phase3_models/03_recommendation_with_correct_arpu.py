#!/usr/bin/env python3
"""
PHASE 3 - RECOMMENDATION WITH BUSINESS RULES
Phân loại thuê bao vào 3 loại dịch vụ ứng và tính toán mức ứng tối ưu:
1. EasyCredit (Ứng có phí 30%)
2. MBFG (Ứng không phí - lợi nhuận từ phần không dùng)
3. ungsanluong (Ứng sản lượng - voice/SMS users)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("PHASE 3 - RECOMMENDATION WITH BUSINESS RULES")
print("Phân loại service type và tính advance amount dựa trên business rules")
print("="*100)

start_time = datetime.now()

# ==================== LOAD DATA ====================
print("\n[1/6] Loading target subscribers from clustering...")
# Load Group 2 subscribers (expansion targets) from phase3a clustering
df_group2 = pd.read_csv('/data/ut360/output/expansion_group2_all_targets.csv')
print(f"  Group 2 expansion targets from clustering: {len(df_group2):,}")

# Get list of ISDNs to work with
target_isdns = df_group2['isdn'].unique()
print(f"  Unique subscribers to process: {len(target_isdns):,}")

# Load feature data
print("\n[2/6] Loading feature data...")
df_features = pd.read_parquet('/data/ut360/output/datasets/dataset_with_features_202503-202508_CORRECTED.parquet')
print(f"  Total feature records: {len(df_features):,}")

# Filter for target ISDNs and latest month only
df_latest = df_features[
    (df_features['isdn'].isin(target_isdns)) &
    (df_features['data_month'] == '202508')
].drop_duplicates(subset=['isdn'], keep='first').copy()
print(f"  Matched subscribers in August data: {len(df_latest):,}")

# IMPORTANT: Filter for PRE (prepaid) subscribers only
# Business rule: Only offer advance service to prepaid subscribers
if 'subscriber_type' in df_latest.columns:
    initial_count = len(df_latest)
    df_latest = df_latest[df_latest['subscriber_type'] == 'PRE'].copy()
    print(f"  ✓ Filtered for PRE subscribers only: {len(df_latest):,} (removed {initial_count - len(df_latest):,} POS)")
else:
    print(f"  ⚠️ Warning: subscriber_type column not found, proceeding without filter")

# ==================== CALCULATE ARPU ====================
print("\n[3/6] Loading ARPU data from master file...")
df_master = pd.read_parquet('/data/ut360/output/master_with_arpu_correct_202503-202509.parquet')
df_arpu = df_master[
    (df_master['isdn'].isin(target_isdns)) &
    (df_master['data_month'] == '202508')
][['isdn', 'arpu_call', 'arpu_sms', 'arpu_data', 'arpu_total']].copy()
df_arpu = df_arpu.drop_duplicates(subset=['isdn'], keep='first')
print(f"  ARPU records matched: {len(df_arpu):,}")

# Merge ARPU into main dataset
df_latest = df_latest.merge(df_arpu, on='isdn', how='left', suffixes=('', '_y'))
# Drop duplicate columns if any
df_latest = df_latest[[col for col in df_latest.columns if not col.endswith('_y')]]

# Fill missing ARPU with 0
for col in ['arpu_call', 'arpu_sms', 'arpu_data', 'arpu_total']:
    if col not in df_latest.columns:
        df_latest[col] = 0
    else:
        df_latest[col] = df_latest[col].fillna(0)

print(f"  ✓ ARPU data merged")

# ==================== CALCULATE VOICE/SMS PERCENTAGE ====================
print("\n[4/6] Calculating voice_sms_pct...")
df_latest['arpu'] = df_latest['arpu_total']
df_latest['voice_sms_pct'] = np.where(
    df_latest['arpu'] > 0,
    ((df_latest['arpu_call'] + df_latest['arpu_sms']) / df_latest['arpu'] * 100),
    0
)
print(f"  ✓ voice_sms_pct calculated")
print(f"    Mean: {df_latest['voice_sms_pct'].mean():.2f}%")
print(f"    Median: {df_latest['voice_sms_pct'].median():.2f}%")

# ==================== USAGE TIME TABLE ====================
def get_usage_time_hours(advance_amount):
    """Bảng thời gian sử dụng (chỉ áp dụng cho MBFG)"""
    if advance_amount <= 5000:
        return 24
    elif advance_amount <= 15000:
        return 36
    elif advance_amount <= 30000:
        return 48
    else:
        return 60

# ==================== SERVICE TYPE CLASSIFICATION ====================
print("\n[5/6] Classifying service types based on business rules...")

# Initialize columns
df_latest['service_type'] = 'Unknown'
df_latest['advance_amount'] = 0
df_latest['usage_time_hours'] = 0
df_latest['revenue_per_advance'] = 0
df_latest['classification_reason'] = ''

# Fill missing topup columns with 0
for col in ['topup_count_last_1m', 'topup_amount_last_1m', 'topup_count_last_2m', 'avg_topup_amount']:
    if col not in df_latest.columns:
        df_latest[col] = 0
    else:
        df_latest[col] = df_latest[col].fillna(0)

# Rule 1: ungsanluong (Voice/SMS users)
mask_ungsanluong = (df_latest['voice_sms_pct'] > 70)
df_latest.loc[mask_ungsanluong, 'service_type'] = 'ungsanluong'
df_latest.loc[mask_ungsanluong, 'classification_reason'] = 'voice_sms_pct > 70%'

# For ungsanluong, calculate advance amount based on daily usage
# Assume: daily_usage represents VND per day
# Usage time for ungsanluong: Assume same as MBFG table for now (can be adjusted)
df_latest.loc[mask_ungsanluong, 'advance_amount'] = np.minimum(
    np.maximum(
        df_latest.loc[mask_ungsanluong, 'arpu'] * 0.8,  # 80% of ARPU
        10000  # Minimum 10k
    ),
    50000  # Maximum 50k
).round(-3)  # Round to nearest 1000

# Revenue for ungsanluong: Assume 20% markup on average
df_latest.loc[mask_ungsanluong, 'revenue_per_advance'] = df_latest.loc[mask_ungsanluong, 'advance_amount'] * 0.20

# Usage time for ungsanluong: Use same table as MBFG
df_latest.loc[mask_ungsanluong, 'usage_time_hours'] = df_latest.loc[mask_ungsanluong, 'advance_amount'].apply(get_usage_time_hours)

# Rule 2: EasyCredit (Có phí 30%)
# Điều kiện:
# - Nạp ít nhất 1 lần/tháng, mỗi lần >= 50k (hoặc trung bình >= 50k)
# - Ổn định trong 2 tháng liên tiếp
mask_easycredit = (
    (~mask_ungsanluong) &  # Chưa được phân vào ungsanluong
    (df_latest['topup_count_last_1m'] >= 1) &
    (
        (df_latest['topup_amount_last_1m'] >= 50000) |  # Tổng nạp >= 50k
        (df_latest['avg_topup_amount'] >= 50000)  # Hoặc trung bình >= 50k
    ) &
    (df_latest['topup_count_last_2m'] >= 1)  # Có nạp trong 2 tháng
)

df_latest.loc[mask_easycredit, 'service_type'] = 'EasyCredit'
df_latest.loc[mask_easycredit, 'classification_reason'] = 'topup >= 50k/month, consistent 2 months'

# For EasyCredit: Calculate advance amount
# Offer 25k for most, 50k for high ARPU (>100k)
df_latest.loc[mask_easycredit, 'advance_amount'] = np.where(
    df_latest.loc[mask_easycredit, 'arpu'] > 100000,
    50000,  # VIP users
    25000   # Default
)

# Revenue for EasyCredit: 30% fee
df_latest.loc[mask_easycredit, 'revenue_per_advance'] = df_latest.loc[mask_easycredit, 'advance_amount'] * 0.30

# Usage time for EasyCredit: UNLIMITED (until SIM locked)
df_latest.loc[mask_easycredit, 'usage_time_hours'] = -1  # -1 = unlimited

# Rule 3: MBFG (Không phí - profit from unused)
# Điều kiện: Nạp >= 2 lần/tháng, mỗi lần ~20k (<50k)
mask_mbfg = (
    (~mask_ungsanluong) &  # Chưa được phân vào ungsanluong
    (~mask_easycredit) &   # Chưa được phân vào EasyCredit
    (df_latest['topup_count_last_1m'] >= 2)
)

df_latest.loc[mask_mbfg, 'service_type'] = 'MBFG'
df_latest.loc[mask_mbfg, 'classification_reason'] = 'topup >= 2 times/month, amount < 50k'

# For MBFG: Calculate advance amount based on ARPU
# Offer ~1.2x ARPU to ensure they don't use all
df_latest.loc[mask_mbfg, 'advance_amount'] = np.minimum(
    np.maximum(
        (df_latest.loc[mask_mbfg, 'arpu'] * 1.2).round(-3),  # Round to nearest 1000
        10000  # Minimum 10k
    ),
    50000  # Maximum 50k
)

# Revenue for MBFG: Assume 30% unused on average (conservative estimate)
df_latest.loc[mask_mbfg, 'revenue_per_advance'] = df_latest.loc[mask_mbfg, 'advance_amount'] * 0.30

# Usage time for MBFG: From table
df_latest.loc[mask_mbfg, 'usage_time_hours'] = df_latest.loc[mask_mbfg, 'advance_amount'].apply(get_usage_time_hours)

# Fallback: For remaining subscribers (don't meet any criteria)
# Assign to MBFG with minimum 10k
mask_unknown = (df_latest['service_type'] == 'Unknown')
if mask_unknown.sum() > 0:
    df_latest.loc[mask_unknown, 'service_type'] = 'MBFG'
    df_latest.loc[mask_unknown, 'advance_amount'] = 10000
    df_latest.loc[mask_unknown, 'revenue_per_advance'] = 3000  # 30% of 10k
    df_latest.loc[mask_unknown, 'usage_time_hours'] = 24
    df_latest.loc[mask_unknown, 'classification_reason'] = 'fallback - default to MBFG 10k'

print(f"  ✓ Service types classified")

# ==================== STATISTICS ====================
print("\n[6/6] Classification Results:")
print("\n" + "="*100)
print("📊 SERVICE TYPE DISTRIBUTION")
print("="*100)

service_counts = df_latest['service_type'].value_counts()
for service in ['EasyCredit', 'MBFG', 'ungsanluong']:
    if service in service_counts.index:
        count = service_counts[service]
        pct = count / len(df_latest) * 100
        avg_arpu = df_latest[df_latest['service_type'] == service]['arpu'].mean()
        avg_advance = df_latest[df_latest['service_type'] == service]['advance_amount'].mean()
        avg_revenue = df_latest[df_latest['service_type'] == service]['revenue_per_advance'].mean()
        avg_voice_sms_pct = df_latest[df_latest['service_type'] == service]['voice_sms_pct'].mean()

        print(f"\n  {service}: {count:,} subscribers ({pct:.1f}%)")
        print(f"    - Avg ARPU: {avg_arpu:,.0f} VND")
        print(f"    - Avg Advance Amount: {avg_advance:,.0f} VND")
        print(f"    - Avg Revenue per Advance: {avg_revenue:,.0f} VND")
        print(f"    - Avg voice_sms_pct: {avg_voice_sms_pct:.2f}%")

        if service == 'EasyCredit':
            print(f"    - Usage time: UNLIMITED (until SIM locked)")
            print(f"    - Fee: 30% of advance amount")
        elif service == 'MBFG':
            print(f"    - Usage time: 24-60 hours (based on amount)")
            print(f"    - Profit: From unused portion")
        elif service == 'ungsanluong':
            print(f"    - Usage time: 24-60 hours (based on amount)")
            print(f"    - Profit: Markup on voice/SMS usage")

print("\n" + "="*100)
print("📊 ADVANCE AMOUNT DISTRIBUTION")
print("="*100)

advance_bins = [0, 5000, 10000, 15000, 25000, 50000, 100000]
advance_labels = ['<5k', '5k-10k', '10k-15k', '15k-25k', '25k-50k', '>50k']
df_latest['advance_bin'] = pd.cut(df_latest['advance_amount'], bins=advance_bins, labels=advance_labels)

for label in advance_labels:
    count = (df_latest['advance_bin'] == label).sum()
    if count > 0:
        pct = count / len(df_latest) * 100
        print(f"  {label}: {count:,} ({pct:.1f}%)")

# ==================== SAVE RESULTS ====================
print("\n[7/7] Saving results...")

# Select final columns
output_cols = [
    'isdn', 'subscriber_type', 'service_type', 'advance_amount', 'usage_time_hours', 'revenue_per_advance',
    'arpu', 'arpu_call', 'arpu_sms', 'arpu_data', 'voice_sms_pct',
    'topup_count_last_1m', 'topup_amount_last_1m', 'avg_topup_amount',
    'classification_reason'
]

# Make sure all columns exist
for col in output_cols:
    if col not in df_latest.columns:
        if col == 'subscriber_type':
            df_latest[col] = 'PRE'  # Default to PRE if column missing
        else:
            df_latest[col] = 0

df_output = df_latest[output_cols].copy()

# Save to CSV
output_file = 'output/recommendations/final_recommendations_with_business_rules.csv'
df_output.to_csv(output_file, index=False)
print(f"  ✓ Saved: {output_file} ({len(df_output):,} subscribers)")

# Save summary statistics
summary = {
    'total_subscribers': len(df_output),
    'easycredit_count': service_counts.get('EasyCredit', 0),
    'easycredit_pct': service_counts.get('EasyCredit', 0) / len(df_output) * 100,
    'mbfg_count': service_counts.get('MBFG', 0),
    'mbfg_pct': service_counts.get('MBFG', 0) / len(df_output) * 100,
    'ungsanluong_count': service_counts.get('ungsanluong', 0),
    'ungsanluong_pct': service_counts.get('ungsanluong', 0) / len(df_output) * 100,
    'total_revenue_potential': df_output['revenue_per_advance'].sum(),
    'avg_revenue_per_subscriber': df_output['revenue_per_advance'].mean()
}

summary_df = pd.DataFrame([summary])
summary_file = 'output/recommendations/business_rules_summary.csv'
summary_df.to_csv(summary_file, index=False)
print(f"  ✓ Saved summary: {summary_file}")

# Save by service type
for service in ['EasyCredit', 'MBFG', 'ungsanluong']:
    service_df = df_output[df_output['service_type'] == service]
    if len(service_df) > 0:
        service_file = f'output/recommendations/recommendations_{service.lower()}.csv'
        service_df.to_csv(service_file, index=False)
        print(f"  ✓ Saved {service}: {service_file} ({len(service_df):,})")

elapsed = datetime.now() - start_time

print("\n" + "="*100)
print(f"✅ RECOMMENDATION COMPLETED in {elapsed}")
print(f"   Total subscribers: {len(df_output):,}")
print(f"   Total revenue potential: {df_output['revenue_per_advance'].sum():,.0f} VND")
print(f"   Avg revenue per subscriber: {df_output['revenue_per_advance'].mean():,.0f} VND")
print("="*100)
