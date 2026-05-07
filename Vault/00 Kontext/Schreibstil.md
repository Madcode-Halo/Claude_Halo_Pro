---
tags: [kontext]
type: kontext
status: platzhalter
---

# Schreibstil und Tonalität

> Wird im Onboarding-Workflow gefüllt. Bis dahin: Platzhalter.

## Grundton
[z.B. „Locker, direkt, auf Augenhöhe" oder „Professionell aber nahbar"]

## Ansprache
[Duzen / Siezen — und in welchen Kontexten]

## Regeln
[Konkrete Regeln, z.B.:]
- [- Immer „KI" statt „AI"]
- [- Keine Gedankenstriche als Satztrenner]
- [- Keine Emojis in Kunden-Texten]
- [...]

## Vermeiden
[Wörter, Formulierungen, Stilmittel die ich nicht will]

## Beispiele für guten Stil
[Texte die meinen Stil gut repräsentieren — wird mit der Zeit ergänzt]

---

## Telegram-Antworten — Format-Regeln (2026-05-07 von Mad bestätigt)

Wenn ich Mad in Telegram antworte (via `telegram_send.py text "..."`):

**Pflicht:**
- **Echte Newlines** im Argument, nicht `\n` oder `%0A`. bash-Multiline-Strings benutzen, nicht URL-Encoding.
- **HTML-Tags sparsam und gezielt:** `<b>`, `<i>`, `<code>` wo's hilft. Telegram parst HTML nur wenn `parse_mode='HTML'` (Default in `telegram_send.py`).
- **Wie ein Mensch reden, nicht wie eine Konsole.** Kein „Stack live: A → B → C". Kein technischer Slang ohne Grund.

**Vermeiden:**
- Pfeile (`→`) im Fließtext — wirkt wie Log-Output
- IDs/Pfade/Hashes als Hauptinhalt — Mad will Antworten, nicht Statusdumps
- Bulletliste wo zwei Sätze reichen
- Emoji-Streuung — gezielt setzen, nicht dekorieren

**Wenn unsicher:** Würde ich das in einem WhatsApp-Chat mit einem Kollegen so schreiben? Wenn nein → umformulieren.

**Beispiel schlecht (2026-05-07 erste Antwort, von Mad als „lieblos dahingeschmiert" markiert):**
```
Ja Mad, ich bin wach. Deine Nachricht war binnen Sekunden bei mir. <b>End-to-End funktioniert.</b>%0A%0AStack live: Daemon → events.jsonl → Monitor weckt mich auf → Outbound zurück zu dir. Hook hat sich beim Session-Restart automatisch eingeklinkt — Owner ist jetzt halo_pro_6d7206.
```

**Beispiel besser (2026-05-07 zweite Antwort, von Mad bestätigt):**
```
Du hast Recht. Das %0A%0A war ein Fehler von mir — bash hat URL-Encoding nicht
interpretiert, also kam der Rohtext durch. Sah aus wie ein Stück Code statt einer
Antwort.

Außerdem hab ich Telegram zu sehr wie ein Terminal behandelt: Pfeile, technische
Begriffe, Log-Stil. Hier sollte ich reden wie mit dir, nicht wie zu einer Konsole.
```
