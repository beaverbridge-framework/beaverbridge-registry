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
LABELS_EN_CSV = CROSSWALKS / "labels-en.csv"
# What an instance is a copy of: a Wikidata project, a Wikibase, an OpenStreetMap selection, anything else. Stated in
# registry/sources.json (field "type"), written to the catalogue record as bbr:sourceType, shown as a facet.
SOURCE_TYPES = ["wikidata", "wikibase", "osm", "other"]
ROLES = ["instance_of", "subclass_of", "part_of", "coordinates", "equivalent_class",
         "wikidata_equivalent", "external_match"]


def ensure_dirs() -> None:
    for p in (REGISTRY, RAW, CROSSWALKS, METADATA, DIST, DOCS):
        p.mkdir(parents=True, exist_ok=True)


def load_sources() -> list[dict]:
    """The instances of registry/sources.json; every one must state its source type (SOURCE_TYPES) and have a unique id."""
    instances = json.loads(SOURCES.read_text(encoding="utf-8"))["instances"]
    seen = set()
    for inst in instances:
        if inst.get("type") not in SOURCE_TYPES:
            raise ValueError(f"{SOURCES.name}: instance {inst.get('id')!r} needs \"type\": one of {', '.join(SOURCE_TYPES)} "
                             f"(found {inst.get('type')!r})")
        if inst["id"] in seen:
            raise ValueError(f"{SOURCES.name}: instance id {inst['id']!r} is used twice")
        seen.add(inst["id"])
    return instances


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


def canonical_bnodes(graph):
    """The graph with every blank node renamed after what it stands for, so two runs write the same bytes.

    rdflib gives a blank node a new random name at every parse. A "some value" statement of a Wikibase (the source
    knows there is a value, not which) is such a node; without a stable name the bundle would differ between two runs.
    The name is a hash of the statements that mention the node. Two blank nodes with the same statements get the
    same name and become one: for "some value" that means two unknown values of the same property of the same
    subject are written once, which the bundle does not use to tell them apart.
    """
    from rdflib import BNode, Graph

    nodes = {n for triple in graph for n in triple if isinstance(n, BNode)}
    if not nodes:
        return graph
    name = {}
    for b in nodes:
        parts = [("in", str(s), str(p)) for s, p, _ in graph.triples((None, None, b))]
        parts += [("out", str(p), str(o)) for _, p, o in graph.triples((b, None, None)) if not isinstance(o, BNode)]
        name[b] = BNode("b" + sha256_bytes(repr(sorted(parts)).encode("utf-8"))[:24])
    out = Graph()
    for s, p, o in graph:
        out.add((name.get(s, s), p, name.get(o, o)))
    return out


def write_ntriples(graph, path: Path) -> None:
    """Sorted, de-duplicated N-Triples: the canonical form, so two runs can be compared byte for byte."""
    lines = sorted({ln for ln in canonical_bnodes(graph).serialize(format="nt").splitlines() if ln.strip()})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def read_labels_en() -> list[dict]:
    """crosswalks/labels-en.csv: English labels that the registry adds where an instance has none (instance, id, label_en)."""
    if not LABELS_EN_CSV.exists():
        return []
    with LABELS_EN_CSV.open(encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh) if r.get("instance")]
