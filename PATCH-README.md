# Patch S11: Facettenseite mit Region, Karte und ohne Modell-Items

| Datei | Änderung |
|---|---|
| `templates/app.js`, `templates/index.html.j2`, `templates/style.css` | Facetten Instanz (mit Lizenz), Region, Klasse, CIDOC CRM; Schalter für Modellklassen; Ansicht Liste/Karte (SVG) |
| `py/step_index.py` | `regions` je Eintrag aus `crosswalks/regions.csv` |
| `crosswalks/regions.csv` | neu: grobe Region-Boxen (von Hand pflegen) |
| `crosswalks/classes.csv` | Chublets Q3 *Instance*: `domain`, Anker `E1_CRM_Entity` (Vorschlag, bitte prüfen) |
| `crosswalks/README.md`, `PRIMER.md` | Beschreibung, S10 abgenommen, S11 erledigt |
| `dist/`, `docs/`, `qmd/` | neu erzeugt |

Dateien in den Repo-Ordner ziehen und ersetzen.

## Abnahme und Push

```cmd
git add -A && git commit -m "S11 facets: region, map, hide model items" && python main.py --strict && git status && git push
```

Erwartet: `--strict` grün (index 996 Einträge, crm-anchors 7 Zeilen, 12 Abfragen mit Zeilen), `nothing to commit, working tree clean`. Auf der Suchseite: 917 von 996 sichtbar; Schalter „Include items of model classes“ zeigt alle 996; Karte zeigt 83 Positionen.
