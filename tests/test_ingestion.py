import pytest
import pandas as pd
from ingestion.cleaner.normalise import clean_file
from ingestion.cleaner.validator import validate
 
def test_clean_file_removes_empty_rows(tmp_path):
    # Create a test XLSX with empty rows (simulating POS export)
    test_data = pd.DataFrame({
        'GROUP': ['RUBIS', None, 'RUBIS'],
        'DEPARTMENT': ['Bakery', None, 'Water'],
        'CLASS': ['Bread', None, 'Bottled'],
        'Code': ['SKU001', None, 'SKU002'],
        'Product Description': ['Bread 400g', None, 'Water 500ml'],
        'Qty': [10, None, 5],
        'Gross Sales(A)': [500, None, 200],
        'Discount(B)': [0, None, 0],
        '(A-B)': [500, None, 200],
        'Vat Amt': [0, None, 0],
        'Unnamed: 10': [None, None, None],
        'Net Sale': [500, None, 200],
        'Cst Ls Vt': [400, None, 150],
        'Unnamed: 13': [None, None, None],
        'Net Contri.': [100, None, 50],
        'Mrgn': [20, None, 25],
        'MkUp ': [25, None, 33],
    })
    f = tmp_path / 'test.xlsx'
    test_data.to_excel(f, index=False)
 
    result = clean_file(str(f), 'TestBranch')
    assert len(result) == 2, 'Empty rows should be removed'
    assert 'Unnamed: 10' not in result.columns
    assert 'branch' in result.columns
 
def test_validate_passes_good_data():
    df = pd.DataFrame({
        'branch': ['Jogoo Road', 'Kingo'],
        'department': ['BAKERY', 'WATER'],
        'sku_code': ['SKU001', 'SKU002'],
        'product_name': ['Bread', 'Water'],
        'quantity': [10, 5],
        'gross_sales': [500, 200],
        'net_sale': [490, 195],
    })
    assert validate(df) == True
