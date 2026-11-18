# beaverbridge-registry 🦫

*Building Bridges from Community Data to Semantic Knowledge.*

A registry for static Wikibase instances published with [wikibase-static](https://github.com/n4o-rse/wikibase-static). It harvests their RDF exports from GitHub Pages, bundles them into one catalogue and publishes a facet page and a browser-based SPARQL page as a static site: no server, no endpoint, no database.

This repository is the prototype of **BeaverBridge**, a Community Hub to CIDOC CRM transformation toolkit. It follows the pattern of the [FDOx registry](https://github.com/FDOx-squirrel/fdo-squirrel-registry).

> **Status: S8 of the work plan, plus the CRM bridge (S5) and the SHACL gate (S6).** Harvest, survey, class bridge, bundle, validation, the facet search page and the browser SPARQL page exist; all planned steps are done. See [`PRIMER.md`](PRIMER.md) (German) for the plan.

The site is built into `docs/` and published with GitHub Pages: https://beaverbridge-framework.github.io/beaverbridge-registry/ (facet search by source type (Wikidata, Wikibase, OpenStreetMap), instance, region, class and CIDOC CRM class, SPARQL in the browser, catalogue, one record per instance, the `bbr:` vocabulary, the bundle as Turtle and N-Triples). `docs/index.html` also opens straight from disk; the query page needs a web server (`python -m http.server -d docs`) or GitHub Pages.

## Running

```
pip install -r requirements.txt
python main.py --list
python main.py
```

`main.py` is the only entry point. Steps that reach the network are not part of the default run: `python main.py harvest`.

## Registered instances

| Id | Source | Pages |
|---|---|---|
| `fuzzy-sl` | [wb-fuzzysl-static](https://github.com/n4o-rse/wb-fuzzysl-static) | https://n4o-rse.github.io/wb-fuzzysl-static/ |
| `chublets` | [chublets-wikibase-demo](https://github.com/n4o-rse/chublets-wikibase-demo) | https://n4o-rse.github.io/chublets-wikibase-demo/ |
| `osm-benchmarks` | [osm-benchmarks-static](https://github.com/n4o-rse/osm-benchmarks-static) | https://n4o-rse.github.io/osm-benchmarks-static/ |
| `squirrelbase` | [wb-squirrelbase-static](https://github.com/n4o-rse/wb-squirrelbase-static) | https://n4o-rse.github.io/wb-squirrelbase-static/ |
| `n4o-prov` | [wb-n4o-prov-static](https://github.com/n4o-rse/wb-n4o-prov-static) | https://n4o-rse.github.io/wb-n4o-prov-static/ |

## Licence

Code: MIT. The generated bundle will be CC BY 4.0; the licence of each harvested instance is preserved per entry.

## Acknowledgements

Part of the DFG-funded NFDI initiative [NFDI4Objects](https://www.nfdi4objects.net/), project number 501836407.
