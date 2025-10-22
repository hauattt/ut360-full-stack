#!/usr/bin/env python3
"""
Convert service_type in recommendations_final_filtered.csv
EasyCredit -> Fee
MBFG -> Free
ungsanluong -> Quota
"""

import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_FILE = BASE_DIR / "output/recommendations/recommendations_final_filtered.csv"
OUTPUT_FILE = BASE_DIR / "output/recommendations/recommendations_final_filtered_typeupdate.csv"

print("="*60)
print("Converting service_type in recommendations file")
print("="*60)

# Read CSV
print(f"\nReading: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)
print(f"Total rows: {len(df):,}")

# Show current service_type distribution
print("\nCurrent service_type distribution:")
print(df['service_type'].value_counts())

# Mapping
service_type_mapping = {
    'EasyCredit': 'Fee',
    'MBFG': 'Free',
    'ungsanluong': 'Quota'
}

# Convert
print("\nConverting service_type...")
df['service_type'] = df['service_type'].map(service_type_mapping)

# Show new distribution
print("\nNew service_type distribution:")
print(df['service_type'].value_counts())

# Save
print(f"\nSaving to: {OUTPUT_FILE}")
df.to_csv(OUTPUT_FILE, index=False)

# Verify
print("\n✓ File saved successfully!")
print(f"File size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")

# Show sample
print("\nSample data (first 3 rows):")
print(df[['isdn', 'subscriber_type', 'service_type', 'advance_amount']].head(3).to_string(index=False))

print("\n" + "="*60)
print("Conversion completed!")
print("="*60)
