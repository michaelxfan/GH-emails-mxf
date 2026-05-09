export type Tier = "P0" | "P1" | "P2" | "P3";

export interface Email {
  id: string;
  outlook_entry_id: string;
  outlook_store_id: string;
  subject: string | null;
  sender_name: string | null;
  sender_email: string | null;
  received_at: string | null;
  body_preview: string | null;
  unread: boolean;
  tier: Tier | null;
  reason: string | null;
  suggested_action: string | null;
  draft_reply: string | null;
  status: string;
  synced_at: string;
}

export interface ActionQueueRow {
  id: string;
  email_id: string;
  action: "archive" | "open_on_work_computer" | "mark_read" | "move_to_folder";
  payload: Record<string, unknown>;
  status: "pending" | "processing" | "completed" | "failed";
  error: string | null;
  requested_at: string;
  processed_at: string | null;
}

export interface AgentHeartbeat {
  id: number;
  last_seen_at: string;
  status: string | null;
  current_version: string | null;
  last_error: string | null;
}

export interface TriageRun {
  id: string;
  started_at: string;
  finished_at: string | null;
  emails_scanned: number;
  emails_synced: number;
  p0_count: number;
  p1_count: number;
  p2_count: number;
  p3_count: number;
  error: string | null;
}
