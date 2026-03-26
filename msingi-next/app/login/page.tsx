"use client";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import styles from "./login.module.css";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError("Please enter email and password"); return; }
    setLoading(true);
    setError("");
    const ok = await login(email, password);
    if (ok) {
      router.push("/dashboard");
    } else {
      setError("Invalid credentials. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className={styles.page}>
      <div className={styles.bg} aria-hidden />
      <div className={styles.card}>
        <div className={styles.logo}>
          <span className={styles.logoMark}>✦</span>
        </div>
        <h1 className={styles.title}>Msingi Retail</h1>
        <p className={styles.subtitle}>Intelligence Platform</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label}>Email</label>
            <input
              className={styles.input}
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Password</label>
            <input
              className={styles.input}
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {error && <p className={styles.error}>{error}</p>}
          <button className={styles.btn} type="submit" disabled={loading}>
            {loading ? <span className={styles.spinner} /> : "Sign In"}
          </button>
        </form>
        <p className={styles.footer}>No account? Contact your administrator</p>
      </div>
    </div>
  );
}
