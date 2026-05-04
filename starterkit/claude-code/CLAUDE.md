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

## Phase B — Model the project

Load `SOP1_ghostcrab_mcp.md` then `SOP2_obsidian_ontologie.md`.

Sequence: JTBD → workspace → schema registration → DDL → workspace inspect → coverage baseline.

**GRAPH_WORKSPACE** — Ne pas pré-configurer. Appeler `ghostcrab_modeling_guidance` (GhostCrab donne les indications), co-construire le modèle avec l'utilisateur, puis `ghostcrab_workspace_create` retourne l'UUID. Cet UUID devient `GRAPH_WORKSPACE` pour toute la session — propager aux agents d'ingestion après création. Utiliser `ghostcrab_workspace_inspect` ou `ghostcrab_workspace_export_model` (depth: `full`) pour retrouver le détail complet du graphe avec tous les champs et leur nature.

Use templates in `../templates/` as starter files. Never hallucinate field names — derive them from the vault structure and the mapping file.

## Phase C — Parse and ingest

Load `SOP2_obsidian_ontologie.md` §7 (injection sequence) then `SOP3_parsing_pipeline.md`.

Critical: use the **same `DATABASE_URL`** for COPY ingestion as the one configured in the GhostCrab MCP server. Never use a different DSN.

Target: `ghostcrab_coverage` ≥ 80% on core schemas before declaring Phase C complete.

## Key constraints

- Read before write: always `ghostcrab_count` → `ghostcrab_search` → `ghostcrab_pack` before any write.
- MCP is not a hot-path: bulk ingestion goes through direct SQL (COPY), never through `ghostcrab_remember` in a loop.
- `schema_id` must be namespaced: `<workspace_id>:<entity_type>`.
- Edge labels must use `UPPER_SNAKE_CASE` (e.g. `DEPENDS_ON`, not `dependsOn` or `DEPENDSON`).
- End each meaningful phase with a checkpoint: `ghostcrab_project` with `note_kind: "checkpoint"`.
