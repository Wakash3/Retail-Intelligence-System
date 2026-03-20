# models/run_all_models.py
# Rubis POS — Master ML Runner
# Runs all 3 models in sequence and generates a combined summary report

import pandas as pd
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.anomaly_detection.margin_anomaly import run_anomaly_detection
from models.stockout_prediction.stockout_risk import run_stockout_prediction
from models.revenue_forecasting.revenue_forecast import run_revenue_forecast

def run_all_models():
    start_time = datetime.now()

    print("="*60)
    print("RUBIS POS — MASTER ML RUNNER")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = {}
    errors = []

    # ─────────────────────────────────────────
    # MODEL 1 — Margin Anomaly Detection
    # ─────────────────────────────────────────
    print("\n[1/3] Running Margin Anomaly Detection...")
    try:
        anomaly_results = run_anomaly_detection()
        critical_count = len(anomaly_results[anomaly_results['severity'] == 'Critical'])
        warning_count = len(anomaly_results[anomaly_results['severity'] == 'Warning'])
        results['anomaly'] = {
            'status': 'success',
            'total_analysed': len(anomaly_results),
            'critical': critical_count,
            'warning': warning_count
        }
        print(f"✓ Anomaly Detection complete — {critical_count} critical, {warning_count} warnings")
    except Exception as e:
        errors.append(f"Anomaly Detection failed: {str(e)}")
        results['anomaly'] = {'status': 'failed', 'error': str(e)}
        print(f"✗ Anomaly Detection FAILED: {e}")

    # ─────────────────────────────────────────
    # MODEL 2 — Stockout Risk Prediction
    # ─────────────────────────────────────────
    print("\n[2/3] Running Stockout Risk Prediction...")
    try:
        stockout_results = run_stockout_prediction()
        critical_count = len(stockout_results[stockout_results['stockout_risk'] == 'Critical'])
        high_count = len(stockout_results[stockout_results['stockout_risk'] == 'High'])
        results['stockout'] = {
            'status': 'success',
            'total_analysed': len(stockout_results),
            'critical': critical_count,
            'high': high_count
        }
        print(f"✓ Stockout Prediction complete — {critical_count} critical, {high_count} high risk")
    except Exception as e:
        errors.append(f"Stockout Prediction failed: {str(e)}")
        results['stockout'] = {'status': 'failed', 'error': str(e)}
        print(f"✗ Stockout Prediction FAILED: {e}")

    # ─────────────────────────────────────────
    # MODEL 3 — Revenue Forecasting
    # ─────────────────────────────────────────
    print("\n[3/3] Running Revenue Forecasting...")
    try:
        branch_baseline, projections, dept_targets = run_revenue_forecast()
        network_current = branch_baseline['total_net_sales'].sum()
        network_month1 = projections[
            projections['month_ahead'] == 1
        ]['projected_net_sales'].sum()
        results['forecast'] = {
            'status': 'success',
            'current_revenue': round(network_current, 2),
            'month1_target': round(network_month1, 2)
        }
        print(f"✓ Revenue Forecast complete — current KES {network_current:,.0f}")
    except Exception as e:
        errors.append(f"Revenue Forecast failed: {str(e)}")
        results['forecast'] = {'status': 'failed', 'error': str(e)}
        print(f"✗ Revenue Forecast FAILED: {e}")

    # ─────────────────────────────────────────
    # COMBINED SUMMARY REPORT
    # ─────────────────────────────────────────
    end_time = datetime.now()
    duration = (end_time - start_time).seconds

    print(f"\n{'='*60}")
    print("MASTER RUNNER SUMMARY")
    print(f"{'='*60}")
    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:  {duration} seconds")
    print(f"{'='*60}")

    for model, result in results.items():
        status = result['status'].upper()
        print(f"{model.upper():20} {status}")

    if errors:
        print(f"\nERRORS:")
        for error in errors:
            print(f"  - {error}")

    # Save combined summary
    os.makedirs('reports', exist_ok=True)
    summary = pd.DataFrame([
        {
            'model': 'Anomaly Detection',
            'status': results.get('anomaly', {}).get('status', 'not run'),
            'critical_alerts': results.get('anomaly', {}).get('critical', 0),
            'warning_alerts': results.get('anomaly', {}).get('warning', 0),
            'run_at': end_time.strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'model': 'Stockout Prediction',
            'status': results.get('stockout', {}).get('status', 'not run'),
            'critical_alerts': results.get('stockout', {}).get('critical', 0),
            'warning_alerts': results.get('stockout', {}).get('high', 0),
            'run_at': end_time.strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'model': 'Revenue Forecast',
            'status': results.get('forecast', {}).get('status', 'not run'),
            'critical_alerts': 0,
            'warning_alerts': 0,
            'run_at': end_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    ])

    summary.to_csv('reports/ml_summary.csv', index=False)
    print(f"\nSummary saved to: reports/ml_summary.csv")
    print(f"{'='*60}")

    return results

if __name__ == '__main__':
    run_all_models()