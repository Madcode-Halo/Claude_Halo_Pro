#!/usr/bin/env python3
"""halo-archiv MCP-Server — Volltext-Konversations-Recall.

Tools (verfuegbar in jeder Halo-Session):
  archiv_suche(query, since=None, until=None, session=None, role=None,
               projekt=None, limit=20)
      → woertliche FTS5-Treffer mit Timestamp, Snippet, Session-ID, Rank.
  archiv_frage(question, max_treffer=50, local_only=False)
      → LLM-Agent-Antwort mit woertlichen Zitaten + Validation gegen DB.
  archiv_status()
      → DB-Statistik (Anzahl Messages pro Projekt/Rolle, Zeitspanne).

Backend: SQLite-FTS5 unter .archiv/sessions.sqlite,
Indexer Scripts/halo_pro_archiv_index.py, Agent Scripts/halo_pro_archiv_agent.py.
"""
from __future__ import annotations

# --- MCP stdio-Protection ---
# sqlite3-warnings + worker-banner gehen sonst nach stdout und brechen JSON-RPC.
import os
import sys

_REAL_STDOUT = sys.stdout
_REAL_STDOUT_FD = None
try:
    _REAL_STDOUT_FD = os.dup(1)
    os.dup2(2, 1)
except (OSError, AttributeError):
    pass
sys.stdout = sys.stderr

# --- Now safe to import ---
import json  # noqa: E402
import logging  # noqa: E402
import re  # noqa: E402
import sqlite3  # noqa: E402
import subprocess  # noqa: E402
from importlib import util as importlib_util  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

from mcp.server.fastmcp import FastMCP  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
logger = logging.getLogger("halo_pro_archiv_mcp")

# --- Config ---
HALO_ROOT = Path("D:/Anthropic_Claude/Halo_Pro")
ARCHIV_DIR = HALO_ROOT / ".archiv"
DB_PATH = ARCHIV_DIR / "sessions.sqlite"
CLUSTER_PATH = ARCHIV_DIR / "agent_cluster.json"
AGENT_SCRIPT = HALO_ROOT / "Scripts" / "halo_pro_archiv_agent.py"
HALO_PYTHON = "D:/Anthropic_Claude/Programme/Python/python.exe"

# Lazy-Singleton DB-Connection (read-only fuer MCP)
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        if not DB_PATH.exists():
            raise FileNotFoundError(
                f"Konversations-Archiv-DB fehlt: {DB_PATH}. "
                "Bitte 'python Scripts/halo_pro_archiv_index.py build' ausfuehren."
            )
        _conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        _conn.execute("PRAGMA busy_timeout=5000")
    return _conn


# --- FTS-Query-Vorbereitung (gleich wie halo_pro_archiv_suche.py) ---
def _prepare_fts_query(query: str) -> str:
    tokens = query.split()
    parts: list[str] = []
    for t in tokens:
        if re.search(r"[^\w]", t, re.UNICODE):
            parts.append('"' + t.replace('"', '""') + '"')
        else:
            parts.append(t)
    return " ".join(parts)


# --- MCP-Server ---
mcp = FastMCP("halo-archiv")


