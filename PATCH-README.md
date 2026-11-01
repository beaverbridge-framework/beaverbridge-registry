# Patch: S1 — Skeleton (beaverbridge-registry)

New repository `beaverbridge-registry`: layout, orchestrator, utilities, licence, citation, `registry/sources.json` (fuzzy-sl and chublets), logo and the colour palette (`design/PALETTE.md`, `design/palette.html`). No harvest logic yet; every step is a stub.

All commands are for Windows `cmd`, one line each.

## 1. Unpack and run

```cmd
cd C:\git && mkdir beaverbridge-registry && cd beaverbridge-registry && git init -b main && tar -xf C:\git\beaverbridge-registry-s1.zip && python -m pip install -r requirements.txt && python main.py --list && python main.py
```

`tar` ships with Windows 10/11. If it is missing, unpack the ZIP by hand into `C:\git\beaverbridge-registry`.

## 2. Check (acceptance of S1)

- `python main.py --list` shows six steps: `harvest` (explicit), `bundle`, `validate`, `index`, `site`, `sparql`.
- `python main.py` exits cleanly and prints "nothing to do" for each default step.
- Determinism: commit, run again, `git status` must be empty.

```cmd
cd C:\git\beaverbridge-registry && git add -A && git commit -m "S1 skeleton" && python main.py && git status
```

Expected: `nothing to commit, working tree clean`.

## 3. Look at the palette

```cmd
cd C:\git\beaverbridge-registry && start design\palette.html
```

## 4. Push (when the empty repo `n4o-rse/beaverbridge-registry` exists on GitHub)

```cmd
cd C:\git\beaverbridge-registry && git remote add origin https://github.com/n4o-rse/beaverbridge-registry.git && git push -u origin main
```

## 5. Next step

New chat: upload `PRIMER.md` (and the bundle from PRIMER A5) and say "S2 bitte" (harvest).
