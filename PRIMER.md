# PRIMER — beaverbridge-registry

Arbeitsplan für das Repo `beaverbridge-framework/beaverbridge-registry`. Wird am Anfang jedes Chats hochgeladen und am Ende zurückgeschrieben. Teil A zuerst lesen, dann nur den Schritt, an dem gearbeitet wird.

---

## Teil A — Immer gültig

### A1 Ausgangslage

**Wofür das Repo da ist.** Vorstufe von BeaverBridge (siehe Konzeptskizze „BeaverBridge", Tagline *Building Bridges from Community Data to Semantic Knowledge*). Das Repo registriert statische Wikibase-Instanzen, holt deren RDF-Exporte und bündelt sie zu einem gemeinsamen Graphen mit Facettenseite und SPARQL-Seite im Browser. Vorbild ist `FDOx-squirrel/fdo-squirrel-registry`. Am Ende wird alles in das Projekt `beaverbridge` überführt.

**Was schon existiert und nicht neu gebaut wird:**

| Repo | Rolle | Pages-Adresse | Erzeuger |
|---|---|---|---|
| `n4o-rse/wikibase-static` | Paket: Harvest, CSV-Import, Build der Static-Seiten | — | — |
| `n4o-rse/fuzzy-sl-static` | Quelle 1: gesicherte Kopie von fuzzy-sl.wikibase.cloud | https://n4o-rse.github.io/fuzzy-sl-static/ | wikibase-static 0.10.0 |
| `n4o-rse/chublets-wikibase-demo` | Quelle 2: Modell-Demo der Chublets-Wikibase | https://n4o-rse.github.io/chublets-wikibase-demo/ | wikibase-static 0.19.0 |
| `FDOx-squirrel/fdo-squirrel-registry` | Vorbild für Pipeline, Gate, Query-Seite | https://fdox-squirrel.github.io/fdo-squirrel-registry/ | — |

**Befunde** (geprüft 2026-11-01 durch Klonen beider Static-Repos):

1. Jede Instanz hat einen **eigenen Namespace** über `rdf_base` in `site.yaml`. Entitäts-IRIs sind deshalb global eindeutig, obwohl die Kurz-IDs kollidieren (`Q1` gibt es in beiden). Ein Umschreiben der IRIs ist **nicht nötig**; nur Anzeige und Facetten brauchen ein Instanz-Präfix.
2. Die **Präfixfamilien unterscheiden sich**: fuzzy-sl-static schreibt `wd:`, `wdt:`, `p:`, `ps:` (mit eigener Basis-IRI), chublets-wikibase-demo schreibt `chb:`, `chbt:`, `chbp:`, `chbps:`. Das ist nur Syntax; nach dem Parsen sind es volle IRIs. Eine gemeinsame Abfrage darf sich nicht auf Präfixnamen stützen.
3. **Property-Pfade unterscheiden sich im Kern:** P1/P2 bedeuten in beiden Instanzen nicht dasselbe (fuzzy-sl: `formatter_property: P18`; Chublets: `P5`; Chublets-Kern: Q1 Class, Q2 Property, Q3 Instance, P1 subclass of, P2 instance of). Eine instanzübergreifende Abfrage nach „instance of" braucht eine **Property-Zuordnung je Instanz** (Crosswalk), kein gemeinsames `P31`.
4. **Veröffentlichte RDF-Dateien** liegen je Instanz unter `docs/downloads/`: `<host>-<repo>.ttl` (Vollexport) und `wikibase-ontology.ttl`. Größen: fuzzy-sl ca. 0,6 MB, Chublets ca. 5,2 MB. Erreichbarkeit über die echten Pages-Adressen ist aus der Sandbox **nicht** prüfbar (Proxy antwortet 403 auf `github.io`, geprüft 2026-11-01); der Harvest wurde gegen lokal ausgelieferte Klone getestet. Die Prüfung am PC steht in der Abnahme von S2.
5. Die Chublets-Demo trägt `counterpart:` in `site.yaml` und schreibt dadurch `owl:sameAs` auf die echte Wikibase `chublets-wikibase.de`. Das ist dort Absicht; die Registry übernimmt es unverändert, behauptet aber selbst nichts darüber.
6. `downloads/wikibase-ontology.ttl` ist in **beiden** Instanzen byte-identisch (11 336 Bytes, 255 Tripel, SHA-256 `5f71c0e8…`) und nennt keinen Instanz-Namespace; es ist die generische Wikibase-Ontologie von wikibase-static (geprüft 2026-11-01). Folge: Sie wird je Instanz geholt, im Bundle aber nur einmal gebraucht, und eine `rdf_base`-Prüfung gilt nur für den Vollexport (`role: export`).
7. Tripelzahlen der Vollexporte (rdflib 7.6.0, 2026-11-01): fuzzy-sl 12 462 (wikibase-static 0.10.0, Daten vom 2025-11-01), Chublets 99 261 (0.19.0, Daten vom 2026-10-25). Beide parsen ohne Fehler.
8. Beide Exporte enthalten ein eigenes DCAT-Dataset (`cat:export` bzw. `chbcat:`) mit Lizenzangabe (CC0). Das ist der Anker für den Katalogeintrag.

### A2 Zielbild

```
registry/sources.json            kuratierte Liste der Instanzen (Name, pages_url, rdf_base, Präfixfamilie)
        │  py/step_harvest.py    HTTP: <pages_url>/downloads/*.ttl  (einziger Netz-Schritt)
        ▼
data/raw/<instanz>/              unverändert, read-only, harvest.json mit Hash und Generator-Version
        │  crosswalks/*.csv      Property-/Klassen-Zuordnung je Instanz → CIDOC CRM
        │  py/step_bundle.py     Katalog (DCAT), Instanz-Präfix, CRM-Anker
        ▼
dist/beaverbridge-registry.ttl   DCAT + Wikibase-RDF + CRM/CRMdig + SKOS
        │  metadata/shapes.ttl   SHACL-Gate → Build stoppt bei Verletzung
        │  py/step_index.py      SPARQL → dist/registry-index.json
        │  py/step_site.py       → docs/index.html (Facetten), docs/instance/<id>.html
        │  queries.yaml
        │  py/step_sparql.py     → docs/sparql.html, docs/downloads/queries/*.rq
        ▼
docs/                            index.html · sparql.html (Pyodide) · Bundle-Download
```

Eigenschaften des Ergebnisses (jede ist prüfbar):

1. **Offline baubar:** Nach dem Harvest läuft alles ohne Netz.
2. **Byte-identisch:** zwei Läufe hintereinander, `git status` zweimal sauber.
3. **Keine leere Query:** Eine Beispiel-Query ohne Zeilen bricht den Build ab.
4. **Herkunft sichtbar:** Jedes Item im Bundle ist über Instanz-Präfix und `dct:source` auf seine Instanz zurückführbar.
5. **Kein Rückverweis erfunden:** Die Registry schreibt `owl:sameAs` nur, wenn die Quelle es schon enthält.

### A3 Querschnittsregeln

- Rohdaten liegen in `data/raw/`, unverändert und read-only. Was daraus entsteht, geht nach `dist/` oder `docs/`.
- Kein `datetime.now()` in Generatoren; Daten kommen aus `RELEASE` oder aus den Quelldaten.
- Zwei Läufe hintereinander, `git status` bleibt sauber.
- Netz nur im Harvest-Schritt, und der gehört nicht zum Standardlauf.
- Graphen werden über sortierte N-Triples serialisiert; JSON mit `sort_keys=True`, `ensure_ascii=False`.
- `PRIMER.md` ist deutsch; Code, Kommentare, README und Ontologie sind britisches Englisch.
- Befehle für Windows `cmd`, immer in **einer** Zeile mit `&&` verkettet.
- Ein Thema pro Chat, ein Repo pro Chat. Offene Entscheidungen werden als Formular gefragt, mit freiem Kommentarfeld.
- `dist/` wird **nicht** ignoriert, denn es enthält die versionierten Produkte.

### A4 Beschlusslage

| Frage | Beschluss | seit |
|---|---|---|
| Repo-Name | `beaverbridge-registry` (Registry = Quellenliste + gemeinsames Bundle) | 2026-11-01 |
| Ort | `github.com/beaverbridge-framework/beaverbridge-registry` (zuerst unter `n4o-rse` geplant, dann `florianthiery`, am 2026-11-01 in die Organisation `beaverbridge-framework` gelegt) | 2026-11-01 |
| Organisation | Perspektivisch ziehen auch die übrigen Repos der Familie nach `beaverbridge-framework`; bis dahin bleiben die Quellen (`fuzzy-sl-static`, `chublets-wikibase-demo`) unter `n4o-rse`, und `sources.json` führt die Adressen je Instanz einzeln | 2026-11-01 |
| Quellen holen | über GitHub Pages (HTTP), Git-Clone nur als späterer Fallback über `config.local.json` | 2026-11-01 |
| IRIs der Items | unverändert aus der Quelle; Eindeutigkeit kommt vom Namespace der Instanz | 2026-11-01 |
| Anzeige bei gleichen IDs | Instanz-Präfix, z. B. `fuzzy-sl:Q1`, `chublets:Q1`, Label dahinter | 2026-11-01 |
| Bundle-Umfang | Items, Properties und Klassen | 2026-11-01 |
| Startinstanzen | `fuzzy-sl-static` und `chublets-wikibase-demo` | 2026-11-01 |
| Rolle der Dateien in `sources.json` | je Datei `role`: `export` (Vollexport, wird gegen `rdf_base` geprüft) oder `ontology` (generische Wikibase-Ontologie) | 2026-11-01 |
| Harvest-Fehler | eine nicht erreichbare Instanz bricht den Lauf nicht ab (Exit 0, Meldung); nur `--strict` macht daraus Exit 1; Stopp nach drei Instanzen ohne Treffer in Folge | 2026-11-01 |
| Manifest ohne Uhr | `harvest.json` enthält Bytes, SHA-256, ETag, Generator und Datenstand aus der Datei selbst, keine Abrufzeit | 2026-11-01 |
| Rohdaten bleiben Bytes | `.gitattributes`: `data/raw/** -text`, damit kein Zeilenende-Umbau den SHA-256 ändert; Dateien werden schreibgeschützt abgelegt | 2026-11-01 |
| Merge gleicher Dinge über Instanzen | kein Merge ohne Beleg; gleiche Namen werden gemeldet, nie verschmolzen | Vorschlag |
| CRM-Anker | Crosswalk-CSV je Instanz als einzige Quelle, Mechanismen wie in fdo-squirrel-registry (`axiom`, `ext-axiom`, `normalise`, `instance`, `none`) | Vorschlag |
| Shapes | Severity nach dem Modalverb des N4O-CIDOC-CRM-Profils (MUST → Fehler, SHOULD → Warnung) | Vorschlag |
| Lizenz | Code MIT; Bundle CC BY 4.0 mit Lizenz je Eintrag erhalten (beide Quellen sind CC0) | Vorschlag |
| Überführung nach `beaverbridge` | am Ende, Schritt S9; durch die Organisation `beaverbridge-framework` womöglich nur noch Umbenennung statt Transfer | Vorschlag |
| Farben und Schrift | Palette aus dem Logo, Hell/Dunkel, Systemschrift der Familie plus optional Bitter für Überschriften; siehe `design/PALETTE.md` | Vorschlag |

### A5 Was in welchem Chat hochgeladen wird

Standard ist ein Bundle des Repos ohne Erzeugtes. Für die Windows-`cmd` (eine Zeile):

```cmd
cd C:\git && robocopy beaverbridge-registry %TEMP%\bbr-bundle /E /XD .git .venv __pycache__ data\raw dist docs /XF config.local.json >nul & powershell -Command "Compress-Archive -Path $env:TEMP\bbr-bundle\* -DestinationPath C:\git\bbr-bundle.zip -Force"
```

Nicht hochladen: `config.local.json`, `.venv/`, `.git/`, `data/raw/`, `dist/*.ttl`, `docs/`. Das Skeleton darf ich im Chat auch frisch von GitHub klonen, wenn die Verbindung steht.

### A6 IRI-Landkarte

| Pfad | Inhalt | Ziel des Redirects | Status |
|---|---|---|---|
| `https://beaverbridge-framework.github.io/beaverbridge-registry/` | Facettenseite | — | geplant |
| `…/sparql.html` | Browser-SPARQL | — | geplant |
| `…/catalog` | `dcat:Catalog` | `downloads/beaverbridge-registry.ttl` | geplant |
| `…/record/<instanz>` | Katalogeintrag je Instanz | `instance/<instanz>.html` | geplant |

Offen: w3id-Prefix und Content Negotiation (Teil D).

---

## Teil B — Schrittübersicht

| ID | Schritt | Repo | hängt ab von | Status |
|---|---|---|---|---|
| S0 | Festlegungen (Name, Ort, IRIs, Anzeige, Umfang) | — | — | erledigt 2026-11-01 |
| S1 | Skeleton: Layout, `main.py`, Utils, Licence, Citation | beaverbridge-registry | S0 | erledigt 2026-11-01 |
| S2 | Harvest: `sources.json`, Pages-Download, `harvest.json`, Hash | beaverbridge-registry | S1 | Code fertig 2026-11-01, Lauf gegen echte Pages am PC offen |
| S3 | Befund je Instanz: Klassen, Properties, Kern-Properties (Crosswalk-Entwurf) | beaverbridge-registry | S2 | offen |
| S4 | Bundle: DCAT-Katalog, Instanz-Präfix, Herkunft | beaverbridge-registry | S2 | offen |
| S5 | CRM-Crosswalk: `crosswalks/*.csv` → `crm_bridge.ttl` | beaverbridge-registry | S3, S4 | offen |
| S6 | SHACL-Gate mit Selbsttest | beaverbridge-registry | S4 | offen |
| S7 | Index und Facettenseite | beaverbridge-registry | S4 | offen |
| S8 | Query-Seite (`queries.yaml`, Pyodide) | beaverbridge-registry | S4 | offen |
| S9 | Überführung nach `beaverbridge` | beaverbridge | S5–S8 | offen |

Unabhängig voneinander: S6, S7 und S8 hängen nur am Bundle (S4) und können in beliebiger Reihenfolge laufen. S3 und S4 können parallel starten, sobald S2 Daten geliefert hat.

---

## Teil C — Die Schritte

## S1 — Skeleton

**Ziel:** Ein Repo, in dem `python main.py` läuft und für jeden Schritt „nichts zu tun" meldet.

**Uploads:** keine; das Skeleton kommt als Patch-ZIP.

Inhalt: `main.py` (Orchestrator mit `--list`, `--only`, `--from`, `--skip`, `--dry-run`, `--strict`), `py/registry_utils.py` (`RELEASE`, Pfade, `ensure_dirs()`, `write_json()`), je eine Stub-Datei `py/step_*.py`, `registry/sources.json` mit den zwei Startinstanzen, `requirements.txt`, `LICENSE`, `CITATION.cff`, `.gitignore` (ohne `dist/`).

**Abnahme:** `python main.py --list` nennt sechs Schritte; `python main.py` endet mit Exit-Code 0 und meldet für jeden Schritt „nothing to do"; ein zweiter Lauf lässt `git status` sauber.

### Erledigt 2026-11-01

Skeleton steht. `main.py --list` nennt sechs Schritte (`harvest` explizit, die anderen im Standardlauf), `python main.py` meldet für jeden „nothing to do". `dist/pipeline_report.txt` enthält keine Zeiten, damit ein zweiter Lauf nichts ändert. Der `git status`-Test auf deiner Seite steht noch aus (siehe PATCH-README).

## S2 — Harvest

**Ziel:** `data/raw/<instanz>/` enthält Vollexport und Ontologie beider Instanzen, unverändert, mit `harvest.json`.

**Uploads:** Bundle (A5).

Kern: `sources.json` führt je Instanz `id`, `pages_url`, `rdf_base`, `prefix_family`. Der Harvest lädt `downloads/*.ttl`, prüft per Bytezahl und SHA-256 gegen den vorherigen Lauf und schreibt nichts neu, wenn nichts neu ist. Eine nicht erreichbare Instanz bricht den Lauf nicht ab; nach drei Fehlern in Folge stoppt er. Wegen der Anubis-Erfahrung bei Wikibase Cloud: Pages selbst ist unkritisch, die Quelle bleibt aber nie direkt im Spiel.

**Abnahme:** `python main.py harvest` holt je Instanz Vollexport und Ontologie; ein zweiter Lauf meldet nur 'unchanged'; `harvest.json` nennt Generator-Version (`0.10.0` bzw. `0.19.0`), Hash und Tripelzahl; nach `git add`, `commit` und erneutem Lauf ist `git status` sauber.

### Erledigt 2026-11-01 (Code; Lauf gegen echte Pages offen)

Umgesetzt in `py/step_harvest.py`: Download per HTTP mit `If-None-Match` (ETag), bei 304 keine Übertragung; bei gleichem SHA-256 wird nichts neu geschrieben; Parse-Prüfung mit rdflib (Tripelzahl im Manifest, Parse-Fehler als Warnung, Datei bleibt unverändert); `--force`, `--instance`, `--local` (liest aus `clone_dir` in `config.local.json`), `--offline`, `--sources`, `--strict`. `main.py` reicht unbekannte Optionen an den Schritt weiter (`python main.py harvest --force`) und schreibt `dist/pipeline_report.txt` nur noch bei einem vollen Lauf.

Getestet gegen lokal ausgelieferte Klone mit ETag-Server: Lauf 1 holt vier Dateien (0,6 MB und 5,2 MB), Lauf 2 meldet viermal 304, das Manifest ist nach Lauf 2 und nach `--force` byte-identisch; `--local` liefert dieselben Hashes; ein toter Port gibt Exit 0, mit `--strict` Exit 1, und legt nichts an.

**Offen für die Abnahme am PC:** Echter Lauf gegen `n4o-rse.github.io`, dann `data/raw/` einchecken.

*(S3–S9 werden angelegt, sobald sie dran sind.)*

---

## Teil D — Offene Punkte

- **Gemeinsame Kern-Properties:** Ob die Registry ein eigenes, kleines Vokabular (`bbr:instanceOf`, `bbr:subclassOf`) über die Instanz-Properties legt oder nur über CRM anchored. Entscheidung in S3.
- **w3id-Prefix** für `…/record/…` und Content Negotiation.
- **Dritte Instanz:** `osm-static-benchmarks` hat ein sehr anderes Modell und wäre der Härtetest, aber erst nach S6.
- **Zenodo-DOI** für das Bundle als FDO (nach S8).
