# SOP 1 — GhostCrab MCP (personal-mcp)

**Edition:** personal-mcp only. Pro PostgreSQL contract → [../pro-mcp/SOP1_ghostcrab_mcp.md](../pro-mcp/SOP1_ghostcrab_mcp.md).

**Version:** 1.0  
**Phase:** B — modeling and query surface (no Postgres DDL, no COPY hot-path).

**Canon:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase B.

---

## Runtime

| Topic | Personal |
|-------|----------|
| Database | SQLite: `agent_facts`, `graph_entity`, `projections`, `ontology_*` |
| MCP tools | ~50 registered, 12 listed by default — see product `docs/reference/operator-catalog.md` |
| Bulk tabular | `gcp brain structured-import` → [SOP5](SOP5_structured_import.md) |
| Bulk documents | `gcp brain document` → [SOP6](SOP6_gcp_document_import.md) |
| Formal ontology | `gcp brain ontology compile` — product `docs/explanation/ontology/README.md` |
| DDL Layer 1 Postgres | **Skip** — use `ghostcrab_schema_register` + SQLite tables |
| mindCLI | **Forbidden** |

---

## Phase B MCP sequence

1. `ghostcrab_status`
2. `ghostcrab_modeling_guidance`
3. `ghostcrab_workspace_create`
4. `ghostcrab_schema_register` for `ghostcrab:*` shapes (not LinkML OWL taxonomies)
5. `ghostcrab_workspace_inspect`, `ghostcrab_coverage`

LinkML OWL path: [SOP2_obsidian_ontologie.md](SOP2_obsidian_ontologie.md) §6 bis + `gcp brain ontology compile`.

---

## Rules

- MCP is for modeling and **unit** writes; bulk tabular → `gcp brain structured-import`; bulk docs → `gcp brain document`.
- Do not use `ghostcrab_ddl_*` for PostgreSQL Layer 1 schemas.
- `remember` / `upsert` / `learn` / `project` / `pack` are MCP-only (no `gcp` subcommands for those).

## Projections

Prepare → materialize → work → audit : [ROUTE_MAP § projections](ROUTE_MAP.md#route-projections) and [../scripts/README_projection_tools.md](../scripts/README_projection_tools.md). SOP2 §7.6–7.7 for `ghostcrab_project` ; gate 7 in [SOP5](SOP5_structured_import.md) for `ghostcrab_pack` / `ghostcrab_projection_get`.

**Companion skills:** [SKILL_ROUTE_MAP.md](SKILL_ROUTE_MAP.md) — `ghostcrab-projection-reviewer` (B1 prep/freeze), `ghostcrab-gap-auditor` (audit), `ghostcrab-operator` + `ghostcrab-json-answer-builder` (runtime Q&A after import).

---

## Templates

- `../templates/mvp_core_contract.yaml`
- `../templates/import_path_choices.yaml` (`edition: personal-mcp`)
