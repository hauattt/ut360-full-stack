#!/usr/bin/env python3
"""
Generate summary statistics for each phase to speed up web visualization
Run this after pipeline completes to create lightweight summary files
"""

import pandas as pd
import json
from pathlib import Path

output_dir = Path('/data/ut360/output/summaries')
output_dir.mkdir(exist_ok=True)

print("Generating phase summaries...")

# ==================== PHASE 1 SUMMARY ====================
print("\n[1/5] Phase 1 - Data Loading...")
try:
    master_file = '/data/ut360/output/datasets/master_full_202503-202508.parquet'
    df = pd.read_parquet(master_file)

    # IMPORTANT: Master file has duplicate records per (isdn, month) due to multiple packages
    # Need to deduplicate before calculating totals
    df_dedup = df.groupby(['isdn', 'data_month'], as_index=False).agg({
        'subscriber_type': 'first',
        'has_advance_in_month': 'first',
        'topup_count': 'first',
        'total_advance_amount': 'first',
        'total_topup_amount': 'first'
    })

    summary = {
        "total_records": int(len(df)),
        "unique_subscribers": int(df['isdn'].nunique()),
        "months": sorted(df['data_month'].unique().tolist()),
        "advance_users": int(df_dedup[df_dedup['has_advance_in_month'] == True]['isdn'].nunique()),
        "topup_users": int(df_dedup[df_dedup['topup_count'] > 0]['isdn'].nunique()),
        "total_advance_amount": float(df_dedup['total_advance_amount'].sum()),
        "total_topup_amount": float(df_dedup['total_topup_amount'].sum())
    }

    # Subscriber type distribution (use deduplicated data)
    subscriber_type_dist = df_dedup.groupby('subscriber_type').size().to_dict()

    # Monthly statistics (use deduplicated data)
    monthly_stats = df_dedup.groupby('data_month').agg({
        'isdn': 'nunique',
        'total_topup_amount': 'sum',
        'total_advance_amount': 'sum'
    }).reset_index()
    monthly_stats.columns = ['month', 'unique_subscribers', 'total_topup', 'total_advance']

    result = {
        "summary": summary,
        "subscriber_type_distribution": subscriber_type_dist,
        "monthly_stats": monthly_stats.to_dict('records')
    }

    with open(output_dir / 'phase1_summary.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Saved: {output_dir / 'phase1_summary.json'}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ==================== PHASE 2 SUMMARY ====================
print("\n[2/5] Phase 2 - Feature Engineering...")
try:
    features_file = '/data/ut360/output/datasets/dataset_with_features_202503-202508_CORRECTED.parquet'
    df = pd.read_parquet(features_file)

    # Get feature columns
    original_cols = ['isdn', 'subscriber_type', 'subscriber_status', 'data_month']
    feature_cols = [col for col in df.columns if col not in original_cols]

    # Sample latest month
    df_latest = df[df['data_month'] == df['data_month'].max()].copy()

    # Feature categories
    advance_features = [col for col in feature_cols if 'advance' in col.lower()]
    topup_features = [col for col in feature_cols if 'topup' in col.lower()]
    financial_features = [col for col in feature_cols if any(x in col.lower() for x in ['balance', 'burn', 'arpu'])]

    # Key metrics
    key_metrics = {}
    for metric in ['topup_freq', 'financial_stress_score', 'usage_intensity']:
        if metric in df_latest.columns:
            value_counts = df_latest[metric].value_counts().to_dict()
            key_metrics[metric] = value_counts

    result = {
        "summary": {
            "total_features": len(feature_cols),
            "advance_features": len(advance_features),
            "topup_features": len(topup_features),
            "financial_features": len(financial_features),
            "total_subscribers": int(df_latest['isdn'].nunique())
        },
        "feature_categories": {
            "advance": advance_features[:10],
            "topup": topup_features[:10],
            "financial": financial_features[:10]
        },
        "key_metrics_distribution": key_metrics
    }

    with open(output_dir / 'phase2_summary.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Saved: {output_dir / 'phase2_summary.json'}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ==================== PHASE 3A SUMMARY ====================
print("\n[3/5] Phase 3A - Clustering...")
try:
    clustering_file = '/data/ut360/output/subscribers_clustered_segmentation.parquet'
    df = pd.read_parquet(clustering_file)

    # Segment distribution
    segment_dist = df.groupby('segment').agg({
        'isdn': 'count',
        'is_advance_user': 'sum'
    }).reset_index()
    segment_dist.columns = ['segment', 'total', 'advance_users']
    segment_dist['advance_rate'] = (segment_dist['advance_users'] / segment_dist['total'] * 100).round(2)

    # Cluster statistics
    cluster_stats = df.groupby('cluster').agg({
        'isdn': 'count',
        'is_advance_user': 'sum'
    }).reset_index()
    cluster_stats.columns = ['cluster', 'total', 'advance_users']
    cluster_stats['advance_rate'] = (cluster_stats['advance_users'] / cluster_stats['total'] * 100).round(2)

    result = {
        "summary": {
            "total_subscribers": int(len(df)),
            "num_clusters": int(df['cluster'].nunique()),
            "expansion_target": int(segment_dist[segment_dist['segment'].str.contains('GROUP_2', na=False)]['total'].sum())
        },
        "segment_distribution": segment_dist.to_dict('records'),
        "cluster_statistics": cluster_stats.to_dict('records')
    }

    with open(output_dir / 'phase3a_summary.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Saved: {output_dir / 'phase3a_summary.json'}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ==================== PHASE 3B SUMMARY ====================
print("\n[4/5] Phase 3B - Business Rules...")
try:
    recommendations_file = '/data/ut360/output/recommendations/final_recommendations_with_business_rules.csv'
    df = pd.read_csv(recommendations_file)

    # Detect column names (support both naming conventions)
    advance_col = 'advance_amount' if 'advance_amount' in df.columns else 'recommended_advance_amount'
    revenue_col = 'revenue_per_advance' if 'revenue_per_advance' in df.columns else 'expected_revenue'

    # Service type distribution
    service_dist = df.groupby('service_type').agg({
        'isdn': 'count',
        advance_col: 'sum',
        revenue_col: 'sum'
    }).reset_index()
    service_dist.columns = ['service_type', 'subscribers', 'total_advance', 'total_revenue']

    # Advance amount distribution
    amount_ranges = [0, 20000, 30000, 40000, 50000, 100000]
    df['amount_range'] = pd.cut(df[advance_col], bins=amount_ranges,
                                 labels=['< 20k', '20-30k', '30-40k', '40-50k', '50k+'])
    amount_dist = df['amount_range'].value_counts().to_dict()

    result = {
        "summary": {
            "total_recommendations": int(len(df)),
            "total_advance_amount": float(df[advance_col].sum()),
            "total_expected_revenue": float(df[revenue_col].sum()),
            "avg_advance_amount": float(df[advance_col].mean())
        },
        "service_type_distribution": service_dist.to_dict('records'),
        "amount_distribution": amount_dist
    }

    with open(output_dir / 'phase3b_summary.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Saved: {output_dir / 'phase3b_summary.json'}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# ==================== PHASE 4 SUMMARY ====================
print("\n[5/5] Phase 4 - Bad Debt Filter...")
try:
    final_file = '/data/ut360/output/recommendations/recommendations_final_filtered.csv'
    df = pd.read_csv(final_file)

    # Detect column names
    advance_col = 'advance_amount' if 'advance_amount' in df.columns else 'recommended_advance_amount'
    revenue_col = 'revenue_per_advance' if 'revenue_per_advance' in df.columns else 'expected_revenue'

    # Risk level distribution
    risk_dist = {}
    if 'bad_debt_risk_level' in df.columns:
        risk_dist = df['bad_debt_risk_level'].value_counts().to_dict()

    # Service type after filtering
    service_dist = df.groupby('service_type').agg({
        'isdn': 'count',
        advance_col: 'sum',
        revenue_col: 'sum'
    }).reset_index()
    service_dist.columns = ['service_type', 'subscribers', 'total_advance', 'total_revenue']

    result = {
        "summary": {
            "final_recommendations": int(len(df)),
            "total_advance_amount": float(df[advance_col].sum()),
            "total_expected_revenue": float(df[revenue_col].sum()),
            "avg_advance_amount": float(df[advance_col].mean())
        },
        "risk_distribution": risk_dist,
        "service_type_distribution": service_dist.to_dict('records')
    }

    with open(output_dir / 'phase4_summary.json', 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Saved: {output_dir / 'phase4_summary.json'}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n" + "="*60)
print("✅ All phase summaries generated successfully!")
print(f"📁 Location: {output_dir}")
print("="*60)
