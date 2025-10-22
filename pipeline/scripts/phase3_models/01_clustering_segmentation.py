#!/usr/bin/env python3
"""
PHASE 3 - CLUSTERING APPROACH: Phân nhóm subscribers theo hành vi
Nhóm 1: Đã ứng (Existing advance users)
Nhóm 2: Hành vi tương tự nhóm đã ứng (Similar - Target expansion)
Nhóm 3: Khác xa - không ứng dù hết tiền (Unlikely)
"""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pickle
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Ensure output directories exist
Path('output/models').mkdir(parents=True, exist_ok=True)

print("="*100)
print("PHASE 3 - CLUSTERING SEGMENTATION")
print("Mục tiêu: Tìm subscribers có hành vi tương tự như advance users")
print("="*100)

start_time = datetime.now()

# ==================== LOAD DATA ====================
print("\n[1/8] Loading data...")
df = pd.read_parquet('/data/ut360/output/datasets/dataset_with_features_202503-202508_CORRECTED.parquet')
print(f"  Total records: {len(df):,}")
print(f"  Unique subscribers: {df['isdn'].nunique():,}")

# Get latest month and deduplicate
df_latest = df[df['data_month'] == '202508'].drop_duplicates(subset=['isdn'], keep='first')
print(f"  August unique subscribers: {len(df_latest):,}")

# ==================== IDENTIFY ADVANCE USERS ====================
print("\n[2/8] Identifying advance users...")
all_advance_users = set(df[df['has_advance_in_month'] == True]['isdn'].unique())
print(f"  Advance users (from 6 months history): {len(all_advance_users):,}")

df_latest['is_advance_user'] = df_latest['isdn'].isin(all_advance_users)
print(f"    - In August: {df_latest['is_advance_user'].sum():,} advance users")
print(f"    - In August: {(~df_latest['is_advance_user']).sum():,} never-advanced users")

# ==================== LOAD CLUSTERING FEATURES ====================
print("\n[3/8] Loading clustering features...")
with open('output/clustering_features.txt', 'r') as f:
    clustering_features = [line.strip() for line in f.readlines()]

print(f"  Total features: {len(clustering_features)}")
print(f"  Feature categories:")
topup_count = len([f for f in clustering_features if 'topup' in f])
financial_count = len([f for f in clustering_features if any(x in f for x in ['balance', 'burn', 'stress'])])
package_count = len([f for f in clustering_features if 'package' in f or 'renewed' in f])
print(f"    - Topup behavior: {topup_count}")
print(f"    - Financial indicators: {financial_count}")
print(f"    - Package usage: {package_count}")
print(f"    - Others: {len(clustering_features) - topup_count - financial_count - package_count}")

# ==================== PREPARE DATA ====================
print("\n[4/8] Preparing data for clustering...")

X = df_latest[clustering_features].copy()

# Handle missing and infinite values
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 999)

print(f"  Data shape: {X.shape}")

# Standardize features (critical for K-Means)
print(f"  Standardizing features...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"  ✓ Data ready for clustering")

# ==================== K-MEANS CLUSTERING ====================
print("\n[5/8] Running K-Means clustering (k=3)...")
print(f"  Training K-Means with 256 CPU cores...")

kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=20,  # Multiple initializations for stability
    max_iter=500
)

cluster_labels = kmeans.fit_predict(X_scaled)
df_latest['cluster'] = cluster_labels

print(f"  ✓ Clustering completed")
print(f"  Inertia (within-cluster sum of squares): {kmeans.inertia_:,.0f}")

# ==================== ANALYZE CLUSTERS ====================
print("\n[6/8] Analyzing clusters...")

