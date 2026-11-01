"""Step: sparql (offline). Builds the query page from queries.yaml, in three forms.

    docs/sparql.html              the page: rdflib under Pyodide, no endpoint, no server
    docs/downloads/queries/*.rq   the same queries as plain files
    qmd/<name>.qmd                the quarto-live notebook (written; rendered only if someone runs Quarto)

All three come from queries.yaml, so they cannot drift apart. Before anything is written every query is executed on the
real bundle here: a query that returns no rows fails the build, because SPARQL does not fail on a mistyped IRI, it
returns nothing. Pyodide and rdflib are pinned, so an archived copy keeps working.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_utils import DIST, DOCS, RELEASE, ROOT, ensure_dirs, jinja_env  # noqa: E402

QUERIES_YAML = ROOT / "queries.yaml"
QMD_DIR = ROOT / "qmd"
PYODIDE_VERSION = "0.26.4"
RDFLIB_VERSION = "7.1.1"
MAX_ROWS = 500  # an unbounded table can hang a phone


def check_queries(cfg: dict, graph_file: Path) -> bool:
    from rdflib import Graph

    g = Graph()
    g.parse(graph_file, format="turtle")
    print(f"  {graph_file.name}: {len(g)} triples")
    ok = True
    for q in cfg["queries"]:
        try:
            rows = list(g.query(cfg["prefixes"] + "\n" + q["sparql"]))
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL {q['id']}: {type(exc).__name__}: {exc}")
            ok = False
            continue
        q["rows_at_build"] = len(rows)
        print(f"  {'ok  ' if rows else 'FAIL'} {q['id']:14s} {len(rows):4d} rows" + ("" if rows else "  (parses, matches nothing)"))
        ok = ok and bool(rows)
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true")
    ap.parse_args()
    ensure_dirs()

    import yaml
    if not QUERIES_YAML.exists():
        print("sparql: queries.yaml is missing")
        return 1
    cfg = yaml.safe_load(QUERIES_YAML.read_text(encoding="utf-8"))
    graph_file = ROOT / cfg["graph"]["file"]
    if not graph_file.exists():
        print("sparql: no bundle, nothing written")
        return 0
    if not check_queries(cfg, graph_file):
        print("sparql: a query does not work; nothing written")
        return 1

    # .rq files: the same text, with a comment header
    out_dir = DOCS / "downloads" / "queries"
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in sorted(out_dir.glob("*.rq")):
        stale.unlink()
    for q in cfg["queries"]:
        intro = "\n".join(f"# {ln}" for ln in textwrap.wrap(" ".join(str(q["intro"]).split()), 76))
        (out_dir / f"{q['id']}.rq").write_text(
            f"# {q['title']}\n{intro}\n\n{cfg['prefixes'].rstrip()}\n\n{q['sparql'].rstrip()}\n", encoding="utf-8", newline="\n")

    graph = dict(cfg["graph"], megabytes=f"{graph_file.stat().st_size / 1e6:.1f}")
    queries = []
    for q in cfg["queries"]:
        item = dict(q)
        item["sparql"] = q["sparql"].rstrip("\n")
        item["rows"] = max(6, item["sparql"].count("\n") + 2)  # sized to the query, no hidden scrollbar
        queries.append(item)

    payload = {"prefixes": cfg["prefixes"], "graph_url": graph["url"], "max_rows": MAX_ROWS,
               "queries": {q["id"]: q["sparql"] for q in queries}}
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False).replace("</", "<\\/")
    html = jinja_env().get_template("sparql.html.j2").render(
        release=RELEASE, root="", title="BeaverBridge registry: query", description=cfg["page"]["intro"][:160],
        page=cfg["page"], graph=graph, queries=queries, payload_json=payload_json,
        pyodide_version=PYODIDE_VERSION, rdflib_version=RDFLIB_VERSION)
    (DOCS / "sparql.html").write_text(html, encoding="utf-8", newline="\n")

    qmd_cfg = dict(cfg["qmd"], megabytes=graph["megabytes"])
    QMD_DIR.mkdir(exist_ok=True)
    qmd = jinja_env(autoescape=False).get_template("sparql.qmd.j2").render(
        qmd=qmd_cfg, queries=queries, rdflib_version=RDFLIB_VERSION, prefixes=cfg["prefixes"].rstrip("\n"))
    (QMD_DIR / qmd_cfg["file"]).write_text(qmd, encoding="utf-8", newline="\n")

    print(f"sparql: {len(queries)} queries, docs/sparql.html, {len(queries)} .rq files, qmd/{qmd_cfg['file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
