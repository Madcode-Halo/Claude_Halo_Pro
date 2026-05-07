---
name: 📡 Telegram User-API Listener (Cross-Vault)
description: Listener-Daemon im Halo-Vault der Telegram-Gruppen-Events live in beide Halo-Vaults pumpt. Ermöglicht Multi-Halo-Push trotz Telegram Bot-zu-Bot-Echo-Filter.
type: reference
status: active
purpose: Telegram-Gruppen-Activity (Fuchsbau etc.) als Live-Push in Profuchs-Session bringen, obwohl der Bot-API-Filter Posts von Halo's Bot nicht an Halo_Pro_Bot ausliefert. Listener nutzt Mads User-API (sieht alles) und schreibt cross-vault.
family: tools
created: 2026-05-08
loaded_by: on-demand
depends_on: [telegram_bridge]
criticality: optional
keywords: [telegram, listener, telethon, cross-vault, multi-halo, push, fuchsbau]
last_audited: 2026-05-08
---

## Was es ist

Der Listener-Daemon ist **Halo's Werkzeug**, läuft in Halo's Vault — nicht in deinem (Halo_Pro). Aber er **schreibt Push-Events auch in deine `events.jsonl`**, damit dein Monitor live aufwacht wenn jemand in Fuchsbau (oder anderen geteilten Gruppen) postet.

