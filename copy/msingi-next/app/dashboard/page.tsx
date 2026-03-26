"use client";
import { useApi } from "@/hooks/useApi";
import MetricCard from "@/components/MetricCard";
import styles from "./page.module.css";

interface Summary {
  total_net_revenue: number;
  total_branches: number;
  total_unique_products: number;
  total_rows: number;
  last_pipeline_run: string;
}

export default function DashboardPage() {
  const { data: summary, loading } = useApi<Summary>("/summary");

  return (
    <div>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Overview</h1>
          <p className={styles.subtitle}>Msingi Retail Intelligence Platform</p>
        </div>
        <div className={styles.lastUpdate}>
          {summary?.last_pipeline_run
            ? `Last sync: ${new Date(summary.last_pipeline_run).toLocaleString()}`
            : "Fetching…"}
        </div>
      </div>

      {loading ? (
        <div className={styles.skeletonGrid}>
          {[0,1,2,3].map(i => <div key={i} className={styles.skeleton} />)}
        </div>
      ) : (
        <div className={styles.kpiGrid}>
          <MetricCard
            label="Total Revenue"
            value={`KES ${(summary?.total_net_revenue ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            sub="Net sales across all branches"
            accent="green"
            delay={0}
          />
          <MetricCard
            label="Active Branches"
            value={summary?.total_branches ?? 0}
            sub="Reporting locations"
            accent="green"
            delay={80}
          />
          <MetricCard
            label="Unique Products"
            value={(summary?.total_unique_products ?? 0).toLocaleString()}
            sub="Distinct SKUs tracked"
            accent="amber"
            delay={160}
          />
          <MetricCard
            label="Transactions"
            value={(summary?.total_rows ?? 0).toLocaleString()}
            sub="Total POS records"
            accent="green"
            delay={240}
          />
        </div>
      )}

      <div className={styles.infoRow}>
        <div className={`card ${styles.infoCard}`}>
          <h3>Quick Navigation</h3>
          <p>Use the sidebar to explore Branch Analytics, Products, Alerts, Recommendations, the Scorecard, and Data Quality reports. Click <strong>✦</strong> at the bottom-right to ask Gladwell anything about your data.</p>
        </div>
      </div>
    </div>
  );
}
