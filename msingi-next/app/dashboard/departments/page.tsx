"use client";
import { useApi } from "@/hooks/useApi";
import DataTable from "@/components/DataTable";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import styles from "../shared.module.css";

const GREEN_SCALE = ["#1A6B3C","#2E7D32","#388E3C","#43A047","#4CAF50","#66BB6A","#81C784","#A5D6A7"];

export default function DepartmentsPage() {
  const { data: departments, loading, error } = useApi<Record<string, unknown>[]>("/departments");

  // Debug: log data
  console.log("Departments data:", departments);
  console.log("Loading:", loading);
  console.log("Error:", error);

  // Flexible column detection
  const revKey = departments?.[0]
    ? Object.keys(departments[0]).find(key =>
        /revenue|net_sale|net_sales|current_revenue/i.test(key)
      ) ?? null
    : null;

  const marginKey = departments?.[0]
    ? Object.keys(departments[0]).find(key =>
        /margin/i.test(key)
      ) ?? null
    : null;

  console.log("revKey:", revKey);
  console.log("marginKey:", marginKey);

  const sorted = (departments ?? []).slice().sort((a, b) => {
    const aRev = revKey ? (a[revKey] as number) || 0 : 0;
    const bRev = revKey ? (b[revKey] as number) || 0 : 0;
    return bRev - aRev;
  });

  console.log("Sorted length:", sorted.length);
  if (sorted.length > 0) {
    console.log("First item:", sorted[0]);
  }

  return (
    <div>
      <h1 className={styles.pageTitle}>Departments</h1>
      <p className={styles.pageSub}>Revenue, margin, and product variety by department</p>

      {loading ? (
        <div className={styles.spinner} />
      ) : error ? (
        <div className={`${styles.alertBox} ${styles.alertFail}`}>
          Error loading departments: {error.message}
        </div>
      ) : (
        <>
          {/* Summary badges */}
          <div className={styles.metaRow}>
            <div className={styles.metaBadge}>
              <strong>{sorted.length}</strong>
              Departments
            </div>
            <div className={styles.metaBadge}>
              <strong>
                KES {sorted
                  .reduce((s, d) => s + (revKey ? (d[revKey] as number) || 0 : 0), 0)
                  .toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </strong>
              Total Revenue
            </div>
            <div className={styles.metaBadge}>
              <strong>
                {sorted
                  .reduce((s, d) => s + ((d.unique_products as number) || (d.total_products as number) || 0), 0)
                  .toLocaleString()}
              </strong>
              Total SKUs
            </div>
          </div>

          <div className={styles.chartGrid}>
            {/* Revenue by Department */}
            <div className={`card ${styles.chartCard}`}>
              <h3 className={styles.chartTitle}>Revenue by Department</h3>
              <div style={{ overflowX: "auto", width: "100%" }}>
                <div style={{ minWidth: "800px" }}>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={sorted} margin={{ top: 8, right: 8, bottom: 48, left: 8 }}>
                      <XAxis dataKey="department" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
                      <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
                      <Tooltip formatter={(v: number) => [`KES ${v.toLocaleString()}`, "Revenue"]} />
                      <Bar dataKey={revKey ?? "total_revenue"} radius={[4,4,0,0]}>
                        {sorted.map((_, i) => (
                          <Cell key={i} fill={GREEN_SCALE[i % GREEN_SCALE.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Margin % by Department */}
            <div className={`card ${styles.chartCard}`}>
              <h3 className={styles.chartTitle}>Avg Margin % by Department</h3>
              <div style={{ overflowX: "auto", width: "100%" }}>
                <div style={{ minWidth: "800px" }}>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={sorted} margin={{ top: 8, right: 8, bottom: 48, left: 8 }}>
                      <XAxis dataKey="department" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" interval={0} />
                      <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                      <Tooltip formatter={(v: number) => [`${v}%`, "Avg Margin"]} />
                      <Bar dataKey={marginKey ?? "avg_margin"} radius={[4,4,0,0]}>
                        {sorted.map((row, i) => {
                          const val = marginKey ? (row[marginKey] as number) || 0 : 0;
                          return (
                            <Cell
                              key={i}
                              fill={val < 5 ? "#D32F2F" : val < 10 ? "#ED6C02" : "#1A6B3C"}
                            />
                          );
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>

          {/* Full table */}
          <div className={`card ${styles.tableCard}`}>
            <h3 className={styles.chartTitle}>Department Performance Details</h3>
            <div style={{ overflowX: "auto", maxHeight: "400px", overflowY: "auto" }}>
              <div style={{ minWidth: "800px" }}>
                <DataTable data={sorted as Record<string, unknown>[]} />
              </div>
            </div>
          </div>
        </>
      )}

      {!loading && sorted.length === 0 && (
        <div className={`${styles.alertBox} ${styles.alertWarn}`} style={{ marginTop: "1rem" }}>
          ⚠ No department data available. Ensure the view <code>vw_department_performance</code> exists and contains data.
        </div>
      )}
    </div>
  );
}
