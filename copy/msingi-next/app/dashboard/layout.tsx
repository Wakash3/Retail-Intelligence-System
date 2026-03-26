"use client";
import { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import NuruChat from "@/components/NuruChat";
import styles from "./layout.module.css";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !token) router.push("/login");
  }, [token, isLoading, router]);

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <span className={styles.spinner} />
      </div>
    );
  }

  if (!token) return null;

  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>{children}</main>
      <NuruChat />
    </div>
  );
}
