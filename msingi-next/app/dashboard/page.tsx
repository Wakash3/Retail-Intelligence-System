"use client";
import { useApi } from "@/hooks/useApi";
import MetricCard from "@/components/MetricCard";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine, CartesianGrid
} from "recharts";
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

const BAR_PALETTE = [
  "#6366F1","#F59E0B","#10B981","#EF4444",
  "#3B82F6","#EC4899","#14B8A6","#F97316",
  "#8B5CF6","#06B6D4","#84CC16","#A78BFA",
];

const tickStyle = { fontSize: 11, fill: "var(--text-secondary, #888)" };

const CustomTooltip = ({ active, payload, label, formatter }: any) => {
  if (!active || !payload?.length) return null;
  const { label: valLabel, value } = formatter(payload[0].value);
  return (
    <div style={{
      background: "var(--card-bg, #1e1e2e)",
      border: "1px solid var(--border-color, #333)",
      borderRadius: 8,
      padding: "10px 14px",
      fontSize: 13,
      color: "var(--text-primary, #f0f0f0)",
      boxShadow: "0 4px 16px rgba(0,0,0,0.25)",
    }}>
      <p style={{ margin: 0, fontWeight: 600, marginBottom: 4 }}>{label}</p>
      <p style={{ margin: 0, color: payload[0].fill }}>{valLabel}: <strong>{value}</strong></p>
    </div>
  );
};

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
          <MetricCard label="Total Revenue" value={`KES ${(summary?.total_net_revenue ?? 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} sub="Net sales across all branches" icon={<FaChartLine />} delay={0} />
          <MetricCard label="Active Branches" value={summary?.total_branches ?? 0} sub="Reporting locations" icon={<FaStore />} delay={80} />
          <MetricCard label="Unique Products" value={(summary?.total_unique_products ?? 0).toLocaleString()} sub="Distinct SKUs tracked" icon={<FaBox />} delay={160} />
          <MetricCard label="Transactions" value={(summary?.total_rows ?? 0).toLocaleString()} sub="Total POS records" icon={<FaReceipt />} delay={240} />
        </div>
      )}

      {display.length > 0 && (
        <div className={sharedStyles.chartGrid} style={{ marginBottom: "1.5rem" }}>
          {revCol && (
            <div className={`card ${sharedStyles.chartCard}`}>
              <h3 className={sharedStyles.chartTitle}>Revenue by Branch</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={display} margin={{ top: 8, right: 16, bottom: 44, left: 8 }} barCategoryGap="30%">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color, rgba(255,255,255,0.08))" vertical={false} />
                  <XAxis dataKey="branch" tick={tickStyle} angle={-30} textAnchor="end" interval={0} axisLine={{ stroke: "var(--border-color, #444)" }} tickLine={false} />
                  <YAxis tick={tickStyle} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "rgba(255,255,255,0.05)" }} content={<CustomTooltip formatter={(v: number) => ({ label: "Revenue", value: `KES ${v.toLocaleString()}` })} />} />
                  <Bar dataKey={revCol} radius={[5,5,0,0]} maxBarSize={44}>
                    {display.map((_, i) => <Cell key={i} fill={BAR_PALETTE[i % BAR_PALETTE.length]} opacity={0.9} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {marginCol && (
            <div className={`card ${sharedStyles.chartCard}`}>
              <h3 className={sharedStyles.chartTitle}>Margin % by Branch</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={display} margin={{ top: 8, right: 16, bottom: 44, left: 8 }} barCategoryGap="30%">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color, rgba(255,255,255,0.08))" vertical={false} />
                  <XAxis dataKey="branch" tick={tickStyle} angle={-30} textAnchor="end" interval={0} axisLine={{ stroke: "var(--border-color, #444)" }} tickLine={false} />
                  <YAxis tick={tickStyle} tickFormatter={(v) => `${v}%`} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "rgba(255,255,255,0.05)" }} content={<CustomTooltip formatter={(v: number) => ({ label: "Avg Margin", value: `${v}%` })} />} />
                  <ReferenceLine y={5} stroke="#EF4444" strokeDasharray="5 4" label={{ value: "5% Min", fill: "#EF4444", fontSize: 11, position: "insideTopRight" }} />
                  <Bar dataKey={marginCol} radius={[5,5,0,0]} maxBarSize={44}>
                    {display.map((row, i) => {
                      const val = Number(row[marginCol!] ?? 0);
                      const fill = val < 5 ? "#EF4444" : val < 10 ? "#F97316" : BAR_PALETTE[i % BAR_PALETTE.length];
                      return <Cell key={i} fill={fill} opacity={0.9} />;
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

