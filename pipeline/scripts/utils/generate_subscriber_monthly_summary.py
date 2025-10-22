#!/usr/bin/env python3
"""
Generate pre-aggregated monthly summary for each subscriber
This allows fast lookup in API without loading 59M records parquet
"""

import pandas as pd
import json
from pathlib import Path

print("="*80)
print("GENERATING SUBSCRIBER MONTHLY SUMMARY")
print("="*80)

# Paths
BASE_DIR = Path("/data/ut360")
master_file = BASE_DIR / "output/master_with_arpu_correct_202503-202509.parquet"
recommendations_file = BASE_DIR / "output/recommendations/recommendations_final_filtered.csv"
output_file = BASE_DIR / "output/subscriber_monthly_summary.parquet"

print(f"\n[1/4] Loading recommendations file...")
df_rec = pd.read_csv(recommendations_file)
print(f"  Recommendations: {len(df_rec):,} subscribers")

# Get list of recommended ISDNs
recommended_isdns = set(df_rec['isdn'].unique())
print(f"  Unique ISDNs: {len(recommended_isdns):,}")

print(f"\n[2/4] Loading master file (this may take a while)...")
# Only load needed columns
columns_needed = ['isdn', 'data_month', 'arpu_call', 'arpu_sms', 'arpu_data', 'arpu_total']
df_master = pd.read_parquet(master_file, columns=columns_needed)
print(f"  Total records: {len(df_master):,}")

print(f"\n[3/4] Filtering for recommended subscribers only...")
df_filtered = df_master[df_master['isdn'].isin(recommended_isdns)]
print(f"  Filtered records: {len(df_filtered):,}")

print(f"\n[4/4] Aggregating monthly data...")
# Group by ISDN and month
monthly_summary = df_filtered.groupby(['isdn', 'data_month']).agg({
    'arpu_call': 'mean',
    'arpu_sms': 'mean',
    'arpu_data': 'mean',
    'arpu_total': 'mean'
}).reset_index()

print(f"  Summary records: {len(monthly_summary):,}")

# Save to parquet
print(f"\n[5/5] Saving to {output_file}...")
monthly_summary.to_parquet(output_file, index=False)

file_size_mb = output_file.stat().st_size / (1024 * 1024)
print(f"  File size: {file_size_mb:.2f} MB")

print("\n" + "="*80)
print("✅ COMPLETED!")
print("="*80)
print(f"\nOutput: {output_file}")
print(f"Records: {len(monthly_summary):,}")
print(f"Unique subscribers: {monthly_summary['isdn'].nunique():,}")
