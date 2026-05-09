"use client";

import type { Tier } from "@/lib/types";

const TABS: Array<Tier | "ALL"> = ["ALL", "P0", "P1", "P2", "P3"];

const TAB_COLORS: Record<string, string> = {
  ALL: "bg-slate-600 text-white",
  P0: "bg-red-700 text-white",
  P1: "bg-orange-700 text-white",
  P2: "bg-blue-700 text-white",
  P3: "bg-green-700 text-white",
};

const TAB_INACTIVE: Record<string, string> = {
  ALL: "text-slate-400 hover:text-slate-200",
  P0: "text-red-400 hover:text-red-200",
  P1: "text-orange-400 hover:text-orange-200",
  P2: "text-blue-400 hover:text-blue-200",
  P3: "text-green-400 hover:text-green-200",
};

interface Props {
  active: Tier | "ALL";
  counts: Record<Tier, number>;
  onChange: (tab: Tier | "ALL") => void;
}

export default function PriorityTabs({ active, counts, onChange }: Props) {
  const total = Object.values(counts).reduce((s, n) => s + n, 0);

  return (
    <div className="flex gap-1 overflow-x-auto no-scrollbar pb-1">
      {TABS.map((tab) => {
        const count = tab === "ALL" ? total : counts[tab];
        const isActive = active === tab;
        return (
          <button
            key={tab}
            onClick={() => onChange(tab)}
            className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold transition-all
              ${isActive ? TAB_COLORS[tab] : `bg-slate-800 border border-slate-700 ${TAB_INACTIVE[tab]}`}`}
          >
            {tab}
            <span
              className={`text-xs rounded-full px-1.5 py-0.5 min-w-[1.25rem] text-center
                ${isActive ? "bg-black/20" : "bg-slate-700 text-slate-400"}`}
            >
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
