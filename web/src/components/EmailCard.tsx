"use client";

import { useState } from "react";
import type { Email, Tier } from "@/lib/types";
import ActionButtons from "./ActionButtons";

const TIER_COLORS: Record<Tier, string> = {
  P0: "bg-red-900/50 text-red-300 border-red-700/50",
  P1: "bg-orange-900/50 text-orange-300 border-orange-700/50",
  P2: "bg-blue-900/50 text-blue-300 border-blue-700/50",
  P3: "bg-green-900/50 text-green-300 border-green-700/50",
};

const TIER_BORDER: Record<Tier, string> = {
  P0: "border-l-red-500",
  P1: "border-l-orange-500",
  P2: "border-l-blue-500",
  P3: "border-l-green-500",
};

function formatTime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 3_600_000) return `${Math.round(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.round(diff / 3_600_000)}h ago`;
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

interface Props {
  email: Email;
  onAction?: (emailId: string, action: string) => void;
}

export default function EmailCard({ email, onAction }: Props) {
  const [expanded, setExpanded] = useState(false);
  const tier = (email.tier ?? "P2") as Tier;

  return (
    <div
      className={`bg-slate-800 rounded-xl border border-slate-700 border-l-4 ${TIER_BORDER[tier]} p-4 transition-all`}
    >
      {/* Header row */}
      <div className="flex items-start gap-3">
        <span
          className={`shrink-0 mt-0.5 px-2 py-0.5 rounded-md text-xs font-bold border ${TIER_COLORS[tier]}`}
        >
          {tier}
        </span>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-slate-100 truncate">
            {email.subject ?? "(no subject)"}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            {email.sender_name ?? email.sender_email ?? "Unknown"}{" "}
            {email.sender_email && email.sender_name && (
              <span className="text-slate-500">· {email.sender_email}</span>
            )}
          </p>
        </div>
        <div className="shrink-0 text-xs text-slate-500">{formatTime(email.received_at)}</div>
      </div>

      {/* Reason */}
      {email.reason && (
        <p className="text-xs text-slate-500 mt-2 ml-[calc(2rem+0.75rem)]">{email.reason}</p>
      )}

      {/* Preview expand */}
      {email.body_preview && (
        <button
          onClick={() => setExpanded((x) => !x)}
          className="ml-[calc(2rem+0.75rem)] mt-2 text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          {expanded ? "▲ hide preview" : "▼ show preview"}
        </button>
      )}
      {expanded && email.body_preview && (
        <p className="ml-[calc(2rem+0.75rem)] mt-2 text-xs text-slate-400 bg-slate-900/50 rounded-lg p-3 whitespace-pre-wrap break-words">
          {email.body_preview}
        </p>
      )}

      {/* Action buttons */}
      <div className="ml-[calc(2rem+0.75rem)]">
        <ActionButtons email={email} onAction={onAction} />
      </div>
    </div>
  );
}
