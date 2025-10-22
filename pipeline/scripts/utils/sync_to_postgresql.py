#!/usr/bin/env python3
"""
UT360 - Sync Recommendation Data to PostgreSQL
Created: 2025-10-22
Purpose: Load parquet files into PostgreSQL database for persistent storage
"""

import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "output"

# PostgreSQL connection settings - DB01
DB_CONFIG = {
    'host': '10.39.223.102',
    'port': 5432,
    'database': 'ut360',
    'user': 'admin',
    'password': 'Vns@2025'
}

def create_database_schema(conn):
    """Create PostgreSQL tables if not exists"""
    cursor = conn.cursor()

    print("Creating database schema...")

    # Table 1: recommendations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id BIGSERIAL PRIMARY KEY,

            -- Subscriber Info
            isdn VARCHAR(255) NOT NULL UNIQUE,
            subscriber_type VARCHAR(10) NOT NULL,

            -- Recommendation
            service_type VARCHAR(50) NOT NULL,
            advance_amount DECIMAL(12,2) NOT NULL,
            revenue_per_advance DECIMAL(12,2) NOT NULL,

            -- Clustering
            cluster_group INTEGER,

            -- Risk
            bad_debt_risk VARCHAR(20) NOT NULL,

            -- ARPU Stats
            arpu_avg_6m DECIMAL(10,2),
            arpu_std_6m DECIMAL(10,2),
            arpu_min_6m DECIMAL(10,2),
            arpu_max_6m DECIMAL(10,2),
            arpu_growth_rate DECIMAL(10,2),
            arpu_trend VARCHAR(20),

            -- Revenue Breakdown
            revenue_call_pct DECIMAL(5,2),
            revenue_sms_pct DECIMAL(5,2),
            revenue_data_pct DECIMAL(5,2),
            user_type VARCHAR(50),

            -- Topup Behavior
            topup_frequency DECIMAL(5,2),
            topup_avg_amount DECIMAL(10,2),
            topup_advance_ratio DECIMAL(10,4),
            topup_frequency_class VARCHAR(20),

            -- Scores
            customer_value_score DECIMAL(5,2),
            advance_readiness_score DECIMAL(5,2),
            priority_score DECIMAL(10,2),

            -- Metadata
            recommendation_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),

            CONSTRAINT chk_subscriber_type CHECK (subscriber_type IN ('PRE', 'POS')),
            CONSTRAINT chk_service_type CHECK (service_type IN ('Fee', 'Free', 'Quota')),
            CONSTRAINT chk_risk CHECK (bad_debt_risk IN ('LOW', 'MEDIUM', 'HIGH'))
        );
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_isdn ON recommendations(isdn);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_service ON recommendations(service_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_risk ON recommendations(bad_debt_risk);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_cluster ON recommendations(cluster_group);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON recommendations(priority_score DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_service_risk ON recommendations(service_type, bad_debt_risk);")

    # Table 2: subscriber_360_profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriber_360_profiles (
            id BIGSERIAL PRIMARY KEY,
            isdn VARCHAR(255) NOT NULL UNIQUE,
            recommendation_id BIGINT REFERENCES recommendations(id),

            -- Basic Info
            subscriber_type VARCHAR(10) NOT NULL,
            service_type VARCHAR(50),
            advance_amount DECIMAL(12,2),
            revenue_per_advance DECIMAL(12,2),

            -- ARPU Statistics
            arpu_avg_6m DECIMAL(10,2),
            arpu_std_6m DECIMAL(10,2),
            arpu_min_6m DECIMAL(10,2),
            arpu_max_6m DECIMAL(10,2),
            arpu_first_month DECIMAL(10,2),
            arpu_last_month DECIMAL(10,2),
            arpu_growth_rate DECIMAL(10,2),
            arpu_trend VARCHAR(20),

            -- Revenue Breakdown
            revenue_call_pct DECIMAL(5,2),
            revenue_sms_pct DECIMAL(5,2),
            revenue_data_pct DECIMAL(5,2),
            user_type VARCHAR(50),

            -- Topup Behavior
            topup_frequency DECIMAL(5,2),
            topup_avg_amount DECIMAL(10,2),
            topup_min_amount DECIMAL(10,2),
            topup_max_amount DECIMAL(10,2),
            topup_advance_ratio DECIMAL(10,4),
            topup_frequency_class VARCHAR(20),

            -- Risk Assessment
            bad_debt_risk VARCHAR(20),
            risk_score DECIMAL(5,2),
            risk_factors JSONB,

            -- KPI Scores
            customer_value_score DECIMAL(5,2),
            advance_readiness_score DECIMAL(5,2),
            revenue_potential DECIMAL(12,2),

            -- Clustering
            cluster_group INTEGER,
            cluster_label VARCHAR(100),

            -- Insights
            classification_reason TEXT,
            strengths JSONB,
            recommendations_text JSONB,

            -- Metadata
            profile_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_360_isdn ON subscriber_360_profiles(isdn);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_360_recommendation ON subscriber_360_profiles(recommendation_id);")

    # Table 3: subscriber_monthly_arpu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriber_monthly_arpu (
            id BIGSERIAL PRIMARY KEY,
            isdn VARCHAR(255) NOT NULL,
            data_month VARCHAR(6) NOT NULL,

            arpu_call DECIMAL(10,2),
            arpu_sms DECIMAL(10,2),
            arpu_data DECIMAL(10,2),
            arpu_total DECIMAL(10,2),

            created_at TIMESTAMP DEFAULT NOW(),

            UNIQUE(isdn, data_month)
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_isdn ON subscriber_monthly_arpu(isdn);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_month ON subscriber_monthly_arpu(data_month);")

    conn.commit()
    print("✓ Database schema created successfully")

def load_recommendations(conn):
    """Load recommendation data from parquet to PostgreSQL"""
    print("\n[1/3] Loading recommendations...")

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
    df['priority_score'] = (
        df.get('customer_value_score', 0) *
        df.get('advance_readiness_score', 0) / 100
    )

    # Prepare data
    today = datetime.now().date()

    columns = [
        'isdn', 'subscriber_type', 'service_type', 'advance_amount', 'revenue_per_advance',
        'cluster_group', 'bad_debt_risk',
        'arpu_avg_6m', 'arpu_std_6m', 'arpu_min_6m', 'arpu_max_6m',
        'arpu_growth_rate', 'arpu_trend',
        'revenue_call_pct', 'revenue_sms_pct', 'revenue_data_pct', 'user_type',
        'topup_frequency', 'topup_avg_amount', 'topup_advance_ratio', 'topup_frequency_class',
        'customer_value_score', 'advance_readiness_score', 'priority_score'
    ]

    # Fill missing columns with None
    for col in columns:
        if col not in df.columns:
            df[col] = None

    # Replace NaN with None for SQL NULL
    df = df.replace({np.nan: None})

    # Prepare insert query
    insert_query = f"""
        INSERT INTO recommendations ({', '.join(columns)}, recommendation_date)
        VALUES %s
        ON CONFLICT (isdn)
        DO UPDATE SET
            service_type = EXCLUDED.service_type,
            advance_amount = EXCLUDED.advance_amount,
            revenue_per_advance = EXCLUDED.revenue_per_advance,
            customer_value_score = EXCLUDED.customer_value_score,
            advance_readiness_score = EXCLUDED.advance_readiness_score,
            priority_score = EXCLUDED.priority_score,
            updated_at = NOW()
    """

    # Prepare data tuples
    data = [
        tuple(row[col] for col in columns) + (today,)
        for _, row in df.iterrows()
    ]

    # Batch insert
    cursor = conn.cursor()
    batch_size = 1000

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        execute_values(cursor, insert_query, batch)
        if (i + batch_size) % 10000 == 0:
            print(f"  Inserted {i + batch_size}/{len(data)} rows...")

    conn.commit()
    print(f"✓ Inserted/Updated {len(data)} recommendations")

def load_360_profiles(conn):
    """Load 360 profile data"""
    print("\n[2/3] Loading 360 profiles...")

    profile_file = OUTPUT_DIR / "subscriber_360_profile.parquet"

    if not profile_file.exists():
        print(f"✗ File not found: {profile_file}")
        return

    df = pd.read_parquet(profile_file)
    print(f"  Loaded {len(df)} profiles from parquet")

    today = datetime.now().date()

    # Prepare data
    columns = [
        'isdn', 'subscriber_type', 'service_type', 'advance_amount', 'revenue_per_advance',
        'arpu_avg_6m', 'arpu_std_6m', 'arpu_min_6m', 'arpu_max_6m',
        'arpu_first_month', 'arpu_last_month', 'arpu_growth_rate', 'arpu_trend',
        'revenue_call_pct', 'revenue_sms_pct', 'revenue_data_pct', 'user_type',
        'topup_frequency', 'topup_avg_amount', 'topup_min_amount', 'topup_max_amount',
        'topup_advance_ratio', 'topup_frequency_class',
        'bad_debt_risk', 'customer_value_score', 'advance_readiness_score',
        'cluster_group'
    ]

    # Fill missing columns
    for col in columns:
        if col not in df.columns:
            df[col] = None

    df = df.replace({np.nan: None})

    # Calculate revenue potential
    df['revenue_potential'] = df.get('revenue_per_advance', 0)

    # Generate insights (simplified)
    df['classification_reason'] = df.apply(
        lambda row: f"Classified as {row.get('user_type', 'Unknown')} based on revenue breakdown",
        axis=1
    )

    insert_query = f"""
        INSERT INTO subscriber_360_profiles (
            {', '.join(columns)},
            revenue_potential, classification_reason, profile_date
        )
        VALUES %s
        ON CONFLICT (isdn)
        DO UPDATE SET
            customer_value_score = EXCLUDED.customer_value_score,
            advance_readiness_score = EXCLUDED.advance_readiness_score,
            revenue_potential = EXCLUDED.revenue_potential,
            updated_at = NOW()
    """

    data = [
        tuple(row[col] for col in columns) +
        (row['revenue_potential'], row['classification_reason'], today)
        for _, row in df.iterrows()
    ]

    cursor = conn.cursor()
    batch_size = 1000

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        execute_values(cursor, insert_query, batch)
        if (i + batch_size) % 10000 == 0:
            print(f"  Inserted {i + batch_size}/{len(data)} rows...")

    conn.commit()
    print(f"✓ Inserted/Updated {len(data)} profiles")

def load_monthly_arpu(conn):
    """Load monthly ARPU data"""
    print("\n[3/3] Loading monthly ARPU...")

    monthly_file = OUTPUT_DIR / "subscriber_monthly_summary.parquet"

    if not monthly_file.exists():
        print(f"✗ File not found: {monthly_file}")
        return

    df = pd.read_parquet(monthly_file)
    print(f"  Loaded {len(df)} monthly records from parquet")

    # Prepare data
    df = df.replace({np.nan: None})

    insert_query = """
        INSERT INTO subscriber_monthly_arpu (isdn, data_month, arpu_call, arpu_sms, arpu_data, arpu_total)
        VALUES %s
        ON CONFLICT (isdn, data_month) DO NOTHING
    """

    data = [
        (row['isdn'], row['data_month'],
         row.get('arpu_call'), row.get('arpu_sms'),
         row.get('arpu_data'), row.get('arpu_total'))
        for _, row in df.iterrows()
    ]

    cursor = conn.cursor()
    batch_size = 5000

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        execute_values(cursor, insert_query, batch)
        if (i + batch_size) % 50000 == 0:
            print(f"  Inserted {i + batch_size}/{len(data)} rows...")

    conn.commit()
    print(f"✓ Inserted {len(data)} monthly ARPU records")

def print_statistics(conn):
    """Print database statistics"""
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)

    cursor = conn.cursor()

    # Total counts
    cursor.execute("SELECT COUNT(*) FROM recommendations")
    rec_count = cursor.fetchone()[0]
    print(f"Total Recommendations: {rec_count:,}")

    cursor.execute("SELECT COUNT(*) FROM subscriber_360_profiles")
    profile_count = cursor.fetchone()[0]
    print(f"Total 360 Profiles: {profile_count:,}")

    cursor.execute("SELECT COUNT(*) FROM subscriber_monthly_arpu")
    monthly_count = cursor.fetchone()[0]
    print(f"Total Monthly ARPU Records: {monthly_count:,}")

    # By service type
    print("\nBy Service Type:")
    cursor.execute("""
        SELECT service_type, COUNT(*) as count,
               SUM(advance_amount) as total_advance,
               SUM(revenue_per_advance) as total_revenue
        FROM recommendations
        GROUP BY service_type
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,} subscribers, "
              f"Advance: {row[2]:,.0f} VND, Revenue: {row[3]:,.0f} VND")

    # By risk level
    print("\nBy Risk Level:")
    cursor.execute("""
        SELECT bad_debt_risk, COUNT(*) as count
        FROM recommendations
        GROUP BY bad_debt_risk
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]:,} subscribers")

    print("="*60)

def main():
    """Main execution"""
    print("="*60)
    print("UT360 - Sync Data to PostgreSQL")
    print("="*60)

    # Connect to PostgreSQL
    try:
        print(f"\nConnecting to PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'ut360' exists: CREATE DATABASE ut360;")
        print("  3. DB_CONFIG credentials are correct")
        return

    try:
        # Create schema
        create_database_schema(conn)

        # Load data
        load_recommendations(conn)
        load_360_profiles(conn)
        load_monthly_arpu(conn)

        # Print statistics
        print_statistics(conn)

        print("\n" + "="*60)
        print("✓ Data sync completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Error during sync: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()
        print("\nPostgreSQL connection closed.")

if __name__ == "__main__":
    main()
