"""Step: bundle (offline). Builds the registry graph from the harvested exports.

The bundle holds what a faceted search and a cross-instance query need, and nothing else:

* per instance, from its export: the items and properties with labels, descriptions, types, direct claims,
  class links (rdfs:subClassOf, owl:equivalentClass, owl:sameAs) and the property metadata that maps a property to its
  direct predicate. Statement, reference and value nodes, the per-entity DCAT datasets and the Wikibase counters are
  left out; their facts stay in data/raw/ and in the instance itself;
* the instance's own catalogue node (title, licence, landing page, ...), so the licence of every entry is kept;
* one catalogue record per instance, with where it was fetched from, the SHA-256 of the file and the generator;
* the roles of crosswalks/core-properties.csv as normalised statements (bbr:instanceOf, bbr:subclassOf, ...), next to
  the unchanged source statement;
* bbr:fromInstance on every entity, pointing to the record of its instance.

Products: dist/beaverbridge-registry.nt (sorted N-Triples, the canonical form), dist/beaverbridge-registry.ttl and
dist/bundle_report.md. No clock is read; dates come from the data.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_utils import (BBR_NS, DIST, RAW, REGISTRY_BASE, ROLES, ensure_dirs, load_sources,  # noqa: E402
                            read_core, write_ntriples)

ROLE_TERM = {"instance_of": "instanceOf", "subclass_of": "subclassOf", "part_of": "partOf",
             "coordinates": "coordinates", "equivalent_class": "equivalentClass",
             "wikidata_equivalent": "wikidataEquivalent", "external_match": "externalMatch"}
RE_WIKIDATA_ID = re.compile(r"[QP][0-9]+")
RE_URL = re.compile(r"https?://\S+")


def export_info(inst: dict) -> tuple[Path | None, dict]:
    manifest = RAW / inst["id"] / "harvest.json"
    if not manifest.exists():
        return None, {}
    for f in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
        if f.get("role", "export") == "export":
            return RAW / inst["id"] / Path(f["path"]).name, f
    return None, {}


def build(instances: list[dict], core_rows: list[dict], warn) -> tuple[object, list[dict]]:
    from rdflib import RDF, RDFS, XSD, Graph, Literal, Namespace, URIRef
    from rdflib.namespace import DCAT, DCTERMS, FOAF, OWL, SKOS

    BBR = Namespace(BBR_NS)
    WB = Namespace("http://wikiba.se/ontology#")
    SCHEMA = Namespace("http://schema.org/")

    out = Graph()
    for pfx, ns in (("bbr", BBR), ("dcat", DCAT), ("dct", DCTERMS), ("foaf", FOAF), ("owl", OWL), ("rdf", RDF),
                    ("rdfs", RDFS), ("schema", SCHEMA), ("skos", SKOS), ("wikibase", WB), ("xsd", XSD)):
        out.bind(pfx, ns)

    entity_keep = {RDF.type, RDFS.label, SKOS.prefLabel, SKOS.altLabel, SCHEMA.name, SCHEMA.description,
                   RDFS.subClassOf, OWL.equivalentClass, OWL.sameAs, WB.propertyType, WB.directClaim}
    catalog_keep = {RDF.type, DCTERMS.title, DCTERMS.description, DCTERMS.license, DCTERMS.modified, DCTERMS.source,
                    DCAT.landingPage, DCTERMS.conformsTo}

    catalogue = URIRef(f"{REGISTRY_BASE}/catalog")
    out.add((catalogue, RDF.type, DCAT.Catalog))
    out.add((catalogue, DCTERMS.title, Literal("BeaverBridge registry of static Wikibase instances", lang="en")))
    out.add((catalogue, DCTERMS.license, URIRef("https://creativecommons.org/licenses/by/4.0/")))
    out.add((catalogue, DCAT.landingPage, URIRef(REGISTRY_BASE + "/")))

    reports = []
    for inst in instances:
        iid = inst["id"]
        path, finfo = export_info(inst)
        if path is None or not path.exists():
            warn(f"{iid}: no harvested export; run  python main.py harvest")
            continue
        base = inst["rdf_base"].rstrip("/")
        direct_prefix = f"{base}/prop/direct/"
        ent_re = re.compile(re.escape(base) + r"/entity/[QP][0-9]+$")
        catalog_iri = URIRef(f"{base}/catalog")
        record = URIRef(f"{REGISTRY_BASE}/record/{iid}")

        src = Graph()
        src.parse(path, format="turtle")
        out.bind(iid, Namespace(f"{base}/entity/"))
        out.bind(f"{iid}-wdt", Namespace(direct_prefix))

        kept = Counter()
        dropped = Counter()
        entities = set()
        for s, p, o in src:
            if isinstance(s, URIRef) and ent_re.match(str(s)):
                if p in entity_keep or str(p).startswith(direct_prefix):
                    out.add((s, p, o))
                    entities.add(s)
                    kept["entity"] += 1
                else:
                    dropped["statement links, counters, reference and qualifier machinery"] += 1
            elif s == catalog_iri:
                if p in catalog_keep:
                    out.add((s, p, o))
                    kept["instance catalogue"] += 1
                else:
                    dropped["links from the instance catalogue to its parts"] += 1
            else:
                dropped["statement, reference, value nodes, per-entity DCAT, ontology blocks"] += 1

        for e in entities:
            out.add((e, BBR.fromInstance, record))

        # roles: one normalised statement per source statement, the source statement stays
        pids = {r["role"]: r["property"] for r in core_rows if r["instance"] == iid and r["property"] != "none"}
        role_counts, role_skipped = Counter(), Counter()
        for role in ROLES:
            pid = pids.get(role)
            if not pid:
                continue
            pred = BBR[ROLE_TERM[role]]
            for s, o in src.subject_objects(URIRef(direct_prefix + pid)):
                value = None
                if role in ("instance_of", "subclass_of", "part_of"):
                    value = o if isinstance(o, URIRef) else None
                elif role == "coordinates":
                    value = o
                elif role in ("equivalent_class", "external_match"):
                    text = str(o)
                    value = o if isinstance(o, URIRef) else (URIRef(text) if RE_URL.fullmatch(text) else None)
                elif role == "wikidata_equivalent":
                    text = str(o).strip()
                    value = URIRef("http://www.wikidata.org/entity/" + text) if RE_WIKIDATA_ID.fullmatch(text) else None
                if value is None:
                    role_skipped[role] += 1
                    continue
                out.add((s, pred, value))
                role_counts[role] += 1
        for role, n in sorted(role_skipped.items()):
            warn(f"{iid}: role {role}: {n} value(s) of {pids[role]} could not be normalised and were skipped")

        # the catalogue record of this instance
        out.add((record, RDF.type, DCAT.CatalogRecord))
        out.add((record, DCTERMS.isPartOf, catalogue))
        out.add((catalogue, DCAT.record, record))
        out.add((record, FOAF.primaryTopic, catalog_iri))
        out.add((record, DCTERMS.title, Literal(inst.get("label", iid), lang="en")))
        out.add((record, BBR.prefix, Literal(iid)))
        out.add((record, DCAT.landingPage, URIRef(inst["pages_url"])))
        out.add((record, DCTERMS.source, URIRef(inst["pages_url"].rstrip("/") + "/" + finfo["path"])))
        out.add((record, BBR.sha256, Literal(finfo["sha256"])))
        out.add((record, BBR.sourceTripleCount, Literal(len(src), datatype=XSD.integer)))
        if finfo.get("generator"):
            out.add((record, BBR.generator, Literal(finfo["generator"])))
        if finfo.get("data_as_of"):
            out.add((record, DCTERMS.modified, Literal(finfo["data_as_of"], datatype=XSD.dateTime)))

        reports.append({"id": iid, "source_triples": len(src), "kept": dict(kept), "dropped": dict(dropped),
                        "entities": len(entities), "roles": dict(role_counts), "skipped": dict(role_skipped)})
        print(f"{iid}: {len(src)} source triples, {sum(kept.values())} kept, {len(entities)} entities, "
              f"{sum(role_counts.values())} role statements")
    return out, reports


def write_report(path: Path, reports: list[dict], total: int) -> None:
    L = ["# Bundle report", "", "Generated by `py/step_bundle.py`. Do not edit.", "",
         "| Instance | Source triples | Kept (entities) | Kept (catalogue) | Entities | Role statements |", "|---|---|---|---|---|---|"]
    for r in reports:
        L.append(f"| {r['id']} | {r['source_triples']} | {r['kept'].get('entity', 0)} | "
                 f"{r['kept'].get('instance catalogue', 0)} | {r['entities']} | {sum(r['roles'].values())} |")
    L += ["", f"The bundle holds **{total}** triples, including one catalogue record per instance and one "
          "`bbr:fromInstance` per entity.", "", "## Left out", ""]
    for r in reports:
        L.append(f"**{r['id']}**")
        L += [f"- {n} triples: {why}" for why, n in sorted(r["dropped"].items())] + [""]
    L += ["## Role statements", "", "| Role | " + " | ".join(r["id"] for r in reports) + " |",
          "|---|" + "---|" * len(reports)]
    for role in ROLES:
        L.append(f"| {ROLE_TERM[role]} | " + " | ".join(str(r["roles"].get(role, 0)) for r in reports) + " |")
    skipped = [(r["id"], role, n) for r in reports for role, n in sorted(r["skipped"].items())]
    if skipped:
        L += ["", "## Values that could not be normalised", ""]
        L += [f"- {iid}, {role}: {n}" for iid, role, n in skipped]
    path.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    ensure_dirs()

    warnings: list[str] = []

    def warn(msg: str) -> None:
        warnings.append(msg)
        print(f"WARNING {msg}")

    graph, reports = build(load_sources(), read_core(), warn)
    if not reports:
        print("bundle: nothing harvested, nothing written")
        return 1 if args.strict else 0

    nt = DIST / "beaverbridge-registry.nt"
    write_ntriples(graph, nt)

    # Turtle is written from the sorted N-Triples, so both files describe the same graph
    from rdflib import Graph
    g2 = Graph()
    g2.parse(nt, format="nt")
    for pfx, ns in graph.namespaces():
        g2.bind(pfx, ns)
    (DIST / "beaverbridge-registry.ttl").write_text(g2.serialize(format="turtle"), encoding="utf-8", newline="\n")

    write_report(DIST / "bundle_report.md", reports, len(g2))
    print(f"bundle: {len(g2)} triples from {len(reports)} instance(s), {len(warnings)} warning(s)")
    return 1 if (warnings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
