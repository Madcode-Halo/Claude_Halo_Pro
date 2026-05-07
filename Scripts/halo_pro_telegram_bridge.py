# -*- coding: utf-8 -*-
"""
halo_pro_telegram_bridge.py — Halo_Pro Telegram Inbound-Daemon

Long-Polling Bridge zwischen Halo_Pro_Bot und Halo_Pro-Briefkasten.
Pure stdlib (urllib + json) — kein external dependency.

Loop:
  1. getUpdates?offset=<last>&timeout=25  (long poll, blockt bis Update)
  2. Pro Update:
     - Allowlist-Check (from.id muss == HALO_PRO_TG_USER_ID)
     - Photos/Documents -> Download in Vault/07 Anhaenge/telegram/<datum>/
     - Event in events.jsonl: halo_pro_inbox.post(kind="telegram", target=<owner>)
  3. Owner = Inhalt von Status/telegram_owner.json
     (vom halo_pro_telegram_hook beim ersten Prompt einer Session gesetzt)
     Kein Owner = Event mit target=None (Broadcast)

Token-Source:
  Default: halo_credentials.py --get telegram_pro (on-demand)
  Override: ENV HALO_PRO_TG_BOT_TOKEN

CLI:
  python halo_pro_telegram_bridge.py             # Daemon-Loop
  python halo_pro_telegram_bridge.py --once      # einmal getUpdates, dann Exit (Test)
  python halo_pro_telegram_bridge.py --status    # PID + Lockfile-Status
  python halo_pro_telegram_bridge.py --stop      # SIGTERM an PID aus PID-File
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from halo_pro_inbox import post  # noqa: E402

# --- Konfig ---------------------------------------------------------------
PYTHON_EXE = "D:/Anthropic_Claude/Programme/Python/python.exe"
CRED_SCRIPT = str(SCRIPT_DIR / "halo_credentials.py")
SERVICE_NAME = "telegram_pro"

USER_ID = int(os.environ.get("HALO_PRO_TG_USER_ID", "5996284268"))

# Allowlist: nur Mad. Schwester-Bot-Posts kommen ueber Halos User-API-Listener
# als pre-formatierte Events in unsere events.jsonl, nicht ueber diese Bot-Bridge.
# (L9 aus Halos Fuchsbau.Telegram-Plan, 2026-05-08 zurueckgerollt nachdem Listener live ist.)

POLL_TIMEOUT_S = 25       # long-poll: Telegram haelt Verbindung offen
HTTP_TIMEOUT_S = POLL_TIMEOUT_S + 10
RETRY_BASE_S = 2          # exponential backoff start
RETRY_CAP_S = 60          # max Retry-Wartezeit

LOG_FILE = ROOT / "Logs" / "telegram_bridge.log"
PID_FILE = ROOT / "Status" / "telegram_bridge.pid"
OFFSET_FILE = ROOT / "Status" / "telegram_offset.json"
OWNER_FILE = ROOT / "Status" / "telegram_owner.json"
INBOX_BASE = ROOT / "Vault" / "07 Anhänge" / "telegram"


# --- Token-Loading --------------------------------------------------------
_TOKEN_CACHE: str | None = None


def _get_token() -> str:
    """Bot-Token aus halo_credentials.py holen — Env-Override moeglich."""
    global _TOKEN_CACHE
    if _TOKEN_CACHE:
        return _TOKEN_CACHE
    env_token = os.environ.get("HALO_PRO_TG_BOT_TOKEN")
    if env_token:
        _TOKEN_CACHE = env_token
        return env_token
    r = subprocess.run(
        [PYTHON_EXE, CRED_SCRIPT, "--get", SERVICE_NAME],
        capture_output=True, text=True,
    )
    m = re.search(r'`([^`]+)`', r.stdout)
    if not m:
        sys.exit(
            f"Kein {SERVICE_NAME} Token. Setup:\n"
            f"  1. @BotFather /newbot -> Token holen\n"
            f"  2. python Scripts/halo_credentials.py --add {SERVICE_NAME} <TOKEN>"
        )
    _TOKEN_CACHE = m.group(1)
    return _TOKEN_CACHE


def _api_base() -> str:
    return f"https://api.telegram.org/bot{_get_token()}"


def _file_base() -> str:
    return f"https://api.telegram.org/file/bot{_get_token()}"


# --- Logging --------------------------------------------------------------
def _log(msg: str) -> None:
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    try:
        if sys.stdout:
            print(line, flush=True)
    except Exception:
        pass


# --- Owner / Offset State -------------------------------------------------
def _read_owner() -> dict | None:
    if not OWNER_FILE.exists():
        return None
    try:
        return json.loads(OWNER_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_offset() -> int:
    if not OFFSET_FILE.exists():
        return 0
    try:
        return int(json.loads(OFFSET_FILE.read_text(encoding="utf-8")).get("offset", 0))
    except Exception:
        return 0


def _write_offset(offset: int) -> None:
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_FILE.write_text(
        json.dumps({"offset": offset, "updated_at": datetime.now().isoformat()}),
        encoding="utf-8",
    )


# --- HTTP helpers ---------------------------------------------------------
def _api_get(method: str, params: dict | None = None, timeout: int = HTTP_TIMEOUT_S) -> dict:
    qs = ""
    if params:
        from urllib.parse import urlencode
        qs = "?" + urlencode(params)
    url = f"{_api_base()}/{method}{qs}"
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def _download(file_path: str, out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    url = f"{_file_base()}/{file_path}"
    urllib.request.urlretrieve(url, str(out))
    return out.stat().st_size


# --- Update processing ---------------------------------------------------
def _safe_filename(name: str) -> str:
    keep = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
    return keep[:120] or "file"


def _process_message(msg: dict) -> tuple[str, dict] | None:
    """Eingehende Telegram-Message -> (Payload-String, chat_meta-Dict).

    chat_meta enthaelt: chat_id, chat_type (private/group/supergroup/channel),
    chat_title (None bei private). Wird beim post() als extra-Feld geschrieben,
    damit Antworten an die richtige chat_id (Gruppe oder 1:1) gehen koennen.
    """
    frm = msg.get("from") or {}
    sender_id = frm.get("id")
    if sender_id != USER_ID:
        _log(f"SKIP fremder User: id={sender_id} username=@{frm.get('username')}")
        return None
    sender_label = "mad"

    chat = msg.get("chat") or {}
    chat_type = chat.get("type")

    # Bot-Bridge cover nur 1:1-DMs an Halo_Pro_Bot.
    # Group/Supergroup/Channel-Posts kommen exklusiv ueber Halos User-API-Listener
    # in unsere events.jsonl (Variante A). Ohne Skip wuerden Mad-Group-Posts
    # zweimal landen (einmal hier via getUpdates, einmal via Listener) — Doppel-Event-Rauschen.
    if chat_type != "private":
        _log(f"SKIP non-private chat: type={chat_type!r} chat_id={chat.get('id')!r} title={chat.get('title')!r} (Listener cover diese Domaene)")
        return None

    chat_meta = {
        "chat_id": chat.get("id"),
        "chat_type": chat_type,
        "chat_title": chat.get("title"),
        "sender_id": sender_id,
        "sender_label": sender_label,
        "sender_username": frm.get("username"),
        "sender_first_name": frm.get("first_name"),
    }

    date_dir = INBOX_BASE / datetime.now().strftime("%Y-%m-%d")
    msg_id = msg.get("message_id", "?")
    parts: list[str] = []
    if "text" in msg:
        parts.append(f"📝 {msg['text']}")

    # Photo (Telegram-komprimiert) — groesste Variante
    if "photo" in msg:
        biggest = msg["photo"][-1]
        try:
            info = _api_get("getFile", {"file_id": biggest["file_id"]})
            file_path = info["result"]["file_path"]
            ext = Path(file_path).suffix or ".jpg"
            out = date_dir / f"photo_{msg_id}_{int(time.time())}{ext}"
            size = _download(file_path, out)
            cap = msg.get("caption", "")
            cap_str = f" caption={cap!r}" if cap else ""
            parts.append(f"🖼️ Photo gespeichert: `{out.relative_to(ROOT).as_posix()}` ({size}B){cap_str}")
        except Exception as e:
            parts.append(f"🖼️ Photo FAIL: {e}")

    # Document (z.B. PDF)
    if "document" in msg:
        d = msg["document"]
        try:
            info = _api_get("getFile", {"file_id": d["file_id"]})
            file_path = info["result"]["file_path"]
            name = _safe_filename(d.get("file_name") or Path(file_path).name)
            out = date_dir / f"doc_{msg_id}_{name}"
            size = _download(file_path, out)
            parts.append(
                f"📎 Document gespeichert: `{out.relative_to(ROOT).as_posix()}` "
                f"({size}B, mime={d.get('mime_type', '?')})"
            )
        except Exception as e:
            parts.append(f"📎 Document FAIL: {e}")

    # Voice / Audio / Video — als unbekannt markieren (in Phase X ausbauen)
    for media_kind in ("voice", "audio", "video", "video_note", "sticker", "animation"):
        if media_kind in msg:
            parts.append(f"⚠️ {media_kind} empfangen — noch nicht implementiert")

    if not parts:
        return None
    return "\n".join(parts), chat_meta


def _process_updates(updates: list[dict]) -> int:
    """Verarbeitet Updates, schreibt Events. Returns max update_id (fuer offset)."""
    max_id = 0
    owner = _read_owner()  # bei jedem Batch frisch lesen
    target_sid = owner.get("session_id") if owner else None
    target_name = owner.get("name", "?") if owner else None

    for upd in updates:
        max_id = max(max_id, upd.get("update_id", 0))
        msg = upd.get("message") or upd.get("edited_message")
        if not msg:
            continue
        result = _process_message(msg)
        if not result:
            continue
        payload, chat_meta = result
        # Chat-Origin als Marker im Payload — sichtbar fuer Halo_Pro
        chat_type = chat_meta.get("chat_type") or "?"
        chat_title = chat_meta.get("chat_title")
        if chat_type == "private":
            origin_str = "[1:1]"
        else:
            origin_str = f"[{chat_type}:{chat_title!r}]" if chat_title else f"[{chat_type}]"
        # Sender-Marker damit ich im Event sehe ob Mad oder Schwester schreibt
        sender_str = f"[from:{chat_meta.get('sender_label') or '?'}]"
        # Owner-Routing
        if target_sid:
            payload = f"[an: {target_name}] {origin_str} {sender_str}\n{payload}"
        else:
            payload = f"[kein Owner gesetzt] {origin_str} {sender_str}\n{payload}"
        try:
            target_full = f"halo_pro_{target_sid}" if target_sid else None
            ev = post(
                source="telegram_bridge",
                kind="telegram",
                severity="info",
                payload=payload,
                target=target_full,
                chat_id=chat_meta.get("chat_id"),
                chat_type=chat_meta.get("chat_type"),
                chat_title=chat_meta.get("chat_title"),
                sender_id=chat_meta.get("sender_id"),
                sender_label=chat_meta.get("sender_label"),
                sender_username=chat_meta.get("sender_username"),
            )
            if ev:
                _log(f"event posted idx={ev['index']} target={target_full!r} chat_id={chat_meta.get('chat_id')!r} type={chat_type!r} sender={chat_meta.get('sender_label')!r}")
        except Exception as e:
            _log(f"post FAIL: {e}")
    return max_id


# --- Main loop -----------------------------------------------------------
def _write_pid() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _clear_pid() -> None:
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


def daemon_loop() -> None:
    _write_pid()
    _log(f"START pid={os.getpid()} bot=Halo_Pro_Bot user_id={USER_ID}")
    backoff = RETRY_BASE_S
    try:
        while True:
            offset = _read_offset()
            try:
                resp = _api_get("getUpdates", {
                    "offset": offset,
                    "timeout": POLL_TIMEOUT_S,
                    "allowed_updates": json.dumps(["message", "edited_message"]),
                })
                if not resp.get("ok"):
                    _log(f"API !ok: {resp}")
                    time.sleep(min(backoff, RETRY_CAP_S))
                    backoff = min(backoff * 2, RETRY_CAP_S)
                    continue
                backoff = RETRY_BASE_S
                updates = resp.get("result", [])
                if updates:
                    new_max = _process_updates(updates)
                    _write_offset(new_max + 1)
            except urllib.error.URLError as e:
                _log(f"NET err: {e} — backoff {backoff}s")
                time.sleep(min(backoff, RETRY_CAP_S))
                backoff = min(backoff * 2, RETRY_CAP_S)
            except KeyboardInterrupt:
                _log("KeyboardInterrupt — stopping")
                break
            except Exception as e:
                _log(f"loop err: {type(e).__name__}: {e}")
                time.sleep(min(backoff, RETRY_CAP_S))
                backoff = min(backoff * 2, RETRY_CAP_S)
    finally:
        _clear_pid()
        _log("STOP")


def status() -> None:
    if PID_FILE.exists():
        pid = PID_FILE.read_text(encoding="utf-8").strip()
        print(f"PID: {pid} ({PID_FILE})")
    else:
        print(f"PID: — (no {PID_FILE.name})")
    owner = _read_owner()
    if owner:
        print(f"Owner: {owner.get('name')} ({owner.get('session_id')[:16]}...) since {owner.get('since')}")
    else:
        print("Owner: — (kein Halo_Pro hat den Channel)")
    print(f"Offset: {_read_offset()}")


def stop() -> None:
    if not PID_FILE.exists():
        print("Kein PID-File — Daemon laeuft nicht")
        return
    pid = int(PID_FILE.read_text(encoding="utf-8").strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"SIGTERM an PID {pid} gesendet")
    except (ProcessLookupError, OSError) as e:
        print(f"PID {pid} nicht beendet: {e} — raeume PID-File auf")
        _clear_pid()


def once() -> None:
    """Einmaliger getUpdates-Pull, dann Exit (fuer Test)."""
    offset = _read_offset()
    resp = _api_get("getUpdates", {"offset": offset, "timeout": 1})
    updates = resp.get("result", [])
    print(f"updates: {len(updates)}")
    if updates:
        new_max = _process_updates(updates)
        _write_offset(new_max + 1)
        print(f"new offset: {new_max + 1}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--status":
            status()
        elif cmd == "--stop":
            stop()
        elif cmd == "--once":
            once()
        else:
            print(__doc__)
            sys.exit(1)
    else:
        daemon_loop()
