"use client";
import { useApi } from "@/hooks/useApi";
import DataTable from "@/components/DataTable";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import styles from "../shared.module.css";

interface ScorecardRow {
  branch: string;
  composite_score: number;
  rank: number;
  total_revenue: number;
  avg_margin: number;
}

function scoreColor(score: number) {
  if (score >= 70) return "#1A6B3C";
  if (score >= 45) return "#ED6C02";
  return "#D32F2F";
}

export default function ScorecardPage() {
  const { data: scorecard, loading } = useApi<ScorecardRow[]>("/scorecard");

  const top = scorecard?.[0];

  return (
    <div>
      <h1 className={styles.pageTitle}>Branch Scorecard</h1>
      <p className={styles.pageSub}>Composite performance ranking across revenue, margin, variety, and stockout</p>

      {loading ? <div className={styles.spinner} /> : (
        <>
          {top && (
            <div className={`${styles.alertBox} ${styles.alertOk}`} style={{ marginBottom: "1rem" }}>
              🏆 Top Performer: <strong>{top.branch}</strong> — Composite Score {top.composite_score}
            </div>
          )}

          <div className={`card ${styles.chartCard}`} style={{ marginBottom: "1rem" }}>
            <h3 className={styles.chartTitle}>Composite Performance Score (0–100)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scorecard ?? []} margin={{ top: 8, right: 8, bottom: 40, left: 8 }}>
                <XAxis dataKey="branch" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number) => [`${v}`, "Score"]} />
                <Bar dataKey="composite_score" radius={[4,4,0,0]} label={{ position: "top", fontSize: 10 }}>
                  {(scorecard ?? []).map((row, i) => (
                    <Cell key={i} fill={scoreColor(row.composite_score)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className={`card ${styles.tableCard}`}>
            <h3 className={styles.chartTitle}>Full Rankings</h3>
            <DataTable data={(scorecard ?? []) as unknown as Record<string,unknown>[]} />
          </div>
        </>
      )}
    </div>
  );
}
