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
9. **P1 und P2 sind vertauscht** (geprüft 2026-11-01, `dist/survey_report.md`): fuzzy-sl P1 *instance of*, P2 *subclass of*; Chublets P2 *instance of*, P1 *subclass of*. Auch *part of* (fuzzy-sl P3, Chublets P122), *Wikidata-Verweis* (P34 gegen P4) und *exact match* (P27 gegen P115) haben verschiedene Nummern. Eine instanzübergreifende Abfrage geht deshalb nur über die Rollen-Tabelle `crosswalks/core-properties.csv`.
10. **Keine gemeinsamen Wikidata-Items:** fuzzy-sl nennt 23, Chublets 34 Wikidata-Q-Nummern, der Schnitt ist leer. Die Domänen (Geo/Archäologie gegen Forschungssoftware) überlappen nicht; Fragen über beide Instanzen betreffen Struktur (Klassen, Properties, CRM-Anker), nicht identische Entitäten.
11. **fuzzy-sl trägt seinen CRM-Anker selbst:** Die Klassen-Items Q146 *E53 Place* und Q147 *E26 Physical Feature* haben über P37 *equivalent class* die CRM-IRI. *Archaeological Site* (52 Items) und *Geological Site* (19) erben E53 über *subclass of*, *Cave* erbt E26 (0 Items). Vierzehn von 19 Klassen haben keinen Anker: die Datenmodell-Klassen (*Spatial Type*, *Source*, *Project*, *Person*, *Certainty Level*, …), aber auch die Fachklassen *Site* und *Provenance Site* sowie *CIDOC-CRM Class* selbst.
12. **Chublets hat keinen CRM-Anker.** Der Klassenbaum hat die Wurzel Q3 *Instance* (387 direkte Instanzen); Q1 *Class* und Q2 *Property* sind Unterklassen von Q3, alle 168 Properties sind Instanzen von Q2. *chublet* (Q106, 442 Items) ist Unterklasse von Q101 *research software* und Q105 *Little Minion*. Klassen und Properties erscheinen also beide als „Instanzen".
13. **Nur Chublets schreibt `rdf:type` auf Klassen-Items** (RDFS-Brücke: 442 auf Q106, 248 auf Q103, …), fuzzy-sl nicht. `rdf:type` taugt daher nicht als gemeinsames Kriterium; die Rolle `instance_of` über die Property schon.
14. **Nutzung:** fuzzy-sl verwendet 18 von 36 Properties, Chublets 32 von 168. Die Wikibase-Mechanik (`owl:Class` mit `owl:complementOf` unter `prop/novalue/…`, je eine pro Property) ist für Abfragen irrelevant und wird ignoriert.
15. **Quelldaten-Auffälligkeiten (bleiben in `data/raw/` unverändert):** In fuzzy-sl P10 *related to* steht an Q46 die Adresse `http://openopenstreetmap.org/node/1257748539` (Tippfehler im Host), und Wikidata-Adressen kommen mit und ohne `www.` vor. Rückmeldung an die Quelle, nicht Korrektur hier.

### A2 Zielbild

