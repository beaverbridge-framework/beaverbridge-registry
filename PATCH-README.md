# Patch S10: osm-benchmarks als dritte Instanz

Nimmt `osm-benchmarks-static` (OSM-Höhenmarken, ODbL 1.0) in die Registry auf. Das Bundle hat danach 20 701 Tripel aus 3 Instanzen, die Facettenseite 996 Einträge.

| Datei | Änderung |
|---|---|
| `registry/sources.json` | neue Instanz `osm-benchmarks` (Export und Ontologie) |
| `data/raw/osm-benchmarks/` | geerntete Dateien und `harvest.json` (Stand 2026-11-01) |
| `crosswalks/core-properties.csv` | 7 Zeilen für die neue Instanz (5 Rollen, 2 mit `none` und Grund) |
| `crosswalks/classes.csv` | 4 Klassen (Class, Property, Instance, Benchmark → E25_Human-Made_Feature als Brücke) |
| `py/step_bridge.py` | CRM-Klassenname darf Bindestrich enthalten |
| `py/step_index.py` | Lizenzkürzel `ODbL-1.0` |
| `PRIMER.md`, `README.md` | Instanz, Befund, Schritte S10 (erledigt) und S11 (offen) |
| `dist/`, `docs/`, `qmd/` | neu erzeugt |

Dateien in den Repo-Ordner ziehen und ersetzen.

## Abnahme und Push

```cmd
git add -A && git commit -m "S10 add osm-benchmarks as third instance" && python main.py --strict && git status && git push
```

Erwartet: `--strict` grün (survey 3 Instanzen, bundle 20701 Tripel, validate 0 Verletzungen, index 996 Einträge, 12 Abfragen mit Zeilen) und `nothing to commit, working tree clean`.
