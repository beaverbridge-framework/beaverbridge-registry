# Patch: S7 — Index und Facettenseite

Baut aus dem Bundle die Suchseite: Facetten mit Zählwerten (Instanz, Klasse, Has, Lizenz), Freitextsuche, Trefferkarten, Hell/Dunkel nach `design/PALETTE.md`. Dazu die Seiten, unter denen die Registry-IRIs auflösen: Katalog, ein Eintrag je Instanz, das `bbr:`-Vokabular. Alles landet in `docs/`, dem Pages-Ordner.

## Inhalt

| Datei | Änderung |
|---|---|
| `py/step_index.py` | neu: Schritt `index` (war Stub), schreibt `dist/registry-index.json` |
| `py/step_site.py` | neu: Schritt `site` (war Stub), schreibt `docs/` |
| `templates/` | neu: `base`, `index`, `catalog`, `record`, `vocab` als Jinja2-Vorlagen, dazu `style.css` und `app.js` |
| `assets/logo-256.jpg` | neu: Logo auf 256 px (15 KB) für die Kopfzeile |
| `docs/` | neu, erzeugt: Seite, Downloads, Index, Vokabular |
| `dist/registry-index.json`, `dist/pipeline_report.txt` | erzeugt |
| `README.md`, `PRIMER.md` | Status, S4 abgenommen, S7 erledigt, neue Beschlüsse |

Dateien in den Repo-Ordner ziehen, Ordnerstruktur beibehalten, vorhandene Dateien ersetzen. Alle Befehle für Windows `cmd`.

## 1. Lauf

```cmd
python main.py
```

Erwartet für die neuen Schritte:

```
[index]
  fuzzy-sl: 137 items, 36 properties
  chublets: 832 items, 168 properties
  index: 969 entries from 2 instance(s), 0 warning(s)
[site]
  site: docs/ with search page (969 entries), catalogue, 2 record page(s), 12 vocabulary term(s)
```

## 2. Ansehen

Die Seite öffnet auch direkt von der Platte, ohne Server:

```cmd
start docs\index.html
```

Prüfen: oben „969 of 969 entries“; Haken bei *fuzzy-sl* ergibt 137, dazu *coordinates* 59; Suche „zoo“ 8 Treffer; der Knopf *Theme* wechselt Auto, Hell, Dunkel.

## 3. Abnahme

Committen, nochmal laufen lassen, der Arbeitsbaum bleibt sauber (`docs/` ist versioniert):

```cmd
git add -A && git commit -m "S7 index and facet page" && python main.py --strict && git status
```

Erwartet: `nothing to commit, working tree clean`.

## 4. Push und Pages einschalten

```cmd
git push
```

Dann auf GitHub: *Settings → Pages → Build and deployment → Source: Deploy from a branch → Branch `main`, Ordner `/docs` → Save*. Nach ein bis zwei Minuten antwortet https://beaverbridge-framework.github.io/beaverbridge-registry/ mit der Seite; dort muss auch `…/vocab/instanceOf` und `…/record/fuzzy-sl` antworten.

## Nächster Schritt

Neuer Chat: `PRIMER.md` hochladen und „S8 bitte“ (Query-Seite mit Pyodide) oder „S5 bitte“ (CRM-Anker, dann kommt eine Facette dazu) oder „S6 bitte“ (SHACL-Gate).
