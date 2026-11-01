# crosswalks

`core-properties.csv` says which property of each registered instance plays which **role**. Property numbers differ between Wikibases (in `chublets` P2 is *instance of*, in `fuzzy-sl` it is P1), so a question across instances has to go through this table and never through a fixed P-number.

| Role | Meaning |
|---|---|
| `instance_of` | the item is an instance of a class |
| `subclass_of` | the item is a subclass of another class |
| `part_of` | the item is part of another item |
| `coordinates` | the item has a geographic position |
| `equivalent_class` | the class item states an equivalent class IRI (e.g. a CIDOC CRM class) |
| `wikidata_equivalent` | the item states its Wikidata Q-number |
| `external_match` | the item states a URL of the same thing elsewhere |

`property` is a P-number or `none`; a `none` row needs a reason in `note`. Every instance in `registry/sources.json` needs one row per role.

The survey step checks every row against the harvested graph (the property exists, its English label and its datatype are the ones stated here) and reports a mismatch as a warning; with `--strict` it stops the build.

Edit this file by hand. It is a source, not a generated artefact.

## classes.csv

`classes.csv` says, for every class of every registered instance, what kind of class it is and which CIDOC CRM class it is anchored to. It is a source: edit it by hand. `py/step_bridge.py` checks it against the survey and writes the bridge (`dist/crm_bridge.ttl`) that the bundle merges.

| Column | Meaning |
|---|---|
| `instance`, `class`, `label_en` | the class as the instance has it; the survey must find it with this English label |
| `kind` | `domain`: the class of the things the instance is about (sites, software). `model`: a class of the data model itself (vocabulary, types, provenance, the roots) |
| `crm` | local name of a CIDOC CRM class (`E53_Place`) or empty |
| `basis` | `source`: the instance states the anchor itself (checked against the survey). `bridge`: the registry states it, because the instance does not. `none`: no anchor of its own |
| `note` | a reason; for `bridge` the reason is required |

Anchors are inherited along `subclass of`: a class without an anchor of its own has the one of its nearest superclass that has one. A `domain` class with neither is reported (SHOULD).

The `bridge` rows and the `kind` column are proposals of the registry, not statements of the instances: correct them here, never in the generated files.
