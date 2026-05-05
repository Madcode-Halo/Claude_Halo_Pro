#!/usr/bin/env python3
"""
halo_pro_archiv_suche.py — Volltext-CLI-Suche im Konversations-Archiv.

Sucht in der von halo_pro_archiv_index.py gepflegten SQLite-FTS5-DB. Liefert
woertliche Treffer mit Timestamp, Session-Kuerzel und BM25-Rank. Filter:
Zeit, Rolle, Session, Projekt.

Beispiele:
  halo_pro_archiv_suche.py "Multi-Stage Discord Lese-Freigabe"
  halo_pro_archiv_suche.py "Schwester" --since 2026-04-28 --until 2026-04-29
  halo_pro_archiv_suche.py "1, 2, 3" --role user --limit 5
  halo_pro_archiv_suche.py "*" --session 3a606d23 --format json
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    _console = Console()
except ImportError:
    _console = None


HALO_ROOT = Path("D:/Anthropic_Claude/Halo_Pro")
DB_PATH = HALO_ROOT / ".archiv" / "sessions.sqlite"


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


# ---------------------------------------------------------------------------
# Query-Bau
# ---------------------------------------------------------------------------
def prepare_fts_query(query: str, raw: bool = False) -> str:
    """
    Macht User-Input FTS5-sicher: Tokens mit Sonderzeichen (Bindestrich,
    Punkt, Slash etc.) werden als Phrase-Quotes gewrappt — sonst liest FTS5
    sie als Boolean-Operatoren oder Spaltennamen.

    --raw skipped das Wrapping fuer FTS5-Power-User (AND/OR/NEAR/Phrase manuell).
    """
    if raw:
        return query
    tokens = query.split()
    parts: list[str] = []
    for t in tokens:
        if re.search(r"[^\w]", t, re.UNICODE):
            t_esc = t.replace('"', '""')
            parts.append(f'"{t_esc}"')
        else:
            parts.append(t)
    return " ".join(parts)



def build_sql(args: argparse.Namespace) -> tuple[str, list[Any]]:
    """
    Baut die SQL-Query mit FTS5 + Filter-WHERE-Clauses.
    Returns (sql, params).
    """
    where: list[str] = []
    params: list[Any] = []

    # FTS5-Match — bei "*" alle Messages
    use_fts = args.query and args.query != "*"
    if use_fts:
        from_clause = (
            "messages m JOIN messages_fts f ON f.rowid = m.id "
        )
        where.append("messages_fts MATCH ?")
        params.append(prepare_fts_query(args.query, raw=args.raw))
        rank = "f.rank"
    else:
        from_clause = "messages m "
        rank = "0"

    if args.since:
        where.append("m.timestamp >= ?")
        params.append(args.since)
    if args.until:
        where.append("m.timestamp <= ?")
        params.append(args.until)
    if args.session:
        where.append("m.session_id LIKE ?")
        params.append(f"{args.session}%")
    if args.role:
        where.append("m.role = ?")
        params.append(args.role)
    if args.projekt:
        where.append("m.projekt_kuerzel = ?")
        params.append(args.projekt)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    if use_fts:
        snippet = "snippet(messages_fts, 0, '<<', '>>', '…', 12)"
    else:
        snippet = "substr(m.content_text, 1, 200)"

    select = (
        f"SELECT m.id, m.timestamp, m.session_id, m.role, "
        f"m.projekt_kuerzel, m.cwd, {rank} AS rank, {snippet} AS snip, "
        f"m.content_text "
        f"FROM {from_clause}{where_sql} "
        f"ORDER BY {'rank' if use_fts else 'm.timestamp DESC'} "
        f"LIMIT ?"
    )
    params.append(args.limit)
    return select, params


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def format_pretty(rows: list[tuple]) -> None:
    if not rows:
        say("Keine Treffer.", "yellow")
        return
    if not _console:
        for r in rows:
            print(f"{r[1]} | {r[3]:9s} | {r[2][:8]} | {r[4]} | {r[7]}")
        return

    t = Table(show_header=True, header_style="bold magenta", expand=True)
    t.add_column("Datum/Zeit", style="cyan", no_wrap=True)
    t.add_column("Rolle", style="green", width=9)
    t.add_column("Session", style="yellow", width=8)
    t.add_column("Projekt", style="blue", width=18)
    t.add_column("Snippet", style="white", overflow="fold")

    for _id, ts, sid, role, kuerzel, cwd, rank, snip, full in rows:
        ts_short = ts[:19].replace("T", " ") if ts else ""
        proj_short = (kuerzel or "")[:18]
        # Highlight FTS-snippet-Marker
        if "<<" in (snip or ""):
            text = Text()
            for chunk in (snip or "").split("<<"):
                if ">>" in chunk:
                    hi, rest = chunk.split(">>", 1)
                    text.append(hi, style="bold yellow on black")
                    text.append(rest)
                else:
                    text.append(chunk)
        else:
            text = Text(snip or "")
        t.add_row(ts_short, role, sid[:8] if sid else "", proj_short, text)

    _console.print(t)


def format_json(rows: list[tuple]) -> None:
    out = []
    for _id, ts, sid, role, kuerzel, cwd, rank, snip, full in rows:
        out.append(
            {
                "timestamp": ts,
                "session_id": sid,
                "role": role,
                "projekt_kuerzel": kuerzel,
                "cwd": cwd,
                "rank": rank,
                "snippet": snip,
                "content_text": full,
            }
        )
    print(json.dumps(out, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(
        prog="halo_pro_archiv_suche",
        description="Volltext-Suche im Halo-Konversations-Archiv (SQLite FTS5).",
    )
    p.add_argument("query", help="FTS5-Query (Phrase in Gänsefüßchen, AND/OR/NEAR, oder '*' für alle)")
    p.add_argument("--since", help="Timestamp-Start (ISO 8601, z.B. 2026-04-28)")
    p.add_argument("--until", help="Timestamp-Ende (ISO 8601)")
    p.add_argument("--session", help="Session-ID-Praefix")
    p.add_argument("--role", choices=["user", "assistant"], help="nur Rolle")
    p.add_argument("--projekt", help="nur Projekt-Kuerzel (z.B. D--Anthropic-Claude-Halo)")
    p.add_argument("--limit", type=int, default=20, help="max Treffer (default 20)")
    p.add_argument("--format", choices=["pretty", "json"], default="pretty")
    p.add_argument("--no-banner", action="store_true", help="Banner unterdruecken (fuer Pipes)")
    p.add_argument(
        "--raw",
        action="store_true",
        help="Query ungewrappt an FTS5 (fuer Boolean/Phrase/NEAR-Syntax)",
    )
    args = p.parse_args()

    if not DB_PATH.exists():
        say(f"DB nicht gefunden: {DB_PATH}. Bitte erst 'halo_pro_archiv_index.py build'.", "red")
        sys.exit(1)

    if args.format == "pretty" and not args.no_banner:
        banner(f"Suche: {args.query!r}")

    sql, params = build_sql(args)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA busy_timeout=5000")
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
    except sqlite3.OperationalError as exc:
        say(f"FTS5-Fehler: {exc}", "red")
        sys.exit(2)
    finally:
        conn.close()

    if args.format == "json":
        format_json(rows)
    else:
        format_pretty(rows)
        if rows and not args.no_banner:
            say(f"\n{len(rows)} Treffer.", "bold green")


if __name__ == "__main__":
    main()
