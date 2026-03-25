import pandas as pd
 
REQUIRED_COLS = ['branch', 'department', 'sku_code', 'product_name',
                  'quantity', 'gross_sales', 'net_sale']

 
def validate(df):
    errors = []
    warnings = []
 
    
    for col in REQUIRED_COLS:
        if col not in df.columns:
            errors.append(f'MISSING COLUMN: {col}')
 
    # Check no negative quantities
    neg_qty = df[df['quantity'] < 0]
    if len(neg_qty) > 0:
        warnings.append(f'{len(neg_qty)} rows with negative quantity')
 
    # Check gross_sales >= net_sale
    bad_sales = df[df['gross_sales'] < df['net_sale']]
    if len(bad_sales) > 0:
        warnings.append(f'{len(bad_sales)} rows where gross_sales < net_sale')
 
    # Check all 5 branches present
    expected = {'Jogoo Road','Kingo','Membley','Thome','Tigoni'}
    found = set(df['branch'].unique())
    missing = expected - found
    if missing:
        warnings.append(f'Missing branches: {missing}')
 
    if errors:
        raise ValueError('Validation FAILED: ' + '; '.join(errors))
 
    for w in warnings:
        print(f'WARNING: {w}')
 
    print(f'Validation PASSED: {len(df)} rows, {df["branch"].nunique()} branches')
    return True
