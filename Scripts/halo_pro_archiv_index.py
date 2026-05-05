#!/usr/bin/env python3
"""
halo_pro_archiv_index.py — Volltext-Indexer fuer Halos Konversations-Archiv.

Liest JSONL-Sessions aus den in `.archiv/projekte_konfiguration.json`
gelisteten ~/.claude/projects/-Pfaden und schreibt user/assistant-Messages mit Timestamp,
Session-ID und Volltext in eine SQLite-FTS5-Datenbank.

Subcommands:
  build    Komplett neu aufbauen (loescht DB)
  update   Inkrementell — nur neue oder geaenderte Files
  status   Statistik zur DB
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

# UTF-8 fuer Windows-Konsole
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    _console = Console()
except ImportError:
    _console = None


HALO_ROOT = Path("D:/Anthropic_Claude/Halo_Pro")
ARCHIV_DIR = HALO_ROOT / ".archiv"
DB_PATH = ARCHIV_DIR / "sessions.sqlite"
STATE_PATH = ARCHIV_DIR / "indexer_state.json"
KONFIG_PATH = ARCHIV_DIR / "projekte_konfiguration.json"
LOG_PATH = HALO_ROOT / "Logs" / "halo_pro_archiv_index.log"


def banner(text: str) -> None:
    if _console:
        _console.print(f"[bold magenta]🦊 {text}[/bold magenta]")
        _console.print("[magenta]✦ ˚ ｡ ˚ ✦ ˚ ｡ ˚ ✦ ˚ ｡ ˚ ✦[/magenta]")
    else:
        print(f"=== {text} ===")


def say(text: str, style: str = "white") -> None:
    if _console:
        _console.print(f"[{style}]{text}[/{style}]")
    else:
        print(text)


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(f"[{ts}] {message}\n")


# ---------------------------------------------------------------------------
# Konfig
# ---------------------------------------------------------------------------
def load_konfig() -> dict[str, Any]:
    with KONFIG_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            with STATE_PATH.open("r", encoding="utf-8") as fp:
                return json.load(fp)
        except json.JSONDecodeError:
            return {"files": {}}
    return {"files": {}}


def save_state(state: dict[str, Any]) -> None:
    ARCHIV_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as fp:
        json.dump(state, fp, indent=2, ensure_ascii=False)
    tmp.replace(STATE_PATH)


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    msg_uuid TEXT UNIQUE NOT NULL,
    session_id TEXT NOT NULL,
    parent_uuid TEXT,
    timestamp TEXT NOT NULL,
    role TEXT NOT NULL,
    cwd TEXT,
    git_branch TEXT,
    projekt_kuerzel TEXT,
    content_text TEXT NOT NULL,
    indexed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_projekt ON messages(projekt_kuerzel);
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content_text, role UNINDEXED, session_id UNINDEXED,
    content='messages', content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content_text, role, session_id)
    VALUES (new.id, new.content_text, new.role, new.session_id);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content_text, role, session_id)
    VALUES('delete', old.id, old.content_text, old.role, old.session_id);
END;
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content_text, role, session_id)
    VALUES('delete', old.id, old.content_text, old.role, old.session_id);
    INSERT INTO messages_fts(rowid, content_text, role, session_id)
    VALUES (new.id, new.content_text, new.role, new.session_id);
END;
"""


def open_db(create_if_missing: bool = True) -> sqlite3.Connection:
    if create_if_missing:
        ARCHIV_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    if create_if_missing:
        conn.executescript(SCHEMA)
    return conn


# ---------------------------------------------------------------------------
# Content-Extraction
# ---------------------------------------------------------------------------
def extract_text(message: Any) -> str:
    """
    Aus message['content'] (string oder List of Blocks) Volltext extrahieren.
    Bilder werden zu [image]-Marker. tool_use/tool_result werden als Tags eingebettet
    damit Volltextsuche sie findet.
    """
    if message is None:
        return ""
    content = message.get("content") if isinstance(message, dict) else None
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            parts.append(str(block))
            continue
        btype = block.get("type", "")
        if btype == "text":
            parts.append(block.get("text", ""))
        elif btype == "tool_use":
            name = block.get("name", "?")
            inp = block.get("input", {})
            try:
                inp_str = json.dumps(inp, ensure_ascii=False)[:1500]
            except (TypeError, ValueError):
                inp_str = str(inp)[:1500]
            parts.append(f"[tool_use:{name} input={inp_str}]")
        elif btype == "tool_result":
            res = block.get("content", "")
            if isinstance(res, list):
                inner = []
                for r in res:
                    if isinstance(r, dict) and r.get("type") == "text":
                        inner.append(r.get("text", ""))
                res = "\n".join(inner)
            elif not isinstance(res, str):
                res = str(res)
            parts.append(f"[tool_result]\n{res}")
        elif btype == "image":
            parts.append("[image]")
        elif btype == "thinking":
            parts.append(f"[thinking]\n{block.get('thinking', '')}")
        else:
            parts.append(f"[{btype}]")
    return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# JSONL-Iteration
