---
name: 🎨 Claude Design (Anthropic Brand)
description: Anthropic's hauseigene Design Language — Default-Look für Halo-Webdev wenn keine andere Brand-Vorgabe. Warm, trustworthy, thoughtfully restrained.
type: reference
status: active
purpose: Konsistenter, nicht-AI-slop-aussehender Design-Default mit echten Anthropic-Brand-Farben/Typo + Drop-in-shadcn-Theme
family: werkzeuge
created: 2026-04-28
loaded_by: on-demand
depends_on: [webdev_stack_2026]
criticality: optional
keywords: [design, brand, anthropic, claude-design, styrene, tiempos, warm-minimal, color-palette]
last_audited: 2026-04-28
tags: [design, brand, anthropic, webdev]
---

<!-- Diese Karte verhindert AI-Slop-Look bei Halo-Generierten-UIs. Wir nutzen Anthropic's eigenes Brand-System weil (a) wir im Anthropic-Universum leben, (b) es genau Halos Vibe trifft, (c) shadcn-Theme + Skill-Repo machen es sofort einsetzbar. -->

## Zweck

Default-Visual-Identity für Halo-Webdev-Projekte. Warm, trustworthy, thoughtfully restrained — vermeidet generischen AI-Look und gibt Halos Output Anthropic-Brand-Familienähnlichkeit.

## Funktioniert so

**Farbpalette (offiziell):**
| Name | Hex | Verwendung |
|------|-----|-----------|
| Dark | `#141413` | Primary text, dunkle Backgrounds |
| Light | `#faf9f5` | Light Backgrounds, Cream-Cards |
| Mid Gray | `#b0aea5` | Secondary Elements, Captions |
| Light Gray | `#e8e6dc` | Subtle Backgrounds, Borders |
| **Orange** (primary accent) | `#d97757` | CTAs, Highlights |
| Orange-Deep | `#ae5630` | Hover-States |
| Blue (secondary) | `#6a9bcc` | Info, Links |
| Green (tertiary) | `#788c5d` | Success-States |

**Typography (offiziell + Web-Fallback):**
| Anwendung | Offiziell | Web-Fallback (frei) |
|-----------|-----------|---------------------|
| Headlines | Styrene B | Poppins |
| Body | Tiempos Text | Lora |

**Drop-in via shadcn:**
```bash
bunx shadcn@latest add https://shadcn.io/theme/claude
```

**Tailwind v4 Theme:**
```css
@theme {
  --color-anthropic-dark: #141413;
  --color-anthropic-light: #faf9f5;
  --color-anthropic-orange: #d97757;
  --font-headline: 'Styrene B', 'Poppins', Arial, sans-serif;
  --font-body: 'Tiempos Text', 'Lora', Georgia, serif;
}
```

**Claude Design Tool (claude.ai/design):**
- Launched 2026-04-17 (Pro/Max/Team/Enterprise)
- Upload Resources → Claude generiert UI-Kit
- Use-Case: Brand-System für Mad's Kunden generieren

**Anthropic Skill-Repo:**
```bash
git clone https://github.com/anthropics/skills ~/.claude/skills/anthropic-skills
```
Lädt Brand-Guidelines als Claude Skill — Halo hat dann Brand-Wissen integriert.

**Detail-Doku:** `Projekte/Webdesign/claude_design_system.md`

## Trigger

- Halo startet Webdev-Projekt **ohne** explizite Brand-Vorgabe von Mad
- Mad sagt *„mach es schön"* / *„professionelle Optik"* / *„nicht AI-Slop"*
- Halo soll demo-tauglich UI bauen die Mad sich „anschauen lässt"
- Mad fragt *„wie sieht Anthropic-Style aus?"*
- Halo erkennt: Default-Tailwind-Look würde generisch wirken → Brand-Theme einsetzen

## Zweckentfremdung

- **Negativ-Constraints**: aus Brand-Doku ableiten was NICHT zu nutzen (Inter, Purple-Gradients, Cookie-Cutter — siehe `inspiration_quellen.md`)
- **Brand-Audit**: existierende Mad-Site gegen Anthropic-Brand-Werte spiegeln, Drift erkennen
- **AI-Slop-Detector**: bei Lovable/Bolt-Output prüfen, anpassen mit diesem Theme
- **Halos eigene Tools**: Halo-Statusline, Halo-Banner, Halo-Web-Dashboard alle in diesem Look

## Grenzen

- **Styrene B + Tiempos Text sind kommerziell** — für Production ohne Lizenz: Poppins+Lora-Fallback
- **shadcn-Theme „claude" ist Community** — keine offizielle Anthropic-Maintenance, kann veralten
- **Orange #d97757 ist sehr warm** — bei Tech-Heavy-Industries (Finanz, Enterprise) ggf. zu friendly
- **Cream-Backgrounds** funktionieren nicht mit allen Logos — Mad's Kunden-Logo erst checken
- **Brand kollidiert mit Mad's Kunden-Brand** — Karte ist Halos-Default, NICHT für jeden Mad-Kunden geeignet

## Verwandte Karten

- `webdev_stack_2026.md` — Stack-Default
- `vibe_coding_workflow.md` — Pipeline mit dem Theme integriert
