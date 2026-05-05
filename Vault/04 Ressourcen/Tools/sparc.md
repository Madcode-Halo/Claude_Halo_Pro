---
name: 🎯 SPARC — 5-Phasen-Workflow
description: Spec → Pseudocode → Architecture → Refine → Complete. Quality-Gate-Werkzeug für Webdesign-Aufträge und Multi-Step-Builds. Konzept aus Ruflo geklaut, schlank für Halo-Solo-Use-Case.
type: reference
status: active
purpose: Webdesign-Aufträge (Claryo.Web + zukünftige Kunden) sauber von Briefing zur Lieferung führen ohne Halluzinations-Drift. Jede Phase liefert ein konkretes Artefakt — ohne Artefakt kein Phasen-Wechsel. Verhindert "ich hab schon mal mit dem Code angefangen" bevor Spec steht.
family: werkzeuge
created: 2026-04-29
loaded_by: on-demand
depends_on: [masterplan.md, werkzeuge_design_prinzip.md]
criticality: kritisch
keywords: [sparc, workflow, webdesign, spec, architecture, pipeline, quality-gate, claryo, multi-phase]
last_audited: 2026-04-29
tags: [quality-gate, workflow, webdesign, halo-kern]
---

<!-- Quality-Gate. Konzept aus Ruflo (MIT) übernommen, Implementation Halo-eigen. Mad-Direktiv 2026-04-29: nur Konzepte klauen, keine Ruflo-Installation wegen 2 CRIT + 9 HIGH Sicherheitslücken. -->

## Zweck

**Webdesign-Auftrag ≠ "schreib mir eine Webseite".** Es gibt einen Bogen vom Briefing bis zur Lieferung — und an jeder Stelle kann gedriftet werden, wenn man zu früh in Code springt.

SPARC zwingt zum Phasen-Denken: jede Phase hat **einen Output**, jeder Output ist Pflicht-Artefakt bevor die nächste Phase startet. Halo darf nicht "schnell mal Code schreiben" wenn die Spec wackelt. Mad sieht jeden Phasen-Übergang im Briefkasten als Event.

Symmetrie zu `masterplan.md`: Masterplan ist für Architektur-Tasks innerhalb eines Projekts. SPARC ist für Auftraggeber-Pipelines (Briefing → Lieferung).

## Die 5 Phasen

### S — Spec (Briefing → strukturierte Anforderungen)

**Output:** `<projekt>/spec.md`

**Inhalt-Pflicht:**
- Wer ist der Auftraggeber? Was ist seine Branche / Zielgruppe?
- Was ist das Geschäftsziel hinter der Webseite (mehr Leads, Markenbild, Self-Service, ...)?
- Was sind die 3 wichtigsten User-Journeys?
- Was sind explizite Non-Goals?
- Welche Inhalte/Daten müssen rein (Texte, Bilder, externe Embeds)?
- Erfolgs-Kriterien (Lighthouse-Score, Time-to-Interactive, Conversion-Rate, ...)?

**Phasen-Übergang erlaubt nur wenn:** Mad bestätigt die Spec mit "OK Spec" oder ändert sie. Bei Auftraggeber-Projekt: schriftliche Bestätigung des Auftraggebers im Spec-File archivieren.

### P — Pseudocode (Site-Map + Component-Tree als Skizze)

**Output:** `<projekt>/pseudocode.md`

**Inhalt-Pflicht:**
- Site-Map (alle Routen)
- Component-Tree pro Route (Header → Hero → ... → Footer)
- State-Flow (woher kommen Daten, wo werden sie gespeichert)
- API-Endpoints wenn dynamisch
- Fehlerfälle (404, leere States, Loading)

**Noch kein Code.** Das ist ein Denk-Werkzeug — wenn die Pseudocode-Skizze schon nicht aufgeht, würde der echte Code es auch nicht.

### A — Architecture (Tech-Stack + Pfade + Abhängigkeiten)

**Output:** `<projekt>/architecture.md`

**Inhalt-Pflicht:**
- Stack-Wahl (z.B. Astro + shadcn + Tailwind v4 + Hono — siehe `Memory/werkzeuge/webdev_stack_2026.md`)
- Folder-Struktur des Repos
- Build-Pipeline (Coolify? Vercel? eigener Server?)
- Auth-Setup (Better-Auth? Keine?)
- DB falls dynamisch
- Environment-Variablen (welche, wo gespeichert)
- Drittanbieter-Services (Analytics, Forms, CMS, ...)

**Phasen-Übergang erlaubt nur wenn:** Halo hat alle Stack-Entscheidungen mit `werkzeuge_design_prinzip.md` validiert (klüger nicht dümmer).

### R — Refine (Bauen + iteriernd verbessern)

**Output:** Live-Code im Repo + Refine-Diffs in `<projekt>/refine_log.md`

**Was hier passiert:**
- Initial-Build der Komponenten (idealerweise via Lovable/Bolt-Skeleton + dann Halo verfeinert — siehe `vibe_coding_workflow.md`)
- Iterative UX-Polish-Runden (`/impeccable polish` für jede Hauptseite)
- A11y-Audit (`/impeccable audit`)
- Performance-Pass (Lighthouse, Bundle-Size, Image-Optimization)
- Content-Pass (echte Texte vom Auftraggeber statt Lorem)

