"""Shared constants and deterministic writers for beaverbridge-registry."""
from __future__ import annotations

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
