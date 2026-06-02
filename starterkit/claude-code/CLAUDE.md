# GhostCrab MCP StarterKit — Claude Code Entrypoint

You are working with the **mindBrain StarterKit** alongside a running GhostCrab MCP instance.

## Your role

Guide the user through the 3-phase GhostCrab workflow. Start with Phase A every session unless the user explicitly confirms GhostCrab MCP is already running and healthy.

## Phase A — Verify GhostCrab MCP (always first)

Load `SOP4_environment_bootstrap.md` from this starterkit directory.

Run through the Phase A checklist:
1. Docker PostgreSQL healthy
2. Migrations applied
3. Smoke test passing (`npm run smoke:mcp`)
4. MCP client connected (24 `ghostcrab_*` tools visible)
5. `ghostcrab_status` returns no critical error

**Do not proceed to Phase B until all Phase A checkpoints pass.**

## Phase B0 — Choose ontology import path

Load `SOP0_import_path_choices.md`. Present LinkML (default) vs MCP incremental. Record in `templates/import_path_choices.yaml`.

## Phase B — Model the project

Load `SOP1_ghostcrab_mcp.md` then `SOP2_obsidian_ontologie.md` (§6 bis LinkML or §7 Voie A MCP per B0).

Sequence: JTBD → workspace → schema registration → DDL → workspace inspect → coverage baseline.

**GRAPH_WORKSPACE** — Ne pas pré-configurer. Appeler `ghostcrab_modeling_guidance` (GhostCrab donne les indications), co-construire le modèle avec l'utilisateur, puis `ghostcrab_workspace_create` retourne l'UUID. Cet UUID devient `GRAPH_WORKSPACE` pour toute la session — propager aux agents d'ingestion après création. Utiliser `ghostcrab_workspace_inspect` ou `ghostcrab_workspace_export_model` (depth: `full`) pour retrouver le détail complet du graphe avec tous les champs et leur nature.

Use templates in `../templates/` as starter files. Never hallucinate field names — derive them from the vault structure and the mapping file.

## Phase C — Parse and ingest

Load `SOP2_obsidian_ontologie.md` §7 Voie A or §6 bis + `SOP3_parsing_pipeline.md`.

Critical: use the **same `DATABASE_URL`** for COPY ingestion as the one configured in the GhostCrab MCP server. Never use a different DSN.

Target: `ghostcrab_coverage` ≥ 80% on core schemas before declaring Phase C complete.

## Phase C2.0 — Choose tabular import path

Load `SOP0_import_path_choices.md` §4. Present structured-import CLI (default Personal) vs SOP5 scripts. Record in `import_path_choices.yaml`.

## Phase C2 — Compile external sources

For CSV/API/JSON/app exports, load `SOP5_source_import_compiler.md` (§1 bis or §3 Voie A per C2.0).

Use the generic templates in `../templates/`:

1. `source_profile.yaml`
2. `mapping_external_to_canonical.yaml`
3. `consumer_contract.yaml`
4. `import_manifest.yaml`

Default to dry-run. Do not write data until the source profile, target model, mapping, and consumer contract are coherent. If a consumer requires a graph viewer, materialize native graph rows and test the declared consumer checks before declaring the import complete.

## Key constraints

- Read before write: always `ghostcrab_count` → `ghostcrab_search` → `ghostcrab_pack` before any write.
- MCP is not a hot-path: bulk ingestion goes through direct SQL (COPY), never through `ghostcrab_remember` in a loop.
- Non-Obsidian imports follow SOP5: source profile → target model → mapping → dry-run JSONB → review exceptions → facets → graph if required → projections → consumers.
- `schema_id` must be namespaced: `<workspace_id>:<entity_type>`.
- Edge labels must use `UPPER_SNAKE_CASE` (e.g. `DEPENDS_ON`, not `dependsOn` or `DEPENDSON`).
- End each meaningful phase with a checkpoint: `ghostcrab_project` with `note_kind: "checkpoint"`.
