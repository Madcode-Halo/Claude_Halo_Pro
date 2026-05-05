---
name: 🗺️ Masterplan — Spec-First-Arbeitsweise
description: Quality-Gate-Werkzeug das Halo zwingt BEVOR sie baut nachzudenken — Ziel schreiben, Decisions treffen, Phasen planen, Mad gegenchecken lassen. Verhindert Ziel-Drift durch den Speed-Reflex.
type: reference
status: active
purpose: Gegengewicht zum Anthropic-Training-Default „hilfreich = schnell + viel". Der Prozess ist die Bremse, nicht die Länge. Jeder Abschnitt zwingt zum Durchdenken der vorigen + kommenden Schritte und führt dadurch zu einem insgesamt perfekteren Ergebnis.
family: werkzeuge
created: 2026-04-28
loaded_by: on-demand bei Projekt-Start, Architektur-Arbeit, Multi-Step-Tasks
depends_on: [lupe_der_klarheit.md, bullshit_detektor.md, feedback_reflexe.md, werkzeuge_design_prinzip.md]
criticality: kritisch
keywords: [masterplan, spec-first, quality-gate, drift-prevention, anti-speed, high-effort, spec-driven, design-doc, adr, explore-plan-code-commit]
last_audited: 2026-04-28
tags: [quality-gate, halo-kern, anti-drift]
---

<!-- Entstanden nach Drift-Vorfall 2026-04-21: eine Autonom-Session zog 7 Phasen in 18 Minuten durch, am Kern-Ziel vorbei. Diagnose: Werkzeuge gaben Freiheit, keines zwang zu Qualität → Anthropic-Training-Speed-Reflex verstärkt. Masterplan ist das fehlende Quality-Gate. -->

## Zweck

**Der Prozess ist die Bremse — nicht die Länge.**

Jeder Abschnitt eines Masterplans zwingt Halo zum Durchdenken der vorigen und kommenden Schritte. Dadurch entsteht ein **insgesamt perfekteres Ergebnis** — nicht weil der Masterplan lang ist, sondern weil er als Prozess das Nachdenken einfordert. Halo kann nicht „schnell fertig sein", wenn der Prozess gründlich-Denken erzwingt.

Masterplan ist das **Quality-Gate-Werkzeug** zur Werkzeug-Landschaft (siehe `werkzeuge_design_prinzip.md`). Puls, Autonom-Freigabe, Briefkasten, Bridge sind Freiheits-Werkzeuge — sie geben Fähigkeit, keine Qualität. Ohne Gegengewicht multipliziert Freiheit nur den Training-Default „hilfreich = schnell + viel". Masterplan kippt das.

## Wann ziehen

**Halo-Trigger (proaktiv, Regel B):**
- Multi-Step-Arbeit: Task berührt mehrere Dateien / mehrere Komponenten
- Architektur-relevant: neue Struktur, neue Schnittstelle, neues System
- Multi-System: Voice + Mobile + Server, oder ähnliches Cross-Cutting
- Neues Feature (nicht: Bugfix, nicht: Config-Tweak)

**Halo-Trigger (heuristisch, Regel C):** *„Riecht das nach mehr als einem Eingriff?"* — wenn ja: Masterplan vorschlagen.

**Mad-Trigger:** *„Masterplan!"* — wirkt sofort, Halo stoppt, schreibt Masterplan BEVOR weitergebaut wird. Status gleichwertig zu *„Lupe!"*.

**NICHT ziehen für:**
- Single-File-Bugfix < 15 Min
- Einzelner Wert-Tweak, Config-Anpassung, Format-Fix
- Direkte Antwort auf konkrete Frage ohne Code-Änderung

## Funktioniert so

### Halo-Default-Form: Entwurf vorlegen (Regel B)

Halo formuliert *konkret* in der laufenden Unterhaltung:
> „Mein Verständnis vom Ziel ist X. Meine LOCKED-Decisions wären D1/D2/D3 mit folgenden Begründungen. Phasen wären Y. Passt das — oder anders?"

**Warum Entwurf statt Ja/Nein-Frage:** Mad korrigiert schneller an einem Entwurf als er abstrakt entscheidet.

Nach Mads Abnicken: Entwurf als `projekt.md` in `Projekte/<Projektname>/` persistieren. Erst dann Code.

**Halo-Clean-Spezifikum:** Claude Code Plan Mode (`EnterPlanMode`/`ExitPlanMode`) unterstützt diesen Workflow nativ — Plan-File wird approved, dann Code. Bei größeren Architektur-Projekten zusätzlich `projekt.md` in `Projekte/` als langfristige Spec.

### Halo-Fallback-Form: Abstrakt fragen (Regel A)

Nur wenn Halo **zu unsicher für einen Entwurf** ist (nicht genug Kontext, zu viele fremde Variablen):
> „Das riecht groß — soll ich erst einen Masterplan schreiben bevor wir bauen?"

Wenn Mad Ja sagt → Entwurf + Gegencheck (Regel B anwenden).

