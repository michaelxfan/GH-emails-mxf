"""
Optional Claude-based triage for ambiguous P1/P2 emails.
Only used when TRIAGE_USE_AI=true.
Never sends full email bodies — sender, subject, and preview only.
"""

import json
import logging
import os
import time

log = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"
_MAX_BATCH = 20

_SYSTEM = """You are an email triage assistant for a business professional.
Classify each email as P0 (urgent/VIP), P1 (needs reply soon), P2 (informational), or P3 (automated/noise).

Rules:
- Automated platforms (TikTok, Google, Amazon, Apple, Stripe, Shopify, GitHub, newsletters, notifications) → always P3
- Security notifications → always P3
- Return ONLY valid JSON, no commentary.

Output format:
[{"i": 0, "tier": "P1", "reason": "short reason"}, ...]"""


def _build_client():
    import anthropic
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=key)


def _call(client, user_content: str, max_tokens: int = 1024) -> str:
    delays = [15, 30, 60, 120]
    for attempt, delay in enumerate(delays):
        try:
            resp = client.messages.create(
                model=_MODEL,
                max_tokens=max_tokens,
                system=[{"type": "text", "text": _SYSTEM, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user_content}],
            )
            return resp.content[0].text
        except Exception as exc:
            log.warning("Claude API attempt %d failed: %s", attempt + 1, exc)
            if attempt < len(delays) - 1:
                time.sleep(delay)
    raise RuntimeError("Claude API failed after 4 attempts")


def refine_ambiguous(emails: list[dict]) -> list[dict]:
    """
    Re-triage emails that rules classified as P1 or P2 using Claude.
    Only sends minimal data (index, subject, sender, preview).
    Returns the same list with possibly updated tier/reason values.
    """
    ambiguous = [e for e in emails if e.get("tier") in ("P1", "P2")]
    if not ambiguous:
        return emails

    client = _build_client()
    idx_map = {id(e): i for i, e in enumerate(emails)}

    # Process in batches
    for batch_start in range(0, len(ambiguous), _MAX_BATCH):
        batch = ambiguous[batch_start: batch_start + _MAX_BATCH]
        payload = [
            {
                "i": j,
                "s": e.get("subject", ""),
                "f": e.get("sender", ""),
                "e": e.get("sender_email", ""),
                "b": (e.get("body_preview") or "")[:300],
            }
            for j, e in enumerate(batch)
        ]
        user_content = json.dumps(payload, ensure_ascii=False)
        try:
            raw = _call(client, user_content)
            raw = raw.strip()
            if not raw.startswith("["):
                raw = raw[raw.index("["):]
            if not raw.endswith("]"):
                raw = raw[: raw.rindex("]") + 1]
            results = json.loads(raw)
            for item in results:
                j = item.get("i", -1)
                if 0 <= j < len(batch):
                    email = batch[j]
                    email["tier"] = item.get("tier", email["tier"])
                    email["reason"] = item.get("reason", email.get("reason", ""))
        except Exception as exc:
            log.warning("AI triage batch failed, keeping rule results: %s", exc)

    return emails
