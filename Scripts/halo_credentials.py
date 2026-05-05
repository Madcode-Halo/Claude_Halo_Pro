# -*- coding: utf-8 -*-
"""
halo_credentials.py — On-Demand-Wrapper für Halo_Pros logins.md

OpSec-Architektur: logins.md liegt unter D:\\Anthropic_Claude\\Halo_Pro\\.credentials\\
und ist via .gitignore vom Repo ausgeschlossen. Halo_Pro holt **einzelne
Einträge** on-demand via diesem CLI — minimaler Context-Exposure.

API:
  python Scripts/halo_credentials.py --list                    # nur Service-Namen, KEINE Werte
  python Scripts/halo_credentials.py --get telegram_pro        # nur den einen Eintrag
  python Scripts/halo_credentials.py --add <service> <value> [--note "X"]
  python Scripts/halo_credentials.py --remove <service>        # entfernt Eintrag (mit Confirm)

Halo_Pros Reflex (in CLAUDE.md verankert):
  - Statt logins.md zu lesen: `--get <service>` rufen
  - Statt Edit auf logins.md: `--add` rufen
  - logins.md wird NIE direkt geöffnet (würde alles in Context laden)

Match-Logik: case-insensitive Substring-Match auf Service-Namen
in Tabellen-Zeilen UND Sektion-Headern. Mehrfach-Match → alle Treffer
ausgeben (Halo_Pro entscheidet welcher passt).
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
LOGINS_FILE = ROOT / ".credentials" / "logins.md"

# ────────────────────────────────────────────────────────────────────
# Lese-Funktionen
# ────────────────────────────────────────────────────────────────────

def _load_lines() -> list[str]:
    if not LOGINS_FILE.exists():
        return []
    return LOGINS_FILE.read_text(encoding="utf-8").splitlines()


def _section_blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Splittet logins.md in (section_name, lines_in_section) Blöcke."""
    blocks: list[tuple[str, list[str]]] = []
    current_name = "Header"
    current_lines: list[str] = []
    for line in lines:
        if re.match(r"^##\s+", line):
            if current_lines:
                blocks.append((current_name, current_lines))
            current_name = re.sub(r"^##\s+", "", line).strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        blocks.append((current_name, current_lines))
    return blocks


def _list_services() -> list[str]:
    """Sammelt alle Service-Namen — gibt NUR Namen zurück, KEINE Werte."""
    lines = _load_lines()
    services: set[str] = set()
    in_table = False
    for line in lines:
        if re.match(r"^\s*\|.*Service.*\|", line, re.IGNORECASE):
            in_table = True
            continue
        if re.match(r"^\s*\|[\s\-:]+\|[\s\-:]+\|", line):
            continue
        if in_table:
            m = re.match(r"^\s*\|\s*([^|]+?)\s*\|", line)
            if m:
                name = m.group(1).strip()
                if name and not name.startswith("-"):
                    services.add(name)
                continue
            else:
                in_table = False
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            services.add(m.group(1).strip())
    return sorted(services)


def _get_entries(query: str) -> list[tuple[str, list[str]]]:
    """Sucht alle Blöcke/Zeilen die zum Query passen (substring, case-insensitive)."""
    q = query.lower().strip()
    lines = _load_lines()
    hits: list[tuple[str, list[str]]] = []

    for section_name, section_lines in _section_blocks(lines):
        if q in section_name.lower():
            hits.append((f"Section: {section_name}", section_lines))

    in_table = False
    for line in lines:
        if re.match(r"^\s*\|.*Service.*\|", line, re.IGNORECASE):
            in_table = True
            continue
        if re.match(r"^\s*\|[\s\-:]+\|[\s\-:]+\|", line):
            continue
        if in_table:
            m = re.match(r"^\s*\|\s*([^|]+?)\s*\|", line)
            if m and q in m.group(1).strip().lower():
                hits.append((f"Tabellen-Zeile: {m.group(1).strip()}", [line]))
            elif not line.strip().startswith("|"):
                in_table = False

    for line in lines:
        m = re.match(r"^\s*-\s+\*\*([^*]+)\*\*:", line)
        if m and q in m.group(1).strip().lower():
            hits.append((f"Bullet: {m.group(1).strip()}", [line]))

    return hits


# ────────────────────────────────────────────────────────────────────
# Schreib-Funktionen
# ────────────────────────────────────────────────────────────────────

