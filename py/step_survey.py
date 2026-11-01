"""Step: survey (offline). Measures every harvested instance and checks crosswalks/core-properties.csv against it.

Reads data/raw/<id>/ (as listed in harvest.json) and writes

    dist/survey.json         machine-readable, sorted keys
    dist/survey_report.md    the same, for people

Nothing here reads the clock or the network. A row of the crosswalk that does not match the graph (unknown property,
other English label, other datatype) is a warning; with --strict it fails the build, so a crosswalk cannot drift away
from the instances it describes.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_utils import CROSSWALKS, DIST, RAW, ensure_dirs, load_sources, write_json  # noqa: E402

CORE_CSV = CROSSWALKS / "core-properties.csv"
ROLES = ["instance_of", "subclass_of", "part_of", "coordinates", "equivalent_class",
         "wikidata_equivalent", "external_match"]
WB = "http://wikiba.se/ontology#"
RE_WIKIDATA = re.compile(r"wikidata\.org/(?:entity|wiki)/(Q\d+)")


def numkey(ident: str) -> tuple:
    m = re.fullmatch(r"([A-Z])(\d+)", ident)
    return (m.group(1), int(m.group(2))) if m else (ident, 0)


def read_core() -> list[dict]:
    with CORE_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def export_path(inst: dict) -> Path | None:
    manifest = RAW / inst["id"] / "harvest.json"
    if not manifest.exists():
        return None
    for f in json.loads(manifest.read_text(encoding="utf-8"))["files"]:
        if f.get("role", "export") == "export":
            return RAW / inst["id"] / Path(f["path"]).name
    return None


def survey_instance(inst: dict, core: dict[str, dict], warn) -> dict:
    from rdflib import RDF, RDFS, Graph, Literal, URIRef

    iid, base = inst["id"], inst["rdf_base"].rstrip("/")
    path = export_path(inst)
    g = Graph()
    g.parse(path, format="turtle")

    def direct(pid):
        return URIRef(f"{base}/prop/direct/{pid}")

    def local(u):
        return str(u).rsplit("/", 1)[-1]

    def label(s):
        ls = [x for x in g.objects(s, RDFS.label) if isinstance(x, Literal)]
        ls.sort(key=lambda x: (x.language != "en", x.language or "", str(x)))
        return str(ls[0]) if ls else ""

    entity = lambda i: URIRef(f"{base}/entity/{i}")  # noqa: E731

    # properties: datatype, English label, number of direct statements
    props = {}
    for s in g.subjects(RDF.type, URIRef(WB + "Property")):
        pid = local(s)
        pt = next(g.objects(s, URIRef(WB + "propertyType")), None)
        props[pid] = {"label": label(s), "datatype": str(pt).rsplit("#", 1)[-1] if pt else "",
                      "uses": sum(1 for _ in g.subject_objects(direct(pid)))}

    items = sorted((local(s) for s in g.subjects(RDF.type, URIRef(WB + "Item"))), key=numkey)

    # crosswalk check
    roles = {}
    for r in ROLES:
        row = core.get(r)
        if row is None:
            warn(f"{iid}: crosswalk has no row for role {r}")
            continue
        pid = row["property"]
        if pid == "none":
            if not row["note"]:
                warn(f"{iid}: role {r} is 'none' but gives no reason in note")
            continue
        p = props.get(pid)
        if p is None:
            warn(f"{iid}: role {r}: property {pid} does not exist")
            continue
        if p["label"].lower() != row["label_en"].lower():
            warn(f"{iid}: role {r}: {pid} is labelled '{p['label']}', the crosswalk says '{row['label_en']}'")
        if p["datatype"] != row["datatype"]:
            warn(f"{iid}: role {r}: {pid} has datatype {p['datatype']}, the crosswalk says {row['datatype']}")
        roles[r] = pid

    def edges(role):
        if role not in roles:  # the crosswalk has no usable property for this role (already warned about)
            return []
        return sorted(((local(s), local(o)) for s, o in g.subject_objects(direct(roles[role]))),
                      key=lambda e: (numkey(e[0]), numkey(e[1])))

    inst_edges, sub_edges = edges("instance_of"), edges("subclass_of")
    classes = {o for _, o in inst_edges} | {x for e in sub_edges for x in e}

    counts = defaultdict(lambda: {"items": 0, "properties": 0})
    for s, o in inst_edges:
        counts[o]["properties" if s.startswith("P") else "items"] += 1
    parents = defaultdict(list)
    for s, o in sub_edges:
        parents[s].append(o)

    class_rows = [{"id": c, "label": label(entity(c)), "instances": counts[c]["items"],
                   "property_instances": counts[c]["properties"], "superclasses": sorted(parents[c], key=numkey)}
                  for c in sorted(classes, key=numkey)]
    roots = [c for c in sorted(classes, key=numkey) if not parents[c]]

    # anchors: classes that state an equivalent class IRI, and those that inherit one through subclass_of
    anchors, inherited = [], []
    if "equivalent_class" in roles:
        own = {local(s): str(o) for s, o in g.subject_objects(direct(roles["equivalent_class"]))}
        anchors = [{"class": c, "label": label(entity(c)), "target": t} for c, t in sorted(own.items(), key=lambda kv: numkey(kv[0]))]
        for c in sorted(classes, key=numkey):
            if c in own:
                continue
            seen, queue = {c}, deque(parents[c])
            while queue:
                a = queue.popleft()
                if a in seen:
                    continue
                seen.add(a)
                if a in own:
                    inherited.append({"class": c, "label": label(entity(c)), "via": a, "target": own[a]})
                    break
                queue.extend(parents[a])

    text = path.read_text(encoding="utf-8")
    return {
        "id": iid, "label": inst.get("label", iid), "rdf_base": base, "file": path.name,
        "triples": len(g), "items": len(items),
        "statements": sum(1 for _ in g.subjects(RDF.type, URIRef(WB + "Statement"))),
        "references": sum(1 for _ in g.subjects(RDF.type, URIRef(WB + "Reference"))),
        "properties": {k: props[k] for k in sorted(props, key=numkey)},
        "roles": roles, "classes": class_rows, "roots": roots, "anchors": anchors, "inherited_anchors": inherited,
        "wikidata_qids": sorted(set(RE_WIKIDATA.findall(text)), key=numkey),
    }


def md_table(header: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def write_report(path: Path, surveys: list[dict], cross: dict) -> None:
    L = ["# Survey of the registered instances", "",
         "Generated by `py/step_survey.py` from `data/raw/`. Do not edit.", ""]
    L += md_table(["Instance", "Triples", "Items", "Properties", "Statements", "References", "Classes"],
                  [[s["id"], s["triples"], s["items"], len(s["properties"]), s["statements"], s["references"],
                    len(s["classes"])] for s in surveys]) + [""]

    L += ["## Roles: the same job, different property", ""]
    L += md_table(["Role"] + [s["id"] for s in surveys],
                  [[r] + [s["roles"].get(r, "none") for s in surveys] for r in ROLES]) + [""]
    if cross["role_ids_differ"]:
        L += ["Roles whose property number differs between instances: " + ", ".join(cross["role_ids_differ"]) + ".", ""]
    L += [f"Wikidata items referenced by more than one instance: **{len(cross['shared_wikidata_qids'])}**"
          + (" (" + ", ".join(cross["shared_wikidata_qids"]) + ")" if cross["shared_wikidata_qids"] else "") + ".", ""]

    for s in surveys:
        L += [f"## {s['id']}", "", f"{s['label']}. Export `{s['file']}`, base `{s['rdf_base']}`.", ""]
        used = sorted(((k, v) for k, v in s["properties"].items() if v["uses"]), key=lambda kv: (-kv[1]["uses"], numkey(kv[0])))
        L += [f"### Properties in use ({len(used)} of {len(s['properties'])})", ""]
        L += md_table(["Property", "Label", "Datatype", "Statements"], [[k, v["label"], v["datatype"], v["uses"]] for k, v in used]) + [""]
        L += ["### Classes", ""]
        L += md_table(["Class", "Label", "Items", "Properties", "Superclass"],
                      [[c["id"], c["label"], c["instances"], c["property_instances"], ", ".join(c["superclasses"])]
                       for c in sorted(s["classes"], key=lambda c: (-c["instances"], numkey(c["id"])))]) + [""]
        L += ["Root classes (no superclass): " + (", ".join(s["roots"]) or "none") + ".", ""]
        if s["anchors"]:
            L += ["### Classes that state an equivalent class IRI", ""]
            L += md_table(["Class", "Label", "Equivalent class"], [[a["class"], a["label"], a["target"]] for a in s["anchors"]]) + [""]
            if s["inherited_anchors"]:
                L += md_table(["Class", "Label", "Inherits from", "Equivalent class"],
                              [[a["class"], a["label"], a["via"], a["target"]] for a in s["inherited_anchors"]]) + [""]
        else:
            L += ["No class of this instance states an equivalent class IRI.", ""]
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

    instances = load_sources()
    rows = read_core()
    surveys = []
    for inst in instances:
        if export_path(inst) is None or not export_path(inst).exists():
            warn(f"{inst['id']}: no harvested export; run  python main.py harvest")
            continue
        core = {r["role"]: r for r in rows if r["instance"] == inst["id"]}
        surveys.append(survey_instance(inst, core, warn))
        s = surveys[-1]
        print(f"{s['id']}: {s['triples']} triples, {s['items']} items, {len(s['properties'])} properties, "
              f"{len(s['classes'])} classes, roles {len(s['roles'])}/{len(ROLES)}")

    known = {i["id"] for i in instances}
    for r in rows:
        if r["instance"] not in known:
            warn(f"crosswalk row for unknown instance {r['instance']}")
        if r["role"] not in ROLES:
            warn(f"crosswalk row with unknown role {r['role']}")

    if not surveys:
        print("survey: nothing harvested, nothing written")
        return 1 if args.strict else 0

    qids = [set(s["wikidata_qids"]) for s in surveys]
    shared = sorted(set.intersection(*qids), key=numkey) if len(qids) > 1 else []
    # only instances that have the role count: "none" is an absence, not a different property number
    differ = [r for r in ROLES if len({s["roles"][r] for s in surveys if r in s["roles"]}) > 1]
    cross = {"shared_wikidata_qids": shared, "role_ids_differ": differ}

    write_json(DIST / "survey.json", {"instances": surveys, "cross": cross, "warnings": warnings})
    write_report(DIST / "survey_report.md", surveys, cross)
    print(f"survey: {len(surveys)} instance(s), {len(warnings)} warning(s)")
    return 1 if (warnings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
