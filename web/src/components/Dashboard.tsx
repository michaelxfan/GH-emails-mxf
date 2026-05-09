"use client";

import { useCallback, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { Email, Tier, TriageRun } from "@/lib/types";
import AgentStatus from "./AgentStatus";
import PriorityTabs from "./PriorityTabs";
import EmailCard from "./EmailCard";

const PAGE_SIZE = 30;

function emptyCounts(): Record<Tier, number> {
  return { P0: 0, P1: 0, P2: 0, P3: 0 };
}

export default function Dashboard() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [counts, setCounts] = useState<Record<Tier, number>>(emptyCounts());
  const [activeTab, setActiveTab] = useState<Tier | "ALL">("ALL");
  const [lastRun, setLastRun] = useState<TriageRun | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchEmails = useCallback(async (tab: Tier | "ALL") => {
    setLoading(true);
    let query = supabase
      .from("emails")
      .select("*")
      .eq("status", "active")
      .order("received_at", { ascending: false })
      .limit(PAGE_SIZE);

    if (tab !== "ALL") {
      query = query.eq("tier", tab);
    }

    const { data } = await query;
    setEmails((data as Email[]) ?? []);
    setLoading(false);
  }, []);

  async function fetchCounts() {
    const tiers: Tier[] = ["P0", "P1", "P2", "P3"];
    const next = emptyCounts();
    await Promise.all(
      tiers.map(async (t) => {
        const { count } = await supabase
          .from("emails")
          .select("id", { count: "exact", head: true })
          .eq("tier", t)
          .eq("status", "active");
        next[t] = count ?? 0;
      })
    );
    setCounts(next);
  }

  async function fetchLastRun() {
    const { data } = await supabase
      .from("triage_runs")
      .select("*")
      .order("started_at", { ascending: false })
      .limit(1)
      .single();
    if (data) setLastRun(data as TriageRun);
  }

  useEffect(() => {
    fetchEmails(activeTab);
    fetchCounts();
    fetchLastRun();
    // Refresh every 60s
    const iv = setInterval(() => {
      fetchEmails(activeTab);
      fetchCounts();
      fetchLastRun();
    }, 60_000);
    return () => clearInterval(iv);
  }, [activeTab, fetchEmails]);

  function handleTabChange(tab: Tier | "ALL") {
    setActiveTab(tab);
    fetchEmails(tab);
  }

  // Optimistic update: mark archived emails as inactive in local state
  function handleAction(emailId: string, action: string) {
    if (action === "archive") {
      setEmails((prev) => prev.filter((e) => e.id !== emailId));
      setCounts((prev) => {
        const email = emails.find((e) => e.id === emailId);
        if (!email?.tier) return prev;
        const t = email.tier as Tier;
        return { ...prev, [t]: Math.max(0, prev[t] - 1) };
      });
    }
  }

  const lastSyncTime = lastRun?.finished_at
    ? new Date(lastRun.finished_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">
          {process.env.NEXT_PUBLIC_APP_NAME ?? "GH-emails-mxf"}
        </h1>
        <AgentStatus />
      </div>

      {/* Stats bar */}
      <div className="bg-slate-800 rounded-xl px-4 py-3 flex items-center gap-4 text-sm flex-wrap">
        <div className="flex gap-3">
          <span className="text-red-400 font-semibold">P0 {counts.P0}</span>
          <span className="text-orange-400 font-semibold">P1 {counts.P1}</span>
          <span className="text-blue-400 font-semibold">P2 {counts.P2}</span>
          <span className="text-green-400 font-semibold">P3 {counts.P3}</span>
        </div>
        {lastSyncTime && (
          <span className="text-slate-500 text-xs ml-auto">synced {lastSyncTime}</span>
        )}
      </div>

      {/* Tabs */}
      <PriorityTabs active={activeTab} counts={counts} onChange={handleTabChange} />

      {/* Email list */}
      {loading ? (
        <div className="text-center text-slate-500 py-16 text-sm">Loading…</div>
      ) : emails.length === 0 ? (
        <div className="text-center text-slate-500 py-16 text-sm">No emails in this tier</div>
      ) : (
        <div className="space-y-3">
          {emails.map((email) => (
            <EmailCard key={email.id} email={email} onAction={handleAction} />
          ))}
        </div>
      )}
    </div>
  );
}
