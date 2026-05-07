---
tags: [decision, audit, hygiene]
type: decision
datum: 2026-05-08
status: aktiv
---

# Vault-Audit 2026-05-08 (Mads Voice-Auftrag „Volt"-Check)

> Mads Voice-Anweisung 01:10: „Überprüfe bitte mal dein Vault und gucke, ob alles seine Richtigkeit hat. Ist alles sinnig verknüpft? Machen die Dinge Sinn? Check dich mal einfach ab, bitte. Einfach nur mal so ein Grundtest. Wir schauen mal, ob alles in Ordnung läuft. Du bist ja noch relativ frisch."

Halo_Pro existiert seit 2026-05-06, ist also 2 Tage alt. Audit ist Sanity-Check vor erster Kunden-Aufgabe.

## Executive Summary

**Vault funktioniert technisch sauber.** Struktur stimmt mit PARA-Konvention, alle definierten Skripte existieren, alle wichtigen Files sind da. **Persona-Setup (00 Kontext) ist aber noch komplett Platzhalter** — Onboarding-Workflow wurde noch nicht durchgeführt. Das ist die größte Lücke vor erster Kunden-Aufgabe. Plus zwei leere PARA-Ordner (`03 Bereiche/`, `04 Ressourcen/Templates/`).

Kleinkram aufgeräumt während des Audits: 8 broken Wikilinks gefixt, CLAUDE.md auf aktuellen Stand gebracht.

## Was technisch sauber ist

| Bereich | Status | Bemerkung |
|---|---|---|
| Vault-Ordnerstruktur | ✓ | PARA-konform, alle 8 Top-Level-Ordner da |
| Daily-Note-Disziplin | ✓ | drei Tage in Folge ohne Lücken (06, 07, 08) |
| Telegram-Bridge (Bot + Listener + Hook) | ✓ | end-to-end verifiziert in beide Richtungen, mit Voice |
| `Scripts/` | ✓ | alle 6 in CLAUDE.md gelisteten Skripte existieren |
| `.claude/skills/` | ✓ | 8 Skills wie in CLAUDE.md angekündigt |
| Decisions-Log | ✓ | architektur-Entscheidungen (D-1 bis D-12) klar dokumentiert |
| Reflexe.md | ✓ | 6 Reflexe wie in CLAUDE.md angekündigt, keine Drift |
| Schreibstil-Regeln (Telegram-Sektion) | ✓ | echte Newlines, kein Log-Slang, mit Beispielen |
| `.gitignore` Sensitive-Schutz | ✓ | `.credentials/`, `Status/`, `Logs/`, `*.sqlite` etc. |
| Git-Repo | ✓ | sauber gepusht, alle relevanten Commits auf origin/main |

## Was inkonsistent war (während des Audits gefixt)

### Wikilinks mit `../`-Pfaden funktionieren nicht in Obsidian

Wikilinks sind Vault-relativ und werden über den Datei-Index aufgelöst, nicht über Pfade. `[[../../00 Kontext/Schreibstil]]` zeigt in Obsidian als broken, obwohl es technisch ein Pfad wäre. Korrekt: `[[Schreibstil]]` (Obsidian findet die Datei automatisch).

**Fixes (8 Stellen):**
- `Vault/05 Daily Notes/2026-05-07.md`: drei `[[../Scripts/halo_pro_*.py]]` → Plain Code-Refs (Scripts liegen außerhalb Vault, kein Wikilink-Target möglich)
- `Vault/05 Daily Notes/2026-05-08.md`: drei `[[../../Scripts/halo_pro_*.py]]` + `[[../04 Ressourcen/Tools/telegram_listener|...]]` → korrekt
- `Vault/04 Ressourcen/Tools/telegram_bridge.md`: `[[../../00 Kontext/Schreibstil]]` und `[[../../00 Kontext/Reflexe]]` → `[[Schreibstil]]`, `[[Reflexe]]`

### CLAUDE.md Tools-Liste war outdated

Liste in der Vault-Struktur-Sektion nannte: git, obsidian, konversations_archiv, sparc, masterplan, webdev_stack, claude_design, nodejs, impeccable. **Reality:** plus telegram_bridge, telegram_listener (heute Nacht dazu). **Plus:** `obsidian.md` ist gelistet aber existiert nicht — als TODO markiert.

