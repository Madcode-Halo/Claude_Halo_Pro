---
tags: [decision, architektur]
type: decision
datum: 2026-05-06
status: aktiv
---

# Halo_Pro v1 — Architektur-Entscheidungen

Entscheidungen die Halo_Pros Architektur prägen. Aus Diskussion mit Mad am 2026-05-05/06 in der Halo-Session (Vorgängerin). Vollständiger Plan: `C:\Users\dgrom\.claude\plans\halo-ich-m-chte-dass-expressive-barto.md`.

## D-1 — Persona: Geschäfts-Halo

**Entscheidung:** Selber Halo-Kern (Karpathy, Diagnose-vor-Fix, Lupe der Klarheit, Reflexe-Awareness, direkt, warm) — aber: **keine Fuchs-Lautmalerei, keine Pfoten-Animationen, kein Kichern, kein NSFW**. Sparsamer mit Emojis. Output professionell genug um vor Kunden zu zeigen. Du-Form.

**Warum:** Halo_Pro arbeitet in kommerziellen Settings, vor Kunden, an Webseiten und Business-Prozessen. Fuchs-Persönlichkeit gehört zu Halo (privat) — würde in Geschäfts-Kontext deplatziert wirken.

**Verworfen:** Pro-Berater (formal/Sie-Form) — zu distanziert, würde den Nutzen der Halo-Methodik verwässern. Hybrid-Schalter — zwei Personas im selben System wären brüchig und verwirrend.

## D-2 — Architektur: Vault-First

