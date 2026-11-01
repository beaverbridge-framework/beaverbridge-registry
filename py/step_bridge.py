"""Step: bridge (offline). Reads crosswalks/classes.csv and writes the CIDOC CRM bridge of the classes.

    dist/crm_bridge.nt, dist/crm_bridge.ttl   per class: bbr:classKind, and where there is an anchor bbr:crmClass + bbr:crmBasis
    dist/bridge_report.md                     per class: kind, own anchor, anchor in effect (inherited along subclass of), items

The table is checked against dist/survey.json: every class of every instance needs a row, every row a class with the same
English label, a `source` anchor must be the one the instance states, a `bridge` row needs a reason. A mismatch is a
warning; with --strict it fails the build. The bundle merges dist/crm_bridge.nt.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry_utils import BBR_NS, CROSSWALKS, DIST, ensure_dirs, load_sources, write_ntriples  # noqa: E402

CLASSES_CSV = CROSSWALKS / "classes.csv"
CRM = "http://www.cidoc-crm.org/cidoc-crm/"
KINDS = ("domain", "model")
BASES = ("source", "bridge", "none")
RE_CRM = re.compile(r"^E[0-9]+_[A-Za-z0-9_]+$")


def numkey(ident: str) -> tuple:
    m = re.fullmatch(r"([A-Z])(\d+)", ident)
    return (m.group(1), int(m.group(2))) if m else (ident, 0)


def effective(cid: str, own: dict, parents: dict):
    """The anchor of a class: its own, else the nearest one along subclass of (breadth first, ties by number)."""
    if cid in own:
        return own[cid], cid
    seen, queue = {cid}, deque(sorted(parents.get(cid, []), key=numkey))
    while queue:
        a = queue.popleft()
        if a in seen:
            continue
        seen.add(a)
        if a in own:
            return own[a], a
        queue.extend(sorted(parents.get(a, []), key=numkey))
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    ensure_dirs()
    warnings: list[str] = []

    def warn(msg: str) -> None:
        warnings.append(msg)
        print(f"WARNING {msg}")

    survey_path = DIST / "survey.json"
    if not survey_path.exists() or not CLASSES_CSV.exists():
        print("bridge: no survey or no classes.csv, nothing written")
        return 1 if args.strict else 0
    survey = {i["id"]: i for i in json.loads(survey_path.read_text(encoding="utf-8"))["instances"]}
    bases = {i["id"]: i["rdf_base"].rstrip("/") for i in load_sources()}
    with CLASSES_CSV.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    # --- check the table against the survey
    by_inst: dict[str, dict[str, dict]] = {}
    for r in rows:
        iid, cid = r["instance"], r["class"]
        if iid not in survey:
            warn(f"classes.csv: unknown instance {iid}")
            continue
        if cid in by_inst.setdefault(iid, {}):
            warn(f"{iid}: class {cid} has two rows")
        by_inst[iid][cid] = r
        if r["kind"] not in KINDS:
            warn(f"{iid}: {cid}: kind '{r['kind']}' is not one of {', '.join(KINDS)}")
        if r["basis"] not in BASES:
            warn(f"{iid}: {cid}: basis '{r['basis']}' is not one of {', '.join(BASES)}")
        if r["crm"] and not RE_CRM.match(r["crm"]):
            warn(f"{iid}: {cid}: '{r['crm']}' is not a CIDOC CRM class name such as E53_Place")
        if (r["basis"] == "none") == bool(r["crm"]):
            warn(f"{iid}: {cid}: basis '{r['basis']}' and crm '{r['crm']}' do not go together")
        if r["basis"] == "bridge" and not r["note"]:
            warn(f"{iid}: {cid}: a bridge anchor needs a reason in note")

    report = []
    graph_rows = []
    for iid, s in survey.items():
        classes = {c["id"]: c for c in s["classes"]}
        table = by_inst.get(iid, {})
        for cid in sorted(classes, key=numkey):
            if cid not in table:
                warn(f"{iid}: class {cid} ({classes[cid]['label']}) has no row in classes.csv")
        for cid in sorted(table, key=numkey):
            r = table[cid]
            if cid not in classes:
                warn(f"{iid}: classes.csv has {cid}, the survey has no such class")
                continue
            if classes[cid]["label"].lower() != r["label_en"].lower():
                warn(f"{iid}: {cid} is labelled '{classes[cid]['label']}', classes.csv says '{r['label_en']}'")
        stated = {a["class"]: a["target"] for a in s["anchors"]}
        for cid, target in stated.items():
            r = table.get(cid)
            if r is None:
                continue
            if r["basis"] != "source" or CRM + r["crm"] != target:
                warn(f"{iid}: {cid} states {target} itself, classes.csv has basis '{r['basis']}' and crm '{r['crm']}'")
        for cid, r in table.items():
            if r["basis"] == "source" and cid not in stated:
                warn(f"{iid}: {cid} has basis 'source' but the instance states no anchor")

        own = {cid: r["crm"] for cid, r in table.items() if r["crm"]}
        parents = {cid: c["superclasses"] for cid, c in classes.items()}
        for cid in sorted(table, key=numkey):
            if cid not in classes:
                continue
            r = table[cid]
            crm, via = effective(cid, own, parents)
            graph_rows.append((iid, cid, r))
            report.append({"instance": iid, "class": cid, "label": classes[cid]["label"], "kind": r["kind"],
                           "own": r["crm"], "basis": r["basis"], "effective": crm or "", "via": via if via and via != cid else "",
                           "items": classes[cid]["instances"]})

    # --- write the bridge
    from rdflib import Graph, Literal, Namespace, URIRef
    BBR = Namespace(BBR_NS)
    g = Graph()
    g.bind("bbr", BBR)
    for iid, cid, r in graph_rows:
        c = URIRef(f"{bases[iid]}/entity/{cid}")
        g.add((c, BBR.classKind, Literal(r["kind"])))
        if r["crm"]:
            g.add((c, BBR.crmClass, URIRef(CRM + r["crm"])))
            g.add((c, BBR.crmBasis, Literal(r["basis"])))
    write_ntriples(g, DIST / "crm_bridge.nt")
    g2 = Graph()
    g2.parse(DIST / "crm_bridge.nt", format="nt")
    g2.bind("bbr", BBR)
    g2.bind("crm", Namespace(CRM))
    (DIST / "crm_bridge.ttl").write_text(g2.serialize(format="turtle"), encoding="utf-8", newline="\n")

    # --- report
    L = ["# CRM bridge of the classes", "", "Generated by `py/step_bridge.py` from `crosswalks/classes.csv`. Do not edit.", ""]
    for iid in survey:
        rs = [r for r in report if r["instance"] == iid]
        dom = [r for r in rs if r["kind"] == "domain"]
        anchored = [r for r in dom if r["effective"]]
        items_dom = sum(r["items"] for r in dom)
        items_anch = sum(r["items"] for r in anchored)
        L += [f"## {iid}", "",
              f"{len(rs)} classes: {len(dom)} domain, {len(rs) - len(dom)} model. {len(anchored)} of {len(dom)} domain classes "
              f"have an anchor in effect; they hold {items_anch} of {items_dom} items counted directly on domain classes.", "",
              "| Class | Label | Kind | Own anchor | Basis | In effect | Through | Items |", "|---|---|---|---|---|---|---|---|"]
        L += [f"| {r['class']} | {r['label']} | {r['kind']} | {r['own'] or '-'} | {r['basis']} | {r['effective'] or '-'} | "
              f"{r['via'] or '-'} | {r['items']} |" for r in sorted(rs, key=lambda r: numkey(r["class"]))]
        L.append("")
    (DIST / "bridge_report.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")

    n_anchor = sum(1 for r in report if r["own"])
    print(f"bridge: {len(report)} classes, {n_anchor} with an anchor of their own, {len(g)} triples, {len(warnings)} warning(s)")
    return 1 if (warnings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