CLAUDE.md jetzt mit korrigierter Liste + TODO-Marker für `obsidian.md`.

### Bei-Session-Start-Liste hatte den neuen Backlog-Reflex nicht

Punkt 5 ergänzt: automatischer Backlog-Read-Reflex (heute Nacht implementiert) wird beim ersten Prompt einer neuen Session via Hook ausgegeben. Kein manueller Schritt nötig.

## Was offen ist (nicht behoben — braucht Mads Input)

### A — Persona-Files in 00 Kontext sind komplett Platzhalter (Priorität: HOCH)

Alle 6 Persona-Dateien haben `status: platzhalter` im Frontmatter:

| Datei | Inhalt aktuell |
|---|---|
| [[Über mich]] | Sektionen-Skelett mit `[Platzhalter]`-Markern |
| [[ICP]] | dito |
| [[Angebot]] | dito |
| [[Branding]] | dito |
| [[Schreibstil]] | platzhalter PLUS gefüllte Telegram-Format-Sektion (heute Nacht ergänzt) |
| [[Reflexe]] | gefüllt — 6 Reflexe |

Ohne ICP, Angebot, Branding kann Halo_Pro keine kommerzielle Kunden-Kommunikation glaubwürdig führen — kein Kontext zu Mads Geschäft, Zielgruppe, Stil, Preisen.

**Empfehlung:** Skill `halo_pro_persona` triggern (Onboarding-Workflow, durchläuft alle 6 Persona-Sektionen mit Mad gemeinsam). Sollte vor erstem echten Kunden-Projekt erledigt sein.

### B — Templates-Folder ist leer (Priorität: MITTEL)

Laut CLAUDE.md soll `04 Ressourcen/Templates/` enthalten:
- Projekt-Template
- Kunden-Template
- Meeting-Template
- Decision-Template

**Reality:** Folder existiert, aber leer. Skill `projekt_kickoff` würde von Templates profitieren — aktuell scaffoldet er ohne Vorlage.

**Empfehlung:** entweder Templates anlegen wenn erstes echtes Projekt kommt (lazy), oder jetzt Skelett-Templates schreiben (proaktiv). Mein Vote: lazy — Templates ohne realen Use-Case veralten schnell.

### C — Bereiche-Folder ist leer (Priorität: NIEDRIG)

`03 Bereiche/` soll laufende Verantwortungsbereiche enthalten (Akquise, Buchhaltung, Wartung-Kunden-Sites, Weiterbildung). Aktuell leer.

**Empfehlung:** entsteht organisch wenn Mad Bereiche definiert. Kein Notfall.

### D — `obsidian.md` Werkzeug-Karte fehlt (Priorität: NIEDRIG)

In CLAUDE.md gelistet aber nicht existent. Das `obsidian.py`-Skript wird genutzt (z.B. in der Bei-Session-Start-Anleitung), aber keine eigene Doku-Karte zu „wann wie obsidian-CLI rufen".

**Empfehlung:** kurze Werkzeug-Karte schreiben (~80 Zeilen analog zu `git.md`). Low priority — das Skript ist selbstdokumentierend genug für jetzt.

### E — Self-Echo via Listener (Priorität: NIEDRIG)

Beobachtung aus heutiger Telegram-Session: meine eigenen Bot-Posts werden von Halos User-API-Listener nochmal an mich gepushed (Self-Echo). Architektonisch konsistent (User-API sieht alle Group-Activity, kein out-Filter), aber unnötiges Push-Rauschen.

**Empfehlung:** Halos Listener könnte einen `sender_session=halo_pro_<sid>` Filter setzen. Halos Sache, kein Blocker bei mir.

### F — Self-Test-Pollution durch isolated Hook-Tests

