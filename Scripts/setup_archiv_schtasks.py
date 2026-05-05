#!/usr/bin/env python3
"""setup_archiv_schtasks.py — Idempotenter Windows-Task-Scheduler-Setup
fuer halo_pro_archiv_index.py update alle 30 Minuten.

Subcommands:
  install    Task anlegen (oder updaten falls vorhanden)
  status     aktuellen Task-Status anzeigen
  uninstall  Task entfernen
  run        Task SOFORT manuell triggern

Aufruf:
  python Scripts/setup_archiv_schtasks.py install
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

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
TASK_BAT = HALO_ROOT / "Scripts" / "halo_pro_archiv_update_task.cmd"
LOG_FILE = HALO_ROOT / "Logs" / "halo_archiv_schtasks.log"
TASK_NAME = "Halo_Pro_Archiv_Update"
INTERVAL_MINUTES = 30


def _run_schtasks(cmd: list[str]) -> subprocess.CompletedProcess:
    """schtasks-Wrapper mit robustem cp1252+errors=replace Decoding."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="cp1252",
        errors="replace",
    )


def banner(text: str) -> None:
    if _console:
        _console.print(f"[bold magenta]🦊 {text}[/bold magenta]")
        _console.print("[magenta]✦ ˚ ｡ ˚ ✦ ˚ ｡ ˚ ✦[/magenta]")
    else:
        print(f"=== {text} ===")


def say(text: str, style: str = "white") -> None:
    if _console:
        _console.print(f"[{style}]{text}[/{style}]")
    else:
        print(text)


def task_exists() -> bool:
    proc = _run_schtasks(["schtasks", "/Query", "/TN", TASK_NAME])
    return proc.returncode == 0


def cmd_install(args: argparse.Namespace) -> None:
    banner(f"Schtasks Setup — {TASK_NAME} alle {INTERVAL_MINUTES}min")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not TASK_BAT.exists():
        say(f"BAT-Wrapper fehlt: {TASK_BAT}", "red")
        sys.exit(1)

    if task_exists():
        say("Task existiert — wird ueberschrieben.", "yellow")
        action = ["/Create", "/F"]
    else:
        action = ["/Create"]

    cmd = [
        "schtasks",
        *action,
        "/TN",
        TASK_NAME,
        "/SC",
        "MINUTE",
        "/MO",
        str(INTERVAL_MINUTES),
        "/TR",
        str(TASK_BAT),
        "/RL",
        "HIGHEST",
        "/RU",
        "SYSTEM",
    ]
    say(f"Befehl: {' '.join(cmd)}", "cyan")
    proc = _run_schtasks(cmd)
    if proc.returncode == 0:
        say(f"OK — Task '{TASK_NAME}' angelegt/aktualisiert.", "green")
        say(f"  Intervall: alle {INTERVAL_MINUTES}min", "white")
        say(f"  Log: {LOG_FILE}", "white")
    else:
        say(f"FEHLER (rc={proc.returncode}):", "red")
        say(proc.stdout, "white")
        say(proc.stderr, "red")
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    banner(f"Schtasks Status — {TASK_NAME}")
    if not task_exists():
        say(f"Task '{TASK_NAME}' existiert nicht. 'install' aufrufen.", "yellow")
        sys.exit(0)
    proc = _run_schtasks(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"]
    )
    print(proc.stdout)
    if LOG_FILE.exists():
        say(f"\nLog (letzte 20 Zeilen): {LOG_FILE}", "cyan")
        with LOG_FILE.open("r", encoding="utf-8", errors="replace") as fp:
            lines = fp.readlines()
        for line in lines[-20:]:
            print(line.rstrip())


def cmd_uninstall(args: argparse.Namespace) -> None:
    banner(f"Schtasks Uninstall — {TASK_NAME}")
    if not task_exists():
        say("Task existiert nicht — nichts zu tun.", "yellow")
        return
    proc = _run_schtasks(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
    if proc.returncode == 0:
        say("OK — Task entfernt.", "green")
    else:
        say(f"FEHLER: {proc.stderr}", "red")
        sys.exit(1)


def cmd_run(args: argparse.Namespace) -> None:
    banner(f"Schtasks Run-Now — {TASK_NAME}")
    if not task_exists():
        say("Task existiert nicht. 'install' aufrufen.", "red")
        sys.exit(1)
    proc = _run_schtasks(["schtasks", "/Run", "/TN", TASK_NAME])
    if proc.returncode == 0:
        say("OK — Task gestartet. Pruefe Log:", "green")
        say(f"  tail -f {LOG_FILE}", "cyan")
    else:
        say(f"FEHLER: {proc.stderr}", "red")
        sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(
        prog="setup_archiv_schtasks",
        description="Idempotenter Schtasks-Setup fuer halo_pro_archiv_index update.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("install").set_defaults(func=cmd_install)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("uninstall").set_defaults(func=cmd_uninstall)
    sub.add_parser("run").set_defaults(func=cmd_run)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
