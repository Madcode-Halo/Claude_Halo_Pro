# -*- coding: utf-8 -*-
"""
halo_pro_inbox.py — Halo_Pro-Briefkasten-Library

Append-only Event-Log + Read-Pointer pro Claude-Session.
Multi-Session-safe: Events werden niemals beim Lesen geloescht. Jede Session
hat eigenen Read-Pointer (last_read_index). Kein Race zwischen parallelen
Sessions — beide sehen alle Events bis zum eigenen Pointer.

Adaptiert von Halos halo_inbox.py (D:/Anthropic_Claude/Halo/Scripts/halo_inbox.py).
Unterschiede:
  - ROOT zeigt auf D:/Anthropic_Claude/Halo_Pro/
  - HALO_SOURCE_PREFIX ist 'halo_pro_session_' (kein Konflikt mit Halos events.jsonl)
  - post_as_halo_pro() statt post_as_halo()

Dateien (alle unter Halo_Pro/Status/):
    events.jsonl                 — Event-Log, append-only
    events_archive.jsonl         — Events aelter als 7 Tage (rotate_archive)
    briefkasten_read/<sid>.json  — Read-Pointer pro Session

Event-Schema (eine JSON-Zeile):
    {
      "index": 42,
      "id": "2026-05-07T20:00:00.123456_abc123",
      "source": "telegram_bridge | halo_pro_session_<id> | hook_name | ...",
      "source_host": "<hostname>",
      "kind": "...",
      "target": null | "halo_pro_<session_id>",
      "severity": "info|warning|critical|urgent",
      "timestamp": "2026-05-07T20:00:00.123456",
      "dedup_key": "..." | null,
      "payload": "Nachrichtentext"
    }

API:
    post(source, kind, severity, payload, dedup_key=None, target=None,
         source_host=None) -> dict | None
    post_as_halo_pro(session_id, kind, payload, target=None, severity="info",
                     dedup_key=None, source_host=None) -> dict | None
    get_unread(session_id) -> list[dict]
    mark_read(session_id, last_read_index) -> None
    get_recent_events(limit=3) -> list[dict]
    search_archive(contains=None, source=None, since=None) -> list[dict]
    rotate_archive(days=7) -> int
    is_local(event) -> bool
"""
from __future__ import annotations

import json
import os
import re
import socket
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Portable ROOT — zeigt auf D:/Anthropic_Claude/Halo_Pro/
ROOT = Path(__file__).resolve().parent.parent
STATUS_DIR = ROOT / "Status"
EVENTS_FILE = STATUS_DIR / "events.jsonl"
ARCHIVE_FILE = STATUS_DIR / "events_archive.jsonl"
READ_DIR = STATUS_DIR / "briefkasten_read"

DEDUP_WINDOW_MINUTES = 5
DEDUP_SCAN_LIMIT = 100
DEFAULT_ARCHIVE_DAYS = 7

KIND_VALUES = {
    "program",            # Worker, generischer Programm-Output
    "human",              # Mad direkt
    "system",             # Hook-Aktivitaet, Service-Status
    "tool_menu",          # Tool-Listen
    "halo_pro",           # Halo_Pro-zu-Halo_Pro, generisch
    "status",             # Status-Update einer Session
    "question",           # Frage
    "reply",              # Antwort auf question
    "halo_pro_online",    # Launcher-Lifecycle: Halo_Pro gestartet
    "halo_pro_offline",   # Launcher-Lifecycle: Halo_Pro beendet
    "reflex_alert",       # Reflex-Hinweis
    "telegram",           # halo_pro_telegram_bridge: Inbound-Message von Mad via Telegram
}
SEVERITY_VALUES = {"info", "warning", "critical", "urgent"}

HALO_PRO_SOURCE_PREFIX = "halo_pro_session_"
_SAFE_SESSION_ID = re.compile(r"[^A-Za-z0-9_.\-]")


# --- Helpers --------------------------------------------------------------

def _now() -> datetime:
    return datetime.now()


def _now_iso() -> str:
    return _now().isoformat(timespec="microseconds")


def _ensure_dirs() -> None:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    READ_DIR.mkdir(parents=True, exist_ok=True)


def _safe_session(session_id: str) -> str:
    s = session_id or "unknown"
    return _SAFE_SESSION_ID.sub("_", s)[:128] or "unknown"


def _pointer_path(session_id: str) -> Path:
    return READ_DIR / f"{_safe_session(session_id)}.json"


