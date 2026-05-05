# Halo_Pro

Schlanke, professionelle KI-Geschäftspartnerin. Halos Schwester für kommerzielle Arbeit (Webseiten, Business-Prozesse, beruflicher Nebenstrang).

## Architektur (v1 Lean)

- **Vault-First**: `Vault/` ist Single-Source-of-Truth, PARA-Struktur (00 Kontext bis 07 Anhänge)
- **4 MCPs**: filesystem-pro, obsidian-pro, halo-pro-archiv, powershell
- **Frontend-agnostisch**: Obsidian (claudian-Plugin) + Claude Desktop teilen denselben Vault
- **Memory-Stack**: Persona (CLAUDE.md) → Vault-State → Konversations-Archiv (FTS5 + Cluster-Agent)
- **Backup**: Obsidian Git Plugin → GitHub privat, Auto-Commit alle 10 Min

## Wichtige Pfade

| Was | Wo |
|-----|-----|
| Persona | `Vault/CLAUDE.md` |
| Skills | `Vault/.claude/skills/` |
| Scripts | `Scripts/` |
| Konversations-Archiv | `.archiv/sessions.sqlite` |
| MCP-Master-Config | `MCP/claude_desktop_config.json` |
| Doku | `Docs/Handbuch_Halo_Pro.md` |

## Setup-Plan

`C:\Users\dgrom\.claude\plans\halo-ich-m-chte-dass-expressive-barto.md`
