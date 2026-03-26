"use client";

import { useEffect, useState } from "react";
import { fetchWithAuth } from "@/lib/api";
import { Database, CheckCircle, XCircle, AlertCircle, Clock } from "lucide-react";
import { useRouter } from "next/navigation";

export default function DataQualityPage() {
   const [data, setData] = useState<any>(null);
   const [token, setToken] = useState<string | null>(null);

   const router = useRouter();

   useEffect(() => {
      const tk = localStorage.getItem("token");
      if (!tk) {
         router.push("/login");
         return;
      }
      setToken(tk);
      fetchWithAuth("/data-quality", tk).then(d => setData(d));
   }, [router]);

   return (
      <div className="max-w-[1400px] mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
         <header className="mb-12">
            <h2 className="text-4xl font-extrabold text-foreground tracking-tight">Data Quality Pipeline</h2>
            <p className="text-orange-600 font-bold mt-2 uppercase tracking-[0.2em] text-[11px]">ETL Integrity & Field Validation Report</p>
         </header>

         {data ? (
            <div className="space-y-10">
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                  <div className="bg-card p-8 rounded-[32px] border border-border shadow-sm transition-colors duration-300">
                     <div className="flex items-center gap-4 mb-4">
                        <Database className="w-6 h-6 text-orange-600" />
                        <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Total Rows</span>
                     </div>
                     <h4 className="text-3xl font-black text-foreground">{data.total_rows?.toLocaleString()}</h4>
                  </div>
                  <div className="bg-card p-8 rounded-[32px] border border-border shadow-sm transition-colors duration-300">
                     <div className="flex items-center gap-4 mb-4">
                        <CheckCircle className="w-6 h-6 text-orange-500" />
                        <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">System Health</span>
                     </div>
                     <h4 className="text-3xl font-black text-orange-600">{data.overall_status}</h4>
                  </div>
                  <div className="bg-card p-8 rounded-[32px] border border-border shadow-sm transition-colors duration-300">
                     <div className="flex items-center gap-4 mb-4">
                        <Clock className="w-6 h-6 text-amber-500" />
                        <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest">Last Sync</span>
                     </div>
                     <p className="text-sm font-bold text-foreground truncate">
                        {data?.last_loaded_at?.split('.')?.[0] || "Just Now"}
                     </p>
                  </div>
               </div>

               <div className="bg-card p-10 rounded-[32px] border border-border shadow-sm transition-colors duration-300">
                  <h3 className="text-2xl font-extrabold text-foreground tracking-tight mb-8">Column Integrity</h3>
                  <div className="overflow-x-auto">
                     <table className="w-full text-left">
                        <thead>
                           <tr className="text-[11px] font-bold text-muted-foreground uppercase tracking-widest border-b border-border">
                              <th className="pb-6 px-4">Entity Column</th>
                              <th className="pb-6 px-4 text-center">Missing Val</th>
                              <th className="pb-6 px-4 text-center">Null %</th>
                              <th className="pb-6 px-4 text-right">Integrity</th>
                           </tr>
                        </thead>
                        <tbody className="text-sm font-semibold divide-y divide-border">
                           {data.columns?.map((c: any, i: number) => (
                              <tr key={i} className="hover:bg-orange-50/10 dark:hover:bg-orange-600/5 transition-colors">
                                 <td className="py-6 px-4 text-foreground font-bold">{c.column}</td>
                                 <td className="py-6 px-4 text-center text-muted-foreground">{(c.null_count || 0).toLocaleString()}</td>
                                 <td className="py-6 px-4 text-center text-muted-foreground">{c.null_pct || 0}%</td>
                                 <td className="py-6 px-4 text-right">
                                    <span className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest ${c.status === 'OK' ? 'bg-orange-50 dark:bg-orange-600/10 text-orange-600' : 'bg-red-50 dark:bg-red-950/20 text-red-600'
                                       }`}>
                                       {c.status || "OK"}
                                    </span>
                                 </td>
                              </tr>
                           ))}
                        </tbody>
                     </table>
                  </div>
               </div>
            </div>
         ) : (
            <div className="py-20 text-center text-gray-400 italic bg-gray-50 rounded-[40px] border border-dashed border-gray-200">
               Analyzing data pipeline health...
            </div>
         )}
      </div>
   );
}
