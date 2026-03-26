"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import styles from "./Sidebar.module.css";

const NAV = [
  { href: "/dashboard",    label: "Overview",        icon: "◈" },
  { href: "/dashboard/branches",    label: "Branch Analytics", icon: "⬡" },
  { href: "/dashboard/products",    label: "Products",         icon: "▤" },
  { href: "/dashboard/alerts",      label: "Alerts",           icon: "◉" },
  { href: "/dashboard/recommendations", label: "Recommendations", icon: "✦" },
  { href: "/dashboard/scorecard",   label: "Scorecard",        icon: "◎" },
  { href: "/dashboard/data-quality", label: "Data Quality",    icon: "◫" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.brandIcon}>✦</span>
        <div>
          <span className={styles.brandName}>Msingi</span>
          <span className={styles.brandSub}>Retail Intelligence</span>
        </div>
      </div>

      <nav className={styles.nav}>
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`${styles.navItem} ${active ? styles.active : ""}`}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              <span className={styles.navLabel}>{item.label}</span>
              {active && <span className={styles.activePip} />}
            </Link>
          );
        })}
      </nav>

      <div className={styles.bottom}>
        <div className={styles.userInfo}>
          <div className={styles.avatar}>
            {user?.email?.[0]?.toUpperCase() ?? "U"}
          </div>
          <div className={styles.userDetails}>
            <span className={styles.userEmail}>{user?.email}</span>
            <span className={styles.userRole}>{user?.role ?? "viewer"}</span>
          </div>
        </div>
        <button className={styles.logoutBtn} onClick={logout}>
          ⏻ Logout
        </button>
      </div>
    </aside>
  );
}
