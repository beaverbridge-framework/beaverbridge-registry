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
