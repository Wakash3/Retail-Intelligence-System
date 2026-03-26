import { useState, useEffect, useCallback } from "react";
import { fetchWithAuth } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export function useApi<T>(endpoint: string | null) {
  const { token } = useAuth();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(() => {
    if (!endpoint || !token) return;
    setLoading(true);
    fetchWithAuth(endpoint, token)
      .then((res) => { setData(res); setError(null); })
      .catch(() => setError("Failed to fetch"))
      .finally(() => setLoading(false));
  }, [endpoint, token]);

  useEffect(() => { refetch(); }, [refetch]);

  return { data, loading, error, refetch };
}
