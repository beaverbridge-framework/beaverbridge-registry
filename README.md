# beaverbridge-registry 🦫

*Building Bridges from Community Data to Semantic Knowledge.*

A registry for static Wikibase instances published with [wikibase-static](https://github.com/n4o-rse/wikibase-static). It harvests their RDF exports from GitHub Pages, bundles them into one catalogue and publishes a facet page and a browser-based SPARQL page as a static site: no server, no endpoint, no database.

This repository is the prototype of **BeaverBridge**, a Community Hub to CIDOC CRM transformation toolkit, and will be merged into it. It follows the pattern of the [FDOx registry](https://github.com/FDOx-squirrel/fdo-squirrel-registry).

> **Status: S1 of the work plan.** Only the skeleton exists. See [`PRIMER.md`](PRIMER.md) (German) for the plan.

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
| `fuzzy-sl` | [fuzzy-sl-static](https://github.com/n4o-rse/fuzzy-sl-static) | https://n4o-rse.github.io/fuzzy-sl-static/ |
| `chublets` | [chublets-wikibase-demo](https://github.com/n4o-rse/chublets-wikibase-demo) | https://n4o-rse.github.io/chublets-wikibase-demo/ |

## Licence

Code: MIT. The generated bundle will be CC BY 4.0; the licence of each harvested instance is preserved per entry.

## Acknowledgements

Part of the DFG-funded NFDI initiative [NFDI4Objects](https://www.nfdi4objects.net/), project number 501836407.
