# Ontology JSON vs LinkML validation

`validate_ontology_json_vs_linkml.py` is a read-only gate for SOP2 LinkML projects where JSON ontology artifacts and LinkML models coexist.

Use it before any `gcp brain ontology compile --import-db` when at least one condition is true:

- multiple ontology modules;
- JSON ontology artifacts are the source of truth or a migration source;
- public names differ from internal roles;
- aliases or historical names must be preserved;
- a `mappingProfile` layer maps external applications to canonical domain concepts.

Example:

```bash
python3 starterkit/scripts/validate_ontology_json_vs_linkml.py \
  --json-dir ontology \
  --linkml-dir ontology \
  --manifest ontology/manifest.json \
  --config ontology/<workspace>-contract.yaml \
  --output generated/<workspace>/reports/json_vs_linkml.validation.json \
  --markdown-output generated/<workspace>/reports/json_vs_linkml.validation.md
```

The central contract is both a human design artifact and the validator config. It should include:

- `workspace_id`, edition, target backend, and status;
- canonical ontology ids, public labels, internal roles, aliases, and accepted renames;
- import order and technical entrypoints;
- external application mapping rules, especially `mappingProfile`;
- `aliases` and `checks` sections consumed by the script.

Blocking issues must be resolved before import. Accepted aliases recorded in the contract are not blocking mismatches.