def _read_all_events() -> list[dict]:
    if not EVENTS_FILE.exists():
        return []
    out: list[dict] = []
    with EVENTS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def _append_event(event: dict) -> None:
    _ensure_dirs()
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _next_index() -> int:
    """Index des naechsten Events (= aktuelle Zeilenzahl in events.jsonl)."""
    if not EVENTS_FILE.exists():
        return 0
    count = 0
    with EVENTS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _within_dedup_window(iso_ts: str) -> bool:
    try:
        t = datetime.fromisoformat(iso_ts)
    except Exception:
        return False
    return (_now() - t) <= timedelta(minutes=DEDUP_WINDOW_MINUTES)


def _read_pointer(session_id: str) -> int:
    p = _pointer_path(session_id)
    if not p.exists():
        return -1
    try:
        return int(json.loads(p.read_text(encoding="utf-8")).get("last_read_index", -1))
    except Exception:
        return -1


def _write_pointer(session_id: str, last_read_index: int) -> None:
    _ensure_dirs()
    p = _pointer_path(session_id)
    tmp = p.with_suffix(".json.tmp")
    data = {
        "session_id": session_id,
        "last_read_index": last_read_index,
        "updated_at": _now_iso(),
    }
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


# --- Public API -----------------------------------------------------------

def post(source: str, kind: str, severity: str, payload: str,
         dedup_key: str | None = None,
         target: str | None = None,
         source_host: str | None = None,
         **extra) -> dict | None:
    """Event an events.jsonl anhaengen.

    Returns das geschriebene Event — oder None wenn Dedup greift.
    Raises ValueError bei ungueltigem kind/severity/leerem source.

    **extra: zusaetzliche Felder die ins Event landen (z.B. chat_id, chat_type
    fuer Telegram-Gruppen). Werden direkt ins JSON gemerged.
    """
    if not source:
        raise ValueError("source darf nicht leer sein")
    if kind not in KIND_VALUES:
        raise ValueError(f"kind muss in {KIND_VALUES} sein, war {kind!r}")
    if severity not in SEVERITY_VALUES:
        raise ValueError(f"severity muss in {SEVERITY_VALUES} sein, war {severity!r}")

    _ensure_dirs()

    if dedup_key:
        for existing in reversed(_read_all_events()[-DEDUP_SCAN_LIMIT:]):
            if (existing.get("dedup_key") == dedup_key
                    and _within_dedup_window(existing.get("timestamp", ""))):
                return None

    ts = _now_iso()
    event = {
        "index": _next_index(),
        "id": f"{ts}_{uuid.uuid4().hex[:6]}",
        "source": source,
        "source_host": source_host or socket.gethostname(),
        "kind": kind,
        "target": target,
        "severity": severity,
        "timestamp": ts,
        "dedup_key": dedup_key,
        "payload": payload,
        **extra,
    }
    _append_event(event)
    return event


def post_as_halo_pro(session_id: str, kind: str, payload: str,
                     target: str | None = None,
                     severity: str = "info",
                     dedup_key: str | None = None,
                     source_host: str | None = None) -> dict | None:
    """Helper fuer Halo_Pro-Sessions: source=halo_pro_session_<safe-id>."""
    source = f"{HALO_PRO_SOURCE_PREFIX}{_safe_session(session_id)}"
    return post(source=source, kind=kind, severity=severity,
                payload=payload, dedup_key=dedup_key, target=target,
                source_host=source_host)


def is_local(event: dict) -> bool:
    """True wenn Event vom gleichen Host kam wie der laufende Prozess."""
    host = event.get("source_host")
    if not host:
        return True
    return host.lower() == socket.gethostname().lower()


def get_unread(session_id: str) -> list[dict]:
    """Alle Events mit index > last_read_index der Session.

    Filter:
    - Self-Filter: eigene Posts (source==halo_pro_session_<own_id>) raus
    - Target-Filter: target!=null und target!=session_id raus.
      Target wird tolerant verglichen — akzeptiert sowohl 'halo_pro_<sid>',
      'halo_pro_session_<sid>' als auch nackte UUID.
    """
    last_read = _read_pointer(session_id)
    own_safe = _safe_session(session_id)
    own_source = f"{HALO_PRO_SOURCE_PREFIX}{own_safe}"
    result: list[dict] = []
    for ev in _read_all_events():
        if ev.get("index", -1) <= last_read:
            continue
        if ev.get("source") == own_source:
            continue
        tgt = ev.get("target")
        if tgt is not None:
            tgt_clean = tgt
            # Strip diverse Praefixe in fester Reihenfolge
            for prefix in (HALO_PRO_SOURCE_PREFIX, "halo_pro_"):
                if tgt_clean.startswith(prefix):
                    tgt_clean = tgt_clean[len(prefix):]
                    break
            if _safe_session(tgt_clean) != own_safe:
                continue
        result.append(ev)
    return result


def mark_read(session_id: str, last_read_index: int) -> None:
    """Schreibt neuen Pointer (nach Hook-Injektion aufzurufen)."""
    _write_pointer(session_id, last_read_index)


