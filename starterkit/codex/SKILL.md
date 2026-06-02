# GhostCrab MCP StarterKit — Codex Skill

**Trigger:** use this skill when the user mentions GhostCrab, mindBrain, ontology setup, vault ingestion, or wants to start a new GhostCrab project.

## What this skill does

Guides you through the GhostCrab MCP workflow:

- **Phase A** — verify the GhostCrab MCP environment is running correctly
- **Phase B0** — choose ontology path (LinkML default vs MCP incremental) via `SOP0_import_path_choices.md`
- **Phase B** — accompany the user from vault understanding to ontology decisions (workspace, schemas, DDL, or LinkML compile)
- **Phase C** — parse vault files and ingest into PostgreSQL (or Personal equivalents)
- **Phase C2.0** — choose tabular path (structured-import CLI vs SOP5 scripts)
- **Phase C2** — compile CSV/API/JSON/app exports into validated GhostCrab records

## How to use this skill

1. On activation, read `../QUICKSTART.md` to understand the full 3-phase workflow.
2. Determine which phase to start with (default: Phase A).
3. After Phase A, load `SOP0_import_path_choices.md` before Phase B writes.
4. Load the appropriate SOP from the parent directory.
5. Follow the SOP step by step, using the templates in `../templates/`.
6. Before Phase C2 tabular work, confirm tabular path in `import_path_choices.yaml`.

## SOP files (load as needed)

- `../SOP0_import_path_choices.md` — B0 + C2.0 import path choices
- `../SOP4_environment_bootstrap.md` — Phase A
- `../SOP1_ghostcrab_mcp.md` — Phase B (architecture + DB contract)
- `../SOP2_obsidian_ontologie.md` — Phase B + C (ontology + injection)
- `../SOP3_parsing_pipeline.md` — Phase C (parsing pipeline)
- `../SOP5_source_import_compiler.md` — Phase C2 (CSV/API/JSON/app export compiler)

## Key rules (always enforce)

- Before any domain modeling, confirm GhostCrab MCP is reachable from the current session, not just configured in app settings.
- Minimum live validation path before proposing a model: `ghostcrab_status` first, then `ghostcrab_modeling_guidance`.
- Start from the user's vault and retrieval jobs, not from a preselected ontology structure.
- Treat the vault as a candidate container that may hold one ontology or several ontology families inside one workspace.
- Before proposing schemas, accompany the user through these questions: what the vault is used for in practice, who uses it, which retrieval jobs matter, which note families map to distinct jobs, and whether one working view or several are needed.
- Read before write: count → search → pack before any write.
- MCP is not a bulk ingestion path — use SQL COPY for volume.
- Before Phase B ontology writes, load SOP0 and present LinkML (default) vs MCP incremental; record in `import_path_choices.yaml`.
- LinkML path: LLM generates `ontology/core.yaml`, dry-run `gcp brain ontology compile`, confirm, then `--import-db`.
- Tabular Personal default: `gcp brain structured-import`; alternative: SOP5 scripts (Voie A).
- External imports produce `source_profile.yaml`, `mapping_external_to_canonical.yaml`, `consumer_contract.yaml`, `import_manifest.yaml`.
- If a consumer needs a graph viewer, require native graph materialization and endpoint/count smoke tests.
- `schema_id` format: `<workspace_id>:<entity_type>`.
- Graph edge labels: `UPPER_SNAKE_CASE`.
- Same `DATABASE_URL` for MCP server, migrations, and COPY ingestion.
- End each phase with a checkpoint (`ghostcrab_project`, `note_kind: "checkpoint"`).
- If GhostCrab is configured but not exposed in the current session, stay in diagnostic mode: do not claim MCP validation, do not freeze schemas, and label any proposed structure as documentary or provisional only.
- Never jump from a project label such as "site web", "client project", or "knowledge vault" straight to an ontology draft.
- When several ontology families seem plausible, propose the decomposition first, then the schemas.
- Always make validation status explicit: `diagnostic`, `provisional`, or `MCP-validated`.

## First-turn fuzzy onboarding

When the user's request is vague ("I want to model my vault", "set up GhostCrab for my project"):
- Ask 2–4 clarifying questions (one question mark each, no sub-questions).
- Do not write to GhostCrab or propose storage alternatives on the first turn.
- Do not jump directly to a domain ontology draft before consulting GhostCrab MCP live.
- Help the user decide whether the vault is best modeled as one ontology or as several ontology candidates sharing one workspace.
- Warn that folders alone do not define ontology boundaries.
- End with: `Probable view: <view-name> — <one-line benefit>. I can draft the next GhostCrab prompt once you've answered.`
