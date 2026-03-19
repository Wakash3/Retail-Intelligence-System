# models/revenue_forecasting/revenue_forecast.py
# Rubis POS — Revenue Forecasting Model
# Forecasts branch revenue targets and flags underperforming branches
# NOTE: With one snapshot, this builds the framework and baseline.
# Accuracy improves as more monthly data is loaded into the pipeline.

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
            gross_sales,
            discount,
            net_sale,
            net_contribution,
            margin_pct,
            loaded_at
        FROM pos_sales
        WHERE net_sale > 0
          AND net_sale IS NOT NULL
    """, engine)
    # Extract month and year from loaded_at
    df['loaded_at'] = pd.to_datetime(df['loaded_at'])
    df['year_month'] = df['loaded_at'].dt.to_period('M')
    return df

def calculate_branch_baselines(df):
    # Calculate current branch performance baselines
    branch_baseline = df.groupby('branch').agg(
        total_net_sales=('net_sale', 'sum'),
        total_gross_sales=('gross_sales', 'sum'),
        total_contribution=('net_contribution', 'sum'),
        total_units=('quantity', 'sum'),
        avg_margin=('margin_pct', 'mean'),
        product_count=('sku_code', 'nunique')
    ).reset_index()

    # Calculate network totals
    network_total = branch_baseline['total_net_sales'].sum()
    branch_baseline['network_share_pct'] = (
        branch_baseline['total_net_sales'] / network_total * 100
    ).round(2)

    # Revenue per product — efficiency metric
    branch_baseline['revenue_per_product'] = (
        branch_baseline['total_net_sales'] / branch_baseline['product_count']
    ).round(2)

    return branch_baseline

def calculate_growth_targets(branch_baseline, growth_rate=0.05):
    # Set revenue targets based on current baseline + growth rate
    # Default 5% monthly growth target
    branch_baseline['target_net_sales'] = (
        branch_baseline['total_net_sales'] * (1 + growth_rate)
    ).round(2)

    branch_baseline['target_contribution'] = (
        branch_baseline['total_contribution'] * (1 + growth_rate)
    ).round(2)

    branch_baseline['revenue_gap'] = (
        branch_baseline['target_net_sales'] - branch_baseline['total_net_sales']
    ).round(2)

    return branch_baseline

def calculate_department_targets(df):
    dept_baseline = df.groupby(['branch', 'department']).agg(
        total_net_sales=('net_sale', 'sum'),
        total_contribution=('net_contribution', 'sum'),
        avg_margin=('margin_pct', 'mean'),
        total_units=('quantity', 'sum')
    ).reset_index()

    # Flag underperforming branch/department combinations
    dept_avg = dept_baseline.groupby('department')['total_net_sales'].transform('mean')
    dept_baseline['vs_dept_avg'] = (
        (dept_baseline['total_net_sales'] - dept_avg) / dept_avg * 100
    ).round(2)

    dept_baseline['performance_flag'] = 'On Target'
    dept_baseline.loc[dept_baseline['vs_dept_avg'] < -20, 'performance_flag'] = 'Underperforming'
    dept_baseline.loc[dept_baseline['vs_dept_avg'] > 20, 'performance_flag'] = 'Outperforming'

    return dept_baseline

def project_monthly_revenue(branch_baseline, months=3):
    # Project revenue for next N months using linear growth assumption
    projections = []
    for _, row in branch_baseline.iterrows():
        for month in range(1, months + 1):
            projected = row['total_net_sales'] * (1.05 ** month)
            projections.append({
                'branch': row['branch'],
                'month_ahead': month,
                'projected_net_sales': round(projected, 2),
                'projected_contribution': round(
                    row['total_contribution'] * (1.05 ** month), 2
                )
            })
    return pd.DataFrame(projections)

def run_revenue_forecast():
    print("="*60)
    print("RUBIS POS — REVENUE FORECASTING MODEL")
    print("="*60)

    print("\nLoading data from database...")
    df = get_data()
    print(f"Loaded {len(df)} records")
    print(f"Data period: {df['year_month'].min()} to {df['year_month'].max()}")

    print("\nCalculating branch baselines...")
    branch_baseline = calculate_branch_baselines(df)

    print("Setting growth targets (5% monthly)...")
    branch_baseline = calculate_growth_targets(branch_baseline, growth_rate=0.05)

    print("Calculating department targets...")
    dept_targets = calculate_department_targets(df)

    print("Projecting next 3 months revenue...")
    projections = project_monthly_revenue(branch_baseline, months=3)

    # Display results
    print(f"\n{'='*60}")
    print("CURRENT BRANCH PERFORMANCE BASELINE")
    print(f"{'='*60}")
    print(branch_baseline[[
        'branch', 'total_net_sales', 'total_contribution',
        'avg_margin', 'network_share_pct', 'revenue_per_product'
    ]].to_string(index=False))

    print(f"\n{'='*60}")
    print("BRANCH REVENUE TARGETS (5% growth)")
    print(f"{'='*60}")
    print(branch_baseline[[
        'branch', 'total_net_sales', 'target_net_sales', 'revenue_gap'
    ]].to_string(index=False))

    print(f"\n{'='*60}")
    print("3-MONTH REVENUE PROJECTIONS PER BRANCH")
    print(f"{'='*60}")
    pivot = projections.pivot(
        index='branch',
        columns='month_ahead',
        values='projected_net_sales'
    ).reset_index()
    pivot.columns = ['branch', 'Month 1 (KES)', 'Month 2 (KES)', 'Month 3 (KES)']
    print(pivot.to_string(index=False))

    print(f"\n{'='*60}")
    print("UNDERPERFORMING BRANCH x DEPARTMENT")
    print(f"{'='*60}")
    underperforming = dept_targets[
        dept_targets['performance_flag'] == 'Underperforming'
    ].sort_values('vs_dept_avg')
    print(underperforming[[
        'branch', 'department', 'total_net_sales',
        'vs_dept_avg', 'performance_flag'
    ]].to_string(index=False))

    print(f"\n{'='*60}")
    print("OUTPERFORMING BRANCH x DEPARTMENT")
    print(f"{'='*60}")
    outperforming = dept_targets[
        dept_targets['performance_flag'] == 'Outperforming'
    ].sort_values('vs_dept_avg', ascending=False)
    print(outperforming[[
        'branch', 'department', 'total_net_sales',
        'vs_dept_avg', 'performance_flag'
    ]].to_string(index=False))

    # Network total projection
    network_current = branch_baseline['total_net_sales'].sum()
    network_month1 = projections[projections['month_ahead'] == 1]['projected_net_sales'].sum()
    network_month2 = projections[projections['month_ahead'] == 2]['projected_net_sales'].sum()
    network_month3 = projections[projections['month_ahead'] == 3]['projected_net_sales'].sum()

    print(f"\n{'='*60}")
    print("NETWORK REVENUE PROJECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Current total:    KES {network_current:,.2f}")
    print(f"Month 1 target:   KES {network_month1:,.2f}")
    print(f"Month 2 target:   KES {network_month2:,.2f}")
    print(f"Month 3 target:   KES {network_month3:,.2f}")

    # Save reports
    os.makedirs('reports', exist_ok=True)
    with pd.ExcelWriter('reports/revenue_forecast_report.xlsx', engine='openpyxl') as writer:
        branch_baseline.to_excel(writer, sheet_name='Branch Baseline', index=False)
        projections.to_excel(writer, sheet_name='3 Month Projections', index=False)
        dept_targets.to_excel(writer, sheet_name='Department Targets', index=False)
        underperforming.to_excel(writer, sheet_name='Underperforming', index=False)
        outperforming.to_excel(writer, sheet_name='Outperforming', index=False)

    print(f"\nReport saved to: reports/revenue_forecast_report.xlsx")
    print(f"{'='*60}")

    return branch_baseline, projections, dept_targets

if __name__ == '__main__':
    run_revenue_forecast()