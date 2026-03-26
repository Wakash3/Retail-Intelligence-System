"use client";
import { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";

export default function RootPage() {
  const { token, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      router.replace(token ? "/dashboard" : "/login");
    }
  }, [token, isLoading, router]);

  return null;
}