cluster_stats = []
for cluster_id in range(3):
    cluster_mask = df_latest['cluster'] == cluster_id
    cluster_df = df_latest[cluster_mask]

    total_in_cluster = cluster_df.shape[0]
    advance_in_cluster = cluster_df['is_advance_user'].sum()
    advance_rate = advance_in_cluster / total_in_cluster * 100

    cluster_stats.append({
        'cluster': cluster_id,
        'total_subscribers': total_in_cluster,
        'advance_users': advance_in_cluster,
        'advance_rate': advance_rate
    })

    print(f"\n  Cluster {cluster_id}:")
    print(f"    Total: {total_in_cluster:,} subscribers ({total_in_cluster/len(df_latest)*100:.1f}%)")
    print(f"    Advance users: {advance_in_cluster:,} ({advance_rate:.2f}%)")
    print(f"    Never-advanced: {total_in_cluster - advance_in_cluster:,}")

# Sort clusters by advance_rate to identify groups
cluster_stats_df = pd.DataFrame(cluster_stats).sort_values('advance_rate', ascending=False)
print(f"\n  📊 Clusters ranked by advance rate:")
print(cluster_stats_df.to_string(index=False))

# ==================== MAP TO BUSINESS SEGMENTS ====================
print("\n[7/8] Mapping clusters to business segments...")

# Cluster with highest advance rate = Similar to advance users
# Cluster with lowest advance rate = Unlikely
# Middle cluster = Mixed

highest_cluster = cluster_stats_df.iloc[0]['cluster']
middle_cluster = cluster_stats_df.iloc[1]['cluster']
lowest_cluster = cluster_stats_df.iloc[2]['cluster']

print(f"\n  Business mapping:")
print(f"    Cluster {highest_cluster} (advance rate {cluster_stats_df.iloc[0]['advance_rate']:.1f}%) → Nhóm 1+2 (Similar to advance users)")
print(f"    Cluster {middle_cluster} (advance rate {cluster_stats_df.iloc[1]['advance_rate']:.1f}%) → Mixed")
print(f"    Cluster {lowest_cluster} (advance rate {cluster_stats_df.iloc[2]['advance_rate']:.1f}%) → Nhóm 3 (Unlikely)")

# Create final segments
df_latest['segment'] = 'Unknown'

# Segment existing advance users
df_latest.loc[df_latest['is_advance_user'], 'segment'] = 'GROUP_1_EXISTING'

# Segment never-advanced by cluster
never_advanced_mask = ~df_latest['is_advance_user']

# High similarity cluster → Group 2 (Target expansion)
df_latest.loc[never_advanced_mask & (df_latest['cluster'] == highest_cluster), 'segment'] = 'GROUP_2_SIMILAR'

# Middle cluster → Can be included in Group 2 with lower priority
df_latest.loc[never_advanced_mask & (df_latest['cluster'] == middle_cluster), 'segment'] = 'GROUP_2_MEDIUM'

# Low similarity cluster → Group 3 (Unlikely)
df_latest.loc[never_advanced_mask & (df_latest['cluster'] == lowest_cluster), 'segment'] = 'GROUP_3_UNLIKELY'

# ==================== FINAL STATISTICS ====================
print("\n" + "="*100)
print("📊 FINAL SEGMENTATION RESULTS")
print("="*100)

seg_counts = df_latest['segment'].value_counts()
for seg in ['GROUP_1_EXISTING', 'GROUP_2_SIMILAR', 'GROUP_2_MEDIUM', 'GROUP_3_UNLIKELY']:
    if seg in seg_counts.index:
        count = seg_counts[seg]
        pct = count / len(df_latest) * 100
        print(f"\n  {seg}: {count:,} subscribers ({pct:.1f}%)")

        if seg == 'GROUP_1_EXISTING':
            print(f"    → Current advance users")
        elif seg == 'GROUP_2_SIMILAR':
            print(f"    → HIGH PRIORITY expansion target")
            print(f"    → Hành vi rất giống advance users")
        elif seg == 'GROUP_2_MEDIUM':
            print(f"    → MEDIUM PRIORITY expansion target")
            print(f"    → Hành vi khá giống advance users")
        elif seg == 'GROUP_3_UNLIKELY':
            print(f"    → Low priority - unlikely to advance")

