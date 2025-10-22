"""
PHASE 2: FEATURE ENGINEERING - OPTIMIZED VERSION
NO LOOPS - Pure vectorized operations for 50M records
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("PHASE 2: FEATURE ENGINEERING - OPTIMIZED (NO LOOPS)")
print("="*100)

# Config
DATA_FILE = Path('/data/ut360/output/datasets/master_full_202503-202508.parquet')
OUTPUT_DIR = Path('/data/ut360/output/datasets')

start_time = datetime.now()

# Load data
print("\n[1/5] Loading data...")
df = pd.read_parquet(DATA_FILE)
print(f"  Records: {len(df):,}")

# Sort for rolling operations
df['month_int'] = df['data_month'].astype(int)
df = df.sort_values(['isdn', 'month_int'])

# ==================== TIER 1: ADVANCE HISTORY (11 features) ====================
print("\n[2/5] TIER 1A: ADVANCE HISTORY...")

# Rolling advance features (vectorized)
for window in [1, 2, 3]:
    df[f'advance_count_last_{window}m'] = (
        df.groupby('isdn')['advance_count']
        .rolling(window=window, min_periods=1)
        .sum()
        .shift(1)
        .reset_index(0, drop=True)
        .fillna(0)
    )
    print(f"  ✓ advance_count_last_{window}m")

# Cumsum for history flag
df['has_advance_history'] = (
    df.groupby('isdn')['advance_count']
    .cumsum()
    .shift(1, fill_value=0) > 0
).astype(int)
print(f"  ✓ has_advance_history")

# Months since last advance (simplified)
# Mark months with advance
df['had_advance'] = (df['advance_count'] > 0).astype(int)
# Forward fill last advance month per subscriber
df['last_advance_month'] = df[df['had_advance'] == 1].groupby('isdn')['month_int'].ffill()
df['last_advance_month'] = df.groupby('isdn')['last_advance_month'].ffill()
# Calculate difference
df['months_since_last_advance'] = (df['month_int'] - df['last_advance_month']).fillna(99).astype(int)
df = df.drop(columns=['had_advance', 'last_advance_month'])
print(f"  ✓ months_since_last_advance")

# Repayment indicators
df['is_good_payer'] = (df['avg_repayment_rate'] >= 0.95).astype(int)
df['has_outstanding_debt'] = (df['outstanding_debt'] > 0).astype(int)
df['is_repeat_advancer'] = (df['advance_count'] > 1).astype(int)
print(f"  ✓ is_good_payer, has_outstanding_debt, is_repeat_advancer")

print(f"✅ Created 11 advance history features")

# ==================== TIER 1B: TOPUP INTENSITY (15 features) ====================
print("\n[3/5] TIER 1B: TOPUP INTENSITY...")

# Frequency categories
df['topup_freq_none'] = (df['topup_count'] == 0).astype(int)
df['topup_freq_low'] = ((df['topup_count'] > 0) & (df['topup_count'] <= 2)).astype(int)
df['topup_freq_medium'] = ((df['topup_count'] > 2) & (df['topup_count'] <= 5)).astype(int)
df['topup_freq_high'] = (df['topup_count'] > 5).astype(int)
print(f"  ✓ topup_freq categories")

# Heavy user indicators
topup_75 = df['topup_count'].quantile(0.75)
df['is_heavy_topup_user'] = (df['topup_count'] > topup_75).astype(int)

topup_amt_75 = df['total_topup_amount'].quantile(0.75)
df['topup_amount_high'] = (df['total_topup_amount'] > topup_amt_75).astype(int)

avg_topup_75 = df['avg_topup_amount'].quantile(0.75)
df['avg_topup_high'] = (df['avg_topup_amount'] > avg_topup_75).astype(int)
print(f"  ✓ is_heavy_topup_user, topup_amount_high, avg_topup_high")

# Volatility
df['topup_cv'] = np.where(
    df['avg_topup_amount'] > 0,
    df['std_topup_amount'] / df['avg_topup_amount'],
    0
)
df['topup_is_stable'] = (df['topup_cv'] < 0.5).astype(int)
print(f"  ✓ topup_cv, topup_is_stable")

# Rolling topup (vectorized)
for window in [1, 2, 3]:
    df[f'topup_count_last_{window}m'] = (
        df.groupby('isdn')['topup_count']
        .rolling(window=window, min_periods=1)
        .sum()
        .shift(1)
        .reset_index(0, drop=True)
        .fillna(0)
    )
    df[f'topup_amount_last_{window}m'] = (
        df.groupby('isdn')['total_topup_amount']
        .rolling(window=window, min_periods=1)
        .sum()
        .shift(1)
        .reset_index(0, drop=True)
        .fillna(0)
    )
    print(f"  ✓ topup features last_{window}m")

print(f"✅ Created 15 topup intensity features")

# ==================== TIER 1C + 2: FINANCIAL & BEHAVIORAL (20 features) ====================
print("\n[4/5] TIER 1C & 2: FINANCIAL + BEHAVIORAL...")

# Financial indicators
df['estimated_balance'] = df['total_topup_amount'] - df['total_package_value']
df['balance_is_negative'] = (df['estimated_balance'] < 0).astype(int)
df['balance_is_low'] = (df['estimated_balance'] < 50000).astype(int)
print(f"  ✓ estimated_balance, balance_is_negative, balance_is_low")

# Burn rate
df['burn_rate'] = np.where(
    df['total_topup_amount'] > 0,
    df['total_package_value'] / df['total_topup_amount'],
    999
)
df['burn_rate_capped'] = df['burn_rate'].clip(upper=5)
df['burn_rate_high'] = (df['burn_rate'] > 1.0).astype(int)
df['burn_rate_very_high'] = (df['burn_rate'] > 1.5).astype(int)
print(f"  ✓ burn_rate features")

# Financial stress composite
df['financial_stress_score'] = (
    df['balance_is_negative'].astype(int) +
    df['burn_rate_high'].astype(int) +
    df['has_outstanding_debt'].astype(int) +
    (df['topup_count'] == 0).astype(int) +
    (df['total_package_value'] > df['total_package_value'].quantile(0.9)).astype(int)
)
print(f"  ✓ financial_stress_score")

# Activity
df['is_active_user'] = (df['n3_record_count'] > 0).astype(int)
df['usage_intensity'] = df['n3_record_count']
print(f"  ✓ is_active_user, usage_intensity")

# Package behavior
df['has_multiple_packages'] = (df['num_packages'] > 1).astype(int)
pkg_75 = df['total_package_value'].quantile(0.75)
df['has_high_value_package'] = (df['total_package_value'] > pkg_75).astype(int)
df['package_per_topup_ratio'] = np.where(
    df['topup_count'] > 0,
    df['num_packages'] / df['topup_count'],
    0
)
print(f"  ✓ package features")

# Profile
df['is_prepaid'] = (df['subscriber_type'] == 'PRE').astype(int)
df['is_active_status'] = (df['subscriber_status'] == 'ACTIF').astype(int)
print(f"  ✓ is_prepaid, is_active_status")

# Tenure (if available)
if 'activation_date' in df.columns:
    df['activation_date'] = pd.to_datetime(df['activation_date'], errors='coerce')
    ref_date = pd.to_datetime('2025-08-01')
    df['subscriber_tenure_days'] = (ref_date - df['activation_date']).dt.days.clip(lower=0)
    df['is_new_subscriber'] = (df['subscriber_tenure_days'] < 90).astype(int)
    df['is_mature_subscriber'] = (df['subscriber_tenure_days'] > 365).astype(int)
    print(f"  ✓ tenure features")

print(f"✅ Created 20 financial + behavioral features")

# ==================== TIER 3: INTERACTIONS (4 features) ====================
print("\n[5/5] TIER 3: INTERACTIONS...")

df['heavy_user_good_payer'] = df['is_heavy_topup_user'] * df['is_good_payer']
df['heavy_user_has_debt'] = df['is_heavy_topup_user'] * df['has_outstanding_debt']
df['high_topup_high_package'] = df['topup_amount_high'] * df['has_high_value_package']
df['repeat_advance_good_payer'] = df['is_repeat_advancer'] * df['is_good_payer']
print(f"  ✓ 4 interaction features")

print(f"✅ Created 4 interaction features")

# ==================== SAVE ====================
print("\n" + "="*100)
print("SAVING...")
print("="*100)

# Cleanup
df = df.drop(columns=['month_int'], errors='ignore')

# Count features
original_cols = 30
total_new = 11 + 15 + 20 + 4
print(f"\n📊 Summary:")
print(f"  Original: {original_cols} columns")
print(f"  New features: {total_new}")
print(f"  Total: {len(df.columns)} columns")

# Save
output_file = OUTPUT_DIR / 'dataset_with_features_202503-202508_CORRECTED.parquet'
df.to_parquet(output_file, compression='snappy', index=False)

file_size_mb = output_file.stat().st_size / (1024 * 1024)
print(f"\n💾 Saved:")
print(f"  File: {output_file.name}")
print(f"  Size: {file_size_mb:.2f} MB")
print(f"  Records: {len(df):,}")

# Save feature list
new_features = [col for col in df.columns if col not in [
    'isdn', 'subscriber_type', 'subscriber_status', 'status_detail',
    'activation_date', 'expire_date', 'data_month',
    'most_used_advance_service', 'most_used_topup_channel',
    'has_advance_in_month'
]]

feature_df = pd.DataFrame({'Feature': new_features})
feature_list_file = OUTPUT_DIR / 'feature_list.csv'
feature_df.to_csv(feature_list_file, index=False)

elapsed = datetime.now() - start_time

print(f"\n✅ COMPLETED in {elapsed}")
print(f"   Output: {output_file}")
print("="*100)