```
registry/sources.json            kuratierte Liste der Instanzen (Name, pages_url, rdf_base, Präfixfamilie)
        │  py/step_harvest.py    HTTP: <pages_url>/downloads/*.ttl  (einziger Netz-Schritt)
        ▼
data/raw/<instanz>/              unverändert, read-only, harvest.json mit Hash und Generator-Version
        │  py/step_survey.py     Vermessung + Prüfung von crosswalks/core-properties.csv
        │                        → dist/survey.json, dist/survey_report.md
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
4. **Herkunft sichtbar:** Jedes Item im Bundle ist über `bbr:fromInstance` auf den Katalogeintrag seiner Instanz (mit Quelle, SHA-256, Generator, Datenstand) zurückführbar.
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
| Bundle-Umfang | nur was Facetten und Abfragen über Instanzen brauchen: Entitäten (Items, Properties, Klassen) mit Typ, Labels, Beschreibung, Direktaussagen, Klassenlinks (`rdfs:subClassOf`, `owl:equivalentClass`, `owl:sameAs`), Property-Metadaten; Katalogknoten der Instanz (Titel, Lizenz, Landingpage). Weggelassen: Statement-, Referenz-, Qualifier-Knoten, Zähler, DCAT je Entität, Leerknoten. Die Whitelist steht in `py/step_bundle.py` | 2026-11-01 |
| IRI von `bbr:` | `https://beaverbridge-framework.github.io/beaverbridge-registry/vocab/` (Pages-Pfad, später w3id); Vokabular von Hand in `metadata/bbr.ttl` | 2026-11-01 |
| Katalog-IRIs | Registry `…/catalog`, je Instanz ein `dcat:CatalogRecord` unter `…/record/<id>`; jede Entität trägt `bbr:fromInstance` | 2026-11-01 |
| Seite und Pages | `docs/` wird vollständig von `step_site.py` erzeugt und versioniert (`linguist-generated`); GitHub Pages liefert Branch `main`, Ordner `/docs`; die Seiten brauchen weder Netz noch Drittanbieter | 2026-11-01 |
| Facetten | Instanz, Klasse (mit Instanz-Präfix), Has (Koordinaten, Wikidata-Link, externer Match), Lizenz; Freitext über Label, Beschreibung, Kennung; Einträge sind Items, Properties nur gezählt | 2026-11-01 |
| Adressen der Registry-IRIs | `…/catalog`, `…/record/<id>` und `…/vocab/<Begriff>` werden als `.html`-Dateien ausgeliefert (Pages löst die Endung auf); Content Negotiation gibt es nicht, RDF liegt unter `downloads/` und `vocab/bbr.ttl` | 2026-11-01 |
| Normalisierung | Wikidata-Q/P-Nummern als Text werden zu `http://www.wikidata.org/entity/…`; Werte, die sich nicht normalisieren lassen, werden gemeldet und übersprungen (mit `--strict` Fehler) | 2026-11-01 |
| Startinstanzen | `fuzzy-sl-static` und `chublets-wikibase-demo` | 2026-11-01 |
| Rolle der Dateien in `sources.json` | je Datei `role`: `export` (Vollexport, wird gegen `rdf_base` geprüft) oder `ontology` (generische Wikibase-Ontologie) | 2026-11-01 |
| Harvest-Fehler | eine nicht erreichbare Instanz bricht den Lauf nicht ab (Exit 0, Meldung); nur `--strict` macht daraus Exit 1; Stopp nach drei Instanzen ohne Treffer in Folge | 2026-11-01 |
| Manifest ohne Uhr | `harvest.json` enthält Bytes, SHA-256, ETag, Generator und Datenstand aus der Datei selbst, keine Abrufzeit | 2026-11-01 |
| Rohdaten bleiben Bytes | `.gitattributes`: `data/raw/** -text`, damit kein Zeilenende-Umbau den SHA-256 ändert; Dateien werden schreibgeschützt abgelegt | 2026-11-01 |
| Rollen-Tabelle | `crosswalks/core-properties.csv`: je Rolle (`instance_of`, `subclass_of`, `part_of`, `coordinates`, `equivalent_class`, `wikidata_equivalent`, `external_match`) und Instanz eine Property oder `none` mit Grund; von Hand gepflegt, vom Survey gegen den Graphen geprüft (Property vorhanden, englisches Label und Datentyp gleich) | 2026-11-01 |
| Rollen im Bundle | Eigenes Vokabular `bbr:` zusätzlich: je Rolle eine normalisierte Aussage (`bbr:instanceOf`, `bbr:subclassOf`, …) neben der unveränderten Quellaussage; die CRM-Bridge hängt an `bbr:` | 2026-11-01 |
| Survey im Standardlauf | Schritt `survey` läuft offline im Standardlauf, ohne Harvest gibt er nichts aus (mit `--strict` Fehler); Abweichungen der Rollen-Tabelle sind Warnungen, mit `--strict` Fehler | 2026-11-01 |
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
| S2 | Harvest: `sources.json`, Pages-Download, `harvest.json`, Hash | beaverbridge-registry | S1 | erledigt 2026-11-01 |
| S3 | Befund je Instanz: Klassen, Properties, Kern-Properties (Crosswalk-Entwurf) | beaverbridge-registry | S2 | erledigt 2026-11-01 |
| S4 | Bundle: DCAT-Katalog, Instanz-Präfix, Herkunft | beaverbridge-registry | S2 | erledigt 2026-11-01 |
| S5 | CRM-Crosswalk: `crosswalks/*.csv` → `crm_bridge.ttl` | beaverbridge-registry | S3, S4 | offen |
| S6 | SHACL-Gate mit Selbsttest | beaverbridge-registry | S4 | offen |
| S7 | Index und Facettenseite | beaverbridge-registry | S4 | erledigt 2026-11-01 |
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

