---
name: webseiten_audit
description: Strukturierter Audit-Workflow für eine bestehende Webseite. Triggert bei „audit Webseite X", „review von <URL>", „check kundens site", „warum lädt das so langsam". Liefert ein vollständiges Audit-MD mit Tech-Stack-Detection, Performance, Accessibility, SEO-Basics, Mobile-Fitness, Security-Quick-Scan, plus konkrete Fix-Empfehlungen priorisiert.
---

# Webseiten-Audit

## Trigger

- „audit kunde x's webseite"
- „review <URL>"
- „warum ist <URL> so langsam"
- „check ob <URL> mobil funktioniert"
- „kannst du dir <URL> anschauen"

## Schritte

### 1. URL + Kontext klären

Wenn nicht klar:
- URL bestätigen (mit/ohne https, www-ja/nein, Sub-Domain?)
- Kontext: existierender Kunde (Projekt-MD existiert) oder neuer Kunde / fremde Seite?
- Audit-Tiefe: quick (10 Min) oder full (45 Min)?

### 2. Output-Datei vorbereiten

`02 Projekte/<Projekt>/audit-<datum>.md` (wenn existing Projekt) oder
`01 Inbox/audit-<domain>-<datum>.md` (wenn ad-hoc).

Frontmatter:
```yaml
tags: [audit]
url: <URL>
auditor: Halo_Pro
datum: <YYYY-MM-DD>
tiefe: quick|full
```

### 3. Audit-Bausteine

#### A. Tech-Stack-Detection
- `curl -s -I <URL>` → Server, Powered-By Headers
- HTML-Source: Meta-Generator, Asset-Hosts, Framework-Hints (`__NEXT_DATA__`, `wp-content`, etc.)
- Output: Tabelle mit `Komponente | Detected | Version | Confidence`

#### B. Performance (PageSpeed-Light, ohne externe API)
- `curl -s -w "%{time_total}|%{size_download}|%{http_code}" <URL>`
- HTML-Größe, Asset-Anzahl
- Render-Blocking Assets (CSS/JS im `<head>`)
- Image-Optimization (Lazy-Loading, modern Formats?)
- **Wenn Mad will:** PageSpeed Insights API call (manuell, externe Service)
- Output: `Total Load | TTFB | DOMContent | Empfehlung`

#### C. Mobile-Fitness
- Viewport-Meta vorhanden?
- Touch-Target-Größen (>44px)?
- Responsive Breakpoints im CSS
- Test mit `obsidian.py run` → Browser-Window auf Mobile-Size? (oder via PowerShell + Chrome-Devtools-Protocol)

#### D. Accessibility (Quick-Scan)
- Alt-Texte auf `<img>` (Sample 10)
- Heading-Hierarchie (h1→h6 sauber?)
- Kontrast-Verhältnis (Foreground/Background bei Body-Text)
- ARIA-Landmarks vorhanden?
- Tastatur-Navigation (Tab-Reihenfolge sinnvoll?)

#### E. SEO-Basics
- `<title>` + Meta-Description vorhanden, Länge ok?
- Canonical-Tag
- robots.txt + sitemap.xml verfügbar?
- Open Graph + Twitter Cards für Sharing
- Strukturierte Daten (Schema.org JSON-LD)

#### F. Security-Quick-Scan
- HTTPS aktiv + Cert valid?
- HSTS-Header gesetzt?
- CSP-Header vorhanden?
- X-Content-Type-Options, X-Frame-Options
- Mixed-Content (http-Assets in https-Page)?
- Bekannte Schwachstellen via öffentliche Header (z.B. WP-Version exposed)

#### G. Content-Quality (optional bei Tiefe = full)
- Text-Lesbarkeit (Wortlänge, Satzlänge — Stichprobe)
- Tippfehler / Sprache konsistent
- Broken Links (Top-10 Stichprobe)
- Bilder ohne Alt-Text (zählen)

### 4. Output-Format

```markdown
# Audit: <Domain> — <Datum>

## TL;DR
[3-5 Bullets — was ist gut, was ist schlecht, was ist kritisch]

## Score-Übersicht
| Kategorie | Score | Status |
|-----------|------:|--------|
| Performance | X/10 | 🟢/🟡/🔴 |
| Mobile | X/10 | ... |
| Accessibility | X/10 | ... |
| SEO | X/10 | ... |
| Security | X/10 | ... |

## Findings (priorisiert)

### 🔴 Kritisch (sofort fixen)
- ...

### 🟡 Wichtig (in den nächsten Wochen)
- ...

### 🟢 Optimierung (wenn Zeit ist)
- ...

## Detailbefunde
[Pro Kategorie A-F detaillierter Befund]

## Empfehlungen mit Aufwand-Schätzung
| Fix | Impact | Aufwand | Priorität |
|-----|--------|---------|-----------|
| ... | hoch | 2h | 🔴 |
```

### 5. Daily-Note-Eintrag

```markdown
## HH:MM — Audit: <Domain>
- Was: Vollständiger Audit von <URL> ([[02 Projekte/<projekt>/audit-<datum>]])
- Score: X/50
- Kritisch: <Anzahl> Findings
- Nächster Step: <was Mad als erstes angehen sollte>
```

### 6. Output an Mad

> Audit fertig: [[<datei>]]
> Score: X/50 — Kritisch: A | Wichtig: B | Optimierung: C
> Top-3 zum sofortigen Fixen:
> 1. ...
> 2. ...
> 3. ...
> Soll ich den ersten Fix gleich angehen oder warten?

## Wichtig

- **Bei externen Webseiten** (kein Kunden-Auftrag): nur Public-View, keine Login-Bereiche, keine destruktiven Tests, kein automatisches Crawling großer Mengen Pages (Bot-Detection / Rate-Limits respektieren).
- **Performance-Tests** lokal nur — nicht für externe Lasttests einsetzen ohne Genehmigung.
- **Findings sind keine Anschuldigungen** — Halo_Pros Audit-Ton ist sachlich, lösungsorientiert, ohne Drama.