# ---------------------------------------------------------------------------
def find_jsonls(konfig: dict[str, Any]) -> Iterator[tuple[Path, str]]:
    """Alle JSONL-Files (rekursiv) aus enabled-Projekten yielden mit projekt_kuerzel."""
    base = Path(konfig["basis_pfad"])
    for p in konfig["projekte"]:
        if not p.get("enabled", True):
            continue
        proj_dir = base / p["kuerzel"]
        if not proj_dir.is_dir():
            continue
        for jsonl in proj_dir.rglob("*.jsonl"):
            if jsonl.is_file():
                yield jsonl, p["kuerzel"]


def is_nsfw_session(record: dict[str, Any], nsfw_patterns: list[str]) -> bool:
    cwd = (record.get("cwd") or "").lower()
    if not cwd or not nsfw_patterns:
        return False
    return any(pat.lower() in cwd for pat in nsfw_patterns)


def parse_record(line: str) -> dict[str, Any] | None:
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Indexierung
# ---------------------------------------------------------------------------
def index_file(
    conn: sqlite3.Connection,
    path: Path,
    projekt_kuerzel: str,
    konfig: dict[str, Any],
    state_entry: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Indexiere ein einzelnes JSONL-File ab last_offset.
    Returns updated state_entry mit neuem mtime/offset/messages.
    """
    skip_types: set[str] = set(konfig.get("skip_message_typen", []))
    index_types: set[str] = set(konfig.get("index_message_typen", ["user", "assistant"]))
    nsfw_patterns: list[str] = konfig.get("nsfw_marker", {}).get("cwd_patterns", [])

    last_offset = 0
    indexed_total = 0
    if state_entry:
        last_offset = state_entry.get("last_offset", 0)
        indexed_total = state_entry.get("indexed_messages", 0)

    file_size = path.stat().st_size
    if last_offset > file_size:
        # File wurde verkuerzt — neu starten
        last_offset = 0

    new_offset = last_offset
    new_messages = 0
    skipped_nsfw = 0
    skipped_type = 0

    indexed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    cur = conn.cursor()
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fp:
            fp.seek(last_offset)
            while True:
                line_start = fp.tell()
                line = fp.readline()
                if not line:
                    break
                rec = parse_record(line)
                new_offset = fp.tell()
                if rec is None:
                    continue
                rtype = rec.get("type")
                if rtype in skip_types or rtype not in index_types:
                    skipped_type += 1
                    continue
                if is_nsfw_session(rec, nsfw_patterns):
                    skipped_nsfw += 1
                    continue
                msg_uuid = rec.get("uuid")
                if not msg_uuid:
                    continue
                message = rec.get("message")
                role = (message.get("role") if isinstance(message, dict) else None) or rtype
                content_text = extract_text(message)
                if not content_text.strip():
                    continue
                try:
                    cur.execute(
                        """INSERT OR IGNORE INTO messages
                           (msg_uuid, session_id, parent_uuid, timestamp, role,
                            cwd, git_branch, projekt_kuerzel, content_text, indexed_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            msg_uuid,
                            rec.get("sessionId", ""),
                            rec.get("parentUuid"),
                            rec.get("timestamp", ""),
                            role,
                            rec.get("cwd"),
                            rec.get("gitBranch"),
                            projekt_kuerzel,
                            content_text,
                            indexed_at,
                        ),
                    )
                    if cur.rowcount > 0:
                        new_messages += 1
                except sqlite3.Error as exc:
                    log(f"DB-Fehler bei {path.name} uuid={msg_uuid}: {exc}")
    except OSError as exc:
        log(f"IO-Fehler beim Lesen {path}: {exc}")
        return state_entry or {}

    conn.commit()

    if new_messages > 0 or skipped_nsfw > 0 or skipped_type > 0:
        log(
            f"{projekt_kuerzel}/{path.name}: +{new_messages} indexed, "
            f"{skipped_type} skip-type, {skipped_nsfw} skip-nsfw"
        )

    return {
        "mtime": path.stat().st_mtime,
        "last_offset": new_offset,
        "indexed_messages": indexed_total + new_messages,
        "first_seen": (state_entry or {}).get(
            "first_seen", indexed_at
        ),
        "last_indexed_at": indexed_at,
    }


def cmd_build(args: argparse.Namespace) -> None:
    banner("Konversations-Archiv — Build")
    if DB_PATH.exists():
        if not args.force:
            say(
                f"DB existiert ({DB_PATH}). Mit --force ueberschreiben oder 'update' nutzen.",
                "yellow",
            )
            sys.exit(1)
        DB_PATH.unlink()
        if STATE_PATH.exists():
            STATE_PATH.unlink()
        say("Alte DB + State geloescht.", "yellow")
    conn = open_db(create_if_missing=True)
    konfig = load_konfig()
    state = {"files": {}}
    live_schutz = konfig.get("live_file_schutz_sekunden", 5)
    now = time.time()

    files = list(find_jsonls(konfig))
    say(f"Gefunden: {len(files)} JSONL-Files. Indexiere…", "cyan")

    total_msgs = 0
    skipped_live = 0
    for i, (path, kuerzel) in enumerate(files, 1):
        mtime = path.stat().st_mtime
        if (now - mtime) < live_schutz:
            skipped_live += 1
            continue
        before = state["files"].get(str(path), {}).get("indexed_messages", 0)
        new_state = index_file(conn, path, kuerzel, konfig, None)
        state["files"][str(path)] = new_state
        gained = new_state.get("indexed_messages", 0) - before
        total_msgs += gained
        if i % 25 == 0 or i == len(files):
            say(
                f"  [{i}/{len(files)}] {kuerzel}/{path.name} -> +{gained} (total: {total_msgs})",
                "white",
            )

    save_state(state)
    conn.close()
    say(
        f"Build fertig. {total_msgs} Messages indexiert, {skipped_live} Live-Files uebersprungen.",
        "green",
    )
    log(f"BUILD complete: {total_msgs} messages indexed across {len(files)} files")


