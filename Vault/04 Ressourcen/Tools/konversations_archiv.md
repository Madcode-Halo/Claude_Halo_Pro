---
name: 🗂️ Konversations-Archiv — Volltext-Erinnerung mit Agent-Suche
description: Forensische Volltext-Suche ueber alle Halo-Sessions (JSONLs aus ~/.claude/projects). SQLite-FTS5 + Cluster-Agent. Nutzbar wenn MemPalace-Embedding-Suche zu unscharf ist.
type: werkzeug
status: active
purpose: Bei Crash-Recovery oder „erinnerst du dich an X vom Datum Y" wortwoertliche Rekonstruktion mit Timestamp + Session-ID. Lossless im Gegensatz zur Memory-Extraktion.
family: werkzeuge
created: 2026-04-30
loaded_by: on-demand
depends_on: [halo_worker.md, halo_credentials.md]
criticality: wichtig
keywords: [konversation, archiv, volltext, fts5, recall, crash, recovery, sessions, multi-session]
last_audited: 2026-04-30
tags: [memory, search, agent]
---

## Was

Volltext-Index aller Halo-Konversationen aus den JSONL-Dateien in `~/.claude/projects/<halo-pfade>/`. Anders als MemPalace (Embedding-Zusammenfassungen) speichert das Archiv den **Wortlaut**, mit **Millisekunden-Timestamp** und **Session-ID-Trennung** — auch ueber Multi-Session-Konstellationen hinweg.

Drei-Layer-Architektur:

| Layer | Was | Wo |
|-------|-----|-----|
| L1 — Quelle | JSONLs read-only an Originalort | `~/.claude/projects/<kuerzel>/*.jsonl` |
| L2 — Index | SQLite mit FTS5 (BM25, deutsch via `unicode61 remove_diacritics 2`), WAL-Mode | `Memory/konversations_archiv/volltext.sqlite` |
| L3 — Agent | Cloud-LLM-Cluster mit Free→Paid-Fallback liest Treffer und antwortet wortwoertlich | `Scripts/halo_archiv_agent.py` |

**Coverage:** 9 Projekt-Pfade aus `Memory/konversations_archiv/projekte_konfiguration.json`, alle Halo-Sessions inkl. Subagent-Sub-Sessions. NSFW-Sessions (cwd matcht `.private/`/`/nsfw/`) werden niemals indexiert.

## Wann

