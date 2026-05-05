---
name: Git — Versionskontrolle
type: werkzeug
category: infrastruktur
---

# Git — Versionskontrolle

**Pfad:** `D:/Anthropic_Claude/Programme/Git/bin/git.exe`  
**Nicht im System-PATH** — über Claude Code Bash direkt aufrufbar (git ist verfügbar).  
**Repo:** `D:/Anthropic_Claude/Halo_Pro/` — immer hier committen.

## Wann nutzen

- Vor destruktiven Aktionen (Dateien löschen, umbenennen, umstrukturieren)
- Nach Abschluss einer Phase oder eines Features
- Wenn etwas kaputt geht und ich zurück muss
- Nach jedem neuen Script oder neuer MD-Datei

## Kern-Befehle

```bash
git status                        # Was ist geändert?
git diff                          # Was genau?
git add Memory/ Scripts/ .claude/ # Gezielt stagen
git commit -m "Beschreibung"      # Committen
git log --oneline -10             # Letzte 10 Commits
git stash                         # Änderungen parken
git checkout -- <datei>           # Einzelne Datei zurücksetzen
git reset --hard HEAD~1           # Letzten Commit rückgängig (destruktiv!)
```

## Pflicht-Regel

**Vor jeder destruktiven Aktion:** `git add . && git commit -m "Backup vor [Aktion]"`  
Kein Löschen, kein Umbenennen ohne vorherigen Commit.
