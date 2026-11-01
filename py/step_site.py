"""Step: site (offline). Writes docs/, the GitHub Pages root of the registry.

    docs/index.html                facet search (the index is embedded, so the file also opens from disk)
    docs/catalog.html              the registry catalogue; answers for <REGISTRY_BASE>/catalog
    docs/record/<id>.html          one catalogue record per instance; answers for <REGISTRY_BASE>/record/<id>
    docs/vocab/                    the bbr: vocabulary: bbr.ttl, an overview and one page per term
    docs/downloads/                the bundle as Turtle and N-Triples
    docs/registry-index.json       the facet index
    docs/assets/                   style, script, logo

Pages come from templates/ with Jinja2; files are copied byte for byte. Nothing reads the clock or the network.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_utils import BBR_NS, DIST, DOCS, METADATA, RELEASE, REGISTRY_BASE, ROOT, ensure_dirs  # noqa: E402

TEMPLATES = ROOT / "templates"
LOGO = ROOT / "assets" / "logo-256.jpg"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def vocab_terms() -> tuple[str, list[dict]]:
    from rdflib import RDF, RDFS, Graph, URIRef
    from rdflib.namespace import OWL

    g = Graph()
    g.parse(METADATA / "bbr.ttl", format="turtle")
    intro = str(g.value(URIRef(BBR_NS), RDFS.comment) or "")
    terms = []
    for s in sorted(g.subjects(RDF.type, None), key=str):
        if not str(s).startswith(BBR_NS) or str(s) == BBR_NS:
            continue
        name = str(s)[len(BBR_NS):]
        kinds = {OWL.ObjectProperty: "Object property", OWL.DatatypeProperty: "Datatype property"}
        kind = next((kinds[o] for o in g.objects(s, RDF.type) if o in kinds), "Term")
        short = lambda u: ("bbr:" + str(u)[len(BBR_NS):]) if str(u).startswith(BBR_NS) else g.namespace_manager.normalizeUri(u)  # noqa: E731
        dom, rng = g.value(s, RDFS.domain), g.value(s, RDFS.range)
        terms.append({"name": name, "iri": str(s), "label": str(g.value(s, RDFS.label) or name),
                      "comment": str(g.value(s, RDFS.comment) or ""), "kind": kind,
                      "domain": short(dom) if dom else "", "range": short(rng) if rng else ""})
    terms.sort(key=lambda t: t["name"])
    return intro, terms


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    ensure_dirs()

    index_path = DIST / "registry-index.json"
    if not index_path.exists():
        print("site: no index, nothing written")
        return 1 if args.strict else 0

    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True, trim_blocks=True, lstrip_blocks=True,
                      undefined=StrictUndefined, keep_trailing_newline=True)
    data = json.loads(index_path.read_text(encoding="utf-8"))
    instances = data["instances"]
    common = {"release": RELEASE, "root": ""}

    # embedded data: compact, and "</" cannot close the script element
    data_json = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    write(DOCS / "index.html", env.get_template("index.html.j2").render(
        **common, title="BeaverBridge registry: search", description="Facet search over static Wikibase instances",
        n_entries=len(data["entries"]), instances=instances, triples=data["bundle_triples"], data_json=data_json))
    write(DOCS / "catalog.html", env.get_template("catalog.html.j2").render(
        **common, title="BeaverBridge registry: catalogue", description="Catalogue of the registered instances",
        instances=instances, catalog_iri=REGISTRY_BASE + "/catalog"))
    for i in instances:
        write(DOCS / "record" / f"{i['id']}.html", env.get_template("record.html.j2").render(
            release=RELEASE, root="../", title=f"{i['title']}: catalogue record", description="Catalogue record", i=i))

    intro, terms = vocab_terms()
    vt = env.get_template("vocab.html.j2")
    write(DOCS / "vocab" / "index.html", vt.render(release=RELEASE, root="../", title="BeaverBridge registry vocabulary",
                                                   description="The bbr: terms", ns=BBR_NS, intro=intro, terms=terms, term=None))
    for t in terms:
        write(DOCS / "vocab" / f"{t['name']}.html", vt.render(release=RELEASE, root="../", title=f"bbr:{t['name']}",
                                                              description=t["comment"], term=t))
    copy(METADATA / "bbr.ttl", DOCS / "vocab" / "bbr.ttl")

    copy(DIST / "beaverbridge-registry.ttl", DOCS / "downloads" / "beaverbridge-registry.ttl")
    copy(DIST / "beaverbridge-registry.nt", DOCS / "downloads" / "beaverbridge-registry.nt")
    copy(index_path, DOCS / "registry-index.json")
    copy(TEMPLATES / "style.css", DOCS / "assets" / "style.css")
    copy(TEMPLATES / "app.js", DOCS / "assets" / "app.js")
    copy(LOGO, DOCS / "assets" / "logo.jpg")
    write(DOCS / ".nojekyll", "")

    print(f"site: docs/ with search page ({len(data['entries'])} entries), catalogue, {len(instances)} record page(s), "
          f"{len(terms)} vocabulary term(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