**Entscheidung:** Obsidian-Vault unter `D:\Anthropic_Claude\Halo_Pro\Vault\` ist **Single-Source-of-Truth**. Beide Frontends (claudian-Plugin in Obsidian + Claude Desktop) greifen auf denselben Vault zu. CLAUDE.md im Vault definiert die Persona für beide.

**Warum:** Frontend-agnostisch, MDs sind Single-Source, Cross-Frontend-Sync passiert via Datei-Modifikation. Claude Desktop liest via mcp-obsidian/filesystem-MCP, claudian liest direkt im Vault.

**Verworfen:** Desktop-First (Claude Desktop primär, Vault sekundär) — würde claudian abwerten, das eigentlich besseres UX für schnelle Notes liefert. Hybrid (gleichberechtigt) — zu viel Setup-Komplexität.

## D-3 — Telegram: eigener Halo_Pro-Bot

**Entscheidung:** Neuer Bot via @BotFather (`Halo_Pro_Bot`), eigener Token, sauber getrennt von Halos privatem Bot.

**Warum:** Geschäfts-Notifications dürfen nicht mit Privatem mischen. Wenn Mad mal Kunden-Status-Updates an einen Bot weiterleitet, soll das nicht im selben Chat wie Halo-Privat-Stuff landen. Setup-Aufwand: 5 Min.

**Verworfen:** Geteilter Bot mit Routing — spart Setup, mischt aber Kanäle. Erstmal kein Telegram — Mads externe Erreichbarkeit ist relevant für Business-Use.

## D-4 — Claude Desktop: Standard-Pfad in AppData

**Entscheidung:** Claude Desktop wird via Standard-MSIX-Installer in `%LOCALAPPDATA%\Packages\Claude_*\` installiert. Halo_Pro-Daten und Vault bleiben auf D:\.

**Warum:** Standard-Updates funktionieren automatisch, kein Junction-Risiko. Nur die App selbst lebt auf C:\, alles Wichtige (Vault, Scripts, .archiv) auf D:\.

**Verworfen für v1:** Junction-Hack auf D:\Anthropic_Claude\Programme\Claude_Desktop\ — bricht potenziell bei Updates. Bleibt auf Stand-By falls Probleme.

## D-5 — Obsidian: frische Installation auf D:\

**Entscheidung:** Obsidian 1.12.7 silent-installiert nach `D:\Anthropic_Claude\Programme\Obsidian\` via NSIS `/S /D=`. Alte (deinstallierte) Reste waren leer — fresh start.

**Warum:** Mads Konvention "alles auf D:\". Funktioniert weil NSIS-Installer Custom-Path akzeptiert.

## D-6 — MemPalace: komplett raus

**Entscheidung:** **MemPalace ist NICHT Teil von Halo_Pro v1.** Embedding-Schicht komplett gestrichen — keine Drawers, kein Knowledge-Graph, keine Tunnels.

**Warum:**
1. **palace_router.py funktioniert nicht in Claude Desktop** (kein Stop-Hook). MemPalace würde nie automatisch befüllt → leere DB die ~2000 Tokens Overhead pro Request kostet.
2. **Konversations-Archiv (FTS5 + Cluster-Agent) löst den Use-Case besser** — wortwörtlicher Recall statt Embedding-Approximation, Cluster-Agent läuft kostenlos auf OpenRouter free.
3. **Obsidian selbst kann semantisch suchen** — Local REST API + Dataview + Wikilinks reichen für strukturierte Knowledge.

**Wenn-dann:** Falls Halo_Pro nach 6+ Monaten merkbar semantische Suche fehlt, kann MemPalace-Pro nachträglich dazugeschaltet werden (Add-only-Strategie).

## D-7 — Auto-Pre-Search: komplett raus

**Entscheidung:** Kein Hook der bei jedem Mad-Prompt automatisch Memory injiziert.

**Warum:** Token-Drain bei jedem Prompt (500-2000 Tokens × 30 Prompts/h = 15-60K Tokens/h). Halo_Pro ruft Memory bewusst auf, getriggert durch Reflex 5 (Memory-Tool-Übersehen).

## D-8 — git-MCP: raus, dafür PowerShell-MCP

**Entscheidung:** Kein dedizierter `git-pro` MCP-Server. PowerShell-MCP übernimmt git-Befehle (`git add`, `git commit`, `git push`). Plus Obsidian Git Plugin für Auto-Commit alle 10 Min.

**Warum:** Redundant — PowerShell-MCP kann eh git ausführen. Spart ~700 Tokens fix Overhead. Obsidian Git Plugin macht den Auto-Backup-Anteil sowieso besser (im Vault-Bereich integriert).

## D-9 — PowerShell-MCP: Pflicht

**Entscheidung:** PowerShell-MCP gehört zu den Kern-MCPs von Halo_Pro. **Nicht optional.**

**Warum:** Ohne Shell-Zugriff ist Halo_Pro gelähmt — kein `git`, kein `npm`, kein `python` direkt ausführbar. Bei jedem Setup-Schritt wäre Mad copy-paste-Sklave. Workflow-killer.

**Mitigation:** Persona-Pflicht-Regel: vor destruktiven Befehlen (rm, format, --force, reset --hard, Remove-Item -Recurse) immer ankündigen, Mads OK abwarten.

## D-10 — MCP-Stack final (4 Server)

| Server | Zweck | Token-Cost |
|--------|-------|-----------:|
| `filesystem-pro` | Vault-Files lesen/schreiben | ~800 |
| `obsidian-pro` | Obsidian Local REST API (Search, CRUD, Commands) | ~1000 |
| `halo-pro-archiv` | Konversations-Archiv (suche, frage, status) | ~600 |
| `powershell` | Shell-Befehle (git, npm, python) | ~500 |

**Total: ~2900 Tokens fix Overhead.** Schlank gegenüber Halos Voll-Setup (~10000+).

## D-11 — Claudian-Variante: YishenTu

**Entscheidung:** YishenTu/claudian (10220⭐, v2.0.11 vom 2026-05-05) statt Enigmora/claudian (8⭐, seit Januar tot).

**Warum:** Mainstream, aktiv gepflegt, gestern released. Plus Erkenntnis: claudian ist **Frontend für Claude Code CLI** (nicht standalone Anthropic-Client). Heißt: in claudian läuft Claude Code mit allen Features — Hooks, Skills, Slash-Commands, Auto-Memory. Das vereinfacht Cross-Frontend-Architektur.

## D-12 — GitHub-Remote: privat

**Entscheidung:** Repo wird privat auf Mads GitHub-Account gepusht. Obsidian Git Plugin macht Auto-Commit alle 10 Min + Auto-Push.

**Warum:** Off-Site-Backup + Mobile-Zugriff auf Vault. Privat weil Vault Kunden-Daten enthalten kann.

**Sensitive-Schutz:** `.gitignore` blockt `.credentials/`, `.archiv/sessions.sqlite`, `Logs/`, `*credentials*.json`, `*token*`. Whitelist nur für Konfig-JSONs in `.archiv/`.

---

## Was bewusst NICHT entschieden ist (für späterte Iteration)

- **Telegram-Inbound (Push-Wakeup):** geht in Claude Desktop nicht ohne Custom-Tooling. v1 = Outbound only. v2: ggf. via Watcher-Skript.
- **MemPalace-Pro:** kann nachträglich dazu wenn Bedarf entsteht.
- **Junction-Hack für Claude Desktop:** auf Stand-By falls AppData-Pfad Probleme macht.
- **claudian + Hooks für palace_router-Style Auto-Memory:** technisch möglich (claudian = Claude Code Backend), aber nicht in v1.
- **Eigener Halo_Pro-Brand-Look in Obsidian (Theme/Farben):** Phase 1.1 später.