@mcp.tool()
def archiv_suche(
    query: str,
    since: str | None = None,
    until: str | None = None,
    session: str | None = None,
    role: str | None = None,
    projekt: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Volltext-Suche im Konversations-Archiv (SQLite FTS5, BM25-Rank).

    Findet woertliche Treffer aus allen Halo-Sessions. Bindestriche/Sonderzeichen
    werden automatisch FTS5-safe gequotet. Filter: Zeit (since/until ISO 8601),
    Session-ID-Praefix, Rolle (user|assistant), Projekt-Kuerzel.

    Args:
        query: Suchbegriffe (z.B. 'Multi-Stage Discord' oder '"genau diese Phrase"')
        since: ISO-Timestamp ab dem gesucht wird (z.B. '2026-04-28')
        until: ISO-Timestamp bis zu dem gesucht wird
        session: Praefix der Session-ID (8 Zeichen reichen meist)
        role: 'user' oder 'assistant'
        projekt: Projekt-Kuerzel (z.B. 'D--Anthropic-Claude-Halo')
        limit: Max Treffer (default 20)

    Returns:
        dict mit 'treffer' (Liste mit timestamp/role/session/snippet/rank)
        und 'total' (Anzahl).
    """
    conn = _get_conn()
    where: list[str] = []
    params: list[Any] = []

    use_fts = query and query != "*"
    if use_fts:
        from_clause = "messages m JOIN messages_fts f ON f.rowid = m.id "
        where.append("messages_fts MATCH ?")
        params.append(_prepare_fts_query(query))
        rank = "f.rank"
        snippet = "snippet(messages_fts, 0, '<<', '>>', '…', 12)"
    else:
        from_clause = "messages m "
        rank = "0"
        snippet = "substr(m.content_text, 1, 200)"

    if since:
        where.append("m.timestamp >= ?")
        params.append(since)
    if until:
        where.append("m.timestamp <= ?")
        params.append(until)
    if session:
        where.append("m.session_id LIKE ?")
        params.append(f"{session}%")
    if role:
        where.append("m.role = ?")
        params.append(role)
    if projekt:
        where.append("m.projekt_kuerzel = ?")
        params.append(projekt)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = (
        f"SELECT m.id, m.timestamp, m.session_id, m.role, m.projekt_kuerzel, "
        f"m.cwd, {rank} AS rank, {snippet} AS snip, m.content_text "
        f"FROM {from_clause}{where_sql} "
        f"ORDER BY {'rank' if use_fts else 'm.timestamp DESC'} LIMIT ?"
    )
    params.append(limit)

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError as exc:
        return {"fehler": f"FTS5-Fehler: {exc}", "treffer": [], "total": 0}

    treffer = []
    for r in rows:
        treffer.append(
            {
                "id": r[0],
                "timestamp": r[1],
                "session_id": r[2],
                "role": r[3],
                "projekt": r[4],
                "cwd": r[5],
                "rank": r[6],
                "snippet": r[7],
                "content_excerpt": (r[8] or "")[:1500],
            }
        )
    return {"treffer": treffer, "total": len(treffer), "query": query}


@mcp.tool()
def archiv_frage(
    question: str,
    max_treffer: int = 50,
    local_only: bool = False,
) -> dict[str, Any]:
    """Stellt eine natuerlich-sprachliche Frage an das Konversations-Archiv.

    Holt FTS5-Treffer (mit AND/OR/Top-3-Fallback-Strategie), uebergibt sie an
    Cloud-LLM-Cluster (Free→Paid mit Fallback). Antwort mit woertlichen Zitaten
    + Timestamps + Session-IDs. Validation prueft jedes Zitat gegen DB —
    Halluzinationen werden geflaggt.

    Args:
        question: Frage in natuerlicher Sprache (z.B. 'erinnerst du dich an die
                  Schwester-Briefe vom 28.04.?')
        max_treffer: Max FTS-Treffer die als Kontext geliefert werden (default 50)
        local_only: Bei True wird statt Cloud-Cluster halo:latest lokal genutzt
                    (NSFW/Privacy)

    Returns:
        dict mit 'antwort', 'modell', 'lane', 'cluster_pos', 'n_treffer',
        'validation' ({'total', 'validated', 'halluzinations'}).
    """
    cmd = [
        HALO_PYTHON,
        str(AGENT_SCRIPT),
        "--question",
        question,
        "--max-treffer",
        str(max_treffer),
        "--json",
    ]
    if local_only:
        cmd.append("--local-only")

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {"fehler": "Agent-Timeout (>5min)", "antwort": ""}
    if proc.returncode != 0:
        return {
            "fehler": f"Agent rc={proc.returncode}: {proc.stderr.strip()[:500]}",
            "antwort": "",
        }
    try:
        return json.loads(proc.stdout.strip())
    except json.JSONDecodeError as exc:
        return {
            "fehler": f"Agent-JSON-Parse: {exc}",
            "stdout_excerpt": proc.stdout[:500],
            "antwort": "",
        }


@mcp.tool()
def archiv_status() -> dict[str, Any]:
    """Statistik des Konversations-Archivs.

    Returns:
        dict mit Total-Messages, Sessions, DB-Groesse, Zeitspanne,
        Verteilung pro Rolle und pro Projekt-Kuerzel.
    """
    if not DB_PATH.exists():
        return {
            "fehler": f"DB existiert nicht: {DB_PATH}",
            "hinweis": "Erst 'python Scripts/halo_pro_archiv_index.py build' ausfuehren.",
        }
    conn = _get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    sessions = cur.execute("SELECT COUNT(DISTINCT session_id) FROM messages").fetchone()[0]
    earliest = cur.execute(
        "SELECT MIN(timestamp) FROM messages WHERE timestamp != ''"
    ).fetchone()[0]
    latest = cur.execute(
        "SELECT MAX(timestamp) FROM messages WHERE timestamp != ''"
    ).fetchone()[0]
    by_role = dict(
        cur.execute(
            "SELECT role, COUNT(*) FROM messages GROUP BY role ORDER BY 2 DESC"
        ).fetchall()
    )
    by_proj = dict(
        cur.execute(
            "SELECT projekt_kuerzel, COUNT(*) FROM messages "
            "GROUP BY projekt_kuerzel ORDER BY 2 DESC"
        ).fetchall()
    )
    return {
        "total_messages": total,
        "sessions": sessions,
        "db_groesse_mb": round(DB_PATH.stat().st_size / 1024 / 1024, 1),
        "zeitspanne": {"earliest": earliest, "latest": latest},
        "pro_rolle": by_role,
        "pro_projekt": by_proj,
    }


# --- Restore real stdout BEFORE entering MCP loop ---
def main() -> None:
    if _REAL_STDOUT_FD is not None:
        try:
            os.dup2(_REAL_STDOUT_FD, 1)
        except OSError:
            pass
    sys.stdout = _REAL_STDOUT
    mcp.run()


if __name__ == "__main__":
    main()