### Erledigt 2026-11-01

Umgesetzt in `py/step_harvest.py`: Download per HTTP mit `If-None-Match` (ETag), bei 304 keine Übertragung; bei gleichem SHA-256 wird nichts neu geschrieben; Parse-Prüfung mit rdflib (Tripelzahl im Manifest, Parse-Fehler als Warnung, Datei bleibt unverändert); `--force`, `--instance`, `--local` (liest aus `clone_dir` in `config.local.json`), `--offline`, `--sources`, `--strict`. `main.py` reicht unbekannte Optionen an den Schritt weiter (`python main.py harvest --force`) und schreibt `dist/pipeline_report.txt` nur noch bei einem vollen Lauf.

Getestet gegen lokal ausgelieferte Klone mit ETag-Server: Lauf 1 holt vier Dateien (0,6 MB und 5,2 MB), Lauf 2 meldet viermal 304, das Manifest ist nach Lauf 2 und nach `--force` byte-identisch; `--local` liefert dieselben Hashes; ein toter Port gibt Exit 0, mit `--strict` Exit 1, und legt nichts an.

**Abnahme am PC (Windows, Python 3.10) bestanden:** Alle vier Dateien kamen von den echten Pages, mit denselben Tripelzahlen wie lokal (12 462 und 99 261); der erste Lauf dauerte 7,9 s, der zweite 0,5 s mit viermal `unchanged (304)`; nach Commit und erneutem Lauf war `git status` sauber (Commit `b9f549a`, Rohdaten versioniert in `data/raw/`).

## S3 — Befund je Instanz und Rollen-Tabelle

**Ziel:** Ein offline laufender Schritt vermisst jede geharvestete Instanz und prüft die Rollen-Tabelle gegen die Graphen; die Befunde stehen in A1.

**Uploads:** keine; `data/raw/` kommt aus dem Repo.

Umgesetzt: `py/step_survey.py` (Schritt `survey` im Standardlauf, nach `harvest`, vor `bundle`) schreibt `dist/survey.json` und `dist/survey_report.md`: Zählwerte, Properties im Gebrauch mit Datentyp und Häufigkeit, Klassen mit Instanzzahl und Oberklassen, Wurzelklassen, Klassen mit Anker (`equivalent_class`) samt geerbten Ankern, Wikidata-Q-Nummern je Instanz und ihr Schnitt. `crosswalks/core-properties.csv` (mit `crosswalks/README.md`) ordnet sieben Rollen den Properties zu. Alle Namensräume werden aus `rdf_base` abgeleitet, nicht aus Präfixnamen.

**Abnahme:** `python main.py` läuft durch und meldet 0 Warnungen; zwei Läufe hintereinander lassen `dist/survey.json` und `dist/survey_report.md` byte-identisch und `git status` sauber; ein absichtlich falscher Eintrag in der Rollen-Tabelle erzeugt eine Warnung und mit `--strict` Exit 1.

