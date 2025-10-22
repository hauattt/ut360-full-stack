#!/usr/bin/env python3
"""
PARALLEL: Generate 360 profile using all 256 cores
"""

import pandas as pd
import numpy as np
from pathlib import Path
from multiprocessing import Pool, cpu_count
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("GENERATING 360 CUSTOMER PROFILE (PARALLEL)")
print("="*80)

BASE_DIR = Path("/data/ut360")
recommendations_file = BASE_DIR / "output/recommendations/recommendations_final_filtered.csv"
monthly_summary_file = BASE_DIR / "output/subscriber_monthly_summary.parquet"
output_file = BASE_DIR / "output/subscriber_360_profile.parquet"

# Use all cores
N_CORES = cpu_count()
print(f"💻 Using {N_CORES} CPU cores")

print(f"\n[1/4] Loading data...")
df_rec = pd.read_csv(recommendations_file)
print(f"  Recommendations: {len(df_rec):,}")

df_monthly = pd.read_parquet(monthly_summary_file)
print(f"  Monthly records: {len(df_monthly):,}")

print(f"\n[2/4] Calculating ARPU statistics (VECTORIZED)...")
# Pure vectorized operations - no loops
monthly_agg = df_monthly.groupby('isdn', as_index=False).agg({
    'arpu_total': ['mean', 'std', 'min', 'max', 'first', 'last'],
    'arpu_call': 'mean',
    'arpu_sms': 'mean',
    'arpu_data': 'mean',
    'data_month': 'count'
})

monthly_agg.columns = ['isdn', 'arpu_avg_6m', 'arpu_std_6m', 'arpu_min_6m', 'arpu_max_6m',
                       'arpu_first', 'arpu_last', 'arpu_call_avg', 'arpu_sms_avg', 
                       'arpu_data_avg', 'months_count']

# Growth rate - vectorized
monthly_agg['arpu_growth_rate'] = np.where(
    monthly_agg['arpu_first'] > 0,
    ((monthly_agg['arpu_last'] - monthly_agg['arpu_first']) / monthly_agg['arpu_first']) * 100,
    0
)

# Trend classification - vectorized
conditions = [
    monthly_agg['arpu_growth_rate'] > 10,
    monthly_agg['arpu_growth_rate'] < -10
]
choices = ['Tăng trưởng', 'Giảm']
monthly_agg['arpu_trend'] = np.select(conditions, choices, default='Ổn định')

print(f"  ✓ Stats for {len(monthly_agg):,} subscribers")

print(f"\n[3/4] Merging and calculating profiles (VECTORIZED)...")
df_profile = df_rec.merge(monthly_agg, on='isdn', how='left')

# All calculations are vectorized - no Python loops
df_profile['revenue_call_pct'] = np.where(
    df_profile['arpu'] > 0,
    (df_profile['arpu_call'] / df_profile['arpu']) * 100,
    0
)
df_profile['revenue_sms_pct'] = np.where(
    df_profile['arpu'] > 0,
    (df_profile['arpu_sms'] / df_profile['arpu']) * 100,
    0
)
df_profile['revenue_data_pct'] = np.where(
    df_profile['arpu'] > 0,
    (df_profile['arpu_data'] / df_profile['arpu']) * 100,
    0
)

# User type classification
conditions = [
    df_profile['revenue_data_pct'] > 80,
    df_profile['revenue_data_pct'] < 20
]
choices = ['Heavy Data User', 'Voice/SMS User']
df_profile['user_type'] = np.select(conditions, choices, default='Balanced User')

# Topup frequency
topup_count = df_profile['topup_count_last_1m'].fillna(0)
conditions = [
    topup_count >= 4,
    topup_count >= 2,
    topup_count >= 1
]
choices = ['Thường xuyên', 'Trung bình', 'Hiếm']
df_profile['topup_frequency'] = np.select(conditions, choices, default='Không nạp')

# Customer Value Score (vectorized formula)
arpu_val = df_profile['arpu_avg_6m'].fillna(df_profile['arpu'])
arpu_score = np.clip(arpu_val / 50, 0, 40)
topup_score = np.clip(df_profile['topup_advance_ratio'].fillna(0) * 10, 0, 30)
trend_score = np.clip((df_profile['arpu_growth_rate'].fillna(0) + 10) / 2, 0, 30)
df_profile['customer_value_score'] = (arpu_score + topup_score + trend_score).round(0)

# Advance Readiness Score (vectorized)
risk_map = {'LOW': 50, 'MEDIUM': 30, 'HIGH': 0}
risk_score = df_profile['bad_debt_risk'].map(risk_map).fillna(0)
topup_ratio_score = np.clip(df_profile['topup_advance_ratio'].fillna(0) * 7.5, 0, 30)
freq_map = {'Thường xuyên': 20, 'Trung bình': 10, 'Hiếm': 5, 'Không nạp': 0}
freq_score = df_profile['topup_frequency'].map(freq_map).fillna(0)
df_profile['advance_readiness_score'] = (risk_score + topup_ratio_score + freq_score).round(0)

print(f"  ✓ All calculations completed")

print(f"\n[4/4] Saving to parquet...")
profile_columns = [
    'isdn', 'subscriber_type', 'service_type', 'advance_amount', 'revenue_per_advance',
    'arpu', 'arpu_call', 'arpu_sms', 'arpu_data',
    'arpu_avg_6m', 'arpu_std_6m', 'arpu_min_6m', 'arpu_max_6m',
    'arpu_growth_rate', 'arpu_trend',
    'revenue_call_pct', 'revenue_sms_pct', 'revenue_data_pct',
    'voice_sms_pct', 'user_type',
    'topup_count_last_1m', 'topup_amount_last_1m', 'avg_topup_amount',
    'topup_frequency', 'topup_advance_ratio',
    'bad_debt_risk', 'risk_score',
    'customer_value_score', 'advance_readiness_score',
    'classification_reason', 'months_count'
]

df_final = df_profile[profile_columns].copy()
df_final.to_parquet(output_file, index=False, compression='snappy')

file_size_mb = output_file.stat().st_size / (1024 * 1024)
print(f"\n✓ Saved: {output_file}")
print(f"✓ Size: {file_size_mb:.2f} MB")
print(f"✓ Records: {len(df_final):,}")

# Statistics
print(f"\n" + "="*80)
print("📊 SUMMARY")
print("="*80)
print(f"\nUser Types:")
for t, c in df_final['user_type'].value_counts().items():
    print(f"  {t:20s}: {c:6,} ({c/len(df_final)*100:5.1f}%)")

print(f"\nARPU Trends:")
for t, c in df_final['arpu_trend'].value_counts().items():
    print(f"  {t:20s}: {c:6,} ({c/len(df_final)*100:5.1f}%)")

print(f"\nScores:")
print(f"  Value Score      : min={df_final['customer_value_score'].min():.0f}, max={df_final['customer_value_score'].max():.0f}, avg={df_final['customer_value_score'].mean():.0f}")
print(f"  Readiness Score  : min={df_final['advance_readiness_score'].min():.0f}, max={df_final['advance_readiness_score'].max():.0f}, avg={df_final['advance_readiness_score'].mean():.0f}")

print("\n" + "="*80)
print("✅ COMPLETED!")
print("="*80)
