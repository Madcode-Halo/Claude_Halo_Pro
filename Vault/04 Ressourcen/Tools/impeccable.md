---
name: 🎨 Impeccable — Anti-AI-Slop-Design-Skill
description: Pflicht-Werkzeug für JEDE UI-Implementation — Frontend-Design-Skill (23 Cmds, 35 References, CLI-Detector) der AI-Slop verhindert und production-grade Output erzwingt
type: reference
status: active
purpose: Verhindert generischen AI-Look (Inter/Purple/Glass/Card-in-Card), erzwingt Design-Disziplin via Pre-Flight-Gates, Pipeline shape→craft→audit→polish vor jedem UI-Mutate
family: werkzeuge
created: 2026-04-29
loaded_by: on-demand
depends_on: [webdev_stack_2026, claude_design]
criticality: kritisch
keywords: [impeccable, design, frontend, ui, anti-slop, audit, polish, craft, shape, critique, animate, colorize, typeset, layout, harden, optimize, adapt, clarify]
last_audited: 2026-04-29
tags: [webdev, design, skill, claude-code]
---

<!-- DAS Anti-AI-Slop-Werkzeug. Vor jeder UI: shape oder craft. Vor jedem Deploy: polish + audit. Bei Lovable/Bolt-Output: detect (CLI-Lint). Skill ist user-invocable via /impeccable <cmd> — Halo MUSS bei UI-Tasks präventiv erwähnen. -->

## Zweck

Pflicht-Werkzeug für jede UI-Implementation — verhindert dass Halo (und alle anderen AI-Harnesses) generischen Frontend-Output produziert. Skill von **Paul Bakaus** (Apache 2.0, basiert auf Anthropics eigenem `frontend-design`-Skill). Installiert lokal in `.claude/skills/impeccable/`.

**Kernidee:** AI-generierte UIs konvergieren auf identische Clichés (Inter-Font, Purple-Gradients, nested Cards, gray-on-colored Text). Impeccable bricht diesen Konvergenz-Reflex via Pre-Flight-Gates und 35 referenzierter Design-Disziplinen.

## Funktioniert so

### Skill aufrufen
```
/impeccable <command> [target]
```
User-invocable Skill — Mad oder Halo selbst tippt das. Halo erkennt UI-Kontext und schlägt den passenden Befehl vor.

### Pre-Flight-Gates (PFLICHT vor File-Edit)

| Gate | Check | Bei Fail |
|------|-------|----------|
| **Context** | `node .claude/skills/impeccable/scripts/load-context.mjs` ausgeführt | Loader laufen lassen |
| **Product** | `PRODUCT.md` existiert, >200 chars, kein `[TODO]` | `/impeccable teach` |
| **Command** | Matching reference-File geladen (z.B. `reference/audit.md`) | Reference laden |
| **Craft** | Bei `craft`: user-confirmed shape brief vorhanden | `/impeccable shape`, dann user-bestätigung |
| **Image** | Visual probes generated oder skipped mit Begründung | shape.md / craft.md gate lösen |
| **Mutation** | Alle obigen pass | NICHT editieren bis grün |

Halo MUSS vor File-Edit folgendes ausgeben:
```
IMPECCABLE_PREFLIGHT: context=pass product=pass command_reference=pass shape=pass|not_required image_gate=pass|skipped:<reason> mutation=open
```

### 23 Sub-Befehle (gruppiert)

**Setup-Phase (Pflicht-Phase 0):**
| Cmd | Was |
|-----|-----|
| `/impeccable teach` | PRODUCT.md + DESIGN.md generieren (Users, Brand, Tone, Anti-References) |
| `/impeccable document` | DESIGN.md aus existing Code rückgenerieren (Bestands-Projekt) |
| `/impeccable extract` | Reusable Components + Tokens ins Design-System ziehen |

**Plan/Build (Phase 1):**
| Cmd | Was |
|-----|-----|
| `/impeccable shape` | UX/UI-Plan VOR Code — Brief mit Layout, Hierarchie, Komponenten |
| `/impeccable craft` | Full Shape-then-Build-Flow mit visueller Iteration |

