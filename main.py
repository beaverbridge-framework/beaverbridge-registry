#!/usr/bin/env python3
"""Orchestrator: the only entry point of beaverbridge-registry.

    python main.py                  run all default steps, in order
    python main.py --list           print the steps and exit
    python main.py --only bundle    run one step
    python main.py --from bundle    run this step and everything after
    python main.py --skip site      run everything but this
    python main.py --dry-run        print the plan, run nothing
    python main.py --strict         warnings become errors (what CI runs)
    python main.py harvest          network steps have their own verb
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# (name, module file, in default run?, description)
STEPS = [
    ("harvest", "py/step_harvest.py", False, "fetch RDF exports of the registered instances (network)"),
    ("survey", "py/step_survey.py", True, "measure the harvested instances, check the core-property crosswalk"),
    ("bundle", "py/step_bundle.py", True, "merge harvested graphs into the DCAT catalogue"),
    ("validate", "py/step_validate.py", True, "SHACL gate"),
    ("index", "py/step_index.py", True, "facet index from the bundle"),
    ("site", "py/step_site.py", True, "facet page and instance pages"),
    ("sparql", "py/step_sparql.py", True, "browser SPARQL page and .rq files"),
]


def select(args) -> list:
    names = [s[0] for s in STEPS]
    if args.verb:
        if args.verb not in names:
            sys.exit(f"unknown step: {args.verb}")
        return [s for s in STEPS if s[0] == args.verb]
    if args.only:
        if args.only not in names:
            sys.exit(f"unknown step: {args.only}")
        return [s for s in STEPS if s[0] == args.only]
    chosen = [s for s in STEPS if s[2]]
    if args.from_:
        if args.from_ not in names:
            sys.exit(f"unknown step: {args.from_}")
        start = names.index(args.from_)
        chosen = [s for s in STEPS[start:] if s[2]]
    if args.skip:
        chosen = [s for s in chosen if s[0] != args.skip]
    return chosen


def run_step(step, strict: bool, log: list, extra: list) -> tuple[int, float]:
    name, path, _, _ = step
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cmd = [sys.executable, str(ROOT / path)] + (["--strict"] if strict else []) + extra
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    for line in proc.stdout:
        line = line.rstrip("\n")
        print(f"  {line}")
        log.append(f"  {line}")
    return proc.wait(), time.perf_counter() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("verb", nargs="?", help="run one step that is not in the default run (e.g. harvest)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--from", dest="from_")
    ap.add_argument("--skip")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true")
    args, extra = ap.parse_known_args()  # unknown options go to the step, e.g.  python main.py harvest --force

    if args.list:
        for name, path, default, desc in STEPS:
            print(f"{name:10} {'default' if default else 'explicit':9} {desc}")
        return 0

    chosen = select(args)
    if args.dry_run:
        print("plan: " + " -> ".join(s[0] for s in chosen))
        return 0

    log: list[str] = []
    timings = []
    for step in chosen:
        header = f"[{step[0]}]"
        print(header)
        log.append(header)
        code, secs = run_step(step, args.strict, log, extra if (args.verb or args.only) else [])
        timings.append((step[0], secs))
        if code != 0:
            print(f"step {step[0]} failed (exit {code})")
            return code

    total = sum(t for _, t in timings) or 1e-9
    print("\nstep        seconds   share")
    for name, secs in timings:
        print(f"{name:10} {secs:8.2f} {100 * secs / total:6.1f} %")

    if not (args.verb or args.only):
        # Only a full run writes the report, so a single step cannot overwrite it with a fragment.
        report = ROOT / "dist" / "pipeline_report.txt"
        report.parent.mkdir(exist_ok=True)
        # No clock in the output: the report holds step names and lines only; timings stay on the terminal.
        report.write_text("\n".join(log) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
