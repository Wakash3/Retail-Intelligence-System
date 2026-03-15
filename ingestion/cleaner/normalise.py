import pandas as pd
import os, glob
 
COLUMN_MAP = {
    'Unnamed: 0':  'branch',    # Kingo files use this instead of GROUP
    'GROUP':        'branch',
    'DEPARTMENT':   'department',
    'CLASS':        'class',
    'Code':         'sku_code',
    'Product Description': 'product_name',
    'Qty':          'quantity',
    'Gross Sales(A)': 'gross_sales',
    'Discount(B)':  'discount',
    '(A-B)':        'sales_after_discount',
    'Vat Amt':      'vat_amount',
    'Net Sale':     'net_sale',
    'Cst Ls Vt':    'cost_ex_vat',
    'Net Contri.':  'net_contribution',
    'Mrgn':         'margin_pct',
    'MkUp ':        'markup_pct',
}
 
DROP_COLS = ['Unnamed: 10', 'Unnamed: 13']  
def clean_file(filepath, branch_name):
    df = pd.read_excel(filepath)
 
    # 1. Drop empty rows (POS export artifact)
    df = df.dropna(how='all')
 
    # 2. Drop junk columns
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
 
    # 3. Rename columns to standard names
    df = df.rename(columns=COLUMN_MAP)
 
    # 4. Fill missing branch with folder name
    df['branch'] = branch_name
 
    # 5. Add source metadata
    df['source_file']  = os.path.basename(filepath)
    df['source_branch'] = branch_name
    df['loaded_at']    = pd.Timestamp.now()
 
    # 6. Normalise department names (uppercase for consistency)
    if 'department' in df.columns:
        df['department'] = df['department'].astype(str).str.strip().str.upper()
 
    # 7. Keep only rows with a valid SKU code (if the column exists)
    if 'sku_code' in df.columns:
        df = df[df['sku_code'].notna()]
    else:
        # If no SKU code, keep rows with valid sales data
        df = df[df['gross_sales'].notna()]
 
    return df
    print(df.columns)
 
def clean_all(raw_dir='data/raw', clean_dir='data/clean'):
    os.makedirs(clean_dir, exist_ok=True)
    all_frames = []
 
    for branch_folder in os.listdir(raw_dir):
        branch_path = os.path.join(raw_dir, branch_folder)
        if not os.path.isdir(branch_path): continue
 
        for xlsx in glob.glob(f'{branch_path}/*.XLSX') + \
                     glob.glob(f'{branch_path}/*.xlsx'):
            try:
                df = clean_file(xlsx, branch_folder)
                all_frames.append(df)
                print(f'  Cleaned: {branch_folder}/{os.path.basename(xlsx)} -> {len(df)} rows')
            except Exception as e:
                print(f'  ERROR: {xlsx}: {e}')
 
    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(f'{clean_dir}/pos_sales_clean.csv', index=False)
    print(f'Total clean rows: {len(combined)}')
    return combined
  