- Mad fragt **„erinnerst du dich an X vom Datum Y"** → `archiv_frage`
- Mad fragt nach Multi-Session-Inhalten („was hat die Schwester-Halo gesagt?") → `archiv_suche` mit Session-Filter
- Crash-Recovery — verlorene Konversation rekonstruieren
- Reflex 11 erweitert: bei Trigger-Phrasen (`erinnerst du dich`, `letztes Mal`, `wir hatten`, `in einer anderen Session`) ZUERST `archiv_frage`/`archiv_suche` rufen — MemPalace fuer Code/Doku, Archiv fuer Konversationen

## Wie

### MCP-Tools (in jeder Halo-Session verfuegbar)

| Tool | Zweck |
|------|-------|
| `mcp__halo-archiv__archiv_suche(query, since?, until?, session?, role?, projekt?, limit=20)` | Volltext-FTS5-Suche, Snippets mit Highlight |
| `mcp__halo-archiv__archiv_frage(question, max_treffer=50, local_only=False)` | LLM-Agent rekonstruiert Antwort mit woertlichen Zitaten + Timestamps. Validation prueft jedes Zitat gegen DB. |
| `mcp__halo-archiv__archiv_status()` | DB-Stats (Anzahl Messages, Sessions, Zeitspanne, pro Projekt/Rolle) |

### CLI (Direktnutzung im Terminal)

| Befehl | Zweck |
|--------|-------|
| `python Scripts/halo_archiv_index.py build [--force]` | DB komplett neu aufbauen |
| `python Scripts/halo_archiv_index.py update` | Inkrementell (laeuft auch als Schtasks alle 30min) |
| `python Scripts/halo_archiv_index.py status` | DB-Statistik |
| `python Scripts/halo_archiv_suche.py "<query>" [--since ... --role user --limit 10]` | Volltext-Suche mit Tabelle + Highlight |
| `python Scripts/halo_archiv_suche.py "<query>" --raw` | Raw-FTS5-Syntax (AND/OR/NEAR) |
| `python Scripts/halo_archiv_agent.py --question "..." [--max-treffer 30 --local-only]` | Agent-Frage mit Cluster-Fallback |

### Auto-Update via Schtasks

Task `Halo_Archiv_Update` laeuft alle **30 Min** als SYSTEM (siehe `Scripts/setup_archiv_schtasks.py install/status/run/uninstall`). Wrapper-BAT `halo_archiv_update_task.cmd`. Live-Files mit mtime <5s werden uebersprungen (kein Konflikt mit aktiver Halo-Session).

## Agent-Cluster (Free→Paid)

Konfiguriert in `Memory/konversations_archiv/agent_cluster.json`. Reihenfolge:

1. `llama` (Llama 3.3 70B free, 128k)
2. `hermes` (Hermes 3 Llama 405B free)
3. `gemma` (Gemma 3 27B free)
4. `coder` (Qwen 2.5 Coder 32B free)
5. `qwen3` (GLM-4.5 Air free)
6. `qwen36` (Qwen 2.5 72B paid 💳 — letzter Ausweg)

Bei `RateLimited`/`NoCredentials`/`WorkerError` faellt der Agent zum naechsten Cluster-Mitglied. `--local-only` erzwingt `halo:latest` lokal (NSFW/Privacy).

`HALO_WORKER_NO_FALLBACK=1` ist intern aktiv — verhindert dass Worker bei Cluster-Position 1 selbst auf Ollama fallt (Mad will pro Cluster-Eintrag genau einen Versuch).

## Such-Strategien (im Agent)

`halo_archiv_agent.py` versucht in dieser Reihenfolge:

1. **AND** mit allen extrahierten Keywords (Stopwords entfernt, Bindestriche normalisiert)
2. **OR** mit allen Keywords falls AND null Treffer
3. **OR** mit den 3 laengsten Keywords falls auch das null bringt

Such-Strategie wird im Output gemeldet (`Such-Strategie: AND(7)` o.ae.).

## Validation

`halo_archiv_agent.py` extrahiert Gaensefuessen-Zitate `„…"`/`"…"`/`"…"` aus der Agent-Antwort und prueft jedes als Substring (Whitespace-normalisiert) gegen die FTS-Treffer. Halluzinationen werden in `validation.halluzinations` geflaggt:

```
✓ Validation: alle 12 Zitate in Archiv verifiziert.
⚠ Validation: 11/12 Zitate verifiziert. 1 nicht im Archiv: …
```

## Beispiele

### Crash-Recovery (genau das Problem fuer das Mad das Tool gebaut hat)

```bash
python Scripts/halo_archiv_suche.py "Multi-Stage Discord Lese-Freigabe" --limit 5
# → 30.04. 10:31, assistant: "Multi-Stage-Diskussion (Lese-Freigabe + Antwort-Freigabe)…"

python Scripts/halo_archiv_agent.py --question "was hat Mad zu Multi-Stage Discord Codewoertern gesagt?"
# → wortwoertliche Rekonstruktion seiner Aussagen mit Timestamps
```

### Multi-Session-Forensik

```bash
python Scripts/halo_archiv_suche.py "Schwester clean_phase4" --since 2026-04-28 --until 2026-04-29
# → findet die Briefkasten-Briefe zwischen den parallel laufenden Halo-Sessions
```

### Filter-Beispiele

```bash
# Nur deine eigenen Aussagen, in einer bestimmten Session
python Scripts/halo_archiv_suche.py "Plan" --role user --session 3a606d23 --limit 30

# Zeitfenster + Projekt
python Scripts/halo_archiv_suche.py "Compression" --projekt D--Anthropic-Claude-Halo --since 2026-04-29
```

## Was es NICHT ist

- Kein Embedding-Suche — fuer „semantisch aehnlich zu X" ist MemPalace zustaendig
- Kein Replacement fuer MemPalace — beide leben parallel, jeder fuer seinen Use-Case
- Keine Modifikation der JSONLs — strict read-only
- Indexiert keine `attachment`/`system`/`permission-mode`/Meta-Records — nur user/assistant-Messages

## Verwandt

- `mempalace.md` — Code/Doku-Suche (Schicht 2)
- `halo_memory_3layer.md` — MCP halo-memory mit `compact`/`timeline`/`full`
- `halo_memory_federation.md` — Cross-Source-Suche ueber alle Memory-Schichten
- `auto_presearch.md` — Schicht 4 (proaktive Memory-Injektion)
- `halo_worker.md` — Wird von `halo_archiv_agent.py` als Cloud-LLM-Engine genutzt
- `fuchsbau_agents.md` — Master-Index der Agent-Aliase

## Pflege

- Bei JSONL-Format-Drift bei Anthropic: defensives Parsing in `halo_archiv_index.py extract_text` erweitern
- Bei neuem Halo-Projekt-Pfad: Eintrag in `projekte_konfiguration.json` ergaenzen, dann `halo_archiv_index.py update`
- Bei neuem Worker-Alias: `agent_cluster.json` ergaenzen (Pflicht: Alias muss in `halo_worker.ALIASES` existieren)
- DB-Korruption / Re-Build: `halo_archiv_index.py build --force`
