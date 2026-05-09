"""
GH-emails-mxf Windows agent.
Reads Outlook, triages emails, syncs to Supabase, and executes queued actions.
"""

import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── logging setup ──────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "agent.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("agent")

# ── env loading ─────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TRIAGE_USE_AI = os.environ.get("TRIAGE_USE_AI", "false").lower() == "true"
SYNC_INTERVAL = int(os.environ.get("SYNC_INTERVAL_SECONDS", "30"))
DAYS_BACK = int(os.environ.get("DAYS_BACK", "1"))
MAX_EMAILS = int(os.environ.get("MAX_EMAILS", "75"))


def _check_env():
    missing = [k for k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") if not os.environ.get(k)]
    if missing:
        log.error("Missing required env vars: %s", ", ".join(missing))
        sys.exit(1)
    if TRIAGE_USE_AI and not ANTHROPIC_API_KEY:
        log.error("TRIAGE_USE_AI=true but ANTHROPIC_API_KEY is not set")
        sys.exit(1)


# ── action executor ─────────────────────────────────────────────────────────
def _execute_action(action_row: dict) -> tuple[bool, str]:
    import outlook_reader as ol

    email_info = action_row.get("emails") or {}
    entry_id = email_info.get("outlook_entry_id", "")
    store_id = email_info.get("outlook_store_id", "")
    action = action_row.get("action", "")
    payload = action_row.get("payload") or {}

    if not entry_id or not store_id:
        return False, "Missing outlook_entry_id or outlook_store_id"

    if action == "archive":
        return ol.archive_email(entry_id, store_id)
    elif action == "open_on_work_computer":
        return ol.open_email(entry_id, store_id)
    elif action == "mark_read":
        return ol.mark_read(entry_id, store_id)
    elif action == "move_to_folder":
        folder_name = payload.get("folder_name", "")
        if not folder_name:
            return False, "move_to_folder requires payload.folder_name"
        return ol.move_to_folder(entry_id, store_id, folder_name)
    else:
        return False, f"Unknown action: {action}"


# ── main loop ───────────────────────────────────────────────────────────────
def run_cycle():
    import rules
    import supabase_sync as sb

    # 1. Heartbeat
    try:
        sb.update_heartbeat("running")
    except Exception as exc:
        log.warning("Heartbeat update failed: %s", exc)

    # 2. Triage run record
    run_id = None
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        run_id = sb.insert_triage_run({"started_at": started_at})
    except Exception as exc:
        log.warning("Could not insert triage_run: %s", exc)

    emails_scanned = 0
    emails_synced = 0
    counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    run_error = None

    try:
        # 3. Fetch inbox
        import outlook_reader as ol
        log.info("Fetching inbox (days_back=%d, max=%d)…", DAYS_BACK, MAX_EMAILS)
        emails = ol.get_inbox_emails(days_back=DAYS_BACK, max_emails=MAX_EMAILS)
        emails_scanned = len(emails)
        log.info("Fetched %d emails", emails_scanned)

        # 4. Rule-based triage
        result = rules.triage(emails)
        triaged = result["emails"]
        counts = result["counts"]
        log.info("Triage: %s", result["summary"])

        # 5. Optional AI refinement
        if TRIAGE_USE_AI and triaged:
            try:
                import analyzer
                triaged = analyzer.refine_ambiguous(triaged)
                log.info("AI triage complete")
            except Exception as exc:
                log.warning("AI triage failed, using rule results: %s", exc)

        # 6. Upsert to Supabase
        emails_synced = sb.upsert_emails(triaged)

    except Exception as exc:
        log.error("Triage/sync cycle error: %s", exc, exc_info=True)
        run_error = str(exc)
        try:
            sb.update_heartbeat("error", error=str(exc))
        except Exception:
            pass

    # Finish triage run record
    if run_id:
        try:
            sb.finish_triage_run(run_id, {
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "emails_scanned": emails_scanned,
                "emails_synced": emails_synced,
                "p0_count": counts.get("P0", 0),
                "p1_count": counts.get("P1", 0),
                "p2_count": counts.get("P2", 0),
                "p3_count": counts.get("P3", 0),
                "error": run_error,
            })
        except Exception as exc:
            log.warning("Could not finish triage_run: %s", exc)

    # 7. Process action queue
    _process_actions()


def _process_actions():
    import supabase_sync as sb
    try:
        actions = sb.fetch_pending_actions()
        if not actions:
            return
        log.info("Processing %d pending action(s)…", len(actions))
        for action_row in actions:
            action_id = action_row["id"]
            try:
                sb.set_action_processing(action_id)
                ok, err = _execute_action(action_row)
                if ok:
                    sb.complete_action(action_id)
                    log.info("Action %s (%s) completed", action_id[:8], action_row.get("action"))
                else:
                    sb.fail_action(action_id, err)
                    log.warning("Action %s (%s) failed: %s", action_id[:8], action_row.get("action"), err)
            except Exception as exc:
                log.error("Action %s raised: %s", action_id[:8], exc)
                try:
                    sb.fail_action(action_id, str(exc))
                except Exception:
                    pass
    except Exception as exc:
        log.error("Failed to fetch/process action queue: %s", exc)


def main():
    log.info("GH-emails-mxf agent starting (version %s)", "1.0.0")
    log.info("TRIAGE_USE_AI=%s  SYNC_INTERVAL=%ds", TRIAGE_USE_AI, SYNC_INTERVAL)
    _check_env()

    while True:
        try:
            run_cycle()
        except KeyboardInterrupt:
            log.info("Agent stopped by user")
            break
        except Exception as exc:
            log.error("Unexpected error in run_cycle: %s", exc, exc_info=True)

        log.info("Sleeping %ds…", SYNC_INTERVAL)
        try:
            time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            log.info("Agent stopped by user")
            break


if __name__ == "__main__":
    main()
