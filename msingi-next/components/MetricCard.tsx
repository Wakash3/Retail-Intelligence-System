"use client";
import React from "react";
import styles from "./MetricCard.module.css";

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;               // new: optional icon
  accent?: "green" | "amber" | "red";
  delay?: number;
}

export default function MetricCard({
  label,
  value,
  sub,
  icon,
  accent = "green",
  delay = 0,
}: MetricCardProps) {
  const accentClass = styles[accent] || styles.green;

  return (
    <div
      className={`${styles.card} ${accentClass}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={styles.header}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.value}>{value}</div>
      {sub && <div className={styles.sub}>{sub}</div>}
    </div>
  );
}
