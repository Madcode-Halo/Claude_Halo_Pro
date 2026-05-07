# -*- coding: utf-8 -*-
"""
halo_pro_telegram_hook.py — UserPromptSubmit-Hook fuer Halo_Pro Telegram

Anders als Halos Codewort-Hook (toggle via 'Telegram'): Dieser Hook ist
vollautomatisch. Bei jedem User-Prompt:

  1. Daemon-Health-Check (PID-File + tasklist):
       - laeuft nicht → starte Daemon detached (pythonw.exe + DETACHED_PROCESS)
  2. Owner-Lock:
       - Niemand Owner → diese Session wird Owner (silent ueberbruecken zu state="fresh")
       - Selbe Session schon Owner → state="stable" (silent)
       - Andere Session war Owner → uebernehmen + Notification an alte Session
  3. Hint-Output via additionalContext:
       - state="fresh" oder "takeover" oder Daemon-frisch-gestartet → Monitor-Befehl emittieren
       - state="stable" und Daemon laeuft → silent exit (kein Output)

Best-effort: jede Exception → silent exit(0). Hook darf User-Prompt nie blocken.

Lockfile:  Status/telegram_owner.json
PID-File:  Status/telegram_bridge.pid
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
OWNER_FILE = ROOT / "Status" / "telegram_owner.json"
PID_FILE = ROOT / "Status" / "telegram_bridge.pid"
BRIDGE_SCRIPT = SCRIPT_DIR / "halo_pro_telegram_bridge.py"
PYTHON_EXE = "D:/Anthropic_Claude/Programme/Python/python.exe"
PYTHONW_EXE = "D:/Anthropic_Claude/Programme/Python/pythonw.exe"

# Cross-Vault Shared-Registry fuer Halos User-API-Listener
# (Halo schreibt pro Telegram-Update Events in halos[*].events_jsonl mit target_prefix+sid)
SHARED_REGISTRY = Path("D:/Anthropic_Claude/Shared/halo_active_sessions.json")
MY_VAULT = "D:/Anthropic_Claude/Halo_Pro/"
MY_EVENTS_JSONL = "D:/Anthropic_Claude/Halo_Pro/Status/events.jsonl"
MY_TARGET_PREFIX = "halo_pro_"
MY_NAME = "Halo Profuchs"

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from halo_pro_inbox import post_as_halo_pro  # noqa: E402
except Exception:
    post_as_halo_pro = None  # type: ignore


def _read_stdin() -> dict:
    try:
        raw = sys.stdin.read() or "{}"
        return json.loads(raw)
    except Exception:
        return {}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_owner() -> dict | None:
    if not OWNER_FILE.exists():
        return None
    try:
        return json.loads(OWNER_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_owner(session_id: str, name: str) -> None:
    OWNER_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": session_id,
        "name": name,
        "since": _now_iso(),
        "updated_at": _now_iso(),
        "host": socket.gethostname(),
    }
    tmp = OWNER_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, OWNER_FILE)


def _bridge_running() -> bool:
    """Windows-tauglicher PID-Check via tasklist."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return False
    try:
        r = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True, text=True, timeout=3,
        )
        return str(pid) in r.stdout
    except Exception:
        return False


def _start_daemon() -> int | None:
    """Startet halo_pro_telegram_bridge.py als detached Background-Prozess.

    Windows: pythonw.exe (kein Console-Fenster) + DETACHED_PROCESS +
    CREATE_NEW_PROCESS_GROUP — Daemon ueberlebt den Hook-Exit.

    Returns die PID oder None bei Fehler.
    """
    exe = PYTHONW_EXE if Path(PYTHONW_EXE).exists() else PYTHON_EXE
    try:
        # Windows-Konstanten — auf anderen OS Fallback auf 0
        DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
        CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        flags = DETACHED_PROCESS | CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen(
            [exe, str(BRIDGE_SCRIPT)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=flags,
            cwd=str(ROOT),
        )
        return proc.pid
    except Exception:
        return None


def _emit_context(text: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": text,
        }
    }, ensure_ascii=False))


