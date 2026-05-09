"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { AgentHeartbeat } from "@/lib/types";

const OFFLINE_THRESHOLD_MS = 90_000;

export default function AgentStatus() {
  const [heartbeat, setHeartbeat] = useState<AgentHeartbeat | null>(null);

  async function fetchHeartbeat() {
    const { data } = await supabase
      .from("agent_heartbeat")
      .select("*")
      .eq("id", 1)
      .single();
    if (data) setHeartbeat(data as AgentHeartbeat);
  }

  useEffect(() => {
    fetchHeartbeat();
    const interval = setInterval(fetchHeartbeat, 30_000);
    return () => clearInterval(interval);
  }, []);

  const isOnline =
    heartbeat &&
    Date.now() - new Date(heartbeat.last_seen_at).getTime() < OFFLINE_THRESHOLD_MS;

  const lastSeen = heartbeat
    ? new Date(heartbeat.last_seen_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div className="flex items-center gap-2 text-sm">
      <span
        className={`w-2 h-2 rounded-full ${isOnline ? "bg-green-400 animate-pulse" : "bg-slate-500"}`}
      />
      <span className={isOnline ? "text-green-400" : "text-slate-500"}>
        Agent {isOnline ? "online" : "offline"}
      </span>
      {lastSeen && (
        <span className="text-slate-500 text-xs">· last seen {lastSeen}</span>
      )}
    </div>
  );
}