### Erledigt 2026-11-01

Abnahme auf dem PC: Commit 0ce9ff6, Survey 8,8 bis 8,9 s, 0 Warnungen, `--strict` grün, `git status` sauber.

Gemessen: fuzzy-sl 12 462 Tripel, 137 Items, 36 Properties (18 in Gebrauch), 19 Klassen, alle sieben Rollen belegt; Chublets 99 261 Tripel, 832 Items, 168 Properties (32 in Gebrauch), 13 Klassen, fünf Rollen belegt (zwei `none` mit Grund). Befunde 9 bis 15 in A1. Negativtest in einer Kopie mit sechs absichtlichen Fehlern (falsches Label, falscher Datentyp, unbekannte Property, `none` ohne Grund, fehlende Zeile, unbekannte Instanz): alle sechs werden gemeldet; dabei zeigte sich ein Absturz bei fehlender Rolle, der behoben ist.

## S4 — Bundle

**Ziel:** Ein gemeinsamer Graph aus allen Instanzen, begrenzt auf das, was eine Facettensuche wie in der fdo-squirrel-registry und die Abfragen über Instanzen brauchen.

**Uploads:** keine; `data/raw/` kommt aus dem Repo.

Umgesetzt: `py/step_bundle.py` liest je Instanz den Export, behält nur Tripel, deren Subjekt eine Entität (`<base>/entity/Q…|P…`) ist und deren Prädikat auf der Whitelist steht (oder mit `<base>/prop/direct/` beginnt), dazu den Katalogknoten der Instanz. Je Rolle der Rollen-Tabelle entsteht eine normalisierte `bbr:`-Aussage neben der Quellaussage. Je Instanz ein `dcat:CatalogRecord`, je Entität `bbr:fromInstance`. Ausgabe: `dist/beaverbridge-registry.nt` (sortiert, kanonisch), `dist/beaverbridge-registry.ttl` (aus dem NT, mit Präfixen `fuzzy-sl:`, `chublets:`), `dist/bundle_report.md`. `metadata/bbr.ttl` beschreibt die `bbr:`-Begriffe.

**Abnahme:** `python main.py` meldet 0 Warnungen; zwei Läufe hintereinander lassen `dist/` byte-identisch und `git status` sauber; Rollenaussagen im Bericht passen zur Survey-Tabelle.

### Erledigt 2026-11-01

Gemessen: 19 668 Tripel (fuzzy-sl 1 455 von 12 462 behalten, 173 Entitäten, 264 Rollenaussagen; chublets 13 883 von 99 261, 1 007 Entitäten, 2 858 Rollenaussagen). Lauf rund 5 s; NT/TTL/Bericht zweimal byte-identisch. NT 3,4 MB, TTL 0,9 MB.

Abnahme auf dem PC: Commit e9e63f8, Bundle 8,3 bis 8,5 s, `--strict` grün, `git status` sauber, gepusht.

## S7 — Index und Facettenseite

**Ziel:** Eine statische Suchseite über alle Instanzen nach dem Muster der fdo-squirrel-registry: Facetten mit Zählwerten, Trefferkarten, Löschen der Filter; dazu die Seiten, unter denen die Registry-IRIs auflösen.

**Uploads:** keine; gebaut wird aus `dist/beaverbridge-registry.nt`.

Umgesetzt:

