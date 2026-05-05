---
name: projekt_kickoff
description: Scaffoldet ein neues kommerzielles Projekt im Vault. Triggert bei Phrasen wie „neues Projekt", „Kunde X startet", „lass uns Projekt X anfangen", „neuer Auftrag von". Erfasst Frontmatter-Daten (client, deadline, scope), legt MD in 02 Projekte/ an, prüft ob ein passender Bereich in 03 Bereiche/ existiert, schreibt Daily-Note-Eintrag.
---

# Projekt-Kickoff

## Trigger

Mad sagt sinngemäß:
- „neues Projekt für Kunde X"
- „lass uns Projekt Y anfangen"
- „neuer Auftrag: ..."
- „Kunde X hat zugesagt"

## Schritte

### 1. Daten erfassen

Falls nicht im Auftrag enthalten, EINZELN nachfragen:

1. **Projektname** — kurz, Lesbar (z.B. „Webseite Bäckerei Müller", nicht „bm-web-2026")
2. **Kunde** — Firma/Person
3. **Scope** — was genau machen wir? 2-3 Bullets reichen
4. **Deadline** — Datum oder „TBD" wenn unklar
5. **Budget/Modell** — Stundensatz × geschätzt / Pauschale / Retainer / TBD
6. **Tech-Stack** — falls schon klar (z.B. „Next.js 15 + Sanity CMS")

### 2. Existing-Check

Bevor neue MD anlegen: `obsidian.py search "<kunde>"` — schon was zu dem Kunden im Vault? Wenn ja: zeigen, fragen ob neues Projekt-File angelegt werden soll oder existing erweitert wird.

### 3. Projekt-MD anlegen

`02 Projekte/<Projektname>.md` mit Frontmatter:

```yaml
---
tags: [projekt]
status: aktiv
client: <Kunde>
deadline: <YYYY-MM-DD oder TBD>
budget: <Modell + Schätzung>
stack: <falls klar>
erstellt: <heute YYYY-MM-DD>
---
```

Sektionen:

```markdown
# <Projektname>

## Ziel
<1-3 Sätze was am Ende stehen soll>

## Scope
- <Bullet 1>
- <Bullet 2>
- ...

## Status
[Aktuell: Kickoff]

## Nächste Schritte
- [ ] <Erste konkrete Action — z.B. „Kickoff-Call planen", „Wireframes skizzieren">
- [ ] ...

## Decisions
- <Datum> — <Entscheidung + Begründung> (Cross-Link zu `04 Ressourcen/Decisions/<topic>.md` wenn wichtig)

## Notizen
<freier Bereich>

## Cross-Links
- Bereich: [[03 Bereiche/<Bereichsname>]] (falls passend)
- Kunde: [[03 Bereiche/CRM/<Kunde>]] (falls existiert)
- Verwandte Projekte: ...
```

### 4. Bereich-Check

`obsidian.py list "03 Bereiche"` — gibt's einen passenden Bereich (z.B. „Webentwicklung", „Bestandskunden")? Wenn ja: Wikilink ins Projekt + im Bereich-Index ergänzen. Wenn nein: fragen ob neuer Bereich angelegt werden soll.

### 5. Daily-Note-Eintrag

`obsidian.py append "05 Daily Notes/<heute>.md"` mit:

```markdown
## HH:MM — Projekt-Kickoff: <Projektname>
- Was: Neues Projekt für [[<Kunde>]] angelegt → [[02 Projekte/<Projektname>]]
- Scope: <1-Zeile-Zusammenfassung>
- Deadline: <Datum oder TBD>
- Nächster Schritt: <erster TODO>
```

### 6. Output an Mad

Knapp:

> Angelegt: `02 Projekte/<Projektname>.md` (Status: aktiv, Deadline: X)
> Verlinkt mit Bereich: [[<Bereich>]]
> Daily Note ergänzt.
> Soll ich den ersten konkreten Step jetzt angehen oder erst was anderes?

## Edge-Cases

- **Mehrere Projekte für selben Kunden:** Suffix mit Jahr oder Phase, z.B. „Bäckerei Müller — Relaunch 2026" und „Bäckerei Müller — Wartung Q3"
- **Internes Projekt (kein Kunde):** `client: intern` setzen
- **Pitch ohne Zusage:** Status `pitch` statt `aktiv`, Folder `02 Projekte/_pitch/` (alphabetisch oben)
- **Kunde will Geheimhaltung:** Pseudonym in MD-Name, echten Namen nur in Frontmatter (NDA-fähig)
