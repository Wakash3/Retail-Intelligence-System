"use client";
import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { useAuth } from "@/context/AuthContext";
import { fetchWithAuth } from "@/lib/api";
import DataTable from "@/components/DataTable";
import styles from "../shared.module.css";
import ModeToggle from "@/components/ui/ModeToggle";

export default function AlertsPage() {
  const { token } = useAuth();
  const { data: anomalies, loading: l1 } = useApi<Record<string,unknown>[]>("/anomalies/critical");
  const { data: stockout, loading: l2 }  = useApi<Record<string,unknown>[]>("/stockout/critical");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  

  const runAlerts = async () => {
    if (!token) return;
    setRunning(true);
    setResult(null);
    const res = await fetchWithAuth("/alerts/run", token);
    setResult(res ? "Alert checks completed successfully." : "Failed to run alerts.");
    setRunning(false);
  };

  const loading = l1 || l2;

  return (
    <div>
      <h1 className={styles.pageTitle}>Alerts</h1>
      <p className={styles.pageSub}>Critical anomalies and stockout risks</p>

      {loading ? <div className={styles.spinner} /> : (
        <>
          <div className={styles.twoCol}>
            <div className={`card ${styles.section}`}>
              <h3 className={styles.sectionTitle}>Critical Anomalies</h3>
              <DataTable data={anomalies ?? []} />
              {(anomalies?.length ?? 0) > 0 ? (
                <p className={`${styles.alertBox} ${styles.alertWarn}`}>
                  ⚠ {anomalies!.length} critical anomalies detected
                </p>
              ) : (
                <p className={`${styles.alertBox} ${styles.alertOk}`}>✓ No critical anomalies</p>
              )}
            </div>

            <div className={`card ${styles.section}`}>
              <h3 className={styles.sectionTitle}>Stockout Risks</h3>
              <DataTable data={stockout ?? []} />
              {(stockout?.length ?? 0) > 0 ? (
                <p className={`${styles.alertBox} ${styles.alertWarn}`}>
                  ⚠ {stockout!.length} products at stockout risk
                </p>
              ) : (
                <p className={`${styles.alertBox} ${styles.alertOk}`}>✓ No stockout risks detected</p>
              )}
            </div>
          </div>

          <div className={`card ${styles.section}`}>
            <h3 className={styles.sectionTitle}>Manual Alert Trigger</h3>
            <p style={{ fontSize: "0.875rem", color: "var(--muted)", marginBottom: "1rem" }}>
              Run all alert checks immediately — margin, stockout, and revenue targets.
            </p>
            <button className={styles.btn} onClick={runAlerts} disabled={running}>
              {running ? "Running…" : "Run Alert Checks Now"}
            </button>
            {result && (
              <p className={`${styles.alertBox} ${result.includes("Failed") ? styles.alertFail : styles.alertOk}`} style={{ marginTop: "1rem" }}>
                {result.includes("Failed") ? "✕" : "✓"} {result}
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
