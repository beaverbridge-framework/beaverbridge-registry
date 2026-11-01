# Patch: S5 und S6 — CRM-Brücke und SHACL-Gate

**S5:** Jede Klasse bekommt eine Klassenart (`domain` oder `model`) und, wo möglich, einen CIDOC-CRM-Anker, auch bei Chublets, das keinen mitbringt. **S6:** Das Bundle wird gegen 25 SHACL-Regeln geprüft, und vorher beweist ein Selbsttest, dass die Prüfung fehlschlagen kann.

Die Zuordnung in `crosswalks/classes.csv` ist ein **Vorschlag**: Klassenart für alle 32 Klassen, E73 für Chublets-Software, E53 für *Site*. Bitte durchsehen und dort korrigieren.

## Inhalt

| Datei | Änderung |
|---|---|
| `crosswalks/classes.csv` | neu: eine Zeile je Klasse, Art, CRM-Anker, Basis |
| `crosswalks/README.md` | Abschnitt zu `classes.csv` |
| `py/step_bridge.py` | neu: Schritt `bridge` |
| `py/step_validate.py` | neu: Schritt `validate` (war Stub), mit Selbsttest |
| `metadata/shapes.ttl`, `tests/shacl/` | neu: die Regeln, `good.ttl`, `bad.ttl`, `expected.json` |
| `metadata/bbr.ttl` | `bbr:classKind`, `bbr:crmClass`, `bbr:crmBasis` |
| `py/step_bundle.py` | übernimmt die Brücke; Weiterleitungen (7 in Chublets) sind keine Entitäten mehr |
| `py/step_index.py`, `templates/app.js` | Facetten *Kind of class* und *CIDOC CRM* |
| `py/step_site.py` | Downloads `crm_bridge.ttl` und `shapes.ttl` |
| `queries.yaml` | 12 Abfragen: `crm-anchors` mit Basis, neu `class-kinds` und `crm-reach` |
| `main.py` | `bridge` im Standardlauf, nach `survey` |
| `dist/`, `docs/`, `qmd/` | erzeugt |
| `README.md`, `PRIMER.md` | Status, S8 abgenommen, S5 und S6 erledigt, neue Beschlüsse |

Dateien in den Repo-Ordner ziehen, Ordnerstruktur beibehalten, vorhandene Dateien ersetzen. Alle Befehle für Windows `cmd`.

## 0. Vorbereitung

`pyshacl` muss installiert sein (steht in `requirements.txt`):

```cmd
pip install -r requirements.txt
```

## 1. Lauf

```cmd
python main.py
```

Erwartet für die neuen Zeilen:

```
[bridge]
  bridge: 32 classes, 5 with an anchor of their own, 42 triples, 0 warning(s)
[bundle]
  fuzzy-sl: 12462 source triples, 1455 kept, 173 entities, 264 role statements, 0 redirect(s)
  chublets: 99261 source triples, 13883 kept, 1000 entities, 2858 role statements, 7 redirect(s)
  bundle: 19703 triples from 2 instance(s), 0 warning(s)
[validate]
  validate: self-test ok (25 rules fail on bad.ttl, nothing on good.ttl)
  validate: 0 violation(s), 0 warning(s), 27 note(s)
```

## 2. Ansehen

Die Suche öffnet von der Platte. Neue Facetten: *Kind of class* (domain 501, model 462, ohne Klasse 27) und *CIDOC CRM* (E73 Information Object 442, E53 Place 59, ohne Anker 468).

```cmd
start docs\index.html
```

Berichte: `dist\bridge_report.md` (Art und Anker je Klasse, mit Weg der Vererbung) und `dist\validation_report.md`.

```cmd
start dist\bridge_report.md
```

## 3. Abnahme

Committen, nochmal laufen lassen, der Arbeitsbaum bleibt sauber:

```cmd
git add -A && git commit -m "S5 CRM bridge, S6 SHACL gate" && python main.py --strict && git status
```

Erwartet: `nothing to commit, working tree clean`.

## 4. Push

```cmd
git push
```

## Nächster Schritt

Zuerst die Zuordnung in `crosswalks/classes.csv` prüfen. Danach bleibt S9, die Überführung nach `beaverbridge`; dafür neuer Chat mit `PRIMER.md`.
