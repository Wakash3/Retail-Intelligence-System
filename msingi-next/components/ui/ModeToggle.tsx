"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { motion } from "framer-motion";

export default function ModeToggle() {
  // Use resolvedTheme so it handles "system" correctly
  const { setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="flex items-center gap-3 w-full px-4 py-3.5 rounded-2xl text-sm font-semibold text-gray-400 opacity-50">
        <Sun className="w-5 h-5" />
        <span>Loading...</span>
      </div>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      // Added z-50 to ensure it sits on top of other overlapping elements
      className="relative z-50 flex items-center gap-3 w-full px-4 py-3.5 rounded-2xl text-sm font-semibold transition-all duration-200 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 dark:text-zinc-400"
    >
      {isDark ? (
        <>
          <Sun className="w-5 h-5 text-orange-500" />
          <span>Switch to Light</span>
        </>
      ) : (
        <>
          <Moon className="w-5 h-5 text-gray-400" />
          <span>Switch to Dark</span>
        </>
      )}
    </motion.button>
  );
}