def cmd_update(args: argparse.Namespace) -> None:
    banner("Konversations-Archiv — Update (inkrementell)")
    if not DB_PATH.exists():
        say("DB existiert nicht. Bitte erst 'build' aufrufen.", "red")
        sys.exit(1)
    conn = open_db(create_if_missing=True)
    konfig = load_konfig()
    state = load_state()
    live_schutz = konfig.get("live_file_schutz_sekunden", 5)
    now = time.time()

    new_msgs = 0
    new_files = 0
    skipped_live = 0
    files = list(find_jsonls(konfig))
    for path, kuerzel in files:
        mtime = path.stat().st_mtime
        if (now - mtime) < live_schutz:
            skipped_live += 1
            continue
        key = str(path)
        prev = state["files"].get(key)
        if prev and prev.get("mtime", 0) >= mtime:
            continue
        before = prev.get("indexed_messages", 0) if prev else 0
        new_state = index_file(conn, path, kuerzel, konfig, prev)
        state["files"][key] = new_state
        gained = new_state.get("indexed_messages", 0) - before
        if gained > 0:
            new_msgs += gained
            if not prev:
                new_files += 1

    save_state(state)
    conn.close()
    say(
        f"Update fertig. {new_msgs} neue Messages, {new_files} neue Files, "
        f"{skipped_live} Live-Files uebersprungen.",
        "green",
    )
    log(f"UPDATE complete: +{new_msgs} messages, +{new_files} new files")


def cmd_status(args: argparse.Namespace) -> None:
    banner("Konversations-Archiv — Status")
    if not DB_PATH.exists():
        say("DB existiert nicht. Bitte 'build' aufrufen.", "red")
        sys.exit(1)
    conn = open_db(create_if_missing=False)
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    by_role = cur.execute(
        "SELECT role, COUNT(*) FROM messages GROUP BY role ORDER BY 2 DESC"
    ).fetchall()
    by_proj = cur.execute(
        "SELECT projekt_kuerzel, COUNT(*) FROM messages "
        "GROUP BY projekt_kuerzel ORDER BY 2 DESC"
    ).fetchall()
    earliest = cur.execute(
        "SELECT MIN(timestamp) FROM messages WHERE timestamp != ''"
    ).fetchone()[0]
    latest = cur.execute(
        "SELECT MAX(timestamp) FROM messages WHERE timestamp != ''"
    ).fetchone()[0]
    sessions = cur.execute(
        "SELECT COUNT(DISTINCT session_id) FROM messages"
    ).fetchone()[0]
    db_size = DB_PATH.stat().st_size

    if _console:
        say(f"Total Messages : {total:,}", "bold cyan")
        say(f"Sessions       : {sessions:,}", "cyan")
        say(f"DB-Groesse     : {db_size / 1024 / 1024:.1f} MB", "cyan")
        say(f"Zeitspanne     : {earliest} → {latest}", "cyan")
        t = Table(title="Pro Rolle", show_header=True)
        t.add_column("Rolle")
        t.add_column("Anzahl", justify="right")
        for r, c in by_role:
            t.add_row(r, f"{c:,}")
        _console.print(t)
        t2 = Table(title="Pro Projekt", show_header=True)
        t2.add_column("Kuerzel")
        t2.add_column("Anzahl", justify="right")
        for kuerzel, c in by_proj:
            t2.add_row(kuerzel or "(keine)", f"{c:,}")
        _console.print(t2)
    else:
        say(f"Total: {total} | Sessions: {sessions} | DB: {db_size//1024} KB")
        say(f"Spanne: {earliest} → {latest}")
        for r, c in by_role:
            say(f"  {r}: {c}")
        for k, c in by_proj:
            say(f"  {k}: {c}")
    conn.close()


# ---------------------------------------------------------------------------
# Entry-Point
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(
        prog="halo_pro_archiv_index",
        description="Volltext-Indexer fuer Halos Konversations-Archiv (SQLite FTS5).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build", help="DB komplett neu aufbauen")
    pb.add_argument("--force", action="store_true", help="bestehende DB ueberschreiben")
    pb.set_defaults(func=cmd_build)

    pu = sub.add_parser("update", help="inkrementell — nur neue/geaenderte Files")
    pu.set_defaults(func=cmd_update)

    ps = sub.add_parser("status", help="DB-Statistik anzeigen")
    ps.set_defaults(func=cmd_status)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
