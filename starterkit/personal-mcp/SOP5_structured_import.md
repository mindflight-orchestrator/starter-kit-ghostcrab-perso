# SOP 5 — Structured import (personal-mcp)

**Edition:** personal-mcp only. Pro scripts + COPY → [../pro-mcp/SOP5_source_import_compiler.md](../pro-mcp/SOP5_source_import_compiler.md).

**Version:** 0.1  
**Phase:** C2 — CSV/API/JSON → SQLite via `gcp brain structured-import`.

**Canon:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase C2.

---

## Objective

Compile external tabular sources into validated GhostCrab Personal records without PostgreSQL COPY or mindCLI.

Prerequisite: Phase B0 — `structured_import_cli` in `../templates/import_path_choices.yaml`.

**Phase B2 (recommended):** generate deterministic fake business rows before first bulk apply — [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md), [ROUTE_MAP § B2](ROUTE_MAP.md#route-donnees-fictives-metier). Skip only if real sources are already profiled and mapped.

Runbook: `ghostcrab-personal-mcp/docs/setup/structured-import.md`  
Operator matrix: `ghostcrab-personal-mcp/docs/reference/operator-catalog.md`

**Stop MCP** before database-backed `gcp` commands (or `--force`).

---

## Gates

| Gate | StarterKit script (dry-run) | Personal write path |
|------|----------------------------|---------------------|
| 0 | — | `ghostcrab_status`, active workspace |
| 1 | `../scripts/export_model_contract.mjs` | export model or `../templates/mvp_core_contract.yaml` |
| 2 | `../scripts/profile_source.mjs` | `../templates/source_profile.yaml` |
| 3 | `../scripts/validate_mapping_contract.mjs` | `../templates/mapping_external_to_canonical.yaml` |
| 4 | `../scripts/transform_source_to_jsonb.mjs` | `gcp brain structured-import validate` |
| 5 | `../scripts/import_facets.mjs` (plan only) | `register-semantics` → `apply` → `agent_facts` |
| 6 | `../scripts/materialize_graph_from_edges.mjs` | `apply` + `structured-import reindex --scope graph` |
| 7 | — | `ghostcrab_pack`, `ghostcrab_projection_get` |
| 8 | `../scripts/validate_consumer_contract.mjs` | `../templates/consumer_contract.yaml` |
| 9 | `../scripts/audit_import_pipeline.mjs` | `../templates/import_manifest.yaml` |

**Companion skills** ([SKILL_ROUTE_MAP.md](SKILL_ROUTE_MAP.md)):

- **Gate 7:** `ghostcrab-operator` (smoke workflow) + `ghostcrab-json-answer-builder` (structured answer from pack/projection_get).
- **Gates 8–9:** `ghostcrab-gap-auditor` after `audit_ghostcrab_projections.py` for answerability gaps and remediation routing.

---

## Minimal sequence

```bash
gcp brain structured-import validate --model ... --mapping ... --input ...
gcp brain structured-import register-semantics --workspace-id <ws> --model ... --mapping ...
gcp brain structured-import apply --workspace-id <ws> --mapping ... --facets ... --edges ...
gcp brain structured-import reindex --workspace-id <ws> --scope all
```

StarterKit `.mjs` scripts: profiling, mapping, dry-run JSONL only — **not** `generate_copy_migrations.mjs`.

---

## Definition of ready

- Target model loaded; `source_profile.yaml` and mapping complete
- Dry-run clean; `pending_review` reviewed; `pending_ddl` empty or accepted
- Facet/graph counts match; consumers pass; manifest documents the run
