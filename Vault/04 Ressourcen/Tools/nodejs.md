---
name: 🟢 Node.js — JavaScript-Runtime + npm
description: JavaScript-Runtime mit npm-Paketmanager. Halo nutzt es für npm-basierte Tools (OpenCode, MCP-Server shadcn/magic, ad-hoc Frontend-Builds, npx-Pattern).
type: tool
status: active
purpose: Backend für alles npm/npx-basierte das Halo aufruft. Plus Voraussetzung für viele Webdev-Stacks.
family: webdev
created: 2026-04-30
loaded_by: on-demand
depends_on: []
criticality: wichtig
keywords: [nodejs, npm, npx, node, javascript, runtime, opencode, mcp]
last_audited: 2026-04-30
tags: [runtime, system-tool]
---

## Zweck

Node.js + npm sind **System-Voraussetzung** für mehrere Halo-Tools. Halo selbst ruft npm/npx implizit über andere Tools auf, nicht direkt:

- **OpenCode** (`opencode-ai` über npm installiert)
- **MCP-Server `shadcn`** und **`magic`** in `.claude/settings.json` werden via `npx` gestartet
- **Webdev-Stack 2026** (Astro/Next/Hono) — alle npm-basiert
- **Ad-hoc Tools** (claude-mems Endless Mode, andere TS-Repos)

## Funktioniert so

**Pfad:** `D:/Anthropic_Claude/Programme/NodeJS/` (verschoben aus `D:/NodeJS/` 2026-04-30 mit PATH-Update Machine-Level)

**Im PATH:**
```
node.exe  → D:/Anthropic_Claude/Programme/NodeJS/node.exe
npm.cmd   → D:/Anthropic_Claude/Programme/NodeJS/npm.cmd
npx.cmd   → D:/Anthropic_Claude/Programme/NodeJS/npx.cmd
```

**Verifikation:**
```powershell
Get-Command node, npm, npx
```

## Wann Halo es einsetzt

- Implizit über andere Tools (OpenCode-Server, MCP-Server)
- Direkt nur bei Webdev-Tasks (`npm install`, `npm run dev`, `npx <tool>`)

## Caveats

- **PATH-Update bei Move:** wenn Node-Folder verschoben wird, MUSS PATH (Machine + ggf. User) angepasst werden — sonst alle npm-installierten Tools brechen
- **Globale npm-Pakete:** liegen in `%APPDATA%/npm/` — separat von Node-Install. Bleibt auf C: (Konvention, würde sonst jede globale Install brechen)

## Verwandte

- [`opencode.md`](opencode.md) — wichtigster npm-Konsument bei Halo
- [`webdev_stack_2026.md`](webdev_stack_2026.md) — Webdev-Default-Stack der Node braucht
