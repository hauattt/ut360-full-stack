#!/usr/bin/env python3
"""
Test connections to PostgreSQL and Redis servers
Quick verification before running sync scripts
"""

import sys

print("="*60)
print("UT360 - Connection Test")
print("="*60)

# Test 1: PostgreSQL
print("\n[1/2] Testing PostgreSQL connection to DB01...")
print("      Host: 10.39.223.102:5432")
print("      User: admin")
print("      Database: ut360")

try:
    import psycopg2
    conn = psycopg2.connect(
        host='10.39.223.102',
        port=5432,
        database='ut360',
        user='admin',
        password='Vns@2025'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    version = cursor.fetchone()[0]
    print(f"      ✓ Connected successfully!")
    print(f"      Version: {version[:50]}...")

    # Check if tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    if tables:
        print(f"      Existing tables: {len(tables)}")
        for table in tables:
            print(f"        - {table[0]}")
    else:
        print("      No tables yet (will be created on first sync)")

    conn.close()
except ImportError:
    print("      ✗ psycopg2 not installed")
    print("      Run: pip3 install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"      ✗ Connection failed: {e}")
    print("\n      Troubleshooting:")
    print("      - Check network connectivity: telnet 10.39.223.102 5432")
    print("      - Verify credentials: admin/Vns@2025")
    print("      - Check pg_hba.conf allows connection from this IP")
    sys.exit(1)

# Test 2: Redis
print("\n[2/2] Testing Redis connection to WEB01...")
print("      Host: 10.39.223.70:6379")
print("      User: redis")

try:
    import redis
    r = redis.Redis(
        host='10.39.223.70',
        port=6379,
        username='redis',
        password='098poiA',
        decode_responses=True
    )
    r.ping()
    print(f"      ✓ Connected successfully!")

    # Get info
    info = r.info('server')
    print(f"      Version: {info['redis_version']}")

    # Check existing keys
    dbsize = r.dbsize()
    if dbsize > 0:
        print(f"      Existing keys: {dbsize:,}")

        # Check if UT360 keys exist
        ut360_keys = len(r.keys('ut360:*'))
        if ut360_keys > 0:
            print(f"      UT360 keys found: {ut360_keys:,}")
            print("      (Will be cleared on sync)")
    else:
        print("      No keys yet (empty database)")

    r.close()
except ImportError:
    print("      ✗ redis package not installed")
    print("      Run: pip3 install redis")
    sys.exit(1)
except Exception as e:
    print(f"      ✗ Connection failed: {e}")
    print("\n      Troubleshooting:")
    print("      - Check network connectivity: telnet 10.39.223.70 6379")
    print("      - Verify credentials: redis/098poiA")
    print("      - Check Redis ACL settings")
    sys.exit(1)

# Test 3: Check data files
print("\n[3/3] Checking data files...")

from pathlib import Path
import os

base_dir = Path(__file__).parent.parent.parent
output_dir = base_dir / "output"

files_to_check = [
    ("CSV", output_dir / "recommendations/recommendations_final_filtered_typeupdate.csv"),
    ("360 Profile", output_dir / "subscriber_360_profile.parquet"),
    ("Monthly ARPU", output_dir / "subscriber_monthly_summary.parquet")
]

all_files_exist = True
for name, file_path in files_to_check:
    if file_path.exists():
        size_mb = file_path.stat().st_size / 1024 / 1024
        print(f"      ✓ {name}: {size_mb:.2f} MB")
    else:
        print(f"      ✗ {name}: NOT FOUND")
        print(f"        Expected: {file_path}")
        all_files_exist = False

if not all_files_exist:
    print("\n      Some files are missing!")
    print("      Make sure to copy all required files before running sync.")
    sys.exit(1)

# Summary
print("\n" + "="*60)
print("CONNECTION TEST SUMMARY")
print("="*60)
print("✓ PostgreSQL: Connected")
print("✓ Redis: Connected")
print("✓ Data files: All present")
print("\nYou are ready to run sync scripts!")
print("\nNext steps:")
print("  1. python3 scripts/utils/sync_to_postgresql.py")
print("  2. python3 scripts/utils/sync_to_redis.py")
print("="*60)
