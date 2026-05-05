#!/usr/bin/env python3
"""
Halo_Pro Obsidian API — steuert den Halo_Pro-Vault via REST.

Plugin: obsidian-local-rest-api v3.6.1+
Port:   27124 (HTTPS, self-signed cert)
Auth:   Bearer Token (aus halo_credentials.py --get obsidian_api_pro)

Usage:
  python Scripts/obsidian.py status
  python Scripts/obsidian.py read "02 Projekte/KundeX.md"
  python Scripts/obsidian.py write "05 Daily Notes/2026-05-06.md" "# Heute\n..."
  python Scripts/obsidian.py append "05 Daily Notes/2026-05-06.md" "- 14:30 Decision X"
  python Scripts/obsidian.py search "KundeX"
  python Scripts/obsidian.py open "02 Projekte/KundeX.md"
  python Scripts/obsidian.py list ""
  python Scripts/obsidian.py commands
  python Scripts/obsidian.py run "editor:open-search"
  python Scripts/obsidian.py delete "01 Inbox/temp.md"
  python Scripts/obsidian.py tags
  python Scripts/obsidian.py active
"""

import sys
import os
import json
import urllib.request
import urllib.error
import ssl
from pathlib import Path

# ── Konfiguration ────────────────────────────────────────────────────────────

OBSIDIAN_URL = "https://127.0.0.1:27124"
VAULT_PATH   = "D:/Anthropic_Claude/Halo_Pro/Vault"

SCRIPT_DIR = Path(__file__).resolve().parent
CRED_SCRIPT = str(SCRIPT_DIR / "halo_credentials.py")
PYTHON_EXE = "D:/Anthropic_Claude/Programme/Python/python.exe"
SERVICE_NAME = "obsidian_api_pro"


def _get_token():
    """API-Token aus halo_credentials.py holen — parst den Backtick-Wert."""
    import subprocess
    import re
    r = subprocess.run([PYTHON_EXE, CRED_SCRIPT, "--get", SERVICE_NAME],
                       capture_output=True, text=True)
    m = re.search(r'`([^`]+)`', r.stdout)
    if not m:
        sys.exit(f"Kein {SERVICE_NAME} Token. Erst speichern:\n"
                 f"  python Scripts/halo_credentials.py --add {SERVICE_NAME} <TOKEN>\n"
                 f"Token aus Obsidian: Settings -> Community Plugins -> Local REST API -> API Key")
    return m.group(1)


# ── HTTP-Kern ─────────────────────────────────────────────────────────────────

def _req(method, path, body=None, content_type="text/markdown"):
    token = _get_token()
    ctx   = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE

    url     = f"{OBSIDIAN_URL}{path}"
    data    = body.encode() if isinstance(body, str) else body
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  content_type,
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            raw = r.read()
            ct  = r.headers.get("Content-Type", "")
            return json.loads(raw) if "json" in ct else raw.decode(errors="replace")
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        sys.exit(f"HTTP {e.code} {e.reason}: {body_err}")
    except urllib.error.URLError as e:
        sys.exit(f"Verbindung fehlgeschlagen: {e}\n"
                 f"Laeuft Obsidian und ist Local REST API Plugin aktiv?")


# ── Kommandos ─────────────────────────────────────────────────────────────────

def cmd_status():
    r = _req("GET", "/")
    print(json.dumps(r, indent=2, ensure_ascii=False))

def cmd_read(path):
    r = _req("GET", f"/vault/{_enc(path)}")
    print(r)

def cmd_write(path, content):
    _req("PUT", f"/vault/{_enc(path)}", body=content)
    print(f"Geschrieben: {path}")

def cmd_append(path, content):
    _req("POST", f"/vault/{_enc(path)}", body="\n" + content)
    print(f"Angehaengt: {path}")

def cmd_delete(path):
    _req("DELETE", f"/vault/{_enc(path)}")
    print(f"Geloescht: {path}")

def cmd_list(path=""):
    r = _req("GET", f"/vault/{_enc(path)}" if path else "/vault/")
    files = r.get("files", []) if isinstance(r, dict) else []
    for f in files:
        print(f)

def cmd_search(query):
    r = _req("POST", "/search/simple/",
             body=json.dumps({"query": query}),
             content_type="application/json")
    if isinstance(r, list):
        for item in r:
            score = item.get("score", "")
            fname = item.get("filename", "")
            print(f"  [{score:.2f}] {fname}" if score else f"  {fname}")
    else:
        print(r)

def cmd_open(path):
    _req("POST", f"/open/{_enc(path)}")
    print(f"Geoeffnet: {path}")

def cmd_active():
    r = _req("GET", "/active/")
    print(r)

def cmd_tags():
    r = _req("GET", "/tags/")
    print(json.dumps(r, indent=2, ensure_ascii=False))

def cmd_commands():
    r = _req("GET", "/commands/")
    cmds = r.get("commands", []) if isinstance(r, dict) else []
    for c in cmds:
        print(f"  {c.get('id',''):<50} {c.get('name','')}")

def cmd_run(command_id):
    _req("POST", f"/commands/{_enc(command_id)}/")
    print(f"Ausgefuehrt: {command_id}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _enc(s):
    """Minimal URL-Encoding für Pfade (Leerzeichen → %20 etc.)."""
    import urllib.parse
    return urllib.parse.quote(s, safe="/")


# ── Main ──────────────────────────────────────────────────────────────────────

CMDS = {
    "status":   (cmd_status,   0),
    "read":     (cmd_read,     1),
    "write":    (cmd_write,    2),
    "append":   (cmd_append,   2),
    "delete":   (cmd_delete,   1),
    "list":     (cmd_list,     0),
    "search":   (cmd_search,   1),
    "open":     (cmd_open,     1),
    "active":   (cmd_active,   0),
    "tags":     (cmd_tags,     0),
    "commands": (cmd_commands, 0),
    "run":      (cmd_run,      1),
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in CMDS:
        print(__doc__)
        sys.exit(0)
    fn, nargs = CMDS[args[0]]
    if len(args) - 1 < nargs:
        sys.exit(f"'{args[0]}' braucht {nargs} Argument(e)")
    fn(*args[1:1 + nargs])
