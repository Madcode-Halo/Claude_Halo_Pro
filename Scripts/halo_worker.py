# -*- coding: utf-8 -*-
"""
halo_worker.py — Halos Delegations-Werkzeug.

Halo bleibt Mastermind, Worker macht Bulk/Repetitiv. Zwei Lanes:
  1. OpenRouter (Cloud, kostenlose Free-Modelle + paid Fallback)
  2. Ollama lokal (Privacy-pure, offline-fähig)

Auto-Fallback-Reihenfolge:
  ENV `HALO_WORKER_LANE=ollama` → direkt Ollama
  ENV `HALO_WORKER_LANE=openrouter` → nur OpenRouter, kein Fallback
  default → OpenRouter, bei 429/Network-Fail auto-fallback Ollama

Aliase (Karten-Spec 2026-04-17, hier MVP-Subset):
  qwen3     · z-ai/glm-4.5-air:free       Researcher / Standard
  nemotron  · nvidia/llama-3.1-nemotron-ultra-253b-v1:free   1M Context, große Mengen
  coder     · qwen/qwen-2.5-coder-32b-instruct:free          Code/Debug
  llama     · meta-llama/llama-3.3-70b-instruct:free          Speed
  gemma     · google/gemma-3-27b-it:free                      Polierer
  hermes    · nousresearch/hermes-3-llama-3.1-405b:free       Heavy Reasoning
  glm       · z-ai/glm-4.5-air:free                           Uncensored
  qwen36    · qwen/qwen-2.5-72b-instruct           PAID Fallback
  halo      · halo:latest                          Ollama-only (Custom Halo)

Subcommands:
  chat <alias> <prompt>          One-shot
  pipeline <chain>               z.B. "nemotron:Zusammenfassen|coder:Code prüfen"
  roles                          Aliase-Übersicht
  credits                        OpenRouter-Credits/Limits prüfen
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "Scripts" / "halo_credentials.py"
OLLAMA = ROOT / "Scripts" / "ollama_local.py"
OR_API = "https://openrouter.ai/api/v1"

# ────────────────────────────────────────────────────────────────────
# Modell-Aliase
# ────────────────────────────────────────────────────────────────────

# (alias, openrouter-id, ollama-fallback-id, kurze Rolle, paid?)
ALIASES = {
    "qwen3":    ("z-ai/glm-4.5-air:free",                          "qwen3:14b",     "Researcher / Standard",      False),
    "nemotron": ("nvidia/llama-3.1-nemotron-ultra-253b-v1:free",   "qwen3:14b",     "1M Context — große Mengen",  False),
    "coder":    ("qwen/qwen-2.5-coder-32b-instruct:free",          "qwen3:14b",     "Code/Debug",                 False),
    "llama":    ("meta-llama/llama-3.3-70b-instruct:free",         "qwen3.5:9b",    "Speed-Worker",               False),
    "gemma":    ("google/gemma-3-27b-it:free",                     "gemma4:e4b",    "Polierer",                   False),
    "hermes":   ("nousresearch/hermes-3-llama-3.1-405b:free",      "qwen3:14b",     "Heavy Reasoning 405B",       False),
    "glm":      ("z-ai/glm-4.5-air:free",                          "qwen3:14b",     "Uncensored",                 False),
    "qwen36":   ("qwen/qwen-2.5-72b-instruct",                     "qwen3:14b",     "PAID Fallback",              True),
    "halo":     (None,                                              "halo:latest",   "Custom Halo (nur Ollama)",   False),
}

LANE_ENV = os.environ.get("HALO_WORKER_LANE", "auto").lower()
NO_FALLBACK = LANE_ENV == "openrouter" or os.environ.get("HALO_WORKER_NO_FALLBACK")


# ────────────────────────────────────────────────────────────────────
# Halo-Brand
# ────────────────────────────────────────────────────────────────────

def banner(s: str) -> None:
    if HAS_RICH:
        console.print(f"\n[bold magenta]🦊 H a l o Worker · {s} 🦊[/bold magenta]")
        console.print("[magenta]✦ ˚ ｡ ˚[/magenta]\n")
    else:
        print(f"\n🦊 Worker · {s}\n")


def say(m, st="white"):
    console.print(f"[{st}]{m}[/{st}]") if HAS_RICH else print(m)


# ────────────────────────────────────────────────────────────────────
# Credentials
# ────────────────────────────────────────────────────────────────────

def get_openrouter_key() -> str | None:
    k = os.environ.get("OPENROUTER_API_KEY")
    if k:
        return k
    try:
        out = subprocess.check_output(
            [sys.executable, str(CRED), "--get", "OpenRouter"],
            stderr=subprocess.DEVNULL, timeout=5,
        ).decode("utf-8", errors="replace")
        m = re.search(r"sk-or-[a-zA-Z0-9\-_]{20,}", out)
        return m.group(0) if m else None
    except Exception:
        return None


# ────────────────────────────────────────────────────────────────────
# Lanes
# ────────────────────────────────────────────────────────────────────

class WorkerError(Exception): pass
class RateLimited(WorkerError): pass
class NoCredentials(WorkerError): pass


def call_openrouter(model_id: str, prompt: str, system: str | None = None, timeout: int = 120) -> dict:
    key = get_openrouter_key()
    if not key:
        raise NoCredentials("OPENROUTER_API_KEY nicht gesetzt + halo_credentials hat keinen sk-or-Key")
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    body = json.dumps({"model": model_id, "messages": msgs}).encode("utf-8")
    req = urllib.request.Request(
        f"{OR_API}/chat/completions", data=body, method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://halo.local",
            "X-Title": "Halo Worker",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        return {
            "ok": True, "lane": "openrouter", "model": model_id,
            "content": data["choices"][0]["message"]["content"],
            "usage": data.get("usage", {}),
        }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RateLimited(f"OpenRouter 429 für {model_id}")
        body_s = e.read().decode("utf-8", errors="replace")[:200]
        raise WorkerError(f"OpenRouter HTTP {e.code}: {body_s}")
    except urllib.error.URLError as e:
        raise WorkerError(f"OpenRouter network: {e}")


def call_ollama(model_id: str, prompt: str, system: str | None = None) -> dict:
    """Über ollama_local.py worker — JSON-Output."""
    cmd = [sys.executable, str(OLLAMA), "worker", model_id, prompt]
    if system:
        cmd += ["--system", system]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if proc.returncode != 0:
        raise WorkerError(f"ollama: {proc.stderr.strip()[:200]}")
    out = json.loads(proc.stdout.strip())
    if not out.get("ok"):
        raise WorkerError(f"ollama: {out.get('error')}")
    return {
        "ok": True, "lane": "ollama", "model": model_id,
        "content": out["content"],
        "usage": {"prompt_tokens": out.get("prompt_eval_count"),
                  "completion_tokens": out.get("eval_count")},
    }


def dispatch(alias: str, prompt: str, system: str | None = None) -> dict:
    """Lane-Routing mit Auto-Fallback."""
    if alias not in ALIASES:
        raise WorkerError(f"Unbekannter Alias '{alias}'. Liste: roles")
    or_id, ol_id, _, _ = ALIASES[alias]

    # halo:latest hat KEINE OpenRouter-Variante
    if or_id is None or LANE_ENV == "ollama":
        return call_ollama(ol_id, prompt, system)

    # Default: OpenRouter zuerst
    try:
        return call_openrouter(or_id, prompt, system)
    except RateLimited:
        if NO_FALLBACK:
            raise
        say(f"⚠ OpenRouter rate-limited → Fallback Ollama ({ol_id})", "yellow")
        return call_ollama(ol_id, prompt, system)
    except NoCredentials:
        if NO_FALLBACK:
            raise
        say(f"⚠ Kein OpenRouter-Key → Fallback Ollama ({ol_id})", "yellow")
        return call_ollama(ol_id, prompt, system)
    except WorkerError as e:
        if NO_FALLBACK:
            raise
        say(f"⚠ OpenRouter-Fail ({e}) → Fallback Ollama ({ol_id})", "yellow")
        return call_ollama(ol_id, prompt, system)


# ────────────────────────────────────────────────────────────────────
# Subcommands
# ────────────────────────────────────────────────────────────────────

def cmd_chat(args):
    prompt = args.prompt
    if args.stdin or prompt == "-":
        extra = sys.stdin.read()
        prompt = (prompt + "\n\n" + extra) if (prompt and prompt != "-") else extra
    if args.dry_run:
        or_id, ol_id, role, paid = ALIASES.get(args.alias, (None, None, "?", False))
        say(f"DRY-RUN  alias={args.alias}  or={or_id}  ol={ol_id}", "cyan")
        say(f"  Prompt-Länge: {len(prompt)} Zeichen", "white")
        return
    t0 = time.time()
    try:
        res = dispatch(args.alias, prompt, args.system)
    except WorkerError as e:
        sys.exit(f"✗ {e}")
    if args.json:
        res["wallclock_s"] = round(time.time() - t0, 2)
        print(json.dumps(res, ensure_ascii=False))
    else:
        say(f"[lane={res['lane']}  model={res['model']}  {round(time.time()-t0,2)}s]", "magenta")
        print(res["content"])


def cmd_pipeline(args):
    """Pipeline-Mode: 'nemotron:Zusammenfassen|coder:Code prüfen' — Output → next Input."""
    banner("Pipeline")
    stages = [s.strip() for s in args.chain.split("|")]
    current = args.input or (sys.stdin.read() if args.stdin else "")
    if not current:
        sys.exit("✗ Pipeline braucht Input — --input oder --stdin")
    for i, stage in enumerate(stages, 1):
        if ":" not in stage:
            sys.exit(f"✗ Stage {i} ohne ':' — Format ist alias:Anweisung")
        alias, instruction = stage.split(":", 1)
        say(f"[{i}/{len(stages)}] {alias} → {instruction}", "magenta")
        try:
            res = dispatch(alias.strip(),
                           f"{instruction.strip()}\n\n---INPUT---\n{current}",
                           system="Du bist Halo's Worker. Liefere präzise."
                           )
        except WorkerError as e:
            sys.exit(f"✗ Stage {i}: {e}")
        current = res["content"]
        say(f"   ✓ {len(current)} Zeichen out  ({res['lane']})", "green")
    print()
    print(current)


def cmd_roles(args):
    banner("Aliase")
    if HAS_RICH:
        t = Table(box=box.SIMPLE_HEAVY, header_style="bold magenta")
        t.add_column("Alias", style="cyan"); t.add_column("OpenRouter")
        t.add_column("Ollama-Fallback"); t.add_column("Rolle"); t.add_column("Paid?", justify="center")
        for a, (o_id, l_id, role, paid) in ALIASES.items():
            t.add_row(a, o_id or "—", l_id, role, "💳" if paid else "")
        console.print(t)
    else:
        for a, (o_id, l_id, role, paid) in ALIASES.items():
            print(f"  {a:10s}  {role:30s}  {o_id or '—'} | {l_id}{' (PAID)' if paid else ''}")


def cmd_credits(args):
    banner("OpenRouter-Credits")
    key = get_openrouter_key()
    if not key:
        sys.exit("✗ Kein OpenRouter-Key — füge ihn als Service 'OpenRouter' in halo_credentials hinzu (single-line, sk-or-...).")
    req = urllib.request.Request(f"{OR_API}/auth/key", headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8")).get("data", {})
        say(f"  Label: {data.get('label', '—')}", "white")
        say(f"  Limit: {data.get('limit', '—')}", "white")
        say(f"  Usage: {data.get('usage', '—')}", "white")
        say(f"  Limit Remaining: {data.get('limit_remaining', '—')}", "magenta")
    except Exception as e:
        sys.exit(f"✗ {e}")


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(prog="halo_worker", description="Halo → OpenRouter / Ollama")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chat", help="One-shot Chat")
    c.add_argument("alias", help="qwen3/nemotron/coder/llama/gemma/hermes/glm/qwen36/halo (siehe roles)")
    c.add_argument("prompt", help="Prompt — '-' liest stdin")
    c.add_argument("--system", help="System-Prompt")
    c.add_argument("--stdin", action="store_true", help="Stdin an Prompt anhängen")
    c.add_argument("--json", action="store_true", help="JSON-Output (für Pipelines)")
    c.add_argument("--dry-run", action="store_true")
    c.set_defaults(func=cmd_chat)

    pl = sub.add_parser("pipeline", help="Multi-Stage 'alias:instr|alias:instr|...'")
    pl.add_argument("chain"); pl.add_argument("--input"); pl.add_argument("--stdin", action="store_true")
    pl.set_defaults(func=cmd_pipeline)

    sub.add_parser("roles", help="Aliase-Übersicht").set_defaults(func=cmd_roles)
    sub.add_parser("credits", help="OpenRouter-Credits/Limits").set_defaults(func=cmd_credits)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