def get_recent_events(limit: int = 3) -> list[dict]:
    """Letzte N Events ohne Pointer-Update — fuer on-demand Erinnerung."""
    all_events = _read_all_events()
    return all_events[-limit:] if limit > 0 else []


def search_archive(contains: str | None = None,
                   source: str | None = None,
                   since: str | None = None) -> list[dict]:
    """Sucht in events.jsonl + events_archive.jsonl."""
    results: list[dict] = []
    for f in (EVENTS_FILE, ARCHIVE_FILE):
        if not f.exists():
            continue
        with f.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if contains and contains.lower() not in ev.get("payload", "").lower():
                    continue
                if source and ev.get("source") != source:
                    continue
                if since and ev.get("timestamp", "") < since:
                    continue
                results.append(ev)
    return results


def rotate_archive(days: int = DEFAULT_ARCHIVE_DAYS) -> int:
    """Events aelter als `days` in events_archive.jsonl verschieben."""
    if not EVENTS_FILE.exists():
        return 0
    cutoff = _now() - timedelta(days=days)
    keep: list[str] = []
    moved: list[dict] = []
    with EVENTS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                ts = datetime.fromisoformat(ev.get("timestamp", ""))
            except Exception:
                keep.append(line)
                continue
            if ts < cutoff:
                moved.append(ev)
            else:
                keep.append(json.dumps(ev, ensure_ascii=False))
    if not moved:
        return 0

    with ARCHIVE_FILE.open("a", encoding="utf-8") as f:
        for ev in moved:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    tmp = EVENTS_FILE.with_suffix(".jsonl.tmp")
    tmp.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
    os.replace(tmp, EVENTS_FILE)
    return len(moved)


# --- Selbsttest -----------------------------------------------------------

if __name__ == "__main__":
    print(f"=== halo_pro_inbox.py Selbsttest ({ROOT}) ===")
    print(f"Events:  {EVENTS_FILE}")
    print(f"Pointer: {READ_DIR}")
    print()

    print("-- Test 1: post + dedup --")
    ev = post("test_self", "program", "info", "Selbsttest start", dedup_key="self_test")
    print(f"  Event: idx={ev['index']} target={ev['target']!r}")
    ev2 = post("test_self", "program", "info", "Wiederholung", dedup_key="self_test")
    print(f"  Wiederholung: {'DEDUP ok' if ev2 is None else 'FEHLER (kein dedup)'}")

    print("\n-- Test 2: Session A liest, Session B sieht weiter --")
    sid_a, sid_b = "test-session-aaa", "test-session-bbb"
    unread_a = get_unread(sid_a)
    print(f"  A unread vor mark_read: {len(unread_a)}")
    if unread_a:
        mark_read(sid_a, max(e["index"] for e in unread_a))
    print(f"  A nach mark_read: {len(get_unread(sid_a))} (soll 0)")
    print(f"  B unread (Broadcast): {len(get_unread(sid_b))} (soll >0)")

    print("\n-- Test 3: Halo_Pro A postet, sieht eigenen Post nicht --")
    ev = post_as_halo_pro(sid_a, "status", "A arbeitet")
    sees_own = any(e["id"] == ev["id"] for e in get_unread(sid_a))
    print(f"  A sieht eigenen Post: {sees_own} (soll False)")
    sees_b = any(e["id"] == ev["id"] for e in get_unread(sid_b))
    print(f"  B sieht A's Post: {sees_b} (soll True)")

    print("\n-- Test 4: Adressierung target=C --")
    sid_c = "test-session-ccc"
    ev = post_as_halo_pro(sid_a, "reply", "Antwort an C", target=sid_c)
    sees_b = any(e["id"] == ev["id"] for e in get_unread(sid_b))
    sees_c = any(e["id"] == ev["id"] for e in get_unread(sid_c))
    print(f"  B sieht (nicht adressiert): {sees_b} (soll False)")
    print(f"  C sieht (adressiert): {sees_c} (soll True)")

    print("\n-- Test 5: target mit halo_pro_-Praefix --")
    ev = post("ext", "program", "info", "Zu C mit Praefix", target=f"halo_pro_{sid_c}")
    sees_c = any(e["id"] == ev["id"] for e in get_unread(sid_c))
    print(f"  C sieht (target=halo_pro_<sid>): {sees_c} (soll True)")

    print("\n-- Test 6: is_local --")
    ev_local = post("local_test", "program", "info", "lokal")
    print(f"  is_local lokal: {is_local(ev_local)} (soll True)")
    ev_extern = dict(ev_local, source_host="extern-pc-xyz")
    print(f"  is_local extern: {is_local(ev_extern)} (soll False)")

    print("\n=== Selbsttest fertig ===")
