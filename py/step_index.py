"""Step: index (offline). Reads the bundle and writes the data of the facet page.

    dist/registry-index.json   instances and one entry per item, sorted; the page embeds it and publishes it

Everything comes from dist/beaverbridge-registry.nt, nothing from data/raw/ and nothing from the network, so the page
shows exactly what the bundle holds. An entry is an item (wikibase:Item); properties are counted but not listed.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_utils import BBR_NS, DIST, RELEASE, ensure_dirs, load_sources, write_json  # noqa: E402

RE_POINT = re.compile(r"^\s*Point\(\s*(-?[0-9.]+)\s+(-?[0-9.]+)\s*\)\s*$", re.I)
RE_QID = re.compile(r"^http://www\.wikidata\.org/entity/(Q[0-9]+)$")


def numkey(ident: str) -> tuple:
    m = re.fullmatch(r"([A-Z])(\d+)", ident)
    return (m.group(1), int(m.group(2))) if m else (ident, 0)


def licence_label(iri: str) -> str:
    """Short name of a Creative Commons licence IRI; any other IRI stays as it is."""
    m = re.match(r"https?://creativecommons\.org/publicdomain/zero/([0-9.]+)/?$", iri)
    if m:
        return f"CC0-{m.group(1)}"
    m = re.match(r"https?://creativecommons\.org/licenses/([a-z-]+)/([0-9.]+)/?$", iri)
    if m:
        return f"CC-{m.group(1).upper()}-{m.group(2)}"
    return iri


def crm_label(iri) -> str:
    """E53_Place -> 'E53 Place'"""
    return str(iri).rsplit("/", 1)[-1].replace("_", " ")


def pick(values, lang_order=("en",)):
    """One literal: English first, then the other languages in alphabetical order, then untagged."""
    vals = sorted(values, key=lambda v: (getattr(v, "language", None) not in lang_order,
                                         getattr(v, "language", None) or "~", str(v)))
    return str(vals[0]) if vals else ""


def build(warn) -> dict:
    from rdflib import RDF, RDFS, Graph, URIRef
    from rdflib.namespace import DCAT, DCTERMS, FOAF

    g = Graph()
    g.parse(DIST / "beaverbridge-registry.nt", format="nt")

    BBR = lambda t: URIRef(BBR_NS + t)  # noqa: E731
    SCHEMA_NAME, SCHEMA_DESC = URIRef("http://schema.org/name"), URIRef("http://schema.org/description")
    WB_ITEM, WB_PROP = URIRef("http://wikiba.se/ontology#Item"), URIRef("http://wikiba.se/ontology#Property")
    tail = lambda u: str(u).rsplit("/", 1)[-1]  # noqa: E731

    rank = {i["id"]: n for n, i in enumerate(load_sources())}  # order of registry/sources.json
    # kind and effective CRM class per class: own anchor, else the nearest one along bbr:subclassOf
    kind = {c: str(k) for c, k in g.subject_objects(BBR("classKind"))}
    own_crm = {c: x for c, x in g.subject_objects(BBR("crmClass"))}
    supers = {}
    for c, s in g.subject_objects(BBR("subclassOf")):
        supers.setdefault(c, []).append(s)

    def crm_of(c):
        seen, queue = {c}, [c]
        while queue:
            cur = queue.pop(0)
            if cur in own_crm:
                return crm_label(own_crm[cur])
            for s in sorted(supers.get(cur, []), key=lambda u: numkey(tail(u))):
                if s not in seen:
                    seen.add(s)
                    queue.append(s)
        return None

    instances, entries, class_labels = [], [], {}
    for rec in sorted(g.subjects(RDF.type, DCAT.CatalogRecord),
                      key=lambda r: (rank.get(str(g.value(r, BBR("prefix"))), 99), str(r))):
        iid = str(g.value(rec, BBR("prefix")))
        topic = g.value(rec, FOAF.primaryTopic)
        pages_url = str(g.value(rec, DCAT.landingPage))
        lic = g.value(topic, DCTERMS.license)
        lic_label = licence_label(str(lic)) if lic else "unknown"
        if lic is None:
            warn(f"{iid}: the catalogue states no licence")

        members = sorted((s for s in g.subjects(BBR("fromInstance"), rec) if isinstance(s, URIRef)),
                         key=lambda s: numkey(tail(s)))
        label = {s: pick(list(g.objects(s, RDFS.label)) or list(g.objects(s, SCHEMA_NAME))) for s in members}

        n_items = n_props = 0
        for s in members:
            if (s, RDF.type, WB_PROP) in g:
                n_props += 1
            if (s, RDF.type, WB_ITEM) not in g:
                continue
            n_items += 1
            local = tail(s)
            e = {"id": f"{iid}:{local}", "instance": iid, "local": local, "label": label[s] or local,
                 "description": pick(g.objects(s, SCHEMA_DESC)),
                 "url": f"{pages_url.rstrip('/')}/{local}.html"}
            classes = sorted({c for c in g.objects(s, BBR("instanceOf")) if isinstance(c, URIRef)},
                             key=lambda c: numkey(tail(c)))
            e["classes"] = [f"{iid}:{tail(c)}" for c in classes]
            e["kinds"] = sorted({kind[c] for c in classes if c in kind})
            e["crm"] = sorted({x for x in (crm_of(c) for c in classes) if x})
            for c in classes:
                class_labels[f"{iid}:{tail(c)}"] = label.get(c) or tail(c)
            parts = sorted((p for p in g.objects(s, BBR("partOf")) if isinstance(p, URIRef)), key=lambda p: numkey(tail(p)))
            e["part_of"] = [{"id": f"{iid}:{tail(p)}", "label": label.get(p) or tail(p)} for p in parts]
            coords = []
            for c in g.objects(s, BBR("coordinates")):
                m = RE_POINT.match(str(c))
                if m:
                    coords.append([float(m.group(2)), float(m.group(1))])  # [lat, lon]
                else:
                    warn(f"{e['id']}: coordinates not read: {c}")
            e["coordinates"] = sorted(coords)
            e["wikidata"] = sorted({RE_QID.match(str(w)).group(1) for w in g.objects(s, BBR("wikidataEquivalent"))
                                    if RE_QID.match(str(w))}, key=numkey)
            e["matches"] = sorted(str(m) for m in g.objects(s, BBR("externalMatch")))
            e["features"] = [name for name, has in (("coordinates", e["coordinates"]), ("Wikidata link", e["wikidata"]),
                                                    ("external match", e["matches"])) if has]
            entries.append(e)

        instances.append({
            "id": iid, "title": str(g.value(rec, DCTERMS.title)), "pages_url": pages_url, "licence": lic_label,
            "generator": str(g.value(rec, BBR("generator")) or ""), "data_as_of": str(g.value(rec, DCTERMS.modified) or ""),
            "source": str(g.value(rec, DCTERMS.source)), "sha256": str(g.value(rec, BBR("sha256"))),
            "source_triples": int(g.value(rec, BBR("sourceTripleCount")) or 0),
            "record": str(rec), "entities": len(members), "items": n_items, "properties": n_props,
        })
        print(f"{iid}: {n_items} items, {n_props} properties")

    order = {i["id"]: n for n, i in enumerate(instances)}
    entries.sort(key=lambda e: (order[e["instance"]], numkey(e["local"])))
    for e in entries:  # the id and the page address say the rest
        del e["local"]
    return {"release": RELEASE, "bundle_triples": len(g), "instances": instances, "class_labels": class_labels,
            "entries": entries}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    warnings: list[str] = []

    def warn(msg: str) -> None:
        warnings.append(msg)
        print(f"WARNING {msg}")

    if not (DIST / "beaverbridge-registry.nt").exists():
        print("index: no bundle, nothing written")
        return 1 if args.strict else 0
    data = build(warn)
    write_json(DIST / "registry-index.json", data)
    print(f"index: {len(data['entries'])} entries from {len(data['instances'])} instance(s), {len(warnings)} warning(s)")
    return 1 if (warnings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
