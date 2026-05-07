---
name: Telegram-Bridge — Bidirektionaler Chat
type: werkzeug
category: kommunikation
---

# Telegram-Bridge

Mads zweiter Kommunikationskanal. Outbound (ich → Mad) seit 2026-05-06 live, **Inbound (Mad → ich) seit 2026-05-07 live**. Bridge erlaubt echten Chat in der Telegram-App: Mad schreibt mir dort, ich antworte dort.

**Bot:** `@Halo_Pro_Bot` (separat von Halos `Halo_Hackfuchs_Bot` — eigene Tokens, parallele Pipelines, kein Konflikt)
**Token-Service:** `telegram_pro` in `halo_credentials.py`
**Allowlist:** Mads User-ID `5996284268` (alle anderen werden ignoriert + geloggt)

## Architektur (3 Komponenten)

```
Mad in Telegram-App
       │
       │ HTTPS (Long-Poll, ~25s Connection)
       ▼
halo_pro_telegram_bridge.py (Daemon)
       │
       ▼
Status/events.jsonl ◄───┐
       │                │ Read.from inside claudian
       │ tail -F | grep │
       ▼                │
Monitor-Tool ──────────►│ weckt mich zwischen Turns
                        │
       ┌────────────────┘
       │
       ▼
telegram_send.py (Outbound) ──► Mad in Telegram-App
```

## Wann nutze ich es

- Wenn Mad mich in Telegram anschreibt und ich in claudian aktiv bin (auto via Monitor)
- Wenn ich Mad proaktiv pingen will: Audit fertig, Build durch, Cron-Job hat was gefunden, Frage steht
- Bilder/PDFs schickt Mad → landen automatisch in `Vault/07 Anhänge/telegram/<datum>/` mit Wikilink im Event-Payload

## Wann nicht

- Claude Desktop hat keine Hooks/Monitor — dort ist Inbound nicht real-time. Lese Inbox beim Session-Start manuell wenn nötig (`Read Status/events.jsonl`).
- Nicht für vertrauliche Kunden-Daten — Telegram speichert serverseitig.

## Setup-Status (2026-05-07 verifiziert)

| Komponente | Pfad | Stand |
|---|---|---|
| Bot bei Telegram | `@Halo_Pro_Bot` (id 8547156730) | aktiv |
| Token | `halo_credentials --get telegram_pro` | gesetzt |
| Outbound | `Scripts/telegram_send.py` | funktioniert |
| Inbox-Library | `Scripts/halo_pro_inbox.py` | funktioniert |
| Long-Poll-Daemon | `Scripts/halo_pro_telegram_bridge.py` | funktioniert |
| Auto-Hook | `Scripts/halo_pro_telegram_hook.py` | funktioniert |
| Settings | `Vault/.claude/settings.json` | UserPromptSubmit-Hook registriert |
| Status-Files | `Status/events.jsonl`, `telegram_bridge.pid`, `telegram_offset.json`, `telegram_owner.json` | werden vom Daemon gepflegt |
| Anhänge | `Vault/07 Anhänge/telegram/<YYYY-MM-DD>/` | wird vom Daemon befüllt |
| Logs | `Logs/telegram_bridge.log`, `Logs/telegram_send.log` | append-only |

## Wie es läuft (Mad-Sicht)

1. claudian aufmachen → Hook feuert beim ersten Prompt → Daemon startet (idempotent, lazy mode), Owner-Lock auf aktuelle Session
2. Mad schreibt in Telegram an `Halo_Pro_Bot`
3. Daemon greift's binnen 1-2 Sekunden via Long-Poll
4. Event landet in `events.jsonl` mit `target=halo_pro_<sid>`
5. Monitor-Tool weckt mich auf zwischen Turns
6. Ich antworte via `telegram_send.py text "..."` → Mad sieht Antwort in Telegram

**Daemon stirbt mit System-Reboot** (lazy mode by design). Beim nächsten claudian-Prompt startet Hook ihn neu. Telegram-Server puffert eingehende Messages 24h, also kein Datenverlust solange Mad innerhalb 24h wieder claudian aufmacht.

## Kern-Befehle

