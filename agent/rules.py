"""
Rule-based email triage. No API calls — instant classification.
"""

import re

_VIP_SENDERS = {
    "anthony@greenhouse.ca",
    "kevin@greenhouse.ca",
    "chase@greenhouse.ca",
}

_URGENT_SUBJECT_RE = re.compile(
    r"\b(urgent|asap|action required|time.sensitive|critical|deadline|emergency|important)\b",
    re.IGNORECASE,
)

_REPLY_SUBJECT_RE = re.compile(
    r"\b(re:|fwd:|follow.?up|question|request|approval|confirm|schedule|meeting|call|discuss)\b",
    re.IGNORECASE,
)

_AUTO_DOMAIN_RE = re.compile(
    r"@(.*\.)?(tiktok|amazon|google|apple|meta|shopify|slack|notion|hubspot|salesforce|"
    r"stripe|paypal|github|noreply|no-reply|notifications?|newsletter|alerts?|mailer|"
    r"digest|updates?|info|support|donotreply|bounce|sendgrid|mailchimp|klaviyo|"
    r"constantcontact|campaign\.)",
    re.IGNORECASE,
)

_AUTO_SUBJECT_RE = re.compile(
    r"\b(new login|sign.?in|verification|security alert|order|receipt|invoice|"
    r"unsubscribe|welcome|password reset|confirm your|activate your|"
    r"newsletter|digest|weekly|monthly|recap|roundup|notification|reminder)\b",
    re.IGNORECASE,
)

_UNSUBSCRIBE_BODY_RE = re.compile(r"unsubscribe|opt.?out|manage.*preference", re.IGNORECASE)
_READTHROUGH_RE = re.compile(r"newsletter|digest|weekly|monthly|recap|roundup", re.IGNORECASE)


def _is_automated(sender_email: str, subject: str) -> bool:
    return bool(_AUTO_DOMAIN_RE.search(sender_email) or _AUTO_SUBJECT_RE.search(subject))


def _p3_action(subject: str, body_preview: str) -> str:
    if _UNSUBSCRIBE_BODY_RE.search(body_preview):
        return "unsubscribe"
    if _READTHROUGH_RE.search(subject):
        return "readthrough"
    return "archive"


def triage(emails: list[dict]) -> dict:
    """
    Classify each email and return summary.

    Each email dict must have: subject, sender_email, unread, body_preview.
    Returns: {summary: str, counts: {P0,P1,P2,P3}, emails: list[dict+tier+reason+suggested_action]}
    """
    counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    out = []

    for email in emails:
        subject = email.get("subject", "")
        sender_email = (email.get("sender_email") or "").lower()
        unread = email.get("unread", False)
        body = email.get("body_preview", "")
        is_vip = sender_email in _VIP_SENDERS

        if _is_automated(sender_email, subject):
            tier = "P3"
            reason = "Automated sender or notification pattern"
            suggested = _p3_action(subject, body)
        elif is_vip and _URGENT_SUBJECT_RE.search(subject):
            tier = "P0"
            reason = "VIP sender with urgent subject"
            suggested = "reply"
        elif _URGENT_SUBJECT_RE.search(subject):
            tier = "P0"
            reason = "Urgent keywords in subject"
            suggested = "reply"
        elif is_vip:
            tier = "P1"
            reason = "VIP sender"
            suggested = "reply"
        elif _REPLY_SUBJECT_RE.search(subject):
            tier = "P1"
            reason = "Reply-oriented subject"
            suggested = "reply"
        elif unread:
            tier = "P1"
            reason = "Unread email"
            suggested = "read"
        else:
            tier = "P2"
            reason = "Standard informational email"
            suggested = "read"

        counts[tier] += 1
        out.append({**email, "tier": tier, "reason": reason, "suggested_action": suggested})

    p0 = counts["P0"]
    total = len(out)
    if p0:
        summary = f"{p0} urgent email{'s' if p0 > 1 else ''} need attention  •  {total} total"
    else:
        summary = f"{total} emails triaged  •  P1:{counts['P1']} P2:{counts['P2']} P3:{counts['P3']}"

    return {"summary": summary, "counts": counts, "emails": out}
