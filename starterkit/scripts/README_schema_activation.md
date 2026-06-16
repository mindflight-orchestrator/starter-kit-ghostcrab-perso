# GhostCrab schema activation from LinkML

`generate_ghostcrab_schemas_from_linkml.py` converts validated LinkML modules into MCP payloads for GhostCrab Personal.

It does not call MCP and does not write to SQLite. It produces reviewable payload files:

- `schema_register_payloads.jsonl` for `ghostcrab_schema_register`
- `facet_register_payloads.jsonl` for `ghostcrab_facet_register`
- `summary.json` for counters
- `activation_plan.md` for the apply order and read tests

Run it after native LinkML import:

```bash
python3 starterkit/scripts/generate_ghostcrab_schemas_from_linkml.py \
  --linkml-dir generated/linkml_from_json \
  --workspace-id <workspace_id> \
  --output-dir generated/<workspace_id>/ghostcrab_schema_activation
```

For multi-module workspaces, pass modules explicitly when needed:

```bash
python3 starterkit/scripts/generate_ghostcrab_schemas_from_linkml.py \
  --linkml-dir generated/linkml_from_json \
  --workspace-id serenity-v4 \
  --modules production administrative comptabilite decisionnel technique missions \
  --output-dir generated/serenity-v4/ghostcrab_schema_activation
```

Definition of done:

1. LinkML modules are compiled and imported into native `ontology_*`.
2. `schema_register_payloads.jsonl` has been applied with `ghostcrab_schema_register`.
3. `facet_register_payloads.jsonl` has been applied with `ghostcrab_facet_register`.
4. `ghostcrab_schema_list`, representative `ghostcrab_facet_inspect`, and retrieval smoke tests pass.

Do not mark a GhostCrab workspace ready after ontology import alone.
