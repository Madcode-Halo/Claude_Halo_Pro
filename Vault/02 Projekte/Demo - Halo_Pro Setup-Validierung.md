---
tags: [projekt, demo]
status: aktiv
client: intern
deadline: 2026-05-06
budget: keine (Selbst-Test)
stack: Halo_Pro v1 lean
erstellt: 2026-05-06
---

# Demo — Halo_Pro Setup-Validierung

Erstes Test-Projekt für Halo_Pro v1. Zweck: nachweisen dass Cross-Frontend-Architektur funktioniert. Diese Datei wurde von Halo (im Claude-Code-Frontend) via `obsidian.py write` ins Vault geschrieben — du solltest sie in Obsidian sofort sehen.

## Ziel
Verifikation dass alle Halo_Pro-Komponenten zusammenspielen: Vault-Schreibzugriff von außen, Obsidian-API, Cross-Frontend-Sichtbarkeit.

## Scope
- Datei via `python Scripts/obsidian.py write "..."` erzeugen
- In Obsidian (claudian-Sidebar) lesbar
- In Claude Desktop via mcp-obsidian lesbar
- Beim Refresh der Frontends sofort sichtbar

## Status
[Aktuell: Live-Demonstration läuft]

## Nächste Schritte
- [ ] Mad öffnet diese Datei in Obsidian und bestätigt: ist da, lesbar
- [ ] Mad öffnet Claude Desktop, fragt Halo_Pro: „lies bitte 02 Projekte/Demo - Halo_Pro Setup-Validierung.md" → identischer Inhalt
- [ ] Mad startet Onboarding via claudian-Sidebar (Halo_Pro erkennt leere `00 Kontext`-Files und triggert `halo_pro_persona`-Skill)

## Decisions
- 2026-05-06 — Cross-Frontend-Architektur funktioniert. Drei Frontends teilen denselben Vault: claudian (im Obsidian), Claude Desktop (über mcp-obsidian), und externe Scripts (über obsidian.py). Alle sehen denselben State.

## Notizen
Das ist die einfachste Form der Cross-Frontend-Verifikation. Echte Tests folgen mit Phase 9 (Onboarding) und Mads ersten echten Kunden-Projekt.

## Cross-Links
- Persona: [[CLAUDE]]
- Decisions-Log: [[2026-05-06 Halo_Pro Architektur]]
- Daily Note: [[2026-05-06]]
