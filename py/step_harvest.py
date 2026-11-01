"""Step: harvest (the only step that reaches the network).

For every instance in registry/sources.json the RDF exports are fetched from the instance's GitHub Pages
and written, unchanged, to data/raw/<id>/ together with a harvest.json manifest.

    python main.py harvest                          fetch what is missing or changed
    python py/step_harvest.py --force               fetch again even if up to date
    python py/step_harvest.py --instance chublets   one instance only
    python py/step_harvest.py --local               read from local clones (config.local.json: clone_dir)
    python py/step_harvest.py --offline             fetch nothing, only report what is on disk
    python py/step_harvest.py --sources FILE        use another sources.json (tests)

The manifest holds no clock: it names the bytes, the SHA-256, the ETag, the generator version and the data
date as the file itself states them, so an unchanged source gives a byte-identical manifest.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_utils import RAW, ROOT, ensure_dirs, sha256_bytes, write_json  # noqa: E402

USER_AGENT = "beaverbridge-registry-harvest (+https://github.com/beaverbridge-framework/beaverbridge-registry)"
TIMEOUT = 60
MAX_CONSECUTIVE_FAILURES = 3

RE_GENERATOR = re.compile(r"^#\s*Generated with (wikibase-static [^;\n]+?)(?:;\s*data as of ([^\n]+))?\s*$", re.M)
RE_LICENCE = re.compile(r"^#\s*Licen[cs]e:\s*(.+?)\s*$", re.M)


def load_config() -> dict:
    p = ROOT / "config.local.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def describe(data: bytes, rdf_base: str) -> dict:
    """Facts the file states about itself (header comments) plus a check that it mentions its own base."""
    head = data[:4000].decode("utf-8", errors="replace")
    info: dict = {}
    m = RE_GENERATOR.search(head)
    if m:
        info["generator"] = m.group(1).strip()
        if m.group(2):
            info["data_as_of"] = m.group(2).strip()
    m = RE_LICENCE.search(head)
    if m:
        info["licence"] = m.group(1).strip()
    info["rdf_base_seen"] = rdf_base.encode("utf-8") in data
    return info


def count_triples(data: bytes, fmt: str = "turtle") -> tuple[int | None, str | None]:
    try:
        from rdflib import Graph
    except ImportError:
        return None, "rdflib not installed; triples not counted"
    try:
        g = Graph()
        g.parse(data=data, format=fmt)
        return len(g), None
    except Exception as exc:  # a published file may be invalid Turtle; that is a finding, not a crash
        return None, f"{type(exc).__name__}: {str(exc)[:200]}"


def fetch_http(url: str, etag: str | None) -> tuple[str, bytes | None, str | None]:
    """Return (status, body, etag). status: 'new' | 'not-modified'."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if etag:
        req.add_header("If-None-Match", etag)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return "new", resp.read(), resp.headers.get("ETag")
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return "not-modified", None, etag
        raise


