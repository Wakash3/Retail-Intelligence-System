"use client";

import { useEffect, useState } from "react";
import StatsCards from "@/components/StatsCards";
import BranchCharts from "@/components/BranchCharts";
import GladwellChat from "@/components/GladwellChat";
import { fetchWithAuth } from "@/lib/api";
import { Sparkles, RefreshCw, LogIn } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Basic Auth Check
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      router.push("/login");
      return;
    }
    
    setToken(storedToken);
    loadData(storedToken);
  }, [router]);

  const loadData = async (tk: string) => {
    setIsLoading(true);
    try {
      // Fetch summary (Essential)
      let summary = null;
      try {
        summary = await fetchWithAuth("/summary", tk);
      } catch (e) {
        console.error("Summary fetch failed:", e);
      }

      // Fetch branches (Analytical)
      let branches = [];
      try {
        const branchRes = await fetchWithAuth("/branches", tk);
        branches = Array.isArray(branchRes) ? branchRes : [];
      } catch (e) {
        console.error("Branches fetch failed:", e);
      }
      
      let finalBranches = branches;
      if (finalBranches.length === 0) {
        // Fallback: Use scorecard data if branches is empty
        try {
          const scorecard = await fetchWithAuth("/scorecard", tk);
          if (scorecard && Array.isArray(scorecard)) {
            finalBranches = scorecard.map((s: any) => ({
              branch: s.branch,
              total_revenue: s.total_revenue
            }));
          }
        } catch (e) {
          console.error("Scorecard fallback failed:", e);
        }
      }
      
      setData({ summary, branches: finalBranches });
    } catch (e) {
      console.error("Dashboard load crash:", e);
      // If error occurs (like 401), force re-login
      if (e instanceof Error && e.message.includes("401")) {
          localStorage.removeItem("token");
          router.push("/login");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="flex flex-col items-center space-y-4">
            <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="font-bold text-orange-600 uppercase tracking-widest text-[10px]">Verifying Intelligence Session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto pb-24">
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        <header className="mb-12 flex items-center justify-between">
          <div>
            <h2 className="text-4xl font-extrabold text-foreground tracking-tight text-balance">Enterprise Overview</h2>
            <p className="text-muted-foreground font-bold mt-2 uppercase tracking-[0.2em] text-[11px]">Real-time Strategic Insights & Branch Distribution</p>
          </div>
          <button 
            onClick={() => loadData(token)}
            className="p-4 bg-card border border-border rounded-2xl shadow-sm hover:shadow-md transition-all text-muted-foreground hover:text-orange-600 group"
          >
            <RefreshCw className={cn("w-6 h-6 transition-transform group-hover:rotate-180 duration-500", isLoading && "animate-spin")} />
          </button>
        </header>

        <StatsCards summary={data?.summary || null} />

        <div className="mt-12 grid grid-cols-1 gap-12">
          <BranchCharts data={data?.branches || []} />
        </div>

        <GladwellChat summary={data?.summary || null} />

        <footer className="mt-20 border-t border-border pt-10 text-center">
          <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest leading-loose">Msingi Retail Intelligence • Advanced Series • 2026 Edition</p>
        </footer>
      </div>
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}