- `py/step_index.py` liest nur das Bundle und schreibt `dist/registry-index.json`: Instanzen (Titel, Quelle, SHA-256, Generator, Datenstand, Lizenz, Zählwerte), Klassenlabels und ein Eintrag je Item (969: fuzzy-sl 137, chublets 832) mit Label (Englisch zuerst), Beschreibung, Klassen, *part of*, Koordinaten, Wikidata, Match-URLs, Seitenadresse der Instanz (`<pages_url>/<Qn>.html`). Properties werden gezählt, nicht gelistet.
- `py/step_site.py` baut `docs/` aus `templates/` (Jinja2): `index.html` (Daten eingebettet, öffnet auch von der Platte), `catalog.html` (antwortet für `…/catalog`), `record/<id>.html` (antwortet für `…/record/<id>`), `vocab/` (Übersicht, eine Seite je `bbr:`-Begriff, `bbr.ttl`), `downloads/` (Bundle als TTL und NT), `registry-index.json`, `assets/`, `.nojekyll`.
- Facetten: Instanz, Klasse (mit Instanz-Präfix, weil Klassennamen kollidieren können), „Has“ (Koordinaten, Wikidata-Link, externer Match), Lizenz. Innerhalb einer Facette ODER, zwischen Facetten UND; Zählwerte beachten die anderen Facetten. Freitextsuche über Label, Beschreibung, Kennung, Klassen; Zustand in der URL (`#class=…&q=…`); Hell, Dunkel und Auto nach `design/PALETTE.md`; Systemschrift, kein Aufruf an Dritte; kein `innerHTML` mit Daten.
- `assets/logo-256.jpg` ist das Logo auf 256 px verkleinert (15 KB statt 550 KB); das Original bleibt für Dokumente.

**Abnahme:** `python main.py --strict` läuft durch; zwei Läufe lassen `dist/` und `docs/` byte-identisch und `git status` sauber; `docs/index.html` zeigt 969 Einträge, die Filter ändern die Zahl, die Seite zeigt keine Konsolenfehler und läuft bei 390 px Breite ohne waagerechtes Scrollen; nach dem Push zeigt GitHub Pages dieselbe Seite.

### Erledigt 2026-11-01

Getestet in Chromium (Playwright) von der Platte: 969 Einträge, Suche „zoo“ 8 Treffer, fuzzy-sl 137, fuzzy-sl mit Koordinaten 59, Hash-Zustand wird gelesen, kein Konsolenfehler, Breite 390 px ohne Überlauf, Hell und Dunkel geprüft. Dabei gefunden und behoben: In Jinja ist `i.items` die Methode `dict.items`, nicht der Schlüssel; die Seiten waren dadurch nicht byte-identisch (Speicheradresse im Text). Seither `i["items"]`.

Aktivierung: GitHub → Settings → Pages → Branch `main`, Ordner `/docs`.

*(S5, S6, S8 und S9 werden angelegt, sobald sie dran sind.)*

---

## Teil D — Offene Punkte

- **Auflösung von `bbr:`:** Namespace ist entschieden (Pages-Pfad); die Seite `vocab/` selbst entsteht mit der Site in S7. Später w3id.
- **Datenmodell-Klassen gegen Fachklassen:** In fuzzy-sl stehen *Spatial Type*, *Source*, *Project* neben *Archaeological Site*; im Bundle sollten sie unterscheidbar sein (Anker oder Kennzeichnung). Vorschlag in S5.
- **Anker für Chublets:** Die Instanz bringt keinen CRM-Anker mit; er kommt aus der Klassen-Tabelle der Bridge (S5), nicht aus der Quelle.
- **Doppelte Ablage:** `dist/` und `docs/downloads/` halten dieselben 4 MB; mit jeder Änderung des Bundles wächst die Git-Historie um beide. Wenn es stört: `dist/*.nt/.ttl` nicht mehr versionieren und nur `docs/downloads/` behalten.
- **Facette nach CRM-Anker:** kommt mit S5, sobald `crm_bridge.ttl` Anker auch für Chublets liefert; der Index hat dafür Platz.
- **Link zur Query-Seite** in der Kopfzeile (`templates/base.html.j2`) mit S8.
- **w3id-Prefix** für `…/record/…` und Content Negotiation.
- **Dritte Instanz:** `osm-static-benchmarks` hat ein sehr anderes Modell und wäre der Härtetest, aber erst nach S6.
- **Zenodo-DOI** für das Bundle als FDO (nach S8).
