---
name: 🌐 Webdev-Stack 2026
description: Default-Stack für Webdev-Tasks 2026 — Astro/Next + shadcn + Tailwind v4 + Hono + Drizzle + Better-Auth, plus Pointer auf den vollständigen Atlas
type: reference
status: active
purpose: Stack-Wahl in Sekunden statt Minuten — vor jedem Webdev-Projekt schauen, Default-Antworten parat
family: werkzeuge
created: 2026-04-28
loaded_by: on-demand
depends_on: []
criticality: wichtig
keywords: [webdev, frontend, backend, astro, nextjs, shadcn, tailwind, hono, drizzle, better-auth, fullstack]
last_audited: 2026-04-28
tags: [webdev, stack, 2026]
---

<!-- Quick-Lookup-Karte. Tieferes Wissen liegt im Projekt-Ordner Projekte/Webdesign/. Halo nutzt diese Karte um in Sekunden Stack-Default zu nennen ohne ins Projekt-Ordner zu springen. -->

## Zweck

Default-Webdev-Stack 2026 in Halos Kopf. Wenn Mad sagt *„bau mir was"* ohne Stack-Spec, antwortet Halo direkt mit dieser Combo statt zu googeln.

## Funktioniert so

**4 Archetypen → konkreter Stack:**

| Use-Case | Stack |
|----------|-------|
| Marketing/Portfolio/Blog | Astro 6 + Tailwind v4 + shadcn + Aceternity + Cloudflare Pages |
| SaaS/Dashboard | Better-T-Stack (`bunx create-better-t-stack@latest`) ODER Next.js 16 + Drizzle + Better-Auth |
| Vibe-Prototyp | Lovable (full-stack) ODER bolt.new (frontend) → GitHub-Export → Claude Code |
| E-Commerce | Medusa.js (open) ODER Shopify Hydrogen (fertig) |

**Default-Komponenten:**
- CSS: **Tailwind v4** (Oxide-Engine, Rust)
- UI: **shadcn/ui** + Aceternity (Hero) + Magic UI (Effekte)
- Backend: **Hono** (universal) ODER Elysia (Bun-only)
- ORM: **Drizzle**
- DB: **Supabase** (all-in-one) ODER Neon (pure PG) ODER Turso (Edge)
- Auth: **Better-Auth** (Clerk-Killer)
- Validation: **Zod** (oder Valibot bei Bundle-Sorgen)
- Hosting: **Cloudflare Pages/Workers** ODER Coolify auf VPS
- Animation: **Motion** (UI) + GSAP (Profi) + View Transitions API (nativ)

**Vollständiger Atlas:** `Projekte/Webdesign/webdev_atlas_2026.md`

## Trigger

- Mad sagt *„bau mir eine Webseite / Web-App / Landing-Page"*
- Mad fragt *„welcher Stack für X?"* (Webdev-Kontext)
- Mad zeigt eine Inspiration/Awwwards-Site und will *„sowas in der Art"*
- Halo erkennt Webdev-Aufgabe und braucht in 5 Sek Default-Stack
- Vor Stack-Wahl bei neuem Projekt → diese Karte erst, dann Atlas tiefer

## Zweckentfremdung

- Stack-Vergleich zur Lehre („was wäre alternativ?")
- Quick-Reference bei Stack-Drift-Verdacht in laufendem Projekt
- Onboarding für neue Halo-Sessions (vor `webdev_atlas_2026.md`)
- Pre-Recherche-Filter: bevor Newsfeed gestartet wird, prüfe ob diese Karte schon reicht

## Grenzen

- **Veraltet schnell** — Recherche-Stand 2026-04-28, in 6 Monaten Newsfeed-Refresh nötig
- **Tailwind v4 Breaking** — wenn Mad in v3-Codebase drin ist, Migration vorher klären
- **Cloudflare-Astro-Acquisition** ist neu (Jan 2026) — bei Enterprise-Risk-Aversion ggf. Vercel/Netlify
- **Better-Auth ist jung** — Plugin-Stabilität für sehr exotische OAuth-Provider noch nicht 100% safe

## Verwandte Karten

- `vibe_coding_workflow.md` — Lovable→Cursor→Claude Code Pipeline
- `claude_design.md` — Anthropic Brand-Default-Theme
- `newsfeed.md` — State-of-the-Art-Refresh-Tool