**Review (Phase 2):**
| Cmd | Was |
|-----|-----|
| `/impeccable critique` | UX-Review: Hierarchie, Klarheit, emotionale Resonanz |
| `/impeccable audit` | Tech-Quality: a11y, Performance, Responsive |

**Tone-Knöpfe (Phase 3 — Stilistik):**
| Cmd | Was |
|-----|-----|
| `/impeccable bolder` | Langweilige Designs verstärken |
| `/impeccable quieter` | Zu lautes Design beruhigen |
| `/impeccable distill` | Auf Essenz reduzieren |
| `/impeccable delight` | Joy-Momente einfügen |
| `/impeccable overdrive` | Technisch außergewöhnliche Effekte |

**Style-Disziplinen (Phase 3 — Detail):**
| Cmd | Was |
|-----|-----|
| `/impeccable typeset` | Fonts, Hierarchie, Größen fixen |
| `/impeccable layout` | Layout, Spacing, visueller Rhythmus |
| `/impeccable colorize` | Strategische Farb-Setzung |
| `/impeccable animate` | Purposeful Motion (keine Bounce/Elastic) |

**Polish (Phase 4 — Pre-Deploy):**
| Cmd | Was |
|-----|-----|
| `/impeccable polish` | Final pass + Design-System-Alignment + Shipping-Readiness |
| `/impeccable harden` | Error-Handling, i18n, Text-Overflow, Edge-Cases |
| `/impeccable onboard` | First-Run-Flows, Empty-States, Activation-Paths |
| `/impeccable optimize` | Performance-Improvements |
| `/impeccable adapt` | Device-Adaptation |
| `/impeccable clarify` | UX-Copy-Verbesserung |

**Live-Modus:**
| Cmd | Was |
|-----|-----|
| `/impeccable live` | Browser-basierte Element-Iteration (visual variant mode) |

**Shortcut:** `/impeccable pin <cmd>` erzeugt Direkt-Slash-Command (`/audit`, `/polish` etc.).

### CLI-Tool — `npx impeccable detect`

Anti-Slop-Linter, läuft ohne AI-Harness:
```bash
npx impeccable detect src/                    # Verzeichnis scannen
npx impeccable detect index.html              # Datei scannen
npx impeccable detect https://example.com     # Live-URL scannen
npx impeccable detect --fast --json .         # Regex-only, JSON-Output
```

Erkennt: Side-Stripe-Borders, Gradient-Text, Bounce-Easing, Dark-Glows, Line-Length-Issues, Touch-Target-Größen, Missing-Headings, Inadequate-Padding usw.

**Use-Case:** Pre-Commit-Hook oder CI-Step. Bei jedem `git commit` automatisch laufen lassen.

### 35 Reference-Files in `.claude/skills/impeccable/reference/`

**Disziplinen (Designer-Pflicht-Lektüre):**
- `typography.md`, `color-and-contrast.md` (OKLCH, Dark-Mode, a11y)
- `spatial-design.md`, `layout.md`, `motion-design.md`
- `interaction-design.md`, `responsive-design.md`, `ux-writing.md`
- `cognitive-load.md`, `personas.md`, `heuristics-scoring.md`

**Register-Files:**
- `brand.md` — wenn Design IS das Produkt (Marketing, Landing, Portfolio)
- `product.md` — wenn Design SERVES das Produkt (App, Admin, Dashboard)

**Befehl-Referenzen:**
- Eine `.md` pro Sub-Command (audit.md, craft.md, polish.md, shape.md, …)

## Trigger

**Halo MUSS Impeccable präventiv vorschlagen wenn:**
- Mad sagt *„bau mir UI / Webseite / Landing / Dashboard / App"*
- Mad zeigt Lovable/Bolt/v0-Output zur Polish-Übergabe
- Mad sagt *„sieht generisch aus"* / *„zu langweilig"* / *„zu laut"* / *„fühlt sich AI-generiert an"*
- Halo selbst will Frontend-Code schreiben (vor erstem JSX/HTML/CSS)

