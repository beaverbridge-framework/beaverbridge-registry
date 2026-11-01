# Patch: S3 — Survey and role crosswalk

Measures every harvested instance (offline, from `data/raw/`) and checks `crosswalks/core-properties.csv` against it. The crosswalk says which property plays which role in which instance, because the numbers differ: *instance of* is P1 in fuzzy-sl and P2 in chublets.

## Contents

| File | Change |
|---|---|
| `py/step_survey.py` | new: the `survey` step |
| `crosswalks/core-properties.csv` | new: seven roles, one row per instance and role |
| `crosswalks/README.md` | new: what the roles mean |
| `main.py` | `survey` added to the default run, between `harvest` and `bundle` |
| `PRIMER.md` | S2 and S3 done, findings 9 to 15 in A1, new decisions in A4 |

Copy the files into `C:\git\beaverbridge-registry`, keeping the folder structure. All commands are for Windows `cmd`, one line each.

## 1. Run

```cmd
cd C:\git\beaverbridge-registry && python main.py
```

Expected for the survey:

```
fuzzy-sl: 12462 triples, 137 items, 36 properties, 19 classes, roles 7/7
chublets: 99261 triples, 832 items, 168 properties, 13 classes, roles 5/7
survey: 2 instance(s), 0 warning(s)
```

## 2. Check (acceptance of S3)

Commit, run again, the working tree stays clean (the first run creates `dist/survey.json` and `dist/survey_report.md`, which are versioned):

```cmd
cd C:\git\beaverbridge-registry && git add -A && git commit -m "S3 survey and role crosswalk" && python main.py --strict && git status
```

Expected: `nothing to commit, working tree clean`.

Read the report:

```cmd
cd C:\git\beaverbridge-registry && start dist\survey_report.md
```

## 3. Push

```cmd
cd C:\git\beaverbridge-registry && git push
```

## Next step

New chat: upload `PRIMER.md` and say "S4 bitte" (bundle: DCAT catalogue, instance prefix, `bbr:` roles). S6, S7 and S8 can follow in any order after S4.
