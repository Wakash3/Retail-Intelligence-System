"use client";
import { useApi } from "@/hooks/useApi";
import DataTable from "@/components/DataTable";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";
import styles from "../shared.module.css";

const GREEN_SCALE = ["#1A6B3C","#2E7D32","#388E3C","#43A047","#4CAF50","#66BB6A","#81C784","#A5D6A7"];

export default function BranchesPage() {
  const { data: branches, loading } = useApi<Record<string,unknown>[]>("/branches");
  const { data: scorecard } = useApi<Record<string,unknown>[]>("/scorecard");

  // Use branches if available, otherwise fall back to scorecard
  const display = (branches && branches.length > 0) ? branches : scorecard ?? [];

  // Flexible column detection – try to find keys containing revenue/margin
  const revKey = display[0]
    ? Object.keys(display[0]).find(key =>
        /revenue|net_sale|net_sales|current_revenue/i.test(key)
      ) ?? null
    : null;

  const marginKey = display[0]
    ? Object.keys(display[0]).find(key =>
        /margin/i.test(key)
      ) ?? null
    : null;

  // If still no data, show a helpful message
  if (!display.length && !loading) {
    return (
      <div>
        <h1 className={styles.pageTitle}>Branch Analytics</h1>
        <p className={styles.pageSub}>Revenue and margin performance by location</p>
        <div className="alert alert-warning">No branch data available. Please check your database and run the analytics views.</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className={styles.pageTitle}>Branch Analytics</h1>
      <p className={styles.pageSub}>Revenue and margin performance by location</p>

      {loading ? <div className={styles.spinner} /> : (
        <>
          <div className={styles.chartGrid}>
            {revKey && (
              <div className={`card ${styles.chartCard}`}>
                <h3 className={styles.chartTitle}>Revenue by Branch</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={display} margin={{ top: 8, right: 8, bottom: 40, left: 8 }}>
                    <XAxis dataKey="branch" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}K`} />
                    <Tooltip formatter={(v: number) => [`KES ${v.toLocaleString()}`, "Revenue"]} />
                    <Bar dataKey={revKey} radius={[4,4,0,0]}>
                      {display.map((_, i) => (
                        <Cell key={i} fill={GREEN_SCALE[i % GREEN_SCALE.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {marginKey && (
              <div className={`card ${styles.chartCard}`}>
                <h3 className={styles.chartTitle}>Margin % by Branch</h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={display} margin={{ top: 8, right: 8, bottom: 40, left: 8 }}>
                    <XAxis dataKey="branch" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                    <Tooltip formatter={(v: number) => [`${v}%`, "Avg Margin"]} />
                    <ReferenceLine y={5} stroke="#D32F2F" strokeDasharray="4 4" label={{ value: "5% Min", fill: "#D32F2F", fontSize: 11 }} />
                    <Bar dataKey={marginKey} radius={[4,4,0,0]}>
                      {display.map((row, i) => {
                        const val = Number(row[marginKey!] ?? 0);
                        return <Cell key={i} fill={val < 5 ? "#D32F2F" : val < 10 ? "#ED6C02" : "#1A6B3C"} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className={`card ${styles.tableCard}`}>
            <h3 className={styles.chartTitle}>Branch Performance Details</h3>
            <DataTable data={display} />
          </div>
        </>
      )}
    </div>
  );
}