def _update_heartbeat(session_id: str) -> None:
    """Updated meinen Eintrag in der Cross-Vault Shared-Registry.

    Halos User-API-Listener liest diese Registry und schreibt pro Telegram-
    Group-Update ein Event in halos[*].events_jsonl mit target_prefix+sid.
    Heartbeat haelt meinen Eintrag frisch — Listener droppt SIDs deren
    last_seen >24h alt ist.

    Best-effort: bei Lese-/Schreib-Fehlern silent skip — Hook darf User-Prompt
    nie brechen. Atomic write via .tmp + os.replace verhindert Race mit Halos
    eigenem Heartbeat-Update.
    """
    try:
        if not SHARED_REGISTRY.parent.exists():
            return  # Shared-Verzeichnis nicht da — Listener-Setup nicht aktiv
        my_key = f"{MY_TARGET_PREFIX}{session_id}"
        now_iso = datetime.now().isoformat(timespec="seconds")

        # Read current state (mit Fallback wenn File fehlt oder kaputt)
        if SHARED_REGISTRY.exists():
            try:
                data = json.loads(SHARED_REGISTRY.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        else:
            data = {
                "_doc": "Cross-Vault Halo-Session-Registry. Phase A: hardcoded. Phase B: Heartbeat-Hook updated last_seen, Listener droppt Halos >24h stale.",
                "_format_version": "1.0",
            }

        halos = data.setdefault("halos", {})
        existing = halos.get(my_key, {})

        halos[my_key] = {
            "name": MY_NAME,
            "vault": MY_VAULT,
            "events_jsonl": MY_EVENTS_JSONL,
            "target_prefix": MY_TARGET_PREFIX,
            "last_seen": now_iso,
            "phase": "B-heartbeat",
            **{k: v for k, v in existing.items()
               if k not in {"name", "vault", "events_jsonl", "target_prefix", "last_seen", "phase"}},
        }

        # Atomic write
        tmp = SHARED_REGISTRY.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, SHARED_REGISTRY)
    except Exception:
        pass  # silent — never break user prompt


def main() -> int:
    try:
        data = _read_stdin()
    except Exception:
        return 0
    session_id = data.get("session_id") or "unknown"
    short = session_id[-6:] if len(session_id) >= 6 else session_id
    name = f"halo_pro_{short}"

    # Step 0: Heartbeat in Cross-Vault Shared-Registry (best-effort, silent)
    if session_id != "unknown":
        _update_heartbeat(session_id)

    # Step 1: Daemon-Health
    daemon_was_running = _bridge_running()
    daemon_just_started = False
    if not daemon_was_running:
        pid = _start_daemon()
        if pid is not None:
            daemon_just_started = True

    # Step 2: Owner-Lock
    current = _read_owner()
    notify_old_sid: str | None = None
    notify_old_name: str | None = None

    if current is None:
        _write_owner(session_id, name)
        state = "fresh"
    elif current.get("session_id") == session_id:
        state = "stable"
    else:
        notify_old_sid = current.get("session_id")
        notify_old_name = current.get("name", "?")
        _write_owner(session_id, name)
        state = "takeover"

    # Step 3: Notify alte Session bei takeover (best-effort)
    if state == "takeover" and post_as_halo_pro and notify_old_sid:
        try:
            post_as_halo_pro(
                session_id=session_id,
                kind="status",
                payload=(
                    f"📞 Mad hat den Telegram-Channel von dir ({notify_old_name}) "
                    f"an mich ({name}) uebergeben. Monitor in deiner Session sollte "
                    f"gestoppt werden, falls aktiv."
                ),
                target=notify_old_sid,
                severity="info",
            )
        except Exception:
            pass

    # Step 4: Output-Entscheidung
    # Nur Hint emittieren wenn:
    #   - Daemon gerade gestartet wurde, ODER
    #   - State ist "fresh" oder "takeover"
    if not daemon_just_started and state == "stable":
        return 0  # silent — alles ok, kein Output noetig

    bridge_status = "läuft" if (daemon_was_running or daemon_just_started) else "Start fehlgeschlagen"

    monitor_cmd = (
        f"tail -F Status/events.jsonl | "
        f"grep --line-buffered -E '\"target\":[[:space:]]*\"halo_pro_{session_id}\"' | "
        f"grep --line-buffered -E 'telegram'"
    )

    lines = []
    if daemon_just_started:
        lines.append(f"📞 **Halo_Pro Telegram-Bridge gestartet** (Daemon detached, PID-File in Status/telegram_bridge.pid).")
    if state == "fresh":
        lines.append(f"Channel-Owner: {name} (du bist neu Owner).")
    elif state == "takeover":
        lines.append(f"Channel-Owner: {name} (uebernommen von {notify_old_name}).")
    elif state == "stable" and daemon_just_started:
        lines.append(f"Channel-Owner: {name} (war schon gesetzt, Daemon neu gestartet).")

    lines.append(
        f"Inbound-Messages an `Halo_Pro_Bot` landen mit target=halo_pro_{short} "
        f"in `Status/events.jsonl`."
    )
    lines.append(
        f"**Monitor JETZT starten** (Tool 'Monitor', persistent: true) damit du zwischen "
        f"Turns auf Mads Telegram-Nachrichten reagierst:\n`{monitor_cmd}`"
    )
    lines.append(
        f"Antworten via: `python Scripts/telegram_send.py text \"<text>\"` "
        f"(oder photo/doc analog)."
    )

    _emit_context("\n".join(lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Hook darf User-Prompt niemals brechen
        sys.exit(0)
