#!/usr/bin/env python3
"""
PHASE 4 - APPLY BAD DEBT RISK FILTER
Ghép recommendations với logic lọc nợ xấu để ra file cuối cùng
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("="*100)
print("PHASE 4 - APPLY BAD DEBT RISK FILTER")
print("Lọc bad debt risk từ recommendations với business rules")
print("="*100)

start_time = datetime.now()

# ==================== LOAD RECOMMENDATIONS ====================
print("\n[1/5] Loading recommendations with business rules...")
df = pd.read_csv('/data/ut360/output/recommendations/final_recommendations_with_business_rules.csv')
print(f"  Total recommendations: {len(df):,}")

# Show current distribution
print("\n  Current service type distribution:")
for service in ['EasyCredit', 'MBFG', 'ungsanluong']:
    count = (df['service_type'] == service).sum()
    pct = count / len(df) * 100
    print(f"    - {service}: {count:,} ({pct:.1f}%)")

# ==================== CALCULATE BAD DEBT RISK ====================
print("\n[2/5] Calculating bad debt risk...")

# Initialize risk score
df['risk_score'] = 50  # Start at neutral

# Feature 1: Topup vs Advance (MOST IMPORTANT - 40%)
# Nếu nạp tiền >= số tiền ứng → giảm risk mạnh
df['topup_advance_ratio'] = np.where(
    df['advance_amount'] > 0,
    df['topup_amount_last_1m'] / df['advance_amount'],
    0
)

# Apply topup-based risk adjustment
df.loc[df['topup_amount_last_1m'] >= df['advance_amount'], 'risk_score'] -= 40  # Strong reduction
df.loc[(df['topup_amount_last_1m'] > 0) & (df['topup_amount_last_1m'] < df['advance_amount']), 'risk_score'] -= 10  # Some reduction
df.loc[df['topup_amount_last_1m'] == 0, 'risk_score'] += 40  # Strong increase

# MBFG ADJUSTMENT: Free service relies on profit from unused portion, not direct topup
# Users with topup_amount=0 are still valuable if they have good historical behavior
mask_mbfg = df['service_type'] == 'MBFG'
df.loc[mask_mbfg & (df['topup_amount_last_1m'] == 0), 'risk_score'] -= 20  # Reduce penalty from +40 to +20

# Feature 2: Topup frequency (20%)
df.loc[df['topup_count_last_1m'] >= 3, 'risk_score'] -= 15
df.loc[df['topup_count_last_1m'] == 2, 'risk_score'] -= 10
df.loc[df['topup_count_last_1m'] == 1, 'risk_score'] -= 5
df.loc[df['topup_count_last_1m'] == 0, 'risk_score'] += 20

# Feature 3: ARPU stability (20%)
# MBFG ADJUSTMENT: Increase weight on ARPU since it indicates spending capacity
df.loc[df['arpu'] >= 5000, 'risk_score'] -= 15
df.loc[(df['arpu'] >= 2000) & (df['arpu'] < 5000), 'risk_score'] -= 10
df.loc[(df['arpu'] >= 1000) & (df['arpu'] < 2000), 'risk_score'] -= 5
df.loc[df['arpu'] < 500, 'risk_score'] += 10

# MBFG BOOST: Extra reduction for ARPU >= 2000 (shows spending capacity)
df.loc[mask_mbfg & (df['arpu'] >= 2000), 'risk_score'] -= 10

# Feature 4: Average topup amount (20%)
df.loc[df['avg_topup_amount'] >= 100000, 'risk_score'] -= 15
df.loc[(df['avg_topup_amount'] >= 50000) & (df['avg_topup_amount'] < 100000), 'risk_score'] -= 10
df.loc[(df['avg_topup_amount'] >= 20000) & (df['avg_topup_amount'] < 50000), 'risk_score'] -= 5
df.loc[(df['avg_topup_amount'] > 0) & (df['avg_topup_amount'] < 10000), 'risk_score'] += 5

# MBFG BOOST: Extra reduction for avg_topup >= 20k (historical good behavior)
df.loc[mask_mbfg & (df['avg_topup_amount'] >= 20000), 'risk_score'] -= 10

# Classify risk level based on risk_score
def classify_risk(score):
    if score <= 30:
        return 'LOW'
    elif score <= 60:
        return 'MEDIUM'
    else:
        return 'HIGH'

df['bad_debt_risk'] = df['risk_score'].apply(classify_risk)

print(f"  ✓ Bad debt risk calculated")

# ==================== STATISTICS ====================
print("\n[3/5] Risk Distribution:")
print("\n" + "="*100)
print("📊 BAD DEBT RISK BREAKDOWN")
print("="*100)

risk_counts = df['bad_debt_risk'].value_counts()
for risk in ['LOW', 'MEDIUM', 'HIGH']:
    if risk in risk_counts.index:
        count = risk_counts[risk]
        pct = count / len(df) * 100
        avg_topup = df[df['bad_debt_risk'] == risk]['topup_amount_last_1m'].mean()
        avg_advance = df[df['bad_debt_risk'] == risk]['advance_amount'].mean()
        avg_ratio = df[df['bad_debt_risk'] == risk]['topup_advance_ratio'].mean()

        print(f"\n  {risk} risk: {count:,} ({pct:.1f}%)")
        print(f"    - Avg topup last month: {avg_topup:,.0f} VND")
        print(f"    - Avg advance amount: {avg_advance:,.0f} VND")
        print(f"    - Avg topup/advance ratio: {avg_ratio:.2f}x")

# Show breakdown by service type
print("\n" + "="*100)
print("📊 RISK BY SERVICE TYPE")
print("="*100)

for service in ['EasyCredit', 'MBFG', 'ungsanluong']:
    df_service = df[df['service_type'] == service]
    print(f"\n  {service}:")
    for risk in ['LOW', 'MEDIUM', 'HIGH']:
        count = (df_service['bad_debt_risk'] == risk).sum()
        if count > 0:
            pct = count / len(df_service) * 100
            print(f"    - {risk}: {count:,} ({pct:.1f}%)")

# ==================== FILTER HIGH RISK ====================
print("\n[4/5] Filtering high risk subscribers...")

initial_count = len(df)
df_filtered = df[df['bad_debt_risk'].isin(['LOW', 'MEDIUM'])].copy()
filtered_count = len(df_filtered)
removed_count = initial_count - filtered_count

print(f"  ✓ Filtered {removed_count:,} HIGH risk subscribers")
print(f"  ✓ Kept {filtered_count:,} LOW + MEDIUM risk subscribers ({filtered_count/initial_count*100:.1f}%)")

# Show final distribution
print("\n" + "="*100)
print("📊 FINAL DISTRIBUTION (After filtering HIGH risk)")
print("="*100)

for service in ['EasyCredit', 'MBFG', 'ungsanluong']:
    count = (df_filtered['service_type'] == service).sum()
    pct = count / len(df_filtered) * 100
    avg_revenue = df_filtered[df_filtered['service_type'] == service]['revenue_per_advance'].mean()
    total_revenue = df_filtered[df_filtered['service_type'] == service]['revenue_per_advance'].sum()

    print(f"\n  {service}: {count:,} ({pct:.1f}%)")
    print(f"    - Avg revenue: {avg_revenue:,.0f} VND")
    print(f"    - Total revenue: {total_revenue:,.0f} VND")

total_revenue = df_filtered['revenue_per_advance'].sum()
avg_revenue = df_filtered['revenue_per_advance'].mean()
print(f"\n  TOTAL: {len(df_filtered):,} subscribers")
print(f"    - Total revenue potential: {total_revenue:,.0f} VND")
print(f"    - Avg revenue/subscriber: {avg_revenue:,.0f} VND")

# ==================== SAVE RESULTS ====================
print("\n[5/5] Saving final results...")

# Save full file with risk scores
output_full = 'output/recommendations/recommendations_with_risk_full.csv'
df.to_csv(output_full, index=False)
print(f"  ✓ Saved full file: {output_full} ({len(df):,} subscribers)")

# Save filtered file (LOW + MEDIUM only) - THIS IS THE FINAL OUTPUT
output_filtered = 'output/recommendations/recommendations_final_filtered.csv'
df_filtered.to_csv(output_filtered, index=False)
print(f"  ✓ Saved filtered file: {output_filtered} ({len(df_filtered):,} subscribers)")

# Save by service type (filtered)
for service in ['EasyCredit', 'MBFG', 'ungsanluong']:
    df_service = df_filtered[df_filtered['service_type'] == service]
    if len(df_service) > 0:
        output_file = f'output/recommendations/final_{service.lower()}_filtered.csv'
        df_service.to_csv(output_file, index=False)
        print(f"  ✓ Saved {service}: {output_file} ({len(df_service):,})")

# Save summary statistics
summary = {
    'total_subscribers_initial': len(df),
    'total_subscribers_filtered': len(df_filtered),
    'high_risk_removed': removed_count,
    'pass_rate_pct': filtered_count / initial_count * 100,
    'easycredit_count': (df_filtered['service_type'] == 'EasyCredit').sum(),
    'mbfg_count': (df_filtered['service_type'] == 'MBFG').sum(),
    'ungsanluong_count': (df_filtered['service_type'] == 'ungsanluong').sum(),
    'total_revenue_potential': df_filtered['revenue_per_advance'].sum(),
    'avg_revenue_per_subscriber': df_filtered['revenue_per_advance'].mean(),
    'low_risk_count': (df_filtered['bad_debt_risk'] == 'LOW').sum(),
    'medium_risk_count': (df_filtered['bad_debt_risk'] == 'MEDIUM').sum()
}

summary_df = pd.DataFrame([summary])
summary_file = 'output/recommendations/final_summary_with_risk.csv'
summary_df.to_csv(summary_file, index=False)
print(f"  ✓ Saved summary: {summary_file}")

elapsed = datetime.now() - start_time

print("\n" + "="*100)
print(f"✅ BAD DEBT RISK FILTER COMPLETED in {elapsed}")
print(f"   Initial: {initial_count:,} subscribers")
print(f"   Filtered: {filtered_count:,} subscribers ({filtered_count/initial_count*100:.1f}% pass rate)")
print(f"   HIGH risk removed: {removed_count:,} ({removed_count/initial_count*100:.1f}%)")
print(f"   Total revenue potential: {total_revenue:,.0f} VND")
print("="*100)
print(f"\n🎯 FINAL OUTPUT FILE: {output_filtered}")
print("="*100)
