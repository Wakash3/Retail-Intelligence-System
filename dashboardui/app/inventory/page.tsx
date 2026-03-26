"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { fetchWithAuth } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Package, 
  TrendingDown, 
  AlertTriangle, 
  Search, 
  ChevronRight, 
  Filter,
  BarChart3,
  DollarSign
} from "lucide-react";
import { useRouter } from "next/navigation";

const INVENTORY_TABS = [
  { id: "top", label: "Top Sellers", icon: BarChart3 },
  { id: "low-margin", label: "Low Margin", icon: TrendingDown },
  { id: "high-value", label: "High Value", icon: DollarSign },
  { id: "stockout", label: "Stockout Risk", icon: AlertTriangle },
];

export default function InventoryPage() {
  const [data, setData] = useState<Record<string, any[]>>({
    top: [],
    "low-margin": [],
    "high-value": [],
    stockout: []
  });
  const [branches, setBranches] = useState<string[]>([]);
  const [selectedBranch, setSelectedBranch] = useState<string>("System Wide");
  const [activeTab, setActiveTab] = useState("top");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  const router = useRouter();

  const loadInventoryData = useCallback(async (branch: string) => {
    const tk = localStorage.getItem("token");
    if (!tk) return;

    // Cache key
    const cacheKey = `inv_${branch}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      setData(JSON.parse(cached));
      return;
    }

    setIsLoading(true);
    try {
      const bParam = branch === "System Wide" ? "" : `?branch=${encodeURIComponent(branch)}`;
      
      const [top, low, high, stockout] = await Promise.all([
        fetchWithAuth(`/products/top${bParam}`, tk),
        fetchWithAuth(`/products/low-margin${bParam}`, tk),
        fetchWithAuth(`/products/high-value${bParam}`, tk),
        fetchWithAuth(`/stockout/critical${bParam}`, tk)
      ]);

      const newData = {
        top: top || [],
        "low-margin": low || [],
        "high-value": high || [],
        stockout: stockout || []
      };

      setData(newData);
      localStorage.setItem(cacheKey, JSON.stringify(newData));
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load branch list
  useEffect(() => {
    const tk = localStorage.getItem("token");
    if (!tk) {
      router.push("/login");
      return;
    }

    fetchWithAuth("/branches/list", tk).then(list => {
      setBranches(list || []);
      loadInventoryData("System Wide");
    });
  }, [router, loadInventoryData]);

  const handleBranchChange = (branch: string) => {
    setSelectedBranch(branch);
    loadInventoryData(branch);
    setIsDropdownOpen(false);
  };

  const currentList = data[activeTab] || [];
  
  const filteredList = useMemo(() => {
    if (!searchTerm) return currentList;
    return currentList.filter(p => 
      p.product_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.sku_code?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [currentList, searchTerm]);

  const filteredBranches = branches.filter(b => b.toLowerCase().includes(selectedBranch === "System Wide" ? "" : selectedBranch.toLowerCase()));

  // Stats for Cards
  const stats = useMemo(() => ({
    totalSkus: (data["top"] || []).length,
    alerts: (data["low-margin"] || []).length,
    stockouts: (data["stockout"] || []).length
  }), [data]);

  return (
    <div className="max-w-[1400px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-4xl font-extrabold text-white tracking-tight">Inventory Systems</h2>
          <p className="text-orange-600 font-bold mt-2 uppercase tracking-[0.2em] text-[11px]">Comprehensive Stock & Margin Analysis</p>
        </div>

        {/* Searchable Branch Selector */}
        <div className="relative z-50">
           <div className="flex items-center gap-3 px-6 py-4 bg-zinc-900 border border-white/5 rounded-2xl shadow-xl focus-within:border-orange-500 transition-all min-w-[320px]">
              <Filter className="w-4 h-4 text-zinc-500" />
              <input 
                type="text"
                placeholder="Select Branch..."
                value={selectedBranch === "System Wide" && !isDropdownOpen ? "🌍 System Wide" : (selectedBranch === "System Wide" ? "" : selectedBranch)}
                onChange={(e) => {
                  setSelectedBranch(e.target.value);
                  setIsDropdownOpen(true);
                }}
                onFocus={() => {
                  if (selectedBranch === "System Wide") setSelectedBranch("");
                  setIsDropdownOpen(true);
                }}
                className="bg-transparent border-none outline-none font-bold text-sm text-white placeholder:text-zinc-600 w-full"
              />
              <ChevronRight className={cn("w-4 h-4 text-zinc-500 transition-transform", isDropdownOpen ? "-rotate-90" : "rotate-90")} />
           </div>

           <AnimatePresence>
              {isDropdownOpen && (
                <>
                  <div className="fixed inset-0 z-[-1]" onClick={() => {
                    if (!selectedBranch) setSelectedBranch("System Wide");
                    setIsDropdownOpen(false);
                  }} />
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="absolute top-full left-0 right-0 mt-2 bg-zinc-900 border border-white/10 rounded-2xl shadow-2xl max-h-[300px] overflow-y-auto z-[60] p-2"
                  >
                    <button
                      onClick={() => handleBranchChange("System Wide")}
                      className="w-full text-left px-4 py-3 hover:bg-orange-600/10 hover:text-orange-500 rounded-xl text-sm font-bold text-zinc-400 transition-all flex items-center gap-2"
                    >
                      🌍 System Wide
                    </button>
                    {filteredBranches.map(b => (
                      <button
                        key={b}
                        onClick={() => handleBranchChange(b)}
                        className="w-full text-left px-4 py-3 hover:bg-orange-600/10 hover:text-orange-500 rounded-xl text-sm font-bold text-zinc-400 transition-all"
                      >
                        {b}
                      </button>
                    ))}
                  </motion.div>
                </>
              )}
           </AnimatePresence>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
         {[
           { label: "Tracked SKUs", value: stats.totalSkus, icon: Package, color: "text-blue-500", bg: "bg-blue-500/10" },
           { label: "Margin Alerts", value: stats.alerts, icon: TrendingDown, color: "text-red-500", bg: "bg-red-500/10" },
           { label: "Stockout Risks", value: stats.stockouts, icon: AlertTriangle, color: "text-orange-500", bg: "bg-orange-500/10" },
         ].map((card, i) => (
           <div key={i} className="bg-card p-8 rounded-[32px] border border-border flex items-center justify-between">
              <div>
                 <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-1">{card.label}</p>
                 <h4 className="text-3xl font-black text-foreground">{card.value}</h4>
              </div>
              <div className={cn("w-14 h-14 rounded-2xl flex items-center justify-center", card.bg, card.color)}>
                 <card.icon className="w-6 h-6" />
              </div>
           </div>
         ))}
      </div>

      {/* Tabs & Search */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
         <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {INVENTORY_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-widest transition-all flex items-center gap-2 border",
                  activeTab === tab.id 
                    ? "bg-orange-600 text-white border-orange-500 shadow-lg shadow-orange-500/20" 
                    : "bg-card text-muted-foreground border-border hover:border-orange-500/30"
                )}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
         </div>

         <div className="relative min-w-[300px]">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input 
              type="text"
              placeholder="Search by product or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-card border border-border rounded-xl pl-12 pr-6 py-3 font-bold text-sm focus:border-orange-500 outline-none transition-all"
            />
         </div>
      </div>

      {/* Main Table Content */}
      <div className="bg-card rounded-[40px] border border-border overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-[11px] font-black text-muted-foreground uppercase tracking-[0.2em] border-b border-border">
                <th className="py-8 px-8">Product Details</th>
                <th className="py-8 px-6 text-right">Units Sold</th>
                <th className="py-8 px-6 text-right">Inventory Revenue</th>
                <th className="py-8 px-6 text-right">Performance</th>
                <th className="py-8 px-8 text-center">Branch</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-32 text-center">
                     <div className="animate-spin w-10 h-10 border-4 border-orange-600 border-t-transparent rounded-full mx-auto mb-4" />
                     <p className="text-xs font-black text-zinc-500 uppercase tracking-widest">Rebuilding Analytical Models...</p>
                  </td>
                </tr>
              ) : filteredList.length > 0 ? (
                filteredList.map((p, i) => {
                  return (
                    <tr key={i} className="group hover:bg-orange-600/[0.02] transition-colors">
                      <td className="py-8 px-8">
                        <div>
                          <p className="text-[10px] font-black text-orange-600 uppercase tracking-widest mb-1">{p.sku_code || "SKU-N/A"}</p>
                          <h4 className="text-base font-extrabold text-foreground group-hover:text-orange-500 transition-colors">{p.product_name}</h4>
                          <p className="text-xs font-medium text-muted-foreground mt-1">{p.department || "General Department"}</p>
                        </div>
                      </td>
                      <td className="py-8 px-6 text-right font-black text-foreground">
                        {Number(p.total_qty || p.quantity || p.total_units_sold || 0).toLocaleString()}
                      </td>
                      <td className="py-8 px-6 text-right font-black text-orange-600">
                        KES {Number(p.total_revenue || p.net_sale || p.total_net_sales || 0).toLocaleString()}
                      </td>
                      <td className="py-8 px-6 text-right">
                         <span className={cn(
                           "px-3 py-1.5 rounded-lg text-[11px] font-black uppercase tracking-tighter",
                           (p.avg_margin_pct || p.margin_pct || p.avg_margin || 0) >= 15 ? "bg-emerald-500/10 text-emerald-500" :
                           (p.avg_margin_pct || p.margin_pct || p.avg_margin || 0) >= 5 ? "bg-orange-500/10 text-orange-500" :
                           "bg-red-500/10 text-red-500"
                         )}>
                           {Number(p.avg_margin_pct || p.margin_pct || p.avg_margin || 0).toFixed(1)}% Margin
                         </span>
                      </td>
                      <td className="py-8 px-8 text-center">
                         <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-zinc-900 border border-white/5 rounded-full text-[10px] font-black text-zinc-400 uppercase tracking-widest">
                            {p.branch || "Multi"}
                         </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={5} className="py-32 text-center text-muted-foreground italic font-medium">
                    No matching inventory found for current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}