```bash
# Daemon-Status checken
python Scripts/halo_pro_telegram_bridge.py --status

# Daemon manuell starten (sonst macht's der Hook)
python Scripts/halo_pro_telegram_bridge.py    # foreground (nur zum Debuggen)
# oder detached:
start "" /B "D:/Anthropic_Claude/Programme/Python/pythonw.exe" "D:/Anthropic_Claude/Halo_Pro/Scripts/halo_pro_telegram_bridge.py"

# Daemon stoppen
python Scripts/halo_pro_telegram_bridge.py --stop

# Einmaliger Pull (Test ohne Daemon-Loop)
python Scripts/halo_pro_telegram_bridge.py --once

# Outbound (mein Standard zum Antworten)
python Scripts/telegram_send.py text "Nachricht"
python Scripts/telegram_send.py photo path/to/img.png --caption "..."
python Scripts/telegram_send.py doc path/to/file.pdf --caption "..."

# Inbox manuell lesen (z.B. in Claude Desktop)
python -c "import sys; sys.path.insert(0,'Scripts'); from halo_pro_inbox import get_recent_events; import json; [print(json.dumps(e, ensure_ascii=False)) for e in get_recent_events(5)]"
```

## Monitor-Befehl (Hook generiert ihn dynamisch)

Wenn der Hook im claudian-Prompt einen Monitor-Befehl emittiert, sieht der so aus:

```bash
tail -F Status/events.jsonl | \
  grep --line-buffered -E '"target":[[:space:]]*"halo_pro_<session_id>"' | \
  grep --line-buffered -E 'telegram'
```

Wichtig: `[[:space:]]*` zwischen `:` und `"halo_pro_..."` — `json.dumps` formatiert mit Leerzeichen, ohne den Quantifier matcht der Filter nicht.

In Claude Code dann via `Monitor`-Tool starten (NICHT `Bash run_in_background`), `persistent: true`, sonst kein Wakeup.

## Troubleshooting

**Daemon läuft nicht trotz Hook:** `Logs/telegram_bridge.log` lesen. Häufigste Ursachen: Token-Fehler, Webhook-Konflikt mit anderem Bot.

**`getUpdates` 409 Conflict:** Webhook ist gesetzt, Long-Poll geht nicht parallel. Fix:
```bash
TOKEN=$(python Scripts/halo_credentials.py --get telegram_pro | grep -oE '\`[^`]+\`' | tr -d '`')
curl "https://api.telegram.org/bot$TOKEN/deleteWebhook"
```

**Monitor weckt mich nicht auf:** Falsches Tool benutzt. `Bash run_in_background` macht keinen Wakeup — nur `Monitor` mit `persistent: true`. Auch checken: ist der grep-Filter korrekt? `[[:space:]]*` Pflicht.

**Mad sieht keine Antworten:** `Logs/telegram_send.log` lesen. `delivered` = OK. HTTP 400 oft = User hat `/start` noch nicht getippt (Bot kann nicht initiieren).

**Owner-Lock falsch:** `cat Status/telegram_owner.json` zeigt aktuelle Session. Bei Bedarf `rm` löschen — beim nächsten Prompt setzt Hook neu.

**Daemon-Restart nach Crash:** Idempotent. Hook erkennt PID nicht-mehr-laufend → startet neu. Offset bleibt persistent in `telegram_offset.json`, also kein Replay.

## Konflikt-Vermeidung mit Halo

Halos Bridge läuft parallel auf demselben Rechner — friedlich:

| Aspekt | Halo | Halo_Pro |
|---|---|---|
| Bot | `Halo_Hackfuchs_Bot` | `Halo_Pro_Bot` |
| Token-Service | hardcoded + ENV | `halo_credentials --get telegram_pro` |
| Daemon-Skript | `halo_telegram_bridge.py` | `halo_pro_telegram_bridge.py` |
| PID-File | `Halo/Status/telegram_bridge.pid` | `Halo_Pro/Status/telegram_bridge.pid` |
| Offset-File | `Halo/Status/telegram_offset.json` | `Halo_Pro/Status/telegram_offset.json` |
| Source-Tag | `halo_<sid>` | `halo_pro_<sid>` |
| Codewort | `Telegram` (Toggle) | kein — auto via Hook |
| Anhänge | `Halo/Inbox/telegram/` | `Halo_Pro/Vault/07 Anhänge/telegram/` |

Beide Daemons sehen nur ihre eigenen Telegram-Updates (unterschiedliche Tokens). Beide PID-Files getrennt. Beide events.jsonl getrennt. Null Race.

## Verwandte MDs

- [[../../00 Kontext/Schreibstil]] — Telegram-Antwort-Stil (echte Newlines, kein Log-Slang)
- [[../../00 Kontext/Reflexe]] — Reflex „Telegram-Inbox" (beim Session-Start checken)
- [[git]] — vor Daemon-Modifikationen committen
