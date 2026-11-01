# Patch: S1b — repository moved to `beaverbridge-framework`

The repository now lives at https://github.com/beaverbridge-framework/beaverbridge-registry. This patch only updates the references: `PRIMER.md` (repo name, decision on location and organisation, Pages address in A6) and `CITATION.cff` (`repository-code`).

All commands are for Windows `cmd`, one line each.

## Apply

```cmd
cd C:\git\beaverbridge-registry && git remote set-url origin https://github.com/beaverbridge-framework/beaverbridge-registry.git && tar -xf C:\git\beaverbridge-registry-s1b.zip && git add -A && git commit -m "S1b: repository moved to beaverbridge-framework" && git push
```

If your local copy was cloned from the new address already, the `git remote set-url` part does nothing harmful.

## How to check

```cmd
cd C:\git\beaverbridge-registry && findstr /s /i "n4o-rse/beaverbridge-registry florianthiery" PRIMER.md CITATION.cff
```

Only the history line in A4 ("zuerst unter `n4o-rse` geplant, dann `florianthiery`") may match; nothing else.

Then `python main.py` and `git status` as before: working tree stays clean.
