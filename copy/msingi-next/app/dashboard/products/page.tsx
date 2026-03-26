"use client";
import { useApi } from "@/hooks/useApi";
import DataTable from "@/components/DataTable";
import styles from "../shared.module.css";

export default function ProductsPage() {
  const { data: top, loading: l1 }   = useApi<Record<string,unknown>[]>("/products/top?limit=20");
  const { data: low, loading: l2 }   = useApi<Record<string,unknown>[]>("/products/low-margin");
  const { data: high, loading: l3 }  = useApi<Record<string,unknown>[]>("/products/high-value");
  const loading = l1 || l2 || l3;

  return (
    <div>
      <h1 className={styles.pageTitle}>Products</h1>
      <p className={styles.pageSub}>SKU-level performance across all branches</p>

      {loading ? <div className={styles.spinner} /> : (
        <>
          <div className={styles.twoCol}>
            <div className={`card ${styles.section}`}>
              <h3 className={styles.sectionTitle}>Top 20 Products by Revenue</h3>
              <DataTable data={top ?? []} />
            </div>
            <div className={`card ${styles.section}`}>
              <h3 className={styles.sectionTitle}>Low Margin Products</h3>
              <DataTable data={low ?? []} />
              {(low?.length ?? 0) === 0 && (
                <p className={`${styles.alertBox} ${styles.alertOk}`}>✓ No low margin products detected</p>
              )}
            </div>
          </div>

          <div className={`card ${styles.tableCard}`}>
            <h3 className={styles.chartTitle}>High Value Products</h3>
            <DataTable data={high ?? []} />
          </div>
        </>
      )}
    </div>
  );
}
