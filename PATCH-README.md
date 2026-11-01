# Patch: S9 gestrichen, S5 und S6 abgenommen

Nur Dokumentation: Der Schritt S9 (Überführung nach `beaverbridge`) steht nicht mehr im Plan, die Abnahme von S5 und S6 (Commit `328e007`) ist eingetragen.

| Datei | Änderung |
|---|---|
| `PRIMER.md` | S9 aus Teil B, Teil A1 und der Beschlusslage entfernt (dort steht jetzt, dass er gestrichen ist), Abnahme S5/S6 ergänzt |
| `README.md` | Status ohne S9, kein Hinweis mehr auf eine spätere Überführung |

Dateien in den Repo-Ordner ziehen und ersetzen. Es ändert sich nichts an Code und Ausgaben.

## Abnahme und Push

```cmd
git add -A && git commit -m "drop S9, record S5 and S6 acceptance" && python main.py --strict && git status && git push
```

Erwartet: `nothing to commit, working tree clean`.
