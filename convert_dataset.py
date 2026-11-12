"""
Convert the downloaded retail_sales.csv to the format expected by RDCP training scripts.
Expected format: date,store,item,sales (integers)
"""
import pandas as pd
import os

# Load the downloaded dataset
df = pd.read_csv(r'C:\Users\Lenovo\Downloads\archive_extracted\retail_sales.csv')

print(f"Original shape: {df.shape}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"Stores: {df['store_id'].nunique()}")
print(f"Items: {df['item_id'].nunique()}")

# Convert store_id from "store_1" -> 1, item_id from "item_1" -> 1
df['store'] = df['store_id'].str.replace('store_', '').astype(int)
df['item'] = df['item_id'].str.replace('item_', '').astype(int)

# Filter to stores 1-10 (project expects 10 stores)
df = df[(df['store'] >= 1) & (df['store'] <= 10)].copy()

# Select only required columns
df_out = df[['date', 'store', 'item', 'sales']].copy()

# Verify
print(f"\nConverted shape: {df_out.shape}")
print(f"Store range: {df_out['store'].min()}-{df_out['store'].max()}")
print(f"Item range: {df_out['item'].min()}-{df_out['item'].max()}")
print(f"Date range: {df_out['date'].min()} to {df_out['date'].max()}")
print(df_out.head(10))

# Save to project data directory
os.makedirs(r'C:\Users\Lenovo\rdcp\data', exist_ok=True)
output_path = r'C:\Users\Lenovo\rdcp\data\train.csv'
df_out.to_csv(output_path, index=False)
print(f"\nSaved to: {output_path}")

# Verify the split dates work (last 3 months = test)
df_out['date'] = pd.to_datetime(df_out['date'])
max_date = df_out['date'].max()
test_start = max_date - pd.DateOffset(months=3)
print(f"\nTest period would be: {test_start.date()} to {max_date.date()}")
print(f"Train period would be: {df_out['date'].min().date()} to {test_start.date()}")