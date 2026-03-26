"use client";
import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { useAuth } from "@/context/AuthContext";
import { fetchWithAuth } from "@/lib/api";
import DataTable from "@/components/DataTable";
import MetricCard from "@/components/MetricCard";
import styles from "../shared.module.css";
import pageStyles from "./page.module.css";

interface Scorecard { branch: string; }
interface RecommendationResult {
  branch: string;
  benchmark_branch: string;
  recommendations: Record<string,unknown>[];
}

export default function RecommendationsPage() {
  const { token } = useAuth();
  const { data: scorecard } = useApi<Scorecard[]>("/scorecard");
  const [branch, setBranch]   = useState("");
  const [limit, setLimit]     = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<RecommendationResult | null>(null);
  const [error, setError]     = useState("");

  const branches = scorecard?.map(s => s.branch).filter(Boolean) ?? [];

  const getRecommendations = async () => {
    if (!branch || !token) return;
    setLoading(true);
    setError("");
    const res = await fetchWithAuth(`/recommendations/${encodeURIComponent(branch)}?limit=${limit}`, token);
    if (res) setResult(res);
    else setError("No recommendations found.");
    setLoading(false);
  };

  return (
    <div>
      <h1 className={styles.pageTitle}>Recommendations</h1>
      <p className={styles.pageSub}>Cross-branch product recommendations powered by performance benchmarking</p>

      <div className={`card ${styles.section}`} style={{ marginBottom: "1rem" }}>
        <h3 className={styles.sectionTitle}>Product Recommendation Engine</h3>
        <p style={{ fontSize: "0.875rem", color: "var(--muted)", marginBottom: "1.25rem" }}>
          Select a branch to see which products are selling well in the top-performing branch but missing from yours.
        </p>

        <div className={pageStyles.controls}>
          <div className={pageStyles.field}>
            <label className={pageStyles.label}>Select Branch</label>
            <select
              className={pageStyles.select}
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
            >
              <option value="">— Choose branch —</option>
              {branches.sort().map(b => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </div>

          <div className={pageStyles.field}>
            <label className={pageStyles.label}>Recommendations: {limit}</label>
            <input
              type="range" min={1} max={20} value={limit}
              className={pageStyles.range}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
          </div>

          <button className={styles.btn} onClick={getRecommendations} disabled={!branch || loading}>
            {loading ? "Analysing…" : "Get Recommendations"}
          </button>
        </div>
      </div>

      {error && <p className={`${styles.alertBox} ${styles.alertFail}`}>✕ {error}</p>}

      {result && (
        <>
          <div className={pageStyles.metaGrid}>
            <MetricCard label="Recommendations" value={result.recommendations.length} accent="green" />
            <MetricCard
              label="Potential Revenue"
              value={`KES ${result.recommendations
                .reduce((s, r) => s + Number(r.revenue_at_benchmark ?? 0), 0)
                .toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              accent="amber"
            />
            <MetricCard label="Benchmark Branch" value={result.benchmark_branch} accent="green" />
          </div>

          <div className={`card ${styles.tableCard}`}>
            <h3 className={styles.chartTitle}>
              Recommended Products for <strong>{result.branch}</strong>
            </h3>
            <DataTable data={result.recommendations} />
          </div>
        </>
      )}
    </div>
  );
}
