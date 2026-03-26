import styles from "./MetricCard.module.css";

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "green" | "amber" | "red";
  delay?: number;
}

export default function MetricCard({ label, value, sub, accent = "green", delay = 0 }: MetricCardProps) {
  return (
    <div
      className={`${styles.card} ${styles[accent]}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>{value}</span>
      {sub && <span className={styles.sub}>{sub}</span>}
    </div>
  );
}
