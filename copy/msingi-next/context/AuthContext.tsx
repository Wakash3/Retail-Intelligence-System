"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { loginUser } from "@/lib/api";
import { useRouter } from "next/navigation";

interface User {
  email: string;
  role?: string;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

function parseJwt(token: string) {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const stored = sessionStorage.getItem("msingi_token");
    const storedEmail = sessionStorage.getItem("msingi_email");
    if (stored) {
      const payload = parseJwt(stored);
      if (payload && payload.exp * 1000 > Date.now()) {
        setToken(stored);
        setUser({ email: storedEmail || payload.sub || "", role: payload.role });
      } else {
        sessionStorage.removeItem("msingi_token");
        sessionStorage.removeItem("msingi_email");
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    const t = await loginUser(email, password);
    if (t) {
      const payload = parseJwt(t);
      setToken(t);
      setUser({ email, role: payload?.role });
      sessionStorage.setItem("msingi_token", t);
      sessionStorage.setItem("msingi_email", email);
      return true;
    }
    return false;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    sessionStorage.removeItem("msingi_token");
    sessionStorage.removeItem("msingi_email");
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
};