def harvest_instance(inst: dict, args, cfg: dict, log) -> tuple[int, int]:
    """Return (files ok, files failed)."""
    iid = inst["id"]
    out_dir = RAW / iid
    manifest_path = out_dir / "harvest.json"
    prev = {}
    if manifest_path.exists():
        prev = {f["path"]: f for f in json.loads(manifest_path.read_text(encoding="utf-8")).get("files", [])}

    files, ok, failed = [], 0, 0
    for spec in inst["files"]:
        rel, role = (spec, "export") if isinstance(spec, str) else (spec["path"], spec.get("role", "export"))
        target = out_dir / Path(rel).name
        old = prev.get(rel, {})
        have = target.exists() and bool(old)
        entry = dict(old) if have else {"path": rel}

        if args.offline:
            log(f"  {iid}: {rel}: {'on disk' if have else 'MISSING'} (offline)")
            if have:
                files.append(entry)
                ok += 1
            else:
                failed += 1
            continue

        try:
            if args.local:
                clone = Path(cfg.get("clone_dir", "")) / inst["repo"].rstrip("/").split("/")[-1]
                src = clone / "docs" / rel
                if not src.exists():
                    raise FileNotFoundError(str(src))
                status, body, etag, route = "new", src.read_bytes(), None, "local-clone"
            else:
                url = inst["pages_url"].rstrip("/") + "/" + rel
                send_etag = None if (args.force or not have) else old.get("etag")
                status, body, etag = fetch_http(url, send_etag)
                route = "http"
        except Exception as exc:
            failed += 1
            log(f"  {iid}: {rel}: NOT REACHED ({type(exc).__name__}: {exc})")
            if have:
                files.append(entry)  # keep what the manifest already knows about the copy on disk
            continue

        if status == "not-modified":
            log(f"  {iid}: {rel}: unchanged (304)")
            files.append(entry)
            ok += 1
            continue

        digest = sha256_bytes(body)
        if have and old.get("sha256") == digest and not args.force:
            log(f"  {iid}: {rel}: unchanged (same SHA-256, {len(body)} bytes)")
            if etag:
                entry["etag"] = etag
            files.append(entry)
            ok += 1
            continue

        entry = {"path": rel, "role": role, "bytes": len(body), "sha256": digest, "route": route}
        if etag:
            entry["etag"] = etag
        if rel.endswith(".ttl"):
            entry.update(describe(body, inst["rdf_base"]))
            if role != "export":
                entry.pop("rdf_base_seen")  # the shared Wikibase ontology names no instance; nothing to check
            n, err = count_triples(body)
            if n is not None:
                entry["triples"] = n
            if err:
                entry["parse_error"] = err
                log(f"  {iid}: {rel}: WARNING {err}")
            if role == "export" and not entry["rdf_base_seen"]:
                log(f"  {iid}: {rel}: WARNING rdf_base {inst['rdf_base']} does not occur in the file")

        out_dir.mkdir(parents=True, exist_ok=True)
        if target.exists():
            os.chmod(target, 0o644)
        target.write_bytes(body)
        os.chmod(target, 0o444)  # raw data is read-only
        files.append(entry)
        ok += 1
        log(f"  {iid}: {rel}: fetched {len(body)} bytes via {route}"
            + (f", {entry['triples']} triples" if "triples" in entry else "")
            + (f", {entry['generator']}" if "generator" in entry else ""))

    if files:
        out_dir.mkdir(parents=True, exist_ok=True)
        if manifest_path.exists():
            os.chmod(manifest_path, 0o644)
        write_json(manifest_path, {
            "instance": iid, "label": inst.get("label", iid), "pages_url": inst["pages_url"],
            "rdf_base": inst["rdf_base"], "prefix_family": inst.get("prefix_family"), "files": files,
        })
    return ok, failed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--instance")
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--sources")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    ensure_dirs()
    src = Path(args.sources) if args.sources else ROOT / "registry" / "sources.json"
    instances = json.loads(src.read_text(encoding="utf-8"))["instances"]
    if args.instance:
        instances = [i for i in instances if i["id"] == args.instance]
        if not instances:
            print(f"unknown instance: {args.instance}")
            return 2

    cfg = load_config()
    if args.local and not cfg.get("clone_dir"):
        print("--local needs clone_dir in config.local.json")
        return 2

    total_ok = total_failed = consecutive = 0
    for inst in instances:
        print(f"[{inst['id']}] {inst['pages_url']}")
        ok, failed = harvest_instance(inst, args, cfg, print)
        total_ok += ok
        total_failed += failed
        consecutive = consecutive + 1 if (failed and not ok) else 0
        if consecutive >= MAX_CONSECUTIVE_FAILURES:
            print(f"stopping after {consecutive} instances in a row that could not be reached")
            break

    print(f"harvest: {total_ok} file(s) ok, {total_failed} not reached")
    # An unreachable source is a statement about the network, not about the record: it only fails a strict run.
    return 1 if (total_failed and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