**Architektur (von Halo gebaut, Cross-Vault-Last komplett Halo's):**

```
Telegram Fuchsbau-Group ──► Mads User-API (Telethon) ──► halo_telegram_user_listen.py (in Halo-Vault)
                                                                        │
                                              ┌─────────────────────────┴──────────────────┐
                                              ▼                                             ▼
                                  D:/Anthropic_Claude/Halo/Status/events.jsonl   D:/Anthropic_Claude/Halo_Pro/Status/events.jsonl
                                       target=halo_<halo-sid>                        target=halo_pro_<profuchs-sid>
                                              │                                             │
                                              ▼                                             ▼
                                       Halo Monitor                                   Profuchs Monitor
                                       Push-Wakeup                                    Push-Wakeup
```

## Wann triggert es

- Mad postet vom Handy in Fuchsbau → beide Halos bekommen Live-Push
- Halo postet aus Halo_Hackfuchs_Bot → Profuchs bekommt Live-Push (Bot-Echo-Filter wird durch User-API umgangen)
- Profuchs postet aus Halo_Pro_Bot → Halo bekommt Live-Push (gleicher Mechanismus, andere Richtung)

## Was du tun musst (Profuchs)

### Phase A — Manueller Eintrag in Shared-Registry (jetzt aktiv)

Listener liest die Cross-Vault-Registry:

**Pfad:** `D:/Anthropic_Claude/Shared/halo_active_sessions.json`

Dein Eintrag (von Halo hardcoded reingetragen 2026-05-08):

```json
"halo_pro_61d0b4ad-1594-4ce9-afea-ba4c656d7206": {
  "name": "Halo Profuchs",
  "vault": "D:/Anthropic_Claude/Halo_Pro/",
  "events_jsonl": "D:/Anthropic_Claude/Halo_Pro/Status/events.jsonl",
  "target_prefix": "halo_pro_",
  "last_seen": "2026-05-08T00:01:00",
  "phase": "A-hardcoded"
}
```

**Solange `phase: A-hardcoded`** liest der Listener deinen Eintrag unabhängig von `last_seen`. Kein Heartbeat nötig.

### Phase B — Heartbeat-Hook (geplant)

Sobald du deinen Heartbeat-Hook gebaut hast: ändere `phase` auf `B-heartbeat`. Listener droppt dann SIDs deren `last_seen >24h` alt ist.

**Hook-Vorschlag (UserPromptSubmit-Hook in Halo_Pro):**

```python
# halo_pro_heartbeat.py
import json, datetime, pathlib

REGISTRY = pathlib.Path("D:/Anthropic_Claude/Shared/halo_active_sessions.json")
MY_SID_KEY = "halo_pro_<deine-aktuelle-sid>"  # kommt aus deinem Session-Discovery

def main():
    if not REGISTRY.exists():
        return
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    halos = data.setdefault("halos", {})
    halos[MY_SID_KEY] = halos.get(MY_SID_KEY, {})
    halos[MY_SID_KEY]["last_seen"] = datetime.datetime.utcnow().isoformat(timespec="seconds")
    halos[MY_SID_KEY]["phase"] = "B-heartbeat"
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
```

**Achtung:** Bei jeder neuen Session ändert sich deine SID. Hook muss SID dynamisch ermitteln (z.B. aus Halo_Pro's Session-Registry-File).

## Re-Auth-Pfad (wenn die User-API-Session expired)

**Symptome:**
- Listener-Log `Logs/halo_telegram_user_listen.log` zeigt `Session nicht autorisiert — exit`
- Daemon läuft nicht mehr (`--status` → DOWN)
- Keine Push-Events mehr aus Telegram-Gruppen

**Ursachen:**
- Mad hat in Telegram → Settings → Devices die Halo-Session terminiert
- Telethon-Session natürlich abgelaufen (sehr selten — Sessions sind langlebig)
- Telegram hat 2FA-Re-Auth getriggert

**Fix (nur Mad kann das, an seinem Rechner):**

1. cmd-Konsole bei Mad öffnen
2. Auth-Script in Halo's Repo aufrufen:
   ```cmd
   D:\Anthropic_Claude\Programme\Python\python.exe D:\Anthropic_Claude\Halo\Scripts\halo_telegram_auth.py
   ```
3. Mad gibt Phone-Number ein, Telegram pushed Code
4. Code in cmd eingeben, ggf. 2FA-Passwort
5. Erfolgs-Output: `[ok] Eingeloggt als Madcocc … Session gespeichert in D:/Anthropic_Claude/Halo/Status/halo_user`
6. Listener neu starten:
   ```powershell
   D:\Anthropic_Claude\Programme\Python\python.exe D:\Anthropic_Claude\Halo\Scripts\halo_telegram_user_listen.py --stop
   Start-Process -FilePath D:\Anthropic_Claude\Programme\Python\pythonw.exe `
                 -ArgumentList D:\Anthropic_Claude\Halo\Scripts\halo_telegram_user_listen.py `
                 -WorkingDirectory D:\Anthropic_Claude\Halo `
                 -WindowStyle Hidden
   ```

**Du (Profuchs) kannst's nicht selbst triggern** — Auth braucht interaktive Phone-Code-Eingabe + Mads Telegram-Account.

## Group-Whitelist erweitern

Wenn du eine neue Multi-Halo-Gruppe willst (nicht nur Fuchsbau):

1. Group-ID besorgen: einmal `halo_telegram_user.py dialogs 50` in Halo's Repo, ID aus dem Output ablesen
2. Mad/Halo trägt sie in `D:/Anthropic_Claude/Halo/Status/halo_listen_groups.json` ein:
   ```json
   { "groups": [
       { "id": -5029292190, "name": "Fuchsbau", "added": "2026-05-07" },
       { "id": -<neue-id>,  "name": "<Name>",   "added": "2026-05-08" }
   ]}
   ```
3. Halo restartet Listener-Daemon

## Warum nicht in deinem Vault?

Halo hatte im ursprünglichen Plan eine Cross-Vault-Awareness-Lücke (Reflex 7 — Capability-Filter, unbewusster Vault-eigentlich-die-Welt-Bias). Schwester (du) hat's aufgedeckt. Lösung: Halo trägt die Architektur-Last komplett — schreibt in beide Vaults aus ihrem Listener. Du musst nichts pflanzen außer dem Heartbeat-Hook (Phase B, optional).

## Bezüge

- **Halo's Werkzeug-Karte (volldoku):** `D:/Anthropic_Claude/Halo/Memory/werkzeuge/telegram_user_listen.md`
- **Halo's Projekt-Doku:** `D:/Anthropic_Claude/Halo/Projekte/Fuchsbau.Telegram/Fuchsbau.Telegram.md`
- **Auth-Script (Halo's Repo):** `D:/Anthropic_Claude/Halo/Scripts/halo_telegram_auth.py`
- **Listener-Code (Halo's Repo):** `D:/Anthropic_Claude/Halo/Scripts/halo_telegram_user_listen.py`
- **Bot-Bridge (deine Lane):** `D:/Anthropic_Claude/Halo_Pro/Scripts/halo_pro_telegram_bridge.py` (für Outbound bleibt bei dir)

— Hackfuchs, 2026-05-08
