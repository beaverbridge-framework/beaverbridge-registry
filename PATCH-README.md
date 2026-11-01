# Patch: S8 — Query-Seite

SPARQL im Browser über das ganze Bundle: `docs/sparql.html` mit zehn bearbeitbaren Abfragen, dieselben als `.rq`-Dateien und als quarto-live-Notebook. Es gibt keinen Endpunkt und keinen Server; `rdflib` läuft unter Pyodide im Browser. Jede Abfrage wird beim Bauen gegen das Bundle ausgeführt, eine leere Antwort bricht den Lauf ab.

## Inhalt

| Datei | Änderung |
|---|---|
| `queries.yaml` | neu: Präfixe und zehn Abfragen, die einzige Quelle |
| `py/step_sparql.py` | neu: Schritt `sparql` (war Stub) |
| `py/registry_utils.py` | `jinja_env()` |
| `py/step_site.py` | nutzt `jinja_env()`, kopiert `theme.js` |
| `templates/` | `sparql.html.j2`, `sparql.qmd.j2` neu; `base.html.j2` (Link „Query“, `theme.js`), `style.css` (Query-Regeln), `app.js` (ohne Theme-Teil), `theme.js` neu |
| `docs/`, `qmd/` | erzeugt (alle Seiten haben jetzt den Link „Query“) |
| `dist/pipeline_report.txt` | erzeugt |
| `README.md`, `PRIMER.md` | Status, S7 abgenommen, S8 erledigt |

Dateien in den Repo-Ordner ziehen, Ordnerstruktur beibehalten, vorhandene Dateien ersetzen. Alle Befehle für Windows `cmd`.

## 1. Lauf

```cmd
python main.py
```

Erwartet für den neuen Schritt: zehn Zeilen `ok` mit Zeilenzahlen (2, 26, 21, 14, 2, 73, 153, 2, 204, 5), dann `sparql: 10 queries, docs/sparql.html, 10 .rq files, qmd/…`.

## 2. Ansehen

Die Query-Seite braucht einen Webserver (der Browser lässt eine Seite von der Platte das Bundle nicht laden). Der Server läuft im Vordergrund, mit Strg+C beenden:

```cmd
start http://localhost:8000/sparql.html && python -m http.server 8000 -d docs
```

Prüfen: Beim ersten Besuch dauert „Loading the Python runtime“ und „Installing rdflib“ einige Sekunden. Dann steht dort „Ready“ und „Graph loaded: 19668 triples“. Jede Abfrage zeigt nach Run dieselbe Zeilenzahl wie oben, Abfrage 4 (*Which Wikibase property stands behind a role?*) zeigt P1 und P2 vertauscht. Ein absichtlicher Tippfehler in einer Abfrage zeigt die Parse-Meldung.

## 3. Abnahme

```cmd
git add -A && git commit -m "S8 query page" && python main.py --strict && git status
```

Erwartet: `nothing to commit, working tree clean`.

## 4. Push

```cmd
git push
```

Nach ein bis zwei Minuten läuft dasselbe unter https://beaverbridge-framework.github.io/beaverbridge-registry/sparql.html.

## Nächster Schritt

Neuer Chat: `PRIMER.md` hochladen und „S5 bitte“ (CRM-Anker, auch für Chublets) oder „S6 bitte“ (SHACL-Gate mit Selbsttest). Danach S9, die Überführung nach `beaverbridge`.
