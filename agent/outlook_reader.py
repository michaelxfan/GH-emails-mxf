"""
Windows Outlook COM interface.
Local-only — never called from the web frontend.
"""

import logging

log = logging.getLogger(__name__)

_PROPERTY_TAG_SMTP = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"


def _resolve_smtp(item):
    try:
        return item.PropertyAccessor.GetProperty(_PROPERTY_TAG_SMTP) or ""
    except Exception:
        pass
    try:
        exc = item.Sender.GetExchangeUser()
        if exc:
            return exc.PrimarySmtpAddress or ""
    except Exception:
        pass
    return ""


def _get_namespace():
    import win32com.client as win32
    try:
        outlook = win32.GetActiveObject("Outlook.Application")
    except Exception:
        outlook = win32.Dispatch("Outlook.Application")
    return outlook.GetNamespace("MAPI")


def get_inbox_emails(days_back: int = 1, max_emails: int = 75, skip_ids: set | None = None) -> list[dict]:
    import datetime
    ns = _get_namespace()
    inbox = ns.GetDefaultFolder(6)  # olFolderInbox
    items = inbox.Items
    items.Sort("[ReceivedTime]", True)

    cutoff = datetime.datetime.now() - datetime.timedelta(days=days_back)
    skip = skip_ids or set()
    results = []

    for item in items:
        if len(results) >= max_emails:
            break
        try:
            if item.Class != 43:  # olMail
                continue
            received = item.ReceivedTime
            if hasattr(received, "replace"):
                received_naive = received.replace(tzinfo=None)
            else:
                received_naive = received
            if received_naive < cutoff:
                break
            entry_id = item.EntryID
            store_id = item.Parent.StoreID
            if entry_id in skip:
                continue
            body_preview = (item.Body or "")[:800].strip()
            results.append({
                "id": entry_id,
                "store_id": store_id,
                "subject": item.Subject or "(no subject)",
                "sender": item.SenderName or "",
                "sender_email": _resolve_smtp(item),
                "received": received,
                "body_preview": body_preview,
                "unread": item.UnRead,
            })
        except Exception as exc:
            log.debug("Skipping item: %s", exc)

    return results


def get_email_item(entry_id: str, store_id: str):
    ns = _get_namespace()
    return ns.GetItemFromID(entry_id, store_id)


def archive_email(entry_id: str, store_id: str) -> tuple[bool, str]:
    try:
        ns = _get_namespace()
        item = ns.GetItemFromID(entry_id, store_id)
        archive = _get_archive_folder(ns)
        item.Move(archive)
        return True, ""
    except Exception as exc:
        log.error("archive_email failed: %s", exc)
        return False, str(exc)


def _get_archive_folder(ns):
    import win32com.client as win32
    try:
        return ns.GetDefaultFolder(44)  # olFolderArchive
    except Exception:
        pass
    for store in ns.Stores:
        try:
            root = store.GetRootFolder()
            for folder in root.Folders:
                if folder.Name.lower() in ("archive", "archives"):
                    return folder
        except Exception:
            pass
    inbox = ns.GetDefaultFolder(6)
    try:
        return inbox.Folders["Archive"]
    except Exception:
        pass
    archive = inbox.Folders.Add("Archive")
    return archive


def open_email(entry_id: str, store_id: str) -> tuple[bool, str]:
    try:
        ns = _get_namespace()
        item = ns.GetItemFromID(entry_id, store_id)
        inspector = item.GetInspector
        inspector.Activate()
        return True, ""
    except Exception as exc:
        log.error("open_email failed: %s", exc)
        return False, str(exc)


def mark_read(entry_id: str, store_id: str) -> tuple[bool, str]:
    try:
        ns = _get_namespace()
        item = ns.GetItemFromID(entry_id, store_id)
        item.UnRead = False
        item.Save()
        return True, ""
    except Exception as exc:
        log.error("mark_read failed: %s", exc)
        return False, str(exc)


def move_to_folder(entry_id: str, store_id: str, folder_name: str) -> tuple[bool, str]:
    try:
        ns = _get_namespace()
        item = ns.GetItemFromID(entry_id, store_id)
        inbox = ns.GetDefaultFolder(6)
        try:
            target = inbox.Folders[folder_name]
        except Exception:
            target = inbox.Folders.Add(folder_name)
        item.Move(target)
        return True, ""
    except Exception as exc:
        log.error("move_to_folder failed: %s", exc)
        return False, str(exc)
