"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchWithAuth, postWithAuth } from "@/lib/api";
import { 
  Lightbulb, 
  ArrowRight, 
  Target, 
  Search, 
  Sparkles, 
  TrendingUp, 
  DollarSign, 
  RefreshCw,
  AlertCircle,
  ChevronRight
} from "lucide-react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

const STRATEGIES = [
  { id: "assortment", label: "Assortment Gap", icon: Lightbulb, color: "emerald" },
  { id: "price", label: "Price Logic", icon: DollarSign, color: "indigo" },
  { id: "rotation", label: "Stock Rotation", icon: RefreshCw, color: "orange" }
];

export default function RecommendationsPage() {
  const [data, setData] = useState<any>(null);
  const [branches, setBranches] = useState<string[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [activeTab, setActiveTab] = useState("assortment");
  const [aiInsights, setAiInsights] = useState<Record<string, string>>({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  
  const router = useRouter();

  // Load branch list and initial data
  useEffect(() => {
    const tk = localStorage.getItem("token");
    if (!tk) {
      router.push("/login");
      return;
    }

    fetchWithAuth("/branches/list", tk).then(list => {
      setBranches(list || []);
      // Default to first branch if none selected
      if (list && list.length > 0 && !selectedBranch) {
        setSelectedBranch(list[0]);
        loadRecommendations(list[0]);
      }
    });
  }, [router]);

  const loadRecommendations = useCallback(async (branch: string) => {
    const tk = localStorage.getItem("token");
    if (!tk) return;

    // Check Cache
    const cacheKey = `recomm_${branch}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      setData(JSON.parse(cached));
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetchWithAuth(`/recommendations/${branch}/smart`, tk);
      if (res) {
        setData(res);
        localStorage.setItem(cacheKey, JSON.stringify(res));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleBranchChange = (branch: string) => {
    setSelectedBranch(branch);
    loadRecommendations(branch);
    setAiInsights({}); // Clear AI insights when switching branch
    setIsDropdownOpen(false);
  };

  const askGladwell = async () => {
    const tk = localStorage.getItem("token");
    if (!tk || !data || isAnalyzing) return;

    const currentData = data[activeTab];
    if (!currentData || currentData.length === 0) return;

    setIsAnalyzing(true);
    try {
      const insightData = await postWithAuth("/recommendations/analyze", {
        branch: selectedBranch,
        strategy: activeTab,
        data: currentData
      }, tk);

      if (insightData) {
        setAiInsights(prev => ({ ...prev, [activeTab]: insightData.insight }));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const currentList = data ? data[activeTab] : [];
  const filteredBranches = branches.filter(b => b.toLowerCase().includes(selectedBranch.toLowerCase()));

  return (
    <div className="max-w-[1400px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-4xl font-extrabold text-foreground tracking-tight text-white">AI Recommendations</h2>
          <p className="text-muted-foreground font-bold mt-2 uppercase tracking-[0.2em] text-[11px]">Gladwell Strategy & Smart Benchmarking</p>
        </div>

        {/* Searchable Branch Selector */}
        <div className="relative z-50">
           <div className="flex items-center gap-3 px-6 py-4 bg-zinc-900 border border-white/5 rounded-2xl shadow-xl focus-within:border-emerald-500 transition-all min-w-[320px]">
              <Search className="w-4 h-4 text-zinc-500" />
              <input 
                type="text"
                placeholder="Search branch..."
                value={selectedBranch}
                onChange={(e) => {
                  setSelectedBranch(e.target.value);
                  setIsDropdownOpen(true);
                }}
                onFocus={() => setIsDropdownOpen(true)}
                className="bg-transparent border-none outline-none font-bold text-sm text-white placeholder:text-zinc-600 w-full"
              />
              <ChevronRight className={cn("w-4 h-4 text-zinc-500 transition-transform", isDropdownOpen ? "-rotate-90" : "rotate-90")} />
           </div>

           {/* Dropdown List */}
           <AnimatePresence>
              {isDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-[-1]" onClick={() => setIsDropdownOpen(false)} />
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl max-h-[300px] overflow-y-auto z-[60] p-2"
                  >
                    {filteredBranches.length > 0 ? (
                      filteredBranches.map(b => (
                        <button
                          key={b}
                          onClick={() => handleBranchChange(b)}
                          className="w-full text-left px-4 py-3 hover:bg-emerald-600/10 hover:text-emerald-500 rounded-xl text-sm font-bold text-zinc-400 transition-all"
                        >
                          {b}
                        </button>
                      ))
                    ) : (
                      <div className="px-4 py-3 text-sm text-zinc-600 italic">No branches found</div>
                    )}
                  </motion.div>
                </>
              )}
           </AnimatePresence>
        </div>
      </header>

      {/* Strategy Tabs */}
      <div className="flex gap-4 mb-10 overflow-x-auto pb-2 scrollbar-hide">
         {STRATEGIES.map((s) => (
           <button
             key={s.id}
             onClick={() => setActiveTab(s.id)}
             className={cn(
               "px-8 py-4 rounded-2xl font-bold text-sm transition-all flex items-center gap-3 shrink-0 border",
               activeTab === s.id 
                 ? "bg-emerald-600 text-white border-emerald-500 shadow-lg shadow-emerald-500/20" 
                 : "bg-card text-muted-foreground border-border hover:border-emerald-500/50"
             )}
           >
             <s.icon className="w-4 h-4" />
             {s.label}
           </button>
         ))}
      </div>

      <div className="space-y-8">
        {/* Benchmark Context Bar */}
        {data && (
           <div className="bg-zinc-900 border border-white/5 p-8 rounded-[32px] text-white overflow-hidden relative">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
                 <div className="flex items-center gap-6">
                    <div className="w-16 h-16 bg-emerald-600/20 rounded-2xl flex items-center justify-center text-emerald-500">
                       <Target className="w-8 h-8" />
                    </div>
                    <div>
                        <h3 className="text-2xl font-black">{selectedBranch} Strategy</h3>
                        <p className="text-zinc-500 font-bold text-[11px] uppercase tracking-widest mt-1">Benchmarked against system leader: <span className="text-emerald-500">{data.benchmark_branch}</span></p>
                    </div>
                 </div>

                 {/* Ask Gladwell Button */}
                 <button 
                  onClick={askGladwell}
                  disabled={isAnalyzing || !currentList?.length}
                  className={cn(
                    "flex items-center gap-3 px-8 py-4 rounded-xl font-black text-xs uppercase tracking-widest transition-all",
                    aiInsights[activeTab] 
                      ? "bg-emerald-600 text-white" 
                      : "bg-white text-black hover:scale-105"
                  )}
                 >
                    {isAnalyzing ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4" />
                    )}
                    {aiInsights[activeTab] ? "Update Strategy" : "Ask Gladwell"}
                 </button>
              </div>

              {/* AI Narrative Section */}
              <AnimatePresence>
                {aiInsights[activeTab] && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="mt-8 pt-8 border-t border-white/10"
                  >
                     <div className="text-base font-medium text-emerald-400 dark:text-emerald-300 leading-relaxed whitespace-pre-wrap bg-emerald-500/5 p-6 rounded-2xl border border-emerald-500/10">
                       {aiInsights[activeTab]}
                     </div>
                  </motion.div>
                )}
              </AnimatePresence>
           </div>
        )}

        {/* Results List */}
        {isLoading ? (
          <div className="p-20 text-center animate-pulse space-y-4">
             <RefreshCw className="w-10 h-10 text-emerald-600 mx-auto animate-spin" />
             <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Generating Real-time Models...</p>
          </div>
        ) : currentList?.length > 0 ? (
          <div className="grid grid-cols-1 gap-6">
            {currentList.map((r: any, i: number) => (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-card p-8 rounded-[32px] border border-border shadow-sm flex flex-col md:flex-row md:items-center justify-between hover:border-emerald-500/30 transition-all group"
              >
                <div className="flex items-center gap-6">
                  <div className="w-14 h-14 bg-emerald-50 dark:bg-emerald-600/10 rounded-2xl flex items-center justify-center text-emerald-600">
                    {activeTab === 'assortment' ? <Lightbulb className="w-6 h-6" /> : 
                     activeTab === 'price' ? <DollarSign className="w-6 h-6" /> : <RefreshCw className="w-6 h-6" />}
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-1">
                      {activeTab === 'assortment' ? "New SKU Recommendation" : 
                       activeTab === 'price' ? "Margin Correction" : "Inventory Rotation Target"}
                    </p>
                    <h4 className="text-lg font-extrabold text-foreground">{r.product_name}</h4>
                  </div>
                </div>
                
                <div className="flex items-center gap-12 mt-6 md:mt-0">
                  <div className="text-right">
                    <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-1">Performance Signal</p>
                    <p className="text-xl font-black text-foreground">
                      {activeTab === 'price' ? `${(r.avg_margin || 0).toFixed(1)}% → ${(r.system_avg || 0).toFixed(1)}%` : 
                       `KES ${(r.total_revenue || 0).toLocaleString()}`}
                    </p>
                  </div>
                  <div className="p-4 bg-emerald-50 dark:bg-zinc-800 rounded-2xl group-hover:bg-emerald-600 group-hover:text-white transition-all">
                    <ArrowRight className="w-5 h-5" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="p-20 text-center border-2 border-dashed border-border rounded-[40px] space-y-4">
             <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto" />
             <p className="text-muted-foreground font-bold">No critical insights detected for this branch segment.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Helper for cn (same as in Sidebar/other components)
function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}
