#!/usr/bin/env python3
"""
PHASE 1: FULL DATA LOADING
Load tất cả data sources (N1-N10) và tạo master file với đầy đủ base columns
Output: File master có ~30 cột base để Phase 2 tạo features
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import argparse
import warnings
warnings.filterwarnings('ignore')

# Parse command line arguments
parser = argparse.ArgumentParser(description='Phase 1: Load and merge data sources')
parser.add_argument('--n1', nargs='*', help='N1 (ARPU) file paths')
parser.add_argument('--n2', nargs='*', help='N2 (Package) file paths')
parser.add_argument('--n3', nargs='*', help='N3 (Usage) file paths')
parser.add_argument('--n4', nargs='*', help='N4 (Advance) file paths')
parser.add_argument('--n5', nargs='*', help='N5 (Topup) file paths')
parser.add_argument('--n6', nargs='*', help='N6 (Usage Detail) file paths')
parser.add_argument('--n7', nargs='*', help='N7 (Location) file paths')
parser.add_argument('--n8', nargs='*', help='N8 (Device) file paths')
parser.add_argument('--n10', nargs='*', help='N10 (Subscriber Info) file paths')
args = parser.parse_args()

# Configuration
DATA_DIR = Path('/data/ut360/data')
OUTPUT_DIR = Path('/data/ut360/output/datasets')
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

NUM_WORKERS = min(cpu_count(), 128)

# Filter months to match existing dataset: 202503-202508 (6 months only, NO 202509!)
MONTHS_FILTER = ['202503', '202504', '202505', '202506', '202507', '202508']

# File selection từ command line (nếu có)
FILE_SELECTION = {
    'N1': args.n1,
    'N2': args.n2,
    'N3': args.n3,
    'N4': args.n4,
    'N5': args.n5,
    'N6': args.n6,
    'N7': args.n7,
    'N8': args.n8,
    'N10': args.n10
}

print("="*100)
print("PHASE 1: FULL DATA LOADING (N1-N10)")
print("="*100)
print(f"Using {NUM_WORKERS} parallel workers")
print(f"Loading months: {MONTHS_FILTER}")
if any(FILE_SELECTION.values()):
    print("\n📂 File selection from webapp:")
    for folder, files in FILE_SELECTION.items():
        if files:
            print(f"  {folder}: {len(files)} files")
print()

start_time = datetime.now()


def extract_month_from_filename(filepath):
    """Extract YYYYMM from filename"""
    import re
    filename = Path(filepath).name
    match = re.search(r'(\d{6})', filename)
    return match.group(1) if match else None


def load_csv_with_month(file_path):
    """Load a single CSV file with month tagging"""
    try:
        month = extract_month_from_filename(file_path)
        df = pd.read_csv(file_path, low_memory=False)
        df['data_month'] = month
        return df, Path(file_path).name, len(df)
    except Exception as e:
        print(f"  ⚠ Error loading {Path(file_path).name}: {e}")
        return pd.DataFrame(), Path(file_path).name, 0


def parallel_load_csvs(folder_name, data_source_name, months_filter=None):
    """Load all CSVs from a folder in parallel"""
    print(f"\n[Loading {data_source_name}...]")

    # Check if specific files were selected via command line
    selected_files = FILE_SELECTION.get(folder_name)

    if selected_files:
        # Use selected files from webapp
        files = selected_files
        print(f"  Using {len(files)} selected files from webapp")
    else:
        # Use default glob pattern
        files = sorted(glob.glob(str(DATA_DIR / folder_name / f'{folder_name}_*.csv')))

        # Filter by months if specified
        if months_filter:
            files = [f for f in files if any(month in f for month in months_filter)]

    if not files:
        print(f"  ⚠ No {folder_name} files found")
        return pd.DataFrame()

    dfs = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(load_csv_with_month, f): f for f in files}

        for future in as_completed(futures):
            df, filename, record_count = future.result()
            if not df.empty:
                dfs.append(df)
                print(f"  ✓ {filename}: {record_count:,} records")

    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"  📊 Total {data_source_name}: {len(combined_df):,} records")
        return combined_df
    else:
        return pd.DataFrame()


# ==================== LOAD N10 (SUBSCRIBER INFO) ====================
print("\n" + "="*100)
print("STEP 1: LOAD N10 (SUBSCRIBER INFO)")
print("="*100)

df_n10 = parallel_load_csvs('N10', 'N10 - Subscriber Info', MONTHS_FILTER)

# Parse dates
if not df_n10.empty:
    df_n10['activation_date'] = pd.to_datetime(df_n10['activation_date'], format='%d/%m/%Y', errors='coerce')
    df_n10['expire_date'] = pd.to_datetime(df_n10['expire_date'], format='%d/%m/%Y', errors='coerce')
    print(f"  ✓ Unique subscribers: {df_n10['isdn'].nunique():,}")


# ==================== LOAD N4 (ADVANCE DATA) ====================
print("\n" + "="*100)
print("STEP 2: LOAD N4 (ADVANCE DATA)")
print("="*100)

df_n4 = parallel_load_csvs('N4', 'N4 - Advance', MONTHS_FILTER)

df_n4_agg = pd.DataFrame()
if not df_n4.empty:
    print("\n  Processing N4 by (isdn, month)...")

    # Convert amount to numeric
    df_n4['amount'] = pd.to_numeric(df_n4['amount'], errors='coerce').fillna(0)

    # NEW LOGIC: Split by source type (ut = ứng tiền, hu = hoàn ứng/hoàn tiền)
    print("  Separating advance (ut) and repayment (hu) transactions...")

    # Create advance_amount and repayment_amount based on source
    df_n4['advance_amount'] = np.where(df_n4['source'] == 'ut', df_n4['amount'], 0)
    df_n4['repayment_amount'] = np.where(df_n4['source'] == 'hu', df_n4['amount'], 0)

    # CRITICAL LOGIC: Apply service-type-specific transformation
    # Based on investigation: EasyCredit and ungdata247 values need to be divided by 10
    print("  Applying service-type-specific corrections...")
    df_n4['advance_amount_corrected'] = np.where(
        df_n4['advance_service_type'].isin(['EasyCredit', 'ungdata247']),
        df_n4['advance_amount'] / 10,  # Divide by 10 for these services
        df_n4['advance_amount']  # Keep original for others (MBFG, UT_SPLUS, etc.)
    )

    df_n4['repayment_amount_corrected'] = np.where(
        df_n4['advance_service_type'].isin(['EasyCredit', 'ungdata247']),
        df_n4['repayment_amount'] / 10,
        df_n4['repayment_amount']
    )

    # Aggregate by subscriber-month
    df_n4_agg = df_n4.groupby(['isdn', 'data_month'], as_index=False).agg({
        'advance_amount_corrected': ['count', 'sum', 'mean', 'max'],
        'repayment_amount_corrected': 'sum',
        'advance_service_type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown'
    })

    # Flatten column names
    df_n4_agg.columns = ['isdn', 'data_month', 'advance_count', 'total_advance_amount',
                         'avg_advance_amount', 'max_advance_amount', 'total_repayment_amount',
                         'most_used_advance_service']

    # Calculate avg_repayment_rate and outstanding_debt
    df_n4_agg['avg_repayment_rate'] = np.where(
        df_n4_agg['total_advance_amount'] > 0,
        df_n4_agg['total_repayment_amount'] / df_n4_agg['total_advance_amount'],
        0
    )
    df_n4_agg['outstanding_debt'] = (df_n4_agg['total_advance_amount'] - df_n4_agg['total_repayment_amount']).clip(lower=0)

    # Add has_advance_in_month flag
    df_n4_agg['has_advance_in_month'] = (df_n4_agg['advance_count'] > 0)

    print(f"  ✓ Aggregated: {len(df_n4_agg):,} subscriber-months")
    print(f"  ✓ Subscribers with advance: {df_n4_agg['isdn'].nunique():,}")
    print(f"  ✓ Total advance records (ut): {(df_n4['source'] == 'ut').sum():,}")
    print(f"  ✓ Total repayment records (hu): {(df_n4['source'] == 'hu').sum():,}")


# ==================== LOAD N5 (TOPUP DATA) ====================
print("\n" + "="*100)
print("STEP 3: LOAD N5 (TOPUP DATA)")
print("="*100)

df_n5 = parallel_load_csvs('N5', 'N5 - Topup', MONTHS_FILTER)

df_n5_agg = pd.DataFrame()
if not df_n5.empty:
    print("\n  Aggregating N5 by (isdn, month)...")

    # Convert to numeric
    df_n5['topup_amount'] = pd.to_numeric(df_n5['topup_amount'], errors='coerce').fillna(0)

    # Aggregate by subscriber-month
    df_n5_agg = df_n5.groupby(['isdn', 'data_month'], as_index=False).agg({
        'topup_amount': ['count', 'sum', 'mean', 'std', 'max'],
        'topup_channel': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown'
    })

    # Flatten column names
    df_n5_agg.columns = ['isdn', 'data_month', 'topup_count', 'total_topup_amount',
                         'avg_topup_amount', 'std_topup_amount', 'max_topup_amount',
                         'most_used_topup_channel']

    # Fill NaN std with 0
    df_n5_agg['std_topup_amount'] = df_n5_agg['std_topup_amount'].fillna(0)

    print(f"  ✓ Aggregated: {len(df_n5_agg):,} subscriber-months")
    print(f"  ✓ Subscribers with topup: {df_n5_agg['isdn'].nunique():,}")


# ==================== LOAD N2 (PACKAGE DATA) ====================
print("\n" + "="*100)
print("STEP 4: LOAD N2 (PACKAGE DATA)")
print("="*100)

df_n2 = parallel_load_csvs('N2', 'N2 - Package', MONTHS_FILTER)

df_n2_agg = pd.DataFrame()
if not df_n2.empty:
    print("\n  Aggregating N2 by (isdn, month)...")

    # Convert price to numeric
    df_n2['package_price'] = pd.to_numeric(df_n2['package_price'], errors='coerce').fillna(0)
    df_n2['package_cycle'] = pd.to_numeric(df_n2['package_cycle'], errors='coerce').fillna(0)

    # Count active and renewed packages
    df_n2['is_active'] = 1
    df_n2['is_renewed'] = df_n2['package_renewal_datetime'].notna().astype(int)

    # Aggregate
    df_n2_agg = df_n2.groupby(['isdn', 'data_month'], as_index=False).agg({
        'package_code': 'count',  # num_packages
        'package_price': ['sum', 'mean', 'max'],
        'package_cycle': 'mean',
        'is_active': 'sum',
        'is_renewed': 'sum'
    })

    # Flatten column names
    df_n2_agg.columns = ['isdn', 'data_month', 'num_packages', 'total_package_value',
                         'avg_package_price', 'max_package_price', 'avg_package_cycle',
                         'num_active_packages', 'num_renewed_packages']

    print(f"  ✓ Aggregated: {len(df_n2_agg):,} subscriber-months")
    print(f"  ✓ Subscribers with packages: {df_n2_agg['isdn'].nunique():,}")


# ==================== LOAD N1 (ARPU DATA) ====================
print("\n" + "="*100)
print("STEP 5: LOAD N1 (ARPU DATA)")
print("="*100)

df_n1 = parallel_load_csvs('N1', 'N1 - ARPU', MONTHS_FILTER)

df_n1_agg = pd.DataFrame()
if not df_n1.empty:
    print("\n  Processing N1 ARPU data...")

    # Convert ARPU columns to numeric
    arpu_cols = ['arpu_call', 'arpu_sms', 'arpu_data', 'arpu_total']
    for col in arpu_cols:
        if col in df_n1.columns:
            df_n1[col] = pd.to_numeric(df_n1[col], errors='coerce').fillna(0)

    # Group by isdn and month (already have data_month from load)
    df_n1_agg = df_n1[['isdn', 'data_month', 'arpu_call', 'arpu_sms', 'arpu_data', 'arpu_total']].copy()

    print(f"  ✓ ARPU data: {len(df_n1_agg):,} subscriber-months")
    print(f"  ✓ Subscribers with ARPU: {df_n1_agg['isdn'].nunique():,}")


# ==================== LOAD N3 (USAGE DATA) ====================
print("\n" + "="*100)
print("STEP 6: LOAD N3 (USAGE DATA)")
print("="*100)

df_n3 = parallel_load_csvs('N3', 'N3 - Usage', MONTHS_FILTER)

df_n3_agg = pd.DataFrame()
if not df_n3.empty:
    print("\n  Aggregating N3 by (isdn, month)...")

    # Just count number of usage records per subscriber-month
    df_n3_agg = df_n3.groupby(['isdn', 'data_month'], as_index=False).size()
    df_n3_agg.columns = ['isdn', 'data_month', 'n3_record_count']

    print(f"  ✓ Aggregated: {len(df_n3_agg):,} subscriber-months")
    print(f"  ✓ Subscribers with usage: {df_n3_agg['isdn'].nunique():,}")


# ==================== MERGE ALL DATA ====================
print("\n" + "="*100)
print("STEP 7: MERGING ALL DATA SOURCES")
print("="*100)

# Start with N10 as base
master = df_n10.copy()
print(f"  [Base] N10: {len(master):,} records")

# Merge N1 (ARPU) - FIRST to ensure ARPU data is available
if not df_n1_agg.empty:
    master = master.merge(df_n1_agg, on=['isdn', 'data_month'], how='left')
    print(f"  [+N1] After merge: {len(master):,} records")

# Merge N4 (Advance)
if not df_n4_agg.empty:
    master = master.merge(df_n4_agg, on=['isdn', 'data_month'], how='left')
    print(f"  [+N4] After merge: {len(master):,} records")

# Merge N5 (Topup)
if not df_n5_agg.empty:
    master = master.merge(df_n5_agg, on=['isdn', 'data_month'], how='left')
    print(f"  [+N5] After merge: {len(master):,} records")

# Merge N2 (Package)
if not df_n2_agg.empty:
    master = master.merge(df_n2_agg, on=['isdn', 'data_month'], how='left')
    print(f"  [+N2] After merge: {len(master):,} records")

# Merge N3 (Usage)
if not df_n3_agg.empty:
    master = master.merge(df_n3_agg, on=['isdn', 'data_month'], how='left')
    print(f"  [+N3] After merge: {len(master):,} records")

# Fill NaN values
print("\n  Filling missing values...")

# Numeric columns - fill with 0
numeric_cols = [
    'arpu_call', 'arpu_sms', 'arpu_data', 'arpu_total',
    'advance_count', 'total_advance_amount', 'avg_advance_amount', 'max_advance_amount',
    'total_repayment_amount', 'avg_repayment_rate', 'outstanding_debt',
    'topup_count', 'total_topup_amount', 'avg_topup_amount', 'std_topup_amount', 'max_topup_amount',
    'num_packages', 'total_package_value', 'avg_package_price', 'max_package_price',
    'avg_package_cycle', 'num_active_packages', 'num_renewed_packages',
    'n3_record_count'
]

for col in numeric_cols:
    if col in master.columns:
        master[col] = master[col].fillna(0)

# Boolean columns
if 'has_advance_in_month' in master.columns:
    master['has_advance_in_month'] = master['has_advance_in_month'].fillna(False)

# String columns - fill with 'Unknown'
if 'most_used_advance_service' in master.columns:
    master['most_used_advance_service'] = master['most_used_advance_service'].fillna('Unknown')
if 'most_used_topup_channel' in master.columns:
    master['most_used_topup_channel'] = master['most_used_topup_channel'].fillna('Unknown')

print(f"  ✓ Final master dataset:")
print(f"    Records: {len(master):,}")
print(f"    Columns: {len(master.columns)}")
print(f"    Unique subscribers: {master['isdn'].nunique():,}")
print(f"    Months: {sorted(master['data_month'].unique())}")


# ==================== SAVE ====================
print("\n" + "="*100)
print("STEP 8: SAVING MASTER FILE")
print("="*100)

# Generate output filename - fixed name for Phase 2 input
output_file = OUTPUT_DIR / 'master_full_202503-202508.parquet'

master.to_parquet(output_file, compression='snappy', index=False)

file_size_mb = output_file.stat().st_size / (1024 * 1024)

print(f"\n💾 Saved:")
print(f"  File: {output_file.name}")
print(f"  Path: {output_file}")
print(f"  Size: {file_size_mb:.1f} MB")
print(f"  Records: {len(master):,}")
print(f"  Columns: {len(master.columns)}")

# Show column list
print(f"\n📊 Columns in master file ({len(master.columns)}):")
for i, col in enumerate(master.columns, 1):
    print(f"  {i:2d}. {col}")

elapsed = datetime.now() - start_time
print(f"\n⏱ Total time: {elapsed}")
print("="*100)
print("✅ PHASE 1 COMPLETED")
print("="*100)
print(f"\nOutput file: {output_file}")
print("\nNext step: Run Phase 2 to create features from this master file")
