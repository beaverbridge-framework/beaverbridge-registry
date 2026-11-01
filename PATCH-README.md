# Patch: S2 — Harvest

Fetches the RDF exports of the registered instances from their GitHub Pages and stores them unchanged in `data/raw/<id>/`, with a `harvest.json` manifest (bytes, SHA-256, ETag, generator version, data date, triple count).

## Contents

| File | Change |
|---|---|
| `py/step_harvest.py` | new: the harvest step |
| `main.py` | forwards unknown options to the step (`python main.py harvest --force`); only a full run writes `dist/pipeline_report.txt` |
| `registry/sources.json` | each file now has a `role` (`export` or `ontology`) |
| `.gitattributes` | new: LF everywhere, `data/raw/**` kept byte-for-byte |
| `PRIMER.md` | S2 status, findings in A1, new rows in A4 |

Copy the files into `C:\git\beaverbridge-registry`, keeping the folder structure. All commands are for Windows `cmd`, one line each.

## 1. Can the Pages be reached? (before the first run)

```cmd
curl.exe -sI https://n4o-rse.github.io/fuzzy-sl-static/downloads/wikibase-ontology.ttl && curl.exe -sI https://n4o-rse.github.io/chublets-wikibase-demo/downloads/wikibase-ontology.ttl
```

Both must start with `HTTP/2 200`. If one says 404 or 403, send me the first lines of the answer.

## 2. Harvest

```cmd
cd C:\git\beaverbridge-registry && python -m pip install -r requirements.txt && python main.py harvest
```

Expected: four lines `fetched …`, with 12 462 triples for fuzzy-sl and 99 261 for chublets (these are the numbers measured on the local clones; Pages may carry newer data).

## 3. Check (acceptance of S2)

Second run fetches nothing:

```cmd
cd C:\git\beaverbridge-registry && python main.py harvest
```

Expected: four lines `unchanged (304)`.

Commit, run again, the working tree stays clean:

```cmd
cd C:\git\beaverbridge-registry && git add -A && git commit -m "S2 harvest" && python main.py harvest && python main.py && git status
```

Expected: `nothing to commit, working tree clean`.

## 4. Push

```cmd
cd C:\git\beaverbridge-registry && git push
```

## Other options

```cmd
cd C:\git\beaverbridge-registry && python main.py harvest --force --instance chublets
```

`--local` reads from local clones instead (set `{"clone_dir": "C:\\git"}` in `config.local.json`, copy of `config.local.example.json`); `--offline` only reports what is on disk.

## Next step

New chat: upload `PRIMER.md` (and the bundle from A5) and say "S3 bitte".
