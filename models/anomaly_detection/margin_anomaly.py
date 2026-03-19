# models/anomaly_detection/margin_anomaly.py
# Rubis POS — Margin Anomaly Detection Model
# Detects products with abnormally low margins within their department

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import joblib

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
            net_contribution,
            margin_pct
        FROM pos_sales
        WHERE margin_pct IS NOT NULL
          AND net_sale > 0
          AND department IS NOT NULL
    """, engine)
    return df

def calculate_department_benchmarks(df):
    benchmarks = df.groupby('department')['margin_pct'].agg([
        'mean', 'std', 'median', 'count'
    ]).reset_index()
    benchmarks.columns = ['department', 'dept_avg_margin', 'dept_std_margin',
                          'dept_median_margin', 'dept_product_count']
    # Fill zero std with small value to avoid division by zero
    benchmarks['dept_std_margin'] = benchmarks['dept_std_margin'].fillna(1).replace(0, 1)
    return benchmarks

def calculate_branch_benchmarks(df):
    benchmarks = df.groupby(['department', 'branch'])['margin_pct'].agg([
        'mean', 'std'
    ]).reset_index()
    benchmarks.columns = ['department', 'branch', 'branch_dept_avg', 'branch_dept_std']
    benchmarks['branch_dept_std'] = benchmarks['branch_dept_std'].fillna(1).replace(0, 1)
    return benchmarks

def detect_anomalies(df, dept_benchmarks, branch_benchmarks, z_threshold=-2.0):
    # Merge department benchmarks
    df = df.merge(dept_benchmarks, on='department', how='left')

    # Calculate Z-score per product within its department
    df['z_score'] = (df['margin_pct'] - df['dept_avg_margin']) / df['dept_std_margin']

    # Merge branch benchmarks
    df = df.merge(branch_benchmarks, on=['department', 'branch'], how='left')

    # Flag anomalies
    df['is_anomaly'] = df['z_score'] < z_threshold

    # Severity classification
    df['severity'] = 'Normal'
    df.loc[df['z_score'] < -1, 'severity'] = 'Watch'
    df.loc[df['z_score'] < -2, 'severity'] = 'Warning'
    df.loc[df['z_score'] < -3, 'severity'] = 'Critical'

    # Margin gap — how far below department average
    df['margin_gap'] = df['margin_pct'] - df['dept_avg_margin']

    # Revenue impact — estimated loss from low margin
    df['revenue_impact'] = df['margin_gap'] * df['net_sale'] / 100

    return df

def run_anomaly_detection():
    print("="*60)
    print("RUBIS POS — MARGIN ANOMALY DETECTION")
    print("="*60)

    print("\nLoading data from database...")
    df = get_data()
    print(f"Loaded {len(df)} product records")

    print("\nCalculating department benchmarks...")
    dept_benchmarks = calculate_department_benchmarks(df)

    print("Calculating branch benchmarks...")
    branch_benchmarks = calculate_branch_benchmarks(df)

    print("Running anomaly detection...")
    results = detect_anomalies(df, dept_benchmarks, branch_benchmarks)

    # Summary
    anomalies = results[results['is_anomaly']]
    critical = results[results['severity'] == 'Critical']
    warning = results[results['severity'] == 'Warning']

    print(f"\n{'='*60}")
    print(f"DETECTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total products analysed:  {len(results)}")
    print(f"Anomalies detected:       {len(anomalies)}")
    print(f"  Critical:               {len(critical)}")
    print(f"  Warning:                {len(warning)}")

    print(f"\n{'='*60}")
    print("CRITICAL ANOMALIES (Z-score < -3)")
    print(f"{'='*60}")
    critical_display = critical[[
        'product_name', 'branch', 'department',
        'margin_pct', 'dept_avg_margin', 'z_score', 'revenue_impact'
    ]].sort_values('z_score')
    print(critical_display.to_string(index=False))

    print(f"\n{'='*60}")
    print("UNDERPERFORMING DEPARTMENTS (avg margin below network average)")
    print(f"{'='*60}")
    network_avg = df['margin_pct'].mean()
    underperforming_depts = dept_benchmarks[
        dept_benchmarks['dept_avg_margin'] < network_avg
    ].sort_values('dept_avg_margin')
    print(f"Network average margin: {network_avg:.2f}%")
    print(underperforming_depts[[
        'department', 'dept_avg_margin', 'dept_median_margin', 'dept_product_count'
    ]].to_string(index=False))

    print(f"\n{'='*60}")
    print("UNDERPERFORMING BRANCH x DEPARTMENT COMBINATIONS")
    print(f"{'='*60}")
    branch_dept = results.groupby(['branch', 'department']).agg(
        avg_margin=('margin_pct', 'mean'),
        dept_avg=('dept_avg_margin', 'first')
    ).reset_index()
    branch_dept['gap'] = branch_dept['avg_margin'] - branch_dept['dept_avg']
    underperforming = branch_dept[branch_dept['gap'] < -2].sort_values('gap')
    print(underperforming.to_string(index=False))

    # Save results
    os.makedirs('reports', exist_ok=True)
    results.to_csv('reports/anomaly_detection_results.csv', index=False)

    with pd.ExcelWriter('reports/anomaly_detection_report.xlsx', engine='openpyxl') as writer:
        critical[['product_name', 'branch', 'department', 'margin_pct',
                  'dept_avg_margin', 'z_score', 'severity', 'revenue_impact']]\
            .sort_values('z_score')\
            .to_excel(writer, sheet_name='Critical Anomalies', index=False)

        warning[['product_name', 'branch', 'department', 'margin_pct',
                 'dept_avg_margin', 'z_score', 'severity', 'revenue_impact']]\
            .sort_values('z_score')\
            .to_excel(writer, sheet_name='Warning Anomalies', index=False)

        dept_benchmarks.to_excel(writer, sheet_name='Department Benchmarks', index=False)

        underperforming.to_excel(writer, sheet_name='Underperforming Branch Dept', index=False)

    print(f"\nReports saved to:")
    print(f"  reports/anomaly_detection_results.csv")
    print(f"  reports/anomaly_detection_report.xlsx")
    print(f"{'='*60}")

    return results

if __name__ == '__main__':
    run_anomaly_detection()