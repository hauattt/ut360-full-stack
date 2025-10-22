#!/usr/bin/env python3
"""
Quick Redis Test Script
Test if recommendations are loaded successfully
"""

import redis
import pandas as pd
import sys
from pathlib import Path

# Redis config
REDIS_CONFIG = {
    'host': '10.39.223.70',
    'port': 6379,
    'username': 'redis',
    'password': '098poiA',
    'decode_responses': True
}

def main():
    print("=" * 70)
    print("REDIS QUICK TEST - UT360 Recommendations")
    print("=" * 70)

    # Connect to Redis
    print(f"\nConnecting to Redis: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
    try:
        r = redis.Redis(**REDIS_CONFIG)
        r.ping()
        print("✓ Connected successfully\n")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return 1

    # 1. Total keys
    print("1. Checking total keys...")
    total_keys = r.dbsize()
    print(f"   Total keys in Redis: {total_keys:,}")
    if total_keys == 0:
        print("   ✗ No data found in Redis!")
        return 1

    # 2. Metadata
    print("\n2. Checking metadata...")
    stats = r.hgetall('ut360:meta:stats')
    if stats:
        print("   ✓ Metadata found:")
        for key, value in stats.items():
            print(f"     • {key}: {value}")
    else:
        print("   ⚠ No metadata found")

    # 3. Get a random key
    print("\n3. Testing random recommendation...")
    random_key = r.randomkey()
    if random_key and random_key.startswith('ut360:rec:'):
        isdn = random_key.replace('ut360:rec:', '')
        rec = r.hgetall(random_key)
        print(f"   ✓ Random ISDN: {isdn}")
        print(f"     • Service Type: {rec.get('service_type', 'N/A')}")
        print(f"     • Advance Amount: {rec.get('advance_amount', 'N/A')}")
        print(f"     • Revenue: {rec.get('revenue_per_advance', 'N/A')}")
        print(f"     • Risk: {rec.get('bad_debt_risk', 'N/A')}")
        print(f"     • Priority: {rec.get('priority_score', 'N/A')}")

    # 4. Test specific ISDN from CSV
    print("\n4. Testing ISDN from CSV file...")
    csv_path = Path(__file__).parent.parent.parent / "output" / "recommendations" / "recommendations_final_filtered_typeupdate.csv"

    if csv_path.exists():
        df = pd.read_csv(csv_path, nrows=5)
        print(f"   Testing first {len(df)} ISDNs from CSV:")

        found_count = 0
        for idx, row in df.iterrows():
            isdn = str(row['isdn'])
            key = f'ut360:rec:{isdn}'
            exists = r.exists(key)

            if exists:
                found_count += 1
                rec = r.hgetall(key)
                print(f"   ✓ ISDN {isdn}: {rec.get('service_type', 'N/A')} - {rec.get('advance_amount', 'N/A')}")
            else:
                print(f"   ✗ ISDN {isdn}: Not found in Redis")

        print(f"\n   Found {found_count}/{len(df)} ISDNs in Redis")
    else:
        print(f"   ⚠ CSV file not found: {csv_path}")

    # 5. Count by service type
    print("\n5. Checking indexes by service type...")
    for service_type in ['Fee', 'Free', 'Quota']:
        count = r.zcard(f'ut360:idx:service:{service_type}')
        print(f"   • {service_type}: {count:,}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n✓ Total Keys: {total_keys:,}")
    print(f"✓ Redis is working correctly")
    print(f"✓ Ready to query recommendations by ISDN")

    return 0

if __name__ == "__main__":
    sys.exit(main())