**Halo nutzt Impeccable selbst proaktiv wenn:**
- Vor jedem UI-Mutate → Pre-Flight-Gates durchgehen
- Nach UI-Implementation → `/impeccable polish` + `/impeccable audit` vor Deploy
- Bei AI-Builder-Output (Lovable/Bolt/v0) → `npx impeccable detect` zur Slop-Erkennung
- Bei *„fertig"*-Reflex → `/impeccable critique` als externer Blick

**Hard-Rule:** Bei UI-Code-Änderungen ohne PRODUCT.md → `/impeccable teach` zuerst.

## Zweckentfremdung

- **Code-Review-Tool:** Bei Pull-Requests von externen Devs `npx impeccable detect` als objektiver Maßstab
- **Stil-Blueprint:** Reference-Files als Lehrmaterial — `reference/typography.md` lesen lehrt wie ein Designer denkt
- **Slop-Audit für eigene Halo-Tools:** Halo's Statusline, Banner, Web-Dashboards selbst durch `detect` jagen
- **Prompt-Engineering:** Impeccable's command-metadata.json als Pattern für eigene Halo-Skill-Definitionen

## Grenzen

- **Nicht für Backend-Tasks** — Skill explizit „Not for backend-only or non-UI tasks"
- **Pre-Flight-Pflicht ist streng** — `/impeccable craft` ohne shape brief = Skill weigert sich
- **PRODUCT.md erfordert User-Confirmation** — Halo darf nicht eigenständig PRODUCT.md aus Mads Prompt ableiten ohne Bestätigung
- **CLI braucht Node.js** — bei Halo's System (Node v24) gegeben, woanders ggf. nicht
- **Skill-Updates manuell** — kein auto-update, bei neuen Versionen re-clone aus dem Repo
- **Konflikt mit Halo's CLAUDE.md** — der Skill bringt eigene CLAUDE.md im Repo mit; wir nutzen NUR `.claude/skills/impeccable/`, NICHT die Repo-CLAUDE.md
- **Token-Kosten** — Pre-Flight + Reference-Loading kostet bei jedem Aufruf ~5-10k Tokens

## Halos Standard-Pipeline für Webdev

```
1. /impeccable teach     → PRODUCT.md + DESIGN.md
2. /impeccable shape     → UX-Plan, user-confirmation
3. /impeccable craft     → tatsächlicher Build mit visual iteration
4. /impeccable polish    → final pass
5. /impeccable audit     → a11y/perf/responsive Check
6. npx impeccable detect → CLI-Lint vor commit
7. → Deploy
```

## Update-Workflow

Wenn Impeccable in neuer Version released:
```bash
# tmp-Klon, Skill-Folder ersetzen, tmp weg
D:/Anthropic_Claude/Programme/Git/cmd/git.exe clone --depth 1 \
  https://github.com/pbakaus/impeccable.git D:/Anthropic_Claude/tmp_impeccable
rm -rf D:/Anthropic_Claude/Halo_Pro/.claude/skills/impeccable
cp -r D:/Anthropic_Claude/tmp_impeccable/.claude/skills/impeccable \
  D:/Anthropic_Claude/Halo_Pro/.claude/skills/
rm -rf D:/Anthropic_Claude/tmp_impeccable
# Version-Diff in SKILL.md frontmatter checken
```

## Verwandte Karten

- `webdev_stack_2026.md` — Stack-Default (Astro/Next + Tailwind + shadcn)
- `vibe_coding_workflow.md` — Lovable→Cursor→Claude Pipeline (Impeccable als Polish-Layer)
- `claude_design.md` — Anthropic-Brand-Default (Impeccable arbeitet mit beliebigen Brand-Systemen)

## Quellen

- Repo: https://github.com/pbakaus/impeccable
- Site: https://impeccable.style
- License: Apache 2.0 (basiert auf Anthropics `frontend-design`-Skill)
- Author: Paul Bakaus (ehemals Google AMP, Aves Engine)
