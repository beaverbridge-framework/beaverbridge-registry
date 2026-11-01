"""Shared constants and deterministic writers for beaverbridge-registry."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

# No generator reads the clock: dates come from here or from the source data.
RELEASE = "2026-11-01"

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry"
RAW = ROOT / "data" / "raw"
CROSSWALKS = ROOT / "crosswalks"
METADATA = ROOT / "metadata"
DIST = ROOT / "dist"
DOCS = ROOT / "docs"
SOURCES = REGISTRY / "sources.json"

# Where the registry publishes (GitHub Pages of the repository); the vocabulary lives under vocab/.
REGISTRY_BASE = "https://beaverbridge-framework.github.io/beaverbridge-registry"
BBR_NS = REGISTRY_BASE + "/vocab/"

CORE_CSV = CROSSWALKS / "core-properties.csv"
ROLES = ["instance_of", "subclass_of", "part_of", "coordinates", "equivalent_class",
         "wikidata_equivalent", "external_match"]


def ensure_dirs() -> None:
    for p in (REGISTRY, RAW, CROSSWALKS, METADATA, DIST, DOCS):
        p.mkdir(parents=True, exist_ok=True)


def load_sources() -> list[dict]:
    return json.loads(SOURCES.read_text(encoding="utf-8"))["instances"]


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_fingerprint(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_core() -> list[dict]:
    """Rows of crosswalks/core-properties.csv (role, instance, property, label_en, datatype, note)."""
    with CORE_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def jinja_env(autoescape: bool = True):
    """Jinja2 environment over templates/; undefined names are errors, so a typo cannot ship as an empty string."""
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    return Environment(loader=FileSystemLoader(str(ROOT / "templates")), autoescape=autoescape, trim_blocks=True,
                       lstrip_blocks=True, undefined=StrictUndefined, keep_trailing_newline=True)


def write_ntriples(graph, path: Path) -> None:
    """Sorted, de-duplicated N-Triples: the canonical form, so two runs can be compared byte for byte."""
    lines = sorted({ln for ln in graph.serialize(format="nt").splitlines() if ln.strip()})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