ADD_SECTION = "Zugangsdaten"


def _add_entry(service: str, value: str, note: str = "") -> None:
    """Hängt einen neuen Eintrag an die `## Zugangsdaten`-Sektion an."""
    LOGINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOGINS_FILE.exists():
        LOGINS_FILE.write_text(
            "# Halo_Pro — Logins & API Keys\n\n"
            "On-demand via `python Scripts/halo_credentials.py --get <service>`.\n"
            "NIEMALS direkt lesen — würde Tokens in Context laden.\n\n"
            f"## {ADD_SECTION}\n\n",
            encoding="utf-8"
        )

    lines = _load_lines()
    section_idx = None
    for i, line in enumerate(lines):
        if re.match(rf"^##\s+{re.escape(ADD_SECTION)}\s*$", line):
            section_idx = i
            break

    ts = datetime.now().strftime("%Y-%m-%d")
    note_part = f" — {note}" if note else ""
    new_entry = f"- **{service}**: `{value}` _(via halo_credentials.py {ts}{note_part})_"

    if section_idx is None:
        lines.extend(["", f"## {ADD_SECTION}", "", new_entry, ""])
    else:
        insert_at = section_idx + 1
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        lines.insert(insert_at, new_entry)
        if insert_at + 1 >= len(lines) or lines[insert_at + 1].strip() != "":
            lines.insert(insert_at + 1, "")

    LOGINS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _remove_entries(query: str) -> int:
    """Entfernt Bullet-Einträge die query als Substring im Service-Namen haben."""
    q = query.lower().strip()
    lines = _load_lines()
    new_lines: list[str] = []
    removed = 0
    for line in lines:
        m = re.match(r"^\s*-\s+\*\*([^*]+)\*\*:", line)
        if m and q in m.group(1).strip().lower():
            removed += 1
            continue
        new_lines.append(line)
    if removed:
        LOGINS_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return removed


# ────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────

def _cli() -> int:
    p = argparse.ArgumentParser(
        description="Halo_Pro-Credentials — on-demand-Wrapper für logins.md"
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true",
                   help="Alle Service-Namen listen (KEINE Werte)")
    g.add_argument("--get", metavar="SERVICE",
                   help="Eintrag(e) zum Service holen (substring-match)")
    g.add_argument("--add", nargs=2, metavar=("SERVICE", "VALUE"),
                   help="Neuen Eintrag anlegen")
    g.add_argument("--remove", metavar="SERVICE",
                   help="Eintrag(e) entfernen (nur Bullet-Format)")
    p.add_argument("--note", default="", help="Optionale Notiz zum --add")
    p.add_argument("--yes", action="store_true",
                   help="Bestätige --remove ohne Rückfrage")
    args = p.parse_args()

    if args.add:
        service, value = args.add
        _add_entry(service, value, args.note)
        print(f"✓ Eintrag {service!r} angelegt in {LOGINS_FILE}")
        return 0

    if not LOGINS_FILE.exists():
        print(f"(noch keine Credentials angelegt — {LOGINS_FILE} existiert nicht)", file=sys.stderr)
        print(f"→ Mit --add <service> <value> ersten Eintrag anlegen.", file=sys.stderr)
        return 1

    if args.list:
        services = _list_services()
        if not services:
            print("(keine Services gefunden)")
            return 0
        print(f"# Services in logins.md ({len(services)}):")
        for s in services:
            print(f"  - {s}")
        print(f"\n→ Wert holen mit: --get <service>")
        return 0

    if args.get:
        hits = _get_entries(args.get)
        if not hits:
            print(f"(keine Einträge für {args.get!r} gefunden)")
            return 1
        for label, block in hits:
            print(f"## {label}")
            print("\n".join(block))
            print()
        return 0

    if args.remove:
        if not args.yes:
            hits = _get_entries(args.remove)
            if not hits:
                print(f"(keine passenden Einträge für {args.remove!r})")
                return 1
            print("Würde entfernen:")
            for label, block in hits:
                for line in block:
                    if re.match(r"^\s*-\s+\*\*", line):
                        print(f"  {line}")
            print("\n→ Mit --yes wirklich entfernen.")
            return 0
        n = _remove_entries(args.remove)
        print(f"✓ {n} Eintrag/Einträge entfernt")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(_cli())
