import pandas as pd
import numpy as np
import os, glob

COLUMN_MAP = {
    'Unnamed: 0':  'branch',
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
    'Vat Amount':   'vat_amount',
    'Net Sale':     'net_sale',
    'Net Sales':    'net_sale',
    'Cst Ls Vt':    'cost_ex_vat',
    'Cst Ls Vt\n':  'cost_ex_vat',
    'Net Contri.':  'net_contribution',
    'Net Contribution': 'net_contribution',
    'Mrgn':         'margin_pct',
    'Margin ':      'margin_pct',
    'MkUp ':        'markup_pct',
    'Markup ':      'markup_pct',
}

DROP_COLS = ['Unnamed: 10', 'Unnamed: 13']

def clean_file(filepath, branch_name):
    df = pd.read_excel(filepath)

    
    if 'Code' not in df.columns and 'Unnamed: 0' not in df.columns and 'GROUP' not in df.columns:
        return pd.DataFrame()

    
    df = df.dropna(how='all')

    
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])

    
    df = df.rename(columns=COLUMN_MAP)

    
    if 'product_name' not in df.columns and 'class' in df.columns:
        df['product_name'] = df['class']
    if 'sku_code' not in df.columns and 'class' in df.columns:
        df['sku_code'] = df['class']

    
    df['branch'] = branch_name

   
    
    import datetime
    file_mod_time = os.path.getmtime(filepath)
    file_date = datetime.date.fromtimestamp(file_mod_time)

    df['source_file']   = os.path.basename(filepath)
    df['source_branch'] = branch_name
    df['loaded_at']     = pd.Timestamp.now()
    df['sales_date']    = file_date
    df['sales_month']   = file_date.strftime('%Y-%m')
    df['sales_year']    = file_date.year

    
    if 'department' in df.columns:
        df['department'] = df['department'].astype(str).str.strip().str.upper()

    
    if 'sku_code' in df.columns:
        df = df[df['sku_code'].notna()]
    else:
        df = df[df['gross_sales'].notna()]

    
    if 'net_sale' in df.columns:
        df = df[df['net_sale'].notna()]

    
    if 'product_name' in df.columns:
        df = df[df['product_name'].notna()]

    
    df = df.replace([np.inf, -np.inf], np.nan)

    return df

def clean_all(raw_dir='data/raw', clean_dir='data/clean'):
    os.makedirs(clean_dir, exist_ok=True)
    all_frames = []

    for branch_folder in os.listdir(raw_dir):
        branch_path = os.path.join(raw_dir, branch_folder)
        if not os.path.isdir(branch_path): continue

        seen = set()
        for xlsx in glob.glob(f'{branch_path}/*.XLSX') + \
                     glob.glob(f'{branch_path}/*.xlsx'):
            normalized = xlsx.lower()
            if normalized in seen:
                continue
            seen.add(normalized)

            try:
                df = clean_file(xlsx, branch_folder)
                if df.empty:
                    print(f'  SKIPPED (no product data): {branch_folder}/{os.path.basename(xlsx)}')
                    continue
                all_frames.append(df)
                print(f'  Cleaned: {branch_folder}/{os.path.basename(xlsx)} -> {len(df)} rows')
            except Exception as e:
                print(f'  ERROR: {xlsx}: {e}')

    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(f'{clean_dir}/pos_sales_clean.csv', index=False)
    print(f'Total clean rows: {len(combined)}')
    return combined
  