#!/usr/bin/env python3
"""
halo_pro_archiv_agent.py — LLM-Agent fuers Konversations-Archiv.

Workflow:
  1. FTS5-Treffer aus sessions.sqlite holen
  2. System+User-Prompt mit woertlichen Treffern bauen
  3. Cluster aus agent_cluster.json durchiterieren (Free→Paid mit Fallback)
  4. Antwort gegen DB validieren — Zitate die nicht in messages stehen werden geflaggt
  5. --local-only erzwingt Ollama (halo:latest) fuer NSFW/Privacy

Beispiel:
  halo_pro_archiv_agent.py --question "erinnerst du dich an die Schwester-Briefe vom 28.04.?"
  halo_pro_archiv_agent.py --question "was hat Mad zu Multi-Stage gesagt?" --max-treffer 30
  halo_pro_archiv_agent.py --question "..." --local-only
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from importlib import util as importlib_util
from pathlib import Path
from typing import Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    _console = Console()
except ImportError:
    _console = None


HALO_ROOT = Path("D:/Anthropic_Claude/Halo_Pro")
ARCHIV_DIR = HALO_ROOT / ".archiv"
DB_PATH = ARCHIV_DIR / "sessions.sqlite"
CLUSTER_PATH = ARCHIV_DIR / "agent_cluster.json"

# halo_worker via dynamic import (Filename hat keinen Modul-Konflikt mit stdlib)
WORKER_PATH = HALO_ROOT / "Scripts" / "halo_worker.py"


def _load_worker():
    spec = importlib_util.spec_from_file_location("halo_worker", WORKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Kann halo_worker nicht laden: {WORKER_PATH}")
    mod = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def banner(text: str) -> None:
    if _console:
        _console.print(f"[bold magenta]🦊 H a l o Archiv-Agent · {text} 🦊[/bold magenta]")
        _console.print("[magenta]✦ ˚ ｡ ˚ ✦ ˚ ｡ ˚ ✦ ˚ ｡ ˚ ✦[/magenta]")
    else:
        print(f"=== {text} ===")


def say(text: str, style: str = "white") -> None:
    if _console:
        _console.print(f"[{style}]{text}[/{style}]")
    else:
        print(text)


# ---------------------------------------------------------------------------
# Treffer holen
# ---------------------------------------------------------------------------
def prepare_fts_query(query: str) -> str:
    tokens = query.split()
    parts: list[str] = []
    for t in tokens:
        if re.search(r"[^\w]", t, re.UNICODE):
            parts.append('"' + t.replace('"', '""') + '"')
        else:
            parts.append(t)
    return " ".join(parts)


_STOP = {
    "der", "die", "das", "ein", "eine", "und", "oder", "aber", "ist",
    "war", "sind", "waren", "haben", "hatte", "hatten", "wir", "ich",
    "du", "er", "sie", "es", "mit", "von", "zu", "fuer", "für", "auf",
    "in", "an", "im", "am", "den", "dem", "des", "wie", "was", "wer",
    "wann", "warum", "weshalb", "weil", "denn", "doch", "noch", "schon",
    "kann", "kannst", "konnten", "wuerde", "würde", "soll", "sollte",
    "erinnerst", "erinnere", "erinnern", "dich", "mich", "uns", "euch",
    "zwischen", "vom", "vor", "nach", "bei", "ueber", "über", "gibt",
    "the", "a", "an", "and", "or", "but", "is", "was", "be", "do", "did",
}


def extract_keywords(question: str) -> list[str]:
    """Bindestriche/Underscores/Slashes -> Space, dann Tokens >=3 Zeichen ohne Stopwords."""
    cleaned = re.sub(r"[-_/]", " ", question.lower())
    tokens = re.findall(r"[\wäöüÄÖÜß.]{3,}", cleaned)
    keep = [t for t in tokens if t not in _STOP]
    return keep if keep else tokens


def fts_and_query(tokens: list[str]) -> str:
    return prepare_fts_query(" ".join(tokens))


def fts_or_query(tokens: list[str]) -> str:
    parts: list[str] = []
    for t in tokens:
        if re.search(r"[^\w]", t, re.UNICODE):
            parts.append('"' + t.replace('"', '""') + '"')
        else:
            parts.append(t)
    return " OR ".join(parts)


def fetch_hits(question: str, max_treffer: int) -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        say(f"DB fehlt ({DB_PATH}). Bitte erst halo_pro_archiv_index.py build.", "red")
        sys.exit(1)
    keywords = extract_keywords(question)
    if not keywords:
        say("Keine sinnvollen Suchwoerter aus der Frage extrahiert.", "yellow")
        return []
    sql = (
        "SELECT m.id, m.timestamp, m.session_id, m.role, m.projekt_kuerzel, "
        "m.content_text, f.rank "
        "FROM messages m JOIN messages_fts f ON f.rowid = m.id "
        "WHERE messages_fts MATCH ? "
        "ORDER BY f.rank LIMIT ?"
    )

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA busy_timeout=5000")
    cur = conn.cursor()

    rows: list[tuple] = []
    used_strategy = ""
    try:
        # Strategy 1: AND mit allen Keywords
        q_and = fts_and_query(keywords)
        rows = cur.execute(sql, (q_and, max_treffer)).fetchall()
        used_strategy = f"AND({len(keywords)})"

        # Strategy 2: OR mit allen Keywords
        if not rows:
            q_or = fts_or_query(keywords)
            rows = cur.execute(sql, (q_or, max_treffer)).fetchall()
            used_strategy = f"OR({len(keywords)})"

        # Strategy 3: OR mit den 3 längsten Keywords (seltenste/distinktivste)
        if not rows and len(keywords) > 3:
            top = sorted(keywords, key=len, reverse=True)[:3]
            q_top = fts_or_query(top)
            rows = cur.execute(sql, (q_top, max_treffer)).fetchall()
            used_strategy = f"OR-top3({top})"
    except sqlite3.OperationalError as exc:
        say(f"FTS5-Fehler: {exc}", "red")
        sys.exit(2)
    finally:
        conn.close()

    if rows:
        say(f"  ↳ Such-Strategie: {used_strategy}", "cyan")

    hits = []
    for r in rows:
        hits.append(
            {
                "id": r[0],
                "timestamp": r[1],
                "session_id": r[2],
                "role": r[3],
                "projekt": r[4],
                "content": r[5],
                "rank": r[6],
            }
        )
    return hits


# ---------------------------------------------------------------------------
# Prompt-Bau
# ---------------------------------------------------------------------------
def truncate(text: str, max_chars: int = 1500) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + " […gekuerzt…]"


def build_prompt(question: str, hits: list[dict[str, Any]], system_prompt: str) -> str:
    lines = [
        f"Mads Frage: {question}",
        "",
        f"Gefundene Treffer aus dem Archiv (sortiert nach Relevanz, {len(hits)} Stueck):",
        "",
    ]
    for i, h in enumerate(hits, 1):
        ts = h["timestamp"][:19].replace("T", " ") if h["timestamp"] else "?"
        sid = (h["session_id"] or "")[:8]
        proj = h["projekt"] or "?"
        role = h["role"]
        body = truncate(h["content"], 1500)
        lines.append(f"--- Treffer #{i} | {ts} | {role} | session={sid} | projekt={proj} ---")
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cluster-Loop
# ---------------------------------------------------------------------------
def call_cluster(
    cluster: list[dict[str, Any]],
    system: str,
    prompt: str,
    worker,
) -> dict[str, Any]:
    """Iteriert Cluster, faengt Per-Modell-Fehler. ENV-Var muss VOR Worker-
    Import gesetzt sein — siehe main(). Mads Logik: nimm naechsten CLOUD-Alias
    statt internem OpenRouter→Ollama-Fallback."""
    last_error: str = ""
    for entry in cluster:
        alias = entry["alias"]
        say(f"[Cluster Pos {entry['pos']}] versuche {alias} ({entry['tier']})…", "cyan")
        try:
            res = worker.dispatch(alias, prompt, system)
            res["cluster_pos"] = entry["pos"]
            res["cluster_alias"] = alias
            return res
        except worker.RateLimited as e:
            last_error = f"{alias}: 429 ({e})"
            say(f"  ↳ rate-limited, naechster…", "yellow")
        except worker.NoCredentials as e:
            last_error = f"{alias}: keine Credentials ({e})"
            say(f"  ↳ keine Credentials, naechster…", "yellow")
        except worker.WorkerError as e:
            last_error = f"{alias}: {e}"
            say(f"  ↳ Fehler: {e}", "yellow")
    say(f"Alle Cluster-Modelle gescheitert. Letzter Fehler: {last_error}", "red")
    sys.exit(3)


def call_local_only(local_alias: str, system: str, prompt: str, worker) -> dict[str, Any]:
    """NSFW/Privacy-Pfad: zwingt Ollama-Lane."""
    say(f"[--local-only] erzwinge Ollama: {local_alias}", "cyan")
    os.environ["HALO_WORKER_LANE"] = "ollama"
    res = worker.dispatch(local_alias, prompt, system)
    res["cluster_pos"] = 0
    res["cluster_alias"] = local_alias
    return res


# ---------------------------------------------------------------------------
# Zitat-Validation
# ---------------------------------------------------------------------------
def validate_quotes(answer: str, hits: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Extrahiere Gaensefuessen-Zitate aus Antwort, pruefe ob jedes
    in irgendeinem Treffer-Content vorkommt (Substring nach Whitespace-Normalisierung).
    """
    quotes = re.findall(r"[„\"“]([^\"”„]{8,})[\"”]", answer)
    if not quotes:
        return {"total": 0, "validated": 0, "halluzinations": []}

    def normalize(s: str) -> str:
        return re.sub(r"\s+", " ", s).strip().lower()

    normalized_corpus = " ||| ".join(normalize(h["content"]) for h in hits)
    halluzinations: list[str] = []
    validated = 0
    for q in quotes:
        if normalize(q) in normalized_corpus:
            validated += 1
        else:
            halluzinations.append(q)
    return {
        "total": len(quotes),
        "validated": validated,
        "halluzinations": halluzinations,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(
        prog="halo_pro_archiv_agent",
        description="LLM-Agent ueber Halos Konversations-Archiv mit Cluster-Fallback.",
    )
    p.add_argument("--question", required=True, help="Mads Frage in Anfuehrungszeichen")
    p.add_argument("--max-treffer", type=int, default=50, help="max FTS-Treffer (default 50)")
    p.add_argument("--local-only", action="store_true", help="NSFW/Privacy: nur lokal (halo:latest)")
    p.add_argument(
        "--alias-override",
        help="Einzelnen Alias erzwingen (umgeht Cluster, fuer Tests)",
    )
    p.add_argument("--json", action="store_true", help="Roh-JSON statt Pretty-Output")
    args = p.parse_args()

    # ENV VOR worker-Import setzen — sonst greift NO_FALLBACK nicht
    if not args.local_only:
        os.environ["HALO_WORKER_NO_FALLBACK"] = "1"
    else:
        os.environ["HALO_WORKER_LANE"] = "ollama"

    if not args.json:
        banner(args.question)

    # 1. Treffer holen
    hits = fetch_hits(args.question, args.max_treffer)
    if not hits:
        say("Keine Treffer im Archiv. Bitte konkretere Frage stellen.", "yellow")
        sys.exit(0)
    if not args.json:
        say(f"FTS-Treffer: {len(hits)} (Top {min(3, len(hits))} unten)", "cyan")
        for h in hits[:3]:
            ts = h["timestamp"][:19].replace("T", " ") if h["timestamp"] else "?"
            say(f"  • {ts} | {h['role']:9s} | {(h['session_id'] or '')[:8]}", "white")

    # 2. Cluster laden
    with CLUSTER_PATH.open("r", encoding="utf-8") as fp:
        cluster_cfg = json.load(fp)
    system_prompt = cluster_cfg["system_prompt_kompass"]
    cluster = cluster_cfg["cluster"]
    local_alias = cluster_cfg["local_only_fallback"]["alias"]

    # 3. Worker laden + dispatchen
    worker = _load_worker()
    prompt = build_prompt(args.question, hits, system_prompt)

    if args.alias_override:
        say(f"[Override] Alias erzwungen: {args.alias_override}", "yellow")
        try:
            res = worker.dispatch(args.alias_override, prompt, system_prompt)
            res["cluster_pos"] = -1
            res["cluster_alias"] = args.alias_override
        except worker.WorkerError as e:
            say(f"Override-Fehler: {e}", "red")
            sys.exit(3)
    elif args.local_only:
        res = call_local_only(local_alias, system_prompt, prompt, worker)
    else:
        res = call_cluster(cluster, system_prompt, prompt, worker)

    answer = res.get("content", "")

    # 4. Validation
    validation = validate_quotes(answer, hits)

    if args.json:
        out = {
            "question": args.question,
            "n_hits": len(hits),
            "model": res.get("model"),
            "lane": res.get("lane"),
            "cluster_pos": res.get("cluster_pos"),
            "answer": answer,
            "validation": validation,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    say(
        f"\n[Antwort von {res.get('cluster_alias')} via {res.get('lane')} "
        f"(Pos {res.get('cluster_pos')})]",
        "magenta",
    )
    print(answer)

    if validation["total"] > 0:
        if validation["halluzinations"]:
            say(
                f"\n⚠ Validation: {validation['validated']}/{validation['total']} "
                f"Zitate verifiziert. {len(validation['halluzinations'])} nicht im Archiv:",
                "red",
            )
            for h in validation["halluzinations"]:
                say(f"  - {h[:120]}…" if len(h) > 120 else f"  - {h}", "red")
        else:
            say(
                f"\n✓ Validation: alle {validation['validated']} Zitate in Archiv verifiziert.",
                "green",
            )
    else:
        say("\n(keine Gaensefuessen-Zitate in Antwort — Validation skipped)", "white")


if __name__ == "__main__":
    main()