group_2_total = seg_counts.get('GROUP_2_SIMILAR', 0) + seg_counts.get('GROUP_2_MEDIUM', 0)
print(f"\n  🎯 TOTAL EXPANSION TARGET (Group 2): {group_2_total:,} subscribers")
print(f"  📈 Expansion ratio: {group_2_total / len(all_advance_users):.2f}x current base")

# ==================== CLUSTER PROFILES ====================
print("\n" + "="*100)
print("📋 CLUSTER PROFILES (Top features)")
print("="*100)

# Get cluster centers and feature importance
cluster_centers = pd.DataFrame(
    scaler.inverse_transform(kmeans.cluster_centers_),
    columns=clustering_features
)

for cluster_id in range(3):
    print(f"\n  Cluster {cluster_id} characteristics:")

    # Get top 5 features by value
    center = cluster_centers.loc[cluster_id]
    top_features = center.nlargest(5)

    for feat, val in top_features.items():
        overall_mean = X[feat].mean()
        print(f"    - {feat}: {val:.2f} (overall mean: {overall_mean:.2f})")

# ==================== SAVE RESULTS ====================
print("\n[8/8] Saving results...")

# Save full scored dataset
output_file = 'output/subscribers_clustered_segmentation.parquet'
df_latest.to_parquet(output_file, compression='snappy', index=False)
print(f"  ✓ Full dataset: {output_file}")

# Save Group 2 - Similar (High priority)
group_2_similar = df_latest[df_latest['segment'] == 'GROUP_2_SIMILAR'][['isdn', 'cluster', 'segment']].copy()
group_2_similar.to_csv('output/expansion_group2_similar_high_priority.csv', index=False)
print(f"  ✓ Group 2 Similar: output/expansion_group2_similar_high_priority.csv ({len(group_2_similar):,})")

# Save Group 2 - Medium
group_2_medium = df_latest[df_latest['segment'] == 'GROUP_2_MEDIUM'][['isdn', 'cluster', 'segment']].copy()
group_2_medium.to_csv('output/expansion_group2_medium_priority.csv', index=False)
print(f"  ✓ Group 2 Medium: output/expansion_group2_medium_priority.csv ({len(group_2_medium):,})")

# Save combined Group 2
group_2_all = df_latest[df_latest['segment'].isin(['GROUP_2_SIMILAR', 'GROUP_2_MEDIUM'])][['isdn', 'cluster', 'segment']].copy()
group_2_all.to_csv('output/expansion_group2_all_targets.csv', index=False)
print(f"  ✓ Group 2 All: output/expansion_group2_all_targets.csv ({len(group_2_all):,})")

# Save model
model_data = {
    'kmeans': kmeans,
    'scaler': scaler,
    'features': clustering_features,
    'cluster_mapping': {
        'highest': int(highest_cluster),
        'middle': int(middle_cluster),
        'lowest': int(lowest_cluster)
    }
}

with open('output/models/clustering_model.pkl', 'wb') as f:
    pickle.dump(model_data, f)
print(f"  ✓ Model: output/models/clustering_model.pkl")

# Save summary
summary = {
    'total_subscribers': len(df_latest),
    'group_1_existing': seg_counts.get('GROUP_1_EXISTING', 0),
    'group_2_similar': seg_counts.get('GROUP_2_SIMILAR', 0),
    'group_2_medium': seg_counts.get('GROUP_2_MEDIUM', 0),
    'group_2_total': group_2_total,
    'group_3_unlikely': seg_counts.get('GROUP_3_UNLIKELY', 0),
    'expansion_ratio': group_2_total / len(all_advance_users),
    'kmeans_inertia': kmeans.inertia_
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv('output/clustering_summary.csv', index=False)
print(f"  ✓ Summary: output/clustering_summary.csv")

elapsed = datetime.now() - start_time

print("\n" + "="*100)
print(f"✅ CLUSTERING COMPLETED in {elapsed}")
print(f"   Expansion targets identified: {group_2_total:,} subscribers")
print(f"   Target split: {seg_counts.get('GROUP_2_SIMILAR', 0):,} high + {seg_counts.get('GROUP_2_MEDIUM', 0):,} medium")
print("="*100)
