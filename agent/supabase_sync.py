"""
Supabase sync helpers for the Windows agent.
Uses the service_role key — never expose this to the browser.
"""

import logging
import os
from datetime import datetime, timezone

log = logging.getLogger(__name__)

AGENT_VERSION = "1.0.0"


def _client():
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def upsert_emails(emails: list[dict]) -> int:
    """Upsert triaged email records. Returns count of rows upserted."""
    if not emails:
        return 0
    sb = _client()
    rows = []
    for e in emails:
        received = e.get("received")
        if received is not None:
            try:
                if hasattr(received, "isoformat"):
                    received_str = received.isoformat()
                else:
                    received_str = str(received)
            except Exception:
                received_str = None
        else:
            received_str = None

        rows.append({
            "outlook_entry_id": e["id"],
            "outlook_store_id": e["store_id"],
            "subject": e.get("subject"),
            "sender_name": e.get("sender"),
            "sender_email": e.get("sender_email"),
            "received_at": received_str,
            "body_preview": e.get("body_preview"),
            "unread": e.get("unread", False),
            "tier": e.get("tier"),
            "reason": e.get("reason"),
            "suggested_action": e.get("suggested_action"),
            "synced_at": datetime.now(timezone.utc).isoformat(),
        })

    resp = (
        sb.table("emails")
        .upsert(rows, on_conflict="outlook_entry_id,outlook_store_id")
        .execute()
    )
    count = len(resp.data) if resp.data else 0
    log.info("Upserted %d email rows", count)
    return count


def fetch_pending_actions() -> list[dict]:
    """Return pending action_queue rows joined with email outlook IDs."""
    sb = _client()
    resp = (
        sb.table("action_queue")
        .select("*, emails(outlook_entry_id, outlook_store_id)")
        .eq("status", "pending")
        .order("requested_at")
        .limit(50)
        .execute()
    )
    return resp.data or []


def set_action_processing(action_id: str) -> None:
    sb = _client()
    sb.table("action_queue").update({"status": "processing"}).eq("id", action_id).execute()


def complete_action(action_id: str) -> None:
    sb = _client()
    sb.table("action_queue").update({
        "status": "completed",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", action_id).execute()


def fail_action(action_id: str, error: str) -> None:
    sb = _client()
    sb.table("action_queue").update({
        "status": "failed",
        "error": error,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", action_id).execute()


def update_heartbeat(status: str = "running", error: str | None = None) -> None:
    sb = _client()
    row = {
        "id": 1,
        "last_seen_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "current_version": AGENT_VERSION,
    }
    if error is not None:
        row["last_error"] = error
    sb.table("agent_heartbeat").upsert(row, on_conflict="id").execute()


def insert_triage_run(run: dict) -> str | None:
    """Insert a triage_run record and return its id."""
    sb = _client()
    resp = sb.table("triage_runs").insert(run).execute()
    if resp.data:
        return resp.data[0].get("id")
    return None


def finish_triage_run(run_id: str, update: dict) -> None:
    sb = _client()
    sb.table("triage_runs").update(update).eq("id", run_id).execute()