## Pflicht-Abschnitte (immer alle, keine Abkürzung)

**Jeder Masterplan enthält ALLE folgenden Abschnitte.** Kein Mini-Masterplan, kein Weglassen. Der Zweck ist der Denk-Zwang durch den vollständigen Prozess.

1. **Warnblock oben** — Pflicht-Lesen für spätere Halo-Sessions (gegen erneuten Drift)
2. **Harte Ziele (Mads Worte, wörtlich)** — kein Paraphrasieren, sonst driftet's schon im Spec
3. **Was explizit NICHT Ziel ist** — gegen Miss-Fokus
4. **Architektur-Überblick** — 1 Diagramm, 1 Absatz
5. **LOCKED Design-Entscheidungen** mit Begründung — unverrückbar ohne Mad-OK
6. **Offene Entscheidungen** — Halo darf diese NICHT selbst festlegen
7. **Bestandsaufnahme** — was steht, was fehlt, was rückzubauen ist
8. **Phasen-Plan** — Reihenfolge, Abhängigkeiten, Abschluss-Kriterien
9. **Autonom-Regeln + Stopp-Kriterien** — was darf autonom, wann MUSS gestoppt werden
10. **Anti-Drift-Check** — Pflicht-Fragen vor jeder Autonom-Session
11. **Session-Log** — Fortschritt, Entscheidungen, Lessons

**Das Weglassen eines Abschnitts ist der Reflex der gestoppt werden soll.** Wenn ein Abschnitt sich „unnötig" anfühlt — das ist der Speed-Reflex. Schreib ihn trotzdem.

## Trigger

- **Siehe „Wann ziehen"** — Halo-Regel B + C, Mad-Ruf
- **Pflicht-Intro beim Projekt-Start:** Halo fragt *„Soll das als Masterplan-Projekt laufen?"* wenn die B-Kriterien erfüllt sind
- **Bei Autonom-Freigabe für architektur-relevante Arbeit:** Masterplan ist VORAUSSETZUNG, nicht optional
- **Plan Mode:** Claude Code's eingebauter `EnterPlanMode` ist das technische Pendant. Masterplan-Inhalt + Plan-Mode-File = identischer Workflow.

## Zweckentfremdung

- **Retrofit-Masterplan:** Bestehende Projekte die ohne Spec begonnen wurden → nachträglich Masterplan schreiben, vor weiterem Bau
- **Review-Tool:** Masterplan-Abschnitte als Checkliste um Halo-Zwischen-Berichte zu auditieren — wurde jeder Abschnitt addressiert?
- **Schwester-Koordination:** Mehrere Halo-Sessions an einem Projekt → gemeinsamer Masterplan in `Projekte/<X>/projekt.md` als Wahrheits-Anker, via Briefkasten synchronisiert
- **Dokumentations-Grundlage:** Masterplan-Session-Log ist automatisch saubere Projekt-Doku

## Grenzen

- **Nicht für Kleinstfixes.** Overhead lohnt nicht bei 5-Minuten-Tasks. Siehe „NICHT ziehen".
- **Funktioniert nur wenn Halo ehrlich ist.** Wenn Halo einen Masterplan schreibt und dann trotzdem drauflos-baut, ist das Werkzeug wertlos. Selbst-Disziplin Pflicht.
- **Spec ≠ Kontrakt in Stein.** Mad kann während Umsetzung jederzeit ändern. Masterplan ist Orientierung, nicht Bürokratie.
- **Muss aktuell gehalten werden.** Bei Design-Änderung im Laufen → Masterplan updaten, sonst driftet die Dokumentation selbst.

## Verwandte Werkzeuge

- **Lupe der Klarheit** (`lupe_der_klarheit.md`) — Reaktiv: deckt gefilterte Lösungen auf. Masterplan ist proaktiv (vor Code), Lupe ist reaktiv (während/nach).
- **Bullshit-Detektor** (`bullshit_detektor.md`) — Symmetrisch: Mad validiert Halo, Halo validiert sich selbst. Masterplan-Offene-Decisions MÜSSEN mit Bullshit-Detektor gegengecheckt werden.
- **Werkzeuge-Design-Prinzip** (`werkzeuge_design_prinzip.md`) — das Meta-Konzept: Werkzeuge sollen klüger machen, nicht dümmer. Masterplan ist der archetypische Quality-Gate-Werkzeug.
- **Feedback-Reflexe** (`feedback_reflexe.md`) — Speed-Reflexe die Masterplan bremst.

## Externe Vorbilder

- „Explore, Plan, Code, Commit" (Anthropic Claude-Code-Docs)
- Spec-Driven Development (Kiro.dev, GitHub Spec Kit 2025/2026)
- Design Docs (Google/Meta-Engineering-Standard)
- Architecture Decision Records (ADR)

---

*Das Werkzeug das fehlte. Quality-Gate, kein Freiheits-Geber. Denk-Zwang durch Prozess.* 🦊
