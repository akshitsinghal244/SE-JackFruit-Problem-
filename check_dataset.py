import pandas as pd
df = pd.read_csv(r'C:\Users\Lenovo\Downloads\archive_extracted\retail_sales.csv')
print('Shape:', df.shape)
print('Date range:', df['date'].min(), 'to', df['date'].max())
print('Stores:', df['store_id'].nunique(), df['store_id'].unique()[:10])
print('Items:', df['item_id'].nunique(), df['item_id'].unique()[:10])
print('Columns:', list(df.columns))
print()
print(df.head(10))