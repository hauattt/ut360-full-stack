#!/usr/bin/env python3
"""
UT360 - Sync Recommendation Data to Redis
Created: 2025-10-22
Purpose: Load parquet files into Redis for high-speed caching
"""

import pandas as pd
import numpy as np
import redis
import json
import sys
from pathlib import Path
from datetime import datetime
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"

# Redis connection settings - WEB01
REDIS_CONFIG = {
    'host': '10.39.223.70',
    'port': 6379,
    'db': 0,
    'password': '098poiA',
    'decode_responses': True,  # Return strings instead of bytes
    'username': 'redis'  # Redis 6.0+ ACL username
}

# TTL (Time To Live) in seconds
TTL_RECOMMENDATION = 7 * 24 * 60 * 60  # 7 days
TTL_PROFILE = 7 * 24 * 60 * 60  # 7 days
TTL_INDEX = 30 * 24 * 60 * 60  # 30 days

def connect_redis():
    """Connect to Redis"""
    print(f"Connecting to Redis: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
    try:
        r = redis.Redis(**REDIS_CONFIG)
        r.ping()
        print("✓ Connected to Redis")
        return r
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        print("\nPlease ensure:")
        print("  1. Redis is running: redis-server")
        print("  2. Redis is accessible on port 6379")
        print("  3. No password required or password is set correctly")
        sys.exit(1)

def clear_old_data(r):
    """Clear old UT360 data from Redis"""
    print("\nClearing old UT360 data...")

    # Get all ut360 keys
    patterns = ['ut360:rec:*', 'ut360:profile:*', 'ut360:idx:*', 'ut360:meta:*']
    total_deleted = 0

    for pattern in patterns:
        keys = r.keys(pattern)
        if keys:
            deleted = r.delete(*keys)
            total_deleted += deleted
            print(f"  Deleted {deleted} keys matching '{pattern}'")

    print(f"✓ Cleared {total_deleted} old keys")

def load_recommendations(r):
    """Load recommendations into Redis as hashes"""
    print("\n[1/4] Loading recommendations...")

    # Read from final recommendations file (with updated service_type)
    rec_file = OUTPUT_DIR / "recommendations" / "recommendations_final_filtered_typeupdate.csv"

    if not rec_file.exists():
        print(f"✗ File not found: {rec_file}")
        return

    df = pd.read_csv(rec_file)
    print(f"  Loaded {len(df)} recommendations from CSV")

    # Load 360 profile for additional fields
    profile_file = OUTPUT_DIR / "subscriber_360_profile.parquet"
    if profile_file.exists():
        df_profile = pd.read_parquet(profile_file)
        df = df.merge(df_profile, on='isdn', how='left', suffixes=('', '_profile'))

    # Calculate priority score
    if 'customer_value_score' in df.columns and 'advance_readiness_score' in df.columns:
        df['priority_score'] = (
            df['customer_value_score'].fillna(0) *
            df['advance_readiness_score'].fillna(0) / 100
        ).round(2)
    else:
        df['priority_score'] = 0.0

    # Replace NaN with empty string for Redis
    df = df.replace({np.nan: ''})

    # Create pipeline for batch operations
    pipe = r.pipeline()
    count = 0

    for idx, row in df.iterrows():
        isdn = row['isdn']
        key = f"ut360:rec:{isdn}"

        # Create hash for this recommendation
        hash_data = {
            'isdn': str(row.get('isdn', '')),
            'subscriber_type': str(row.get('subscriber_type', '')),
            'service_type': str(row.get('service_type', '')),
            'advance_amount': str(row.get('advance_amount', 0)),
            'revenue_per_advance': str(row.get('revenue_per_advance', 0)),
            'cluster_group': str(row.get('cluster_group', '')),
            'bad_debt_risk': str(row.get('bad_debt_risk', '')),
            'arpu_avg_6m': str(row.get('arpu_avg_6m', '')),
            'arpu_growth_rate': str(row.get('arpu_growth_rate', '')),
            'arpu_trend': str(row.get('arpu_trend', '')),
            'customer_value_score': str(row.get('customer_value_score', '')),
            'advance_readiness_score': str(row.get('advance_readiness_score', '')),
            'priority_score': str(row.get('priority_score', '')),
            'user_type': str(row.get('user_type', '')),
            'topup_frequency_class': str(row.get('topup_frequency_class', '')),
            'updated_at': datetime.now().isoformat()
        }

        # Remove empty values
        hash_data = {k: v for k, v in hash_data.items() if v and v != 'nan'}

        # Set hash
        pipe.hset(key, mapping=hash_data)
        pipe.expire(key, TTL_RECOMMENDATION)

        count += 1

        # Execute batch every 1000 records
        if count % 1000 == 0:
            pipe.execute()
            pipe = r.pipeline()
            print(f"  Loaded {count}/{len(df)} recommendations...")

    # Execute remaining
    pipe.execute()
    print(f"✓ Loaded {count} recommendations into Redis")

def load_360_profiles(r):
    """Load 360 profiles into Redis"""
    print("\n[2/4] Loading 360 profiles...")

    profile_file = OUTPUT_DIR / "subscriber_360_profile.parquet"

    if not profile_file.exists():
        print(f"✗ File not found: {profile_file}")
        return

    df = pd.read_parquet(profile_file)
    print(f"  Loaded {len(df)} profiles from parquet")

    # Load monthly ARPU
    monthly_file = OUTPUT_DIR / "subscriber_monthly_summary.parquet"
    df_monthly = None
    if monthly_file.exists():
        df_monthly = pd.read_parquet(monthly_file)

    df = df.replace({np.nan: None})

    pipe = r.pipeline()
    count = 0

    for idx, row in df.iterrows():
        isdn = row['isdn']
        key = f"ut360:profile:{isdn}"

        # Basic info
        basic = {
            'isdn': row.get('isdn'),
            'type': row.get('subscriber_type'),
            'service': row.get('service_type'),
            'advance': float(row.get('advance_amount', 0)),
            'revenue': float(row.get('revenue_per_advance', 0))
        }

        # ARPU stats
        arpu_stats = {
            'avg': float(row.get('arpu_avg_6m', 0)) if row.get('arpu_avg_6m') else None,
            'std': float(row.get('arpu_std_6m', 0)) if row.get('arpu_std_6m') else None,
            'min': float(row.get('arpu_min_6m', 0)) if row.get('arpu_min_6m') else None,
            'max': float(row.get('arpu_max_6m', 0)) if row.get('arpu_max_6m') else None,
            'growth_rate': float(row.get('arpu_growth_rate', 0)) if row.get('arpu_growth_rate') else None,
            'trend': row.get('arpu_trend')
        }

        # Revenue breakdown
        revenue_breakdown = {
            'call_pct': float(row.get('revenue_call_pct', 0)) if row.get('revenue_call_pct') else None,
            'sms_pct': float(row.get('revenue_sms_pct', 0)) if row.get('revenue_sms_pct') else None,
            'data_pct': float(row.get('revenue_data_pct', 0)) if row.get('revenue_data_pct') else None,
            'user_type': row.get('user_type')
        }

        # Topup behavior
        topup_behavior = {
            'frequency': float(row.get('topup_frequency', 0)) if row.get('topup_frequency') else None,
            'avg_amount': float(row.get('topup_avg_amount', 0)) if row.get('topup_avg_amount') else None,
            'ratio': float(row.get('topup_advance_ratio', 0)) if row.get('topup_advance_ratio') else None,
            'frequency_class': row.get('topup_frequency_class')
        }

        # Risk assessment
        risk_assessment = {
            'level': row.get('bad_debt_risk'),
            'score': float(row.get('customer_value_score', 0)) if row.get('customer_value_score') else None,
            'factors': []
        }

        # KPI scores
        kpi_scores = {
            'customer_value': float(row.get('customer_value_score', 0)) if row.get('customer_value_score') else None,
            'advance_readiness': float(row.get('advance_readiness_score', 0)) if row.get('advance_readiness_score') else None,
            'revenue_potential': float(row.get('revenue_per_advance', 0)) if row.get('revenue_per_advance') else None
        }

        # Monthly ARPU
        monthly_arpu = []
        if df_monthly is not None:
            monthly_data = df_monthly[df_monthly['isdn'] == isdn]
            if not monthly_data.empty:
                monthly_arpu = [
                    {
                        'month': m['data_month'],
                        'arpu_call': float(m['arpu_call']) if pd.notna(m['arpu_call']) else None,
                        'arpu_sms': float(m['arpu_sms']) if pd.notna(m['arpu_sms']) else None,
                        'arpu_data': float(m['arpu_data']) if pd.notna(m['arpu_data']) else None,
                        'arpu_total': float(m['arpu_total']) if pd.notna(m['arpu_total']) else None
                    }
                    for _, m in monthly_data.iterrows()
                ]

        # Store as JSON in hash fields
        hash_data = {
            'basic': json.dumps(basic, ensure_ascii=False),
            'arpu_stats': json.dumps(arpu_stats, ensure_ascii=False),
            'revenue_breakdown': json.dumps(revenue_breakdown, ensure_ascii=False),
            'topup_behavior': json.dumps(topup_behavior, ensure_ascii=False),
            'risk_assessment': json.dumps(risk_assessment, ensure_ascii=False),
            'kpi_scores': json.dumps(kpi_scores, ensure_ascii=False),
            'monthly_arpu': json.dumps(monthly_arpu, ensure_ascii=False),
            'updated_at': datetime.now().isoformat()
        }

        pipe.hset(key, mapping=hash_data)
        pipe.expire(key, TTL_PROFILE)

        count += 1

        if count % 1000 == 0:
            pipe.execute()
            pipe = r.pipeline()
            print(f"  Loaded {count}/{len(df)} profiles...")

    pipe.execute()
    print(f"✓ Loaded {count} 360 profiles into Redis")

def create_indexes(r):
    """Create Redis indexes for fast lookup"""
    print("\n[3/4] Creating indexes...")

    # Read data (with updated service_type)
    rec_file = OUTPUT_DIR / "recommendations" / "recommendations_final_filtered_typeupdate.csv"
    profile_file = OUTPUT_DIR / "subscriber_360_profile.parquet"

    if not rec_file.exists() or not profile_file.exists():
        print("✗ Required files not found")
        return

    df = pd.read_csv(rec_file)
    df_profile = pd.read_parquet(profile_file)
    df = df.merge(df_profile, on='isdn', how='left', suffixes=('', '_profile'))

    # Calculate priority score
    if 'customer_value_score' in df.columns and 'advance_readiness_score' in df.columns:
        df['priority_score'] = (
            df['customer_value_score'].fillna(0) *
            df['advance_readiness_score'].fillna(0) / 100
        ).round(2)
    else:
        df['priority_score'] = 0.0

    pipe = r.pipeline()

    # Index 1: By Service Type (Sorted Set by priority)
    print("  Creating service type indexes (sorted sets)...")
    for service_type in df['service_type'].unique():
        if pd.notna(service_type):
            key = f"ut360:idx:service:{service_type}"
            service_df = df[df['service_type'] == service_type]

            for _, row in service_df.iterrows():
                score = row.get('priority_score', 0)
                pipe.zadd(key, {row['isdn']: score})

            pipe.expire(key, TTL_INDEX)

    # Index 2: By Risk Level (Set)
    print("  Creating risk level indexes (sets)...")
    for risk_level in df['bad_debt_risk'].unique():
        if pd.notna(risk_level):
            key = f"ut360:idx:risk:{risk_level}"
            risk_df = df[df['bad_debt_risk'] == risk_level]

            for isdn in risk_df['isdn']:
                pipe.sadd(key, isdn)

            pipe.expire(key, TTL_INDEX)

    # Index 3: By Cluster (Set)
    print("  Creating cluster indexes (sets)...")
    for cluster_id in df['cluster_group'].unique():
        if pd.notna(cluster_id):
            key = f"ut360:idx:cluster:{int(cluster_id)}"
            cluster_df = df[df['cluster_group'] == cluster_id]

            for isdn in cluster_df['isdn']:
                pipe.sadd(key, isdn)

            pipe.expire(key, TTL_INDEX)

    # Execute all
    pipe.execute()
    print("✓ Created all indexes")

def create_metadata(r):
    """Create metadata hash"""
    print("\n[4/4] Creating metadata...")

    rec_file = OUTPUT_DIR / "recommendations" / "recommendations_final_filtered_typeupdate.csv"

    if not rec_file.exists():
        print("✗ File not found")
        return

    df = pd.read_csv(rec_file)
    profile_file = OUTPUT_DIR / "subscriber_360_profile.parquet"
    if profile_file.exists():
        df_profile = pd.read_parquet(profile_file)
        df = df.merge(df_profile, on='isdn', how='left', suffixes=('', '_profile'))

    # Calculate stats (with new service_type names)
    metadata = {
        'total_subscribers': str(len(df)),
        'total_fee': str(len(df[df['service_type'] == 'Fee'])),
        'total_free': str(len(df[df['service_type'] == 'Free'])),
        'total_quota': str(len(df[df['service_type'] == 'Quota'])),
        'total_low_risk': str(len(df[df['bad_debt_risk'] == 'LOW'])),
        'total_medium_risk': str(len(df[df['bad_debt_risk'] == 'MEDIUM'])),
        'avg_advance_amount': str(round(df['advance_amount'].mean(), 2)),
        'total_revenue_potential': str(round(df['revenue_per_advance'].sum(), 2)),
        'last_updated': datetime.now().isoformat(),
        'data_version': 'v1.0'
    }

    r.hset('ut360:meta:stats', mapping=metadata)
    r.expire('ut360:meta:stats', TTL_INDEX)

    print("✓ Created metadata")

def print_statistics(r):
    """Print Redis statistics"""
    print("\n" + "="*60)
    print("REDIS STATISTICS")
    print("="*60)

    # Count keys
    rec_count = len(r.keys('ut360:rec:*'))
    profile_count = len(r.keys('ut360:profile:*'))
    idx_count = len(r.keys('ut360:idx:*'))

    print(f"Recommendation Hashes: {rec_count:,}")
    print(f"360 Profile Hashes: {profile_count:,}")
    print(f"Index Keys: {idx_count:,}")

    # Metadata
    meta = r.hgetall('ut360:meta:stats')
    if meta:
        print("\nMetadata:")
        print(f"  Total Subscribers: {meta.get('total_subscribers', 0):}")
        print(f"  EasyCredit: {meta.get('total_easycredit', 0):}")
        print(f"  MBFG: {meta.get('total_mbfg', 0):}")
        print(f"  ungsanluong: {meta.get('total_ungsanluong', 0):}")
        print(f"  LOW Risk: {meta.get('total_low_risk', 0):}")
        print(f"  MEDIUM Risk: {meta.get('total_medium_risk', 0):}")
        print(f"  Last Updated: {meta.get('last_updated', 'N/A')}")

    # Memory usage
    info = r.info('memory')
    used_memory_mb = info['used_memory'] / 1024 / 1024
    print(f"\nRedis Memory Used: {used_memory_mb:.2f} MB")

    print("="*60)

def main():
    """Main execution"""
    print("="*60)
    print("UT360 - Sync Data to Redis")
    print("="*60)

    # Connect to Redis
    r = connect_redis()

    start_time = time.time()

    try:
        # Clear old data
        clear_old_data(r)

        # Load data
        load_recommendations(r)
        load_360_profiles(r)
        create_indexes(r)
        create_metadata(r)

        # Print statistics
        print_statistics(r)

        elapsed = time.time() - start_time
        print(f"\n✓ Data sync completed in {elapsed:.2f} seconds!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Error during sync: {e}")
        import traceback
        traceback.print_exc()
    finally:
        r.close()
        print("\nRedis connection closed.")

if __name__ == "__main__":
    main()