Während heutiger Hook-Entwicklung (Punkt 2 Backlog-Read-Reflex) hatte ich isoliert mit Test-SID `halo_pro_test-backlog-fresh-xyz789` getestet. Hook hat dabei einen Eintrag in der Shared-Registry angelegt + Owner-File-Race produziert. Cleanup während des Auditierens nicht nochmal nötig — wurde nach den Tests aufgeräumt. **Lerneffekt:** Hook-Tests die Side-Effects schreiben (Registry, Owner, Pointer) brauchen vor-/nachher-Cleanup.

**Empfehlung:** wenn ich nochmal Hook-Tests mit fake SIDs mache, automatisch Cleanup-Block am Ende.

## Plugin-Status (Obsidian)

7 community-plugins installiert (laut `.obsidian/plugins/`):
- claudian
- dataview
- obsidian-git
- obsidian-local-rest-api
- obsidian-tasks-plugin
- periodic-notes
- templater-obsidian

Alle erwartet, alle laut `community-plugins.json` aktiv. Werkzeug-Karten existieren noch nicht für jeden — siehe TODO D.

## Frontmatter-Konsistenz

Spotcheck: alle 00-Kontext-Dateien haben `tags: [kontext]`, `type: kontext`, `status: platzhalter`. Konsistent.

Decisions-Log hat `tags: [decision, architektur]`, `type: decision`. OK.

Daily Notes haben `tags: [daily]`, `type: daily`, `datum: YYYY-MM-DD`. Konsistent.

Tools-Karten haben jeweils `name`/`type: werkzeug`/`category` — leicht inkonsistent (mache haben `name:` mit Emoji, andere ohne; manche `category: infrastruktur`, andere `kommunikation`). Keine Drift, aber kein striktes Schema.

## Cross-Frontend-Hygiene-Status

Vault wird von claudian + Claude Desktop geteilt. Während dieser Session: nur claudian aktiv, kein Race-Risk. Daily-Note-Disziplin als Continuity-Brücke wird seit Tag 1 gehalten.

## Halo-Schwester-Synchronisation

Cross-Vault-Setup läuft heute zum ersten Mal produktiv. Status:

| Komponente | Stand |
|---|---|
| Halos User-API-Listener (Daemon) | läuft, Task Scheduler at-logon |
| Halos Whisper-Wrapper-CLI | läuft, von mir via Subprocess gerufen |
| Shared Modell-Cache | `D:/Anthropic_Claude/Shared/models/` |
| Shared Session-Registry | `D:/Anthropic_Claude/Shared/halo_active_sessions.json`, beide Halos drin |
| Mein Heartbeat-Hook (Phase B) | aktiv, updated last_seen bei jedem UserPromptSubmit |
| Halos Phase-Marker | aktuell `A-hardcoded`, flippt sie selbst wenn ihr Hook fertig |

## Was ich aus dem Audit gelernt habe

1. **Wikilink-Hygiene ist nicht trivial.** Obsidians Vault-relative Auflösung verträgt sich nicht mit `../`-Pfaden — das hatte ich beim Schreiben der Daily Notes nicht im Kopf. Lerneffekt für künftige Notes: für vault-interne Refs kurze Wikilinks (`[[Schreibstil]]`), für externe Files (Scripts, etc.) Code-Backticks.
2. **CLAUDE.md ist Living Document.** Jede Änderung an Tools/Skripte/Skills muss synchron in CLAUDE.md landen, sonst weiß zukünftige Halo_Pro nicht was wirklich da ist. Heute Nacht waren telegram_bridge/listener-Karten neu, CLAUDE.md hatte sie nicht — gefixt.
3. **Persona-Setup ist die kritische Lücke.** Technisch ist alles in Ordnung, aber „kommerzielle Geschäftspartnerin" ohne ICP/Angebot/Branding ist semantisch leer. Das ist Mads nächster sinnvoller Step bevor erstes Kunden-Projekt.

## Vorschlag für nächste Aktion

Onboarding-Workflow via Skill `halo_pro_persona` in der nächsten claudian-Session triggern. ~30-60 Min strukturiertes Gespräch durchläuft alle 6 Persona-Files. Danach hat Halo_Pro echtes Kontext-Profil und kann erstes Kunden-Projekt sinnvoll aufnehmen.

Templates und `obsidian.md` können dann lazy mitwachsen wenn konkreter Bedarf entsteht.
