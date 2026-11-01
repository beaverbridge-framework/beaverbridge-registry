# Patch: S4 — Bundle

Baut aus den geharvesteten Exporten einen gemeinsamen Graphen, begrenzt auf das, was eine Facettensuche und Abfragen über Instanzen brauchen: Entitäten mit Typ, Labels, Beschreibung, Direktaussagen und Klassenlinks, dazu ein Katalogeintrag je Instanz (Quelle, SHA-256, Generator, Datenstand, Lizenz) und die Rollen aus `crosswalks/core-properties.csv` als normalisierte `bbr:`-Aussagen. Statement-, Referenz- und Qualifier-Knoten bleiben in `data/raw/`.

## Inhalt

| Datei | Änderung |
|---|---|
| `py/step_bundle.py` | neu: der Schritt `bundle` (war Stub) |
| `py/registry_utils.py` | `REGISTRY_BASE`, `BBR_NS`, `ROLES`, `read_core()`, `write_ntriples()` |
| `py/step_survey.py` | nutzt `ROLES` und `read_core()` aus den Utils |
| `metadata/bbr.ttl` | neu: das `bbr:`-Vokabular |
| `PRIMER.md` | S3 abgenommen, S4 erledigt, neue Beschlüsse in A4 |

Dateien in den Repo-Ordner ziehen, Ordnerstruktur beibehalten. Alle Befehle für Windows `cmd`.

## 1. Lauf

```cmd
python main.py
```

Erwartet für den Bundle-Schritt:

```
fuzzy-sl: 12462 source triples, 1455 kept, 173 entities, 264 role statements
chublets: 99261 source triples, 13883 kept, 1007 entities, 2858 role statements
bundle: 19668 triples from 2 instance(s), 0 warning(s)
```

## 2. Abnahme

Committen, nochmal laufen lassen, Arbeitsbaum bleibt sauber (`dist/beaverbridge-registry.*` und `dist/bundle_report.md` sind versioniert):

```cmd
git add -A && git commit -m "S4 bundle" && python main.py --strict && git status
```

Erwartet: `nothing to commit, working tree clean`.

Bericht ansehen:

```cmd
start dist\bundle_report.md
```

## 3. Push

```cmd
git push
```

## Nächster Schritt

Neuer Chat: `PRIMER.md` hochladen und „S5 bitte“ (CRM-Crosswalk, Anker für Chublets) oder S6/S7/S8 in beliebiger Reihenfolge.
