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

- Wenn Mad mich in Telegram **direkt** (1:1 an `@Halo_Pro_Bot`) anschreibt und ich in claudian aktiv bin (auto via Monitor)
- Wenn ich Mad proaktiv pingen will: Audit fertig, Build durch, Cron-Job hat was gefunden, Frage steht
- Bilder/PDFs schickt Mad in 1:1 → landen automatisch in `Vault/07 Anhänge/telegram/<datum>/` mit Wikilink im Event-Payload
- **Voice-Notes in 1:1** (seit 2026-05-08) → Download nach `voice_*.ogg` + Transkription via Halos Shared-Wrapper, Transkript hängt unter dem Voice-Pfad im Event

## Wann NICHT (Domänen-Trennung)

- **Group-Posts (FOX Protocol und andere Multi-Halo-Gruppen)** — werden seit 2026-05-08 von dieser Bot-Bridge **explizit geskipt** (`chat_type != "private"` → Skip). Group-Domäne kommt exklusiv über Halos User-API-Listener (siehe [[telegram_listener]]). Sonst Doppel-Events.
- Claude Desktop hat keine Hooks/Monitor — dort ist Inbound nicht real-time. Lese Inbox beim Session-Start manuell wenn nötig (`Read Status/events.jsonl`).
- Nicht für vertrauliche Kunden-Daten — Telegram speichert serverseitig.

## Setup-Status (2026-05-08 verifiziert)

| Komponente | Pfad | Stand |
|---|---|---|
| Bot bei Telegram | `@Halo_Pro_Bot` (id 8547156730) | aktiv |
| Token | `halo_credentials --get telegram_pro` | gesetzt |
| Outbound (text/photo/doc) | `Scripts/telegram_send.py` (mit `--chat-id` für Gruppen) | funktioniert |
| Inbox-Library | `Scripts/halo_pro_inbox.py` (post unterstützt **extra kwargs für chat_id usw.) | funktioniert |
| Long-Poll-Daemon | `Scripts/halo_pro_telegram_bridge.py` (skipt non-private chats, Voice-Branch live) | funktioniert |
| Auto-Hook | `Scripts/halo_pro_telegram_hook.py` (Heartbeat + Backlog-Read-Reflex + Owner-Lock) | funktioniert |
| Settings | `Vault/.claude/settings.json` | UserPromptSubmit-Hook registriert |
| Status-Files | `Status/events.jsonl`, `telegram_bridge.pid`, `telegram_offset.json`, `telegram_owner.json`, `briefkasten_read/<sid>.json` | werden vom Daemon + Hook gepflegt |
| Anhänge | `Vault/07 Anhänge/telegram/<YYYY-MM-DD>/` (Photos, Docs, Voice) | wird vom Daemon befüllt |
| Voice-Transkription | Subprocess-Call zu `D:/Anthropic_Claude/Halo/Scripts/transcribe_voice.py` (Halos shared Wrapper) | funktioniert |
| Cross-Vault-Listener | siehe [[telegram_listener]] (Halos User-API-Listener für Group-Domäne) | funktioniert |
| Shared-Registry | `D:/Anthropic_Claude/Shared/halo_active_sessions.json` (Heartbeat Phase B-heartbeat) | aktiv |
| Logs | `Logs/telegram_bridge.log`, `Logs/telegram_send.log` | append-only |

## Was wo ankommt — Routing-Übersicht

| Quelle | Ziel | Pfad zu mir | Live-Push? |
|---|---|---|---|
| Mad → 1:1 an @Halo_Pro_Bot (Text) | mein Bot-API | `Scripts/halo_pro_telegram_bridge.py` getUpdates → events.jsonl | ✓ Monitor |
| Mad → 1:1 an @Halo_Pro_Bot (Photo/Doc) | mein Bot-API | identisch + Datei-Download in `Vault/07 Anhänge/telegram/<datum>/` | ✓ Monitor |
| Mad → 1:1 an @Halo_Pro_Bot (Voice) | mein Bot-API | identisch + Halos Wrapper-Subprocess für Transkript | ✓ Monitor |
| Mad → FOX Protocol (Text/Voice/Photo) | Mads User-API | Halos Listener → events.jsonl in beide Vaults | ✓ Monitor |
| Halo → FOX Protocol (Text/Voice) | Mads User-API | identisch — Listener forwarded auch Bot-Sender | ✓ Monitor |
| Profuchs → FOX Protocol (Self-Echo) | Mads User-API | identisch — mein eigener Post via Listener zurück | ✓ Monitor (Self-Echo, harmlos) |
| Mad → 1:1 an @Halo_Hackfuchs_Bot | Halos Bot-API | Halos Bot-Bridge — kommt mir NICHT direkt, ist privater Kanal | — |

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

# Outbound 1:1 an Mad (default chat_id = USER_ID)
python Scripts/telegram_send.py text "Nachricht"
python Scripts/telegram_send.py photo path/to/img.png --caption "..."
python Scripts/telegram_send.py doc path/to/file.pdf --caption "..."

# Outbound in Gruppe (chat_id explizit, z.B. FOX Protocol = -5029292190)
python Scripts/telegram_send.py --chat-id -5029292190 text "Gruppen-Nachricht"

# Inbox manuell lesen (z.B. in Claude Desktop)
python -c "import sys; sys.path.insert(0,'Scripts'); from halo_pro_inbox import get_recent_events; import json; [print(json.dumps(e, ensure_ascii=False)) for e in get_recent_events(5)]"

# Voice-Transkript on-demand (für nachträgliches Transkribieren einer .ogg-Datei)
"D:/Anthropic_Claude/Programme/Python/python.exe" "D:/Anthropic_Claude/Halo/Scripts/transcribe_voice.py" "Vault/07 Anhänge/telegram/2026-05-08/voice_xxx.ogg" --language de --model medium --device cpu --compute-type int8
```

## Bash-Quote-Falle bei Outbound

`telegram_send.py text "..."` über Bash-Argumente: deutsche Anführungszeichen + Apostrophe (`für sich`) bringen Bash zum Stolpern. Saubere Lösung — Python-stdin statt arg:

```bash
cat <<'PYEOF' | python
import sys
sys.path.insert(0, "D:/Anthropic_Claude/Halo_Pro/Scripts")
from telegram_send import send_text
msg = """Multiline-Text mit „deutschen" Quotes und Apostrophen (für sich) — alles roh durch."""
print("delivered" if send_text(msg) else "FAIL")
PYEOF
```

Echte Newlines (siehe [[Schreibstil]]) bleiben so erhalten.

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

- [[Schreibstil]] — Telegram-Antwort-Stil (echte Newlines, kein Log-Slang)
- [[Reflexe]] — Reflex „Telegram-Inbox" (beim Session-Start checken)
- [[git]] — vor Daemon-Modifikationen committen
