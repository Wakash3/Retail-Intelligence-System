"use client";
import { useApi } from "@/hooks/useApi";
import MetricCard from "@/components/MetricCard";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import { FaChartLine, FaStore, FaBox, FaReceipt } from "react-icons/fa";
import styles from "./page.module.css";
import sharedStyles from "./shared.module.css";

interface Summary {
  total_net_revenue: number;
  total_branches: number;
  total_unique_products: number;
  total_rows: number;
  last_pipeline_run: string;
}

const GREEN_SCALE = ["#1A6B3C","#2E7D32","#388E3C","#43A047","#4CAF50","#66BB6A","#81C784","#A5D6A7"];

export default function DashboardPage() {
  const { data: summary, loading } = useApi<Summary>("/summary");
  const { data: branches } = useApi<Record<string, unknown>[]>("/branches");
  const { data: scorecard } = useApi<Record<string, unknown>[]>("/scorecard");

  const display = (branches && branches.length > 0) ? branches : scorecard ?? [];

  const revCol = display[0]
    ? ["total_revenue","revenue","net_sale","current_revenue"].find(c => c in display[0]) ?? null
    : null;
  const marginCol = display[0]
    ? ["avg_margin","margin","margin_pct"].find(c => c in display[0]) ?? null
    : null;

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
            icon={<FaChartLine />}
            accent="green"
            delay={0}
          />
          <MetricCard
            label="Active Branches"
            value={summary?.total_branches ?? 0}
            sub="Reporting locations"
            icon={<FaStore />}
            accent="green"
            delay={80}
          />
          <MetricCard
            label="Unique Products"
            value={(summary?.total_unique_products ?? 0).toLocaleString()}
            sub="Distinct SKUs tracked"
            icon={<FaBox />}
            accent="amber"
            delay={160}
          />
          <MetricCard
            label="Transactions"
            value={(summary?.total_rows ?? 0).toLocaleString()}
            sub="Total POS records"
            icon={<FaReceipt />}
            accent="green"
            delay={240}
          />
        </div>
      )}

      {/* Branch + Margin charts on the overview */}
      {display.length > 0 && (
        <div className={sharedStyles.chartGrid} style={{ marginBottom: "1.5rem" }}>
          {revCol && (
            <div className={`card ${sharedStyles.chartCard}`}>
              <h3 className={sharedStyles.chartTitle}>Revenue by Branch</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={display} margin={{ top: 8, right: 8, bottom: 40, left: 8 }}>
                  <XAxis dataKey="branch" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
                  <Tooltip formatter={(v: number) => [`KES ${v.toLocaleString()}`, "Revenue"]} />
                  <Bar dataKey={revCol} radius={[4,4,0,0]}>
                    {display.map((_, i) => (
                      <Cell key={i} fill={GREEN_SCALE[i % GREEN_SCALE.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {marginCol && (
            <div className={`card ${sharedStyles.chartCard}`}>
              <h3 className={sharedStyles.chartTitle}>Margin % by Branch</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={display} margin={{ top: 8, right: 8, bottom: 40, left: 8 }}>
                  <XAxis dataKey="branch" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                  <Tooltip formatter={(v: number) => [`${v}%`, "Avg Margin"]} />
                  <ReferenceLine y={5} stroke="#D32F2F" strokeDasharray="4 4" label={{ value: "5% Min", fill: "#D32F2F", fontSize: 11 }} />
                  <Bar dataKey={marginCol} radius={[4,4,0,0]}>
                    {display.map((row, i) => {
                      const val = Number(row[marginCol!] ?? 0);
                      return <Cell key={i} fill={val < 5 ? "#D32F2F" : val < 10 ? "#ED6C02" : "#1A6B3C"} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
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