**Refine ist die einzige Phase die mehrere Tage/Wochen dauern kann.** Andere Phasen sind Kurz.

### C — Complete (Lieferung + Übergabe)

**Output:** `<projekt>/complete.md` + Deploy + Briefkasten-Critical-Push

**Pflicht-Checkliste:**
- [ ] Lighthouse > 90 (mobile + desktop)
- [ ] A11y-Score > 95 (keine kritischen Issues)
- [ ] SEO-Basics (OG-Tags, Sitemap, robots.txt, Canonical)
- [ ] Forms tested (echte Submission, Spam-Schutz)
- [ ] Analytics installed wenn vereinbart
- [ ] Auftraggeber hat Zugang (Repo-Invite ODER Hand-off-Doku ODER beides)
- [ ] Backup des finalen Standes (`git tag v1.0` + Backup-Werkzeug)
- [ ] Rechnung gestellt
- [ ] Briefkasten-Event `severity=info`, `kind=projekt_complete`

**Erst wenn ALLE Häkchen** → Status auf `completed` setzen, in `Projekte/abgeschlossen/` verschieben.

## Funktioniert so

**Trigger:** neuer Webdesign-Auftrag oder Multi-Phase-Build der einen klaren Auftraggeber/Output-Zweck hat.

**Wer steuert:** Halo führt durch die Phasen, Mad bestätigt Phasen-Übergänge. Bei Auftraggeber-Projekten: Spec wird vom Auftraggeber gegengezeichnet.

**Briefkasten-Pflicht:** jeder Phasen-Übergang als Event:
```python
from halo_inbox import post
post(source="sparc", kind="program", severity="info",
     payload="<projekt>: Phase A→R abgeschlossen — architecture.md liegt")
```

## Trigger

- Mad sagt *"Auftrag von <Kunde>"* / *"neuer Webdesign-Job"* → SPARC vorschlagen
- Mad ruft direkt *"SPARC für <projekt>"* → Phase S beginnt
- Bei `Projekte/<x>/projekt.md` mit `type: webdesign-auftrag` → SPARC ist Default-Workflow

## Zweckentfremdung

- **Software-Builds (nicht-Webdesign):** geht auch — z.B. Halo-Tool-Refactor, Mobile-App-Feature
- **Migration-Projekte:** Spec = "was wandert wohin", Pseudo = Daten-Mapping, Arch = Migration-Tooling, Refine = iterative Cutover, Complete = alter Stack abschalten
- **Auftraggeber-Reporting:** Phase S+P als Angebot-Dokument nutzen — sieht professionell aus, schützt vor Scope-Creep
- **Templating für Halo-eigene Werkzeuge:** wenn ein neues Halo-Werkzeug substantieller wird, kann SPARC strukturieren

## Grenzen

- **Nicht für Mini-Tasks** — wer einen Bugfix braucht, soll keine Spec schreiben. Faustregel: > 4h Aufwand → SPARC. Sonst Surgical-Change.
- **Refine kann driften** — die Refine-Phase ist die längste und gefährlichste. Halo soll regelmäßig (alle paar Tage) prüfen ob noch Spec-konform gebaut wird, sonst Phase R → S Rückkopplung.
- **Komplett-Phase ist Pflicht** — nicht "ach reicht so". Auftraggeber-Übergabe ohne Lighthouse-Check ist Reputations-Risiko.
- **SPARC ersetzt nicht Masterplan** — Masterplan ist für Architektur innerhalb eines Builds (z.B. "wie strukturiere ich die Auth?"). SPARC ist für den Bogen Briefing→Lieferung.

## Verwandte Werkzeuge

- **Masterplan** (`masterplan.md`) — innerhalb-Projekt-Architektur. SPARC ist die übergeordnete Pipeline.
- **Werkzeuge-Design-Prinzip** (`werkzeuge_design_prinzip.md`) — wird in Phase A bei Stack-Wahl referenziert
- **Webdev-Stack 2026** (`webdev_stack_2026.md`) — Default-Stack-Wahl für Phase A
- **Vibe-Coding-Workflow** (`vibe_coding_workflow.md`) — wird in Phase R für Initial-Skeleton + Polish referenziert
- **Impeccable-Skill** (`/impeccable`) — Frontend-Polish in Phase R (audit/polish/animate)
- **Briefkasten** (`briefkasten.md`) — Phasen-Übergänge als Events
- **Backup** (`backup.md`) — Pflicht-Snapshot in Phase C

## Externe Vorbilder

- **SPARC** (Reuven Cohen / Ruflo) — ursprüngliches Konzept (MIT-lizenziert, Inspiration übernommen)
- **Design-Sprint** (Google Ventures) — verwandt aber zeitgebunden auf 5 Tage
- **Phase-Gate-Process** (klassische Engineering-Methode) — gleiche Idee, schwerer formalisiert

---

*Konzept aus Ruflo, Implementation Halo-eigen. Schlank für Solo-Use-Case. Halo zwingt sich zur Phasen-Disziplin — Drift ohne Spec ist nicht erlaubt.* 🎯
