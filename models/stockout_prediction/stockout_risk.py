# models/stockout_prediction/stockout_risk.py
# Rubis POS — Stockout Risk Prediction Model
# Predicts which products are at highest risk of running out of stock
# based on sales velocity relative to quantity sold

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

def get_data():
    engine = create_engine(os.getenv('DB_URL'))
    df = pd.read_sql("""
        SELECT
            sku_code,
            product_name,
            branch,
            department,
            quantity,
            net_sale,
            gross_sales,
            net_contribution,
            margin_pct
        FROM pos_sales
        WHERE quantity IS NOT NULL
          AND quantity > 0
          AND net_sale > 0
    """, engine)
    return df

def calculate_sales_velocity(df):
    # Sales velocity = units sold relative to average for that department
    dept_avg_qty = df.groupby('department')['quantity'].transform('mean')
    dept_std_qty = df.groupby('department')['quantity'].transform('std').fillna(1).replace(0, 1)

    # Velocity score — how fast this product sells vs department average
    df['velocity_score'] = (df['quantity'] - dept_avg_qty) / dept_std_qty

    # Revenue velocity — how much revenue per unit
    df['revenue_per_unit'] = df['net_sale'] / df['quantity']

    # Network average revenue per unit per department
    dept_avg_revenue = df.groupby('department')['revenue_per_unit'].transform('mean')
    df['revenue_velocity'] = df['revenue_per_unit'] / dept_avg_revenue

    return df

def calculate_reorder_priority(df):
    # Combine velocity score and revenue velocity into a priority score
    # High quantity sold + high revenue per unit = highest reorder priority
    df['priority_score'] = (
        (df['velocity_score'] * 0.5) +
        (df['revenue_velocity'] * 0.3) +
        (df['margin_pct'].fillna(0) / 100 * 0.2)
    )

    # Risk classification
    df['stockout_risk'] = 'Low'
    df.loc[df['velocity_score'] > 1, 'stockout_risk'] = 'Medium'
    df.loc[df['velocity_score'] > 2, 'stockout_risk'] = 'High'
    df.loc[df['velocity_score'] > 3, 'stockout_risk'] = 'Critical'

    return df

def run_stockout_prediction():
    print("="*60)
    print("RUBIS POS — STOCKOUT RISK PREDICTION")
    print("="*60)

    print("\nLoading data from database...")
    df = get_data()
    print(f"Loaded {len(df)} product records")

    print("\nCalculating sales velocity...")
    df = calculate_sales_velocity(df)

    print("Calculating reorder priority scores...")
    df = calculate_reorder_priority(df)

    # Summary
    critical = df[df['stockout_risk'] == 'Critical']
    high = df[df['stockout_risk'] == 'High']
    medium = df[df['stockout_risk'] == 'Medium']

    print(f"\n{'='*60}")
    print("STOCKOUT RISK SUMMARY")
    print(f"{'='*60}")
    print(f"Total products analysed:  {len(df)}")
    print(f"Critical risk:            {len(critical)}")
    print(f"High risk:                {len(high)}")
    print(f"Medium risk:              {len(medium)}")

    print(f"\n{'='*60}")
    print("CRITICAL STOCKOUT RISK PRODUCTS")
    print(f"{'='*60}")
    critical_display = critical[[
        'product_name', 'branch', 'department',
        'quantity', 'net_sale', 'velocity_score', 'priority_score'
    ]].sort_values('priority_score', ascending=False)
    print(critical_display.to_string(index=False))

    print(f"\n{'='*60}")
    print("TOP 20 HIGH PRIORITY REORDER LIST (across all branches)")
    print(f"{'='*60}")
    reorder_list = df.groupby(['sku_code', 'product_name', 'department']).agg(
        total_quantity=('quantity', 'sum'),
        total_net_sales=('net_sale', 'sum'),
        branches_selling=('branch', 'nunique'),
        avg_velocity=('velocity_score', 'mean'),
        avg_priority=('priority_score', 'mean'),
        avg_margin=('margin_pct', 'mean')
    ).reset_index().sort_values('avg_priority', ascending=False).head(20)
    print(reorder_list.to_string(index=False))

    print(f"\n{'='*60}")
    print("STOCKOUT RISK BY BRANCH")
    print(f"{'='*60}")
    branch_risk = df[df['stockout_risk'].isin(['Critical', 'High'])]\
        .groupby('branch')['product_name'].count()\
        .reset_index()\
        .rename(columns={'product_name': 'high_risk_products'})\
        .sort_values('high_risk_products', ascending=False)
    print(branch_risk.to_string(index=False))

    print(f"\n{'='*60}")
    print("STOCKOUT RISK BY DEPARTMENT")
    print(f"{'='*60}")
    dept_risk = df[df['stockout_risk'].isin(['Critical', 'High'])]\
        .groupby('department')['product_name'].count()\
        .reset_index()\
        .rename(columns={'product_name': 'high_risk_products'})\
        .sort_values('high_risk_products', ascending=False)
    print(dept_risk.to_string(index=False))

    # Save results
    os.makedirs('reports', exist_ok=True)
    with pd.ExcelWriter('reports/stockout_risk_report.xlsx', engine='openpyxl') as writer:
        critical[['product_name', 'branch', 'department', 'quantity',
                  'net_sale', 'velocity_score', 'priority_score', 'stockout_risk']]\
            .sort_values('priority_score', ascending=False)\
            .to_excel(writer, sheet_name='Critical Risk', index=False)

        high[['product_name', 'branch', 'department', 'quantity',
              'net_sale', 'velocity_score', 'priority_score', 'stockout_risk']]\
            .sort_values('priority_score', ascending=False)\
            .to_excel(writer, sheet_name='High Risk', index=False)

        reorder_list.to_excel(writer, sheet_name='Top 20 Reorder List', index=False)
        branch_risk.to_excel(writer, sheet_name='Risk by Branch', index=False)
        dept_risk.to_excel(writer, sheet_name='Risk by Department', index=False)

    print(f"\nReport saved to: reports/stockout_risk_report.xlsx")
    print(f"{'='*60}")

    return df

if __name__ == '__main__':
    run_stockout_prediction()
