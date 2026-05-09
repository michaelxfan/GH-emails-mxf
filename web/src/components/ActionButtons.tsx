"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";
import type { Email } from "@/lib/types";

interface Props {
  email: Email;
  onAction?: (emailId: string, action: string) => void;
}

const ACTIONS = [
  { key: "archive", label: "Archive", icon: "📥" },
  { key: "open_on_work_computer", label: "Open", icon: "💻" },
  { key: "mark_read", label: "Mark Read", icon: "✓" },
] as const;

export default function ActionButtons({ email, onAction }: Props) {
  const [pending, setPending] = useState<string | null>(null);
  const [done, setDone] = useState<Set<string>>(new Set());

  async function queueAction(action: string) {
    if (pending || done.has(action)) return;
    setPending(action);
    try {
      const { error } = await supabase.from("action_queue").insert({
        email_id: email.id,
        action,
        payload: {},
      });
      if (error) throw error;
      setDone((prev) => { const s = new Set(prev); s.add(action); return s; });
      onAction?.(email.id, action);
    } catch (err) {
      console.error("Failed to queue action:", err);
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="flex gap-2 flex-wrap mt-3">
      {ACTIONS.map(({ key, label, icon }) => {
        const isDone = done.has(key);
        const isLoading = pending === key;
        return (
          <button
            key={key}
            onClick={() => queueAction(key)}
            disabled={!!pending || isDone}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all
              ${isDone
                ? "bg-green-900/40 text-green-400 border border-green-700/50 cursor-default"
                : "bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600 disabled:opacity-50 disabled:cursor-not-allowed"
              }`}
          >
            <span>{isLoading ? "…" : icon}</span>
            {isDone ? `${label} queued` : label}
          </button>
        );
      })}
    </div>
  );
}
