"use client";
import { useApi } from "@/hooks/useApi";
import DataTable from "@/components/DataTable";
import MetricCard from "@/components/MetricCard";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend, Cell
} from "recharts";
import styles from "../shared.module.css";
import dqStyles from "./page.module.css";

interface QualityColumn {
  column: string;
  null_count: number;
  null_pct: number;
  status: string;
}

interface DataQuality {
  total_rows: number;
  source_files_loaded: number;
  last_loaded_at: string;
  earliest_sale: string;
  latest_sale: string;
  overall_status: string;
  columns: QualityColumn[];
}

interface ForecastRow {
  branch: string;
  current_revenue: number;
  month1_target: number;
  month2_target: number;
  month3_target: number;
  avg_margin: number;
}

const FORECAST_COLORS = ["#1A6B3C", "#2E7D32", "#43A047", "#81C784"];

export default function DataQualityPage() {
  const { data: dq, loading: l1, refetch } = useApi<DataQuality>("/data-quality");
  const { data: forecast, loading: l2 }    = useApi<ForecastRow[]>("/forecast");

  const loading = l1 || l2;

  const statusClass = (s: string) => {
    if (s === "OK")   return "badge badge-ok";
    if (s === "FAIL") return "badge badge-fail";
    return "badge badge-warn";
  };

  const trimDate = (d: string | null | undefined) => {
    if (!d || d === "None" || d === "null") return "N/A";
    return String(d).slice(0, 10);
  };

  return (
    <div>
      <h1 className={styles.pageTitle}>Data Quality</h1>
      <p className={styles.pageSub}>Pipeline health, completeness checks, and revenue forecast</p>

      {loading ? (
        <div className={styles.spinner} />
      ) : (
        <>
          {/* ── Overall Status Banner ── */}
          {dq && (
            <div
              className={`${dqStyles.banner} ${
                dq.overall_status === "OK"
                  ? dqStyles.bannerOk
                  : dqStyles.bannerFail
              }`}
            >
              <span className={statusClass(dq.overall_status)}>
                {dq.overall_status}
              </span>
              <span className={dqStyles.bannerText}>
                {dq.overall_status === "OK"
                  ? "All data quality checks passed"
                  : "One or more columns failed quality checks — review below"}
              </span>
              <button className={`${styles.btnOutline} ${dqStyles.refreshBtn}`} onClick={refetch}>
                ↺ Refresh
              </button>
            </div>
          )}

          {/* ── KPI Row ── */}
          <div className={dqStyles.kpiRow}>
            <MetricCard
              label="Total Rows"
              value={(dq?.total_rows ?? 0).toLocaleString()}
              accent="green"
              delay={0}
            />
            <MetricCard
              label="Source Files"
              value={dq?.source_files_loaded ?? 0}
              accent="green"
              delay={80}
            />
            <MetricCard
              label="Earliest Sale"
              value={trimDate(dq?.earliest_sale)}
              accent="amber"
              delay={160}
            />
            <MetricCard
              label="Latest Sale"
              value={trimDate(dq?.latest_sale)}
              accent="green"
              delay={240}
            />
          </div>

          {/* ── Column Quality Table ── */}
          {dq?.columns && dq.columns.length > 0 && (
            <div className={`card ${styles.tableCard}`} style={{ marginBottom: "1rem" }}>
              <div className={dqStyles.tableHeader}>
                <h3 className={styles.chartTitle} style={{ marginBottom: 0 }}>
                  Column Quality Report
                </h3>
                {dq.columns.filter(c => c.status === "FAIL").length > 0 ? (
                  <p className={`${styles.alertBox} ${styles.alertFail}`} style={{ marginBottom: 0, marginTop: 0 }}>
                    ✕ {dq.columns.filter(c => c.status === "FAIL").length} column(s) failed
                  </p>
                ) : (
                  <p className={`${styles.alertBox} ${styles.alertOk}`} style={{ marginBottom: 0, marginTop: 0 }}>
                    ✓ All columns passed
                  </p>
                )}
              </div>

              {/* Custom quality table with colour-coded status */}
              <div style={{ overflowX: "auto" }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Null Count</th>
                      <th>Null %</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dq.columns.map((col) => (
                      <tr key={col.column}>
                        <td style={{ fontWeight: 500 }}>{col.column}</td>
                        <td>{col.null_count.toLocaleString()}</td>
                        <td>{col.null_pct}%</td>
                        <td>
                          <span className={statusClass(col.status)}>
                            {col.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── Revenue Forecast ── */}
          {forecast && forecast.length > 0 && (
            <>
              <div className={`card ${styles.tableCard}`} style={{ marginBottom: "1rem" }}>
                <h3 className={styles.chartTitle}>Revenue Forecast Table</h3>
                <DataTable data={forecast as unknown as Record<string, unknown>[]} />
              </div>

              <div className={`card ${styles.chartCard}`}>
                <h3 className={styles.chartTitle}>Revenue Forecast by Branch (3-Month Projection)</h3>
                <ResponsiveContainer width="100%" height={340}>
                  <BarChart
                    data={forecast}
                    margin={{ top: 8, right: 16, bottom: 44, left: 8 }}
                    barCategoryGap="25%"
                  >
                    <XAxis
                      dataKey="branch"
                      tick={{ fontSize: 11 }}
                      angle={-30}
                      textAnchor="end"
                      interval={0}
                    />
                    <YAxis
                      tick={{ fontSize: 11 }}
                      tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
                    />
                    <Tooltip
                      formatter={(v: number, name: string) => [
                        `KES ${v.toLocaleString()}`,
                        name.replace(/_/g, " "),
                      ]}
                    />
                    <Legend
                      wrapperStyle={{ fontSize: "0.78rem", paddingTop: "12px" }}
                    />
                    {(
                      ["current_revenue", "month1_target", "month2_target", "month3_target"] as const
                    ).map((key, i) => (
                      <Bar
                        key={key}
                        dataKey={key}
                        name={key.replace(/_/g, " ")}
                        fill={FORECAST_COLORS[i]}
                        radius={[3, 3, 0, 0]}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
