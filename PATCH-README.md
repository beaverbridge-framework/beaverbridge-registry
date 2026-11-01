# Patch S11b: Leaflet-Basiskarte und Sortierung

| Datei | Änderung |
|---|---|
| `templates/app.js` | Kartenansicht: Leaflet 1.9.4 + MapLibre GL 5.24.0 + OpenFreeMap „Positron“ (wie LinkedOpenOgham), erst beim ersten Öffnen der Karte geladen; SVG-Karte bleibt als Rückfall. Sortierung: Titel ohne Buchstaben am Anfang (DOIs, Zahlen) kommen ans Ende |
| `templates/index.html.j2`, `templates/style.css` | Container für die Leaflet-Karte |
| `PRIMER.md` | zweite Drittanbieter-Ausnahme dokumentiert |
| `docs/`, `dist/`, `qmd/` | neu erzeugt |

Dateien in den Repo-Ordner ziehen und ersetzen.

## Abnahme und Push

```cmd
git add -A && git commit -m "S11b leaflet basemap, letters first in sort" && python main.py --strict && git status && git push
```

Erwartet: `--strict` grün, `nothing to commit, working tree clean`. Nach dem Deploy auf der Suchseite „Map“ öffnen: Basiskarte mit Punkten, Klick auf einen Punkt zeigt Label und Link; Liste beginnt mit „ABMA_tutorials“.
