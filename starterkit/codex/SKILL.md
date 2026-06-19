# GhostCrab MCP StarterKit — Codex Skill

**Trigger:** GhostCrab, mindBrain, ontology, vault ingestion, new GhostCrab project.

## How to use

1. Read `../EDITIONS.md`.
2. **Default:** `../personal-mcp/ROUTE_MAP.md` + `../personal-mcp/SOP_SEQUENCE.md`
3. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`
4. Use the chosen folder's `SOP_SEQUENCE.md` as the source of truth. SOP0–SOP6 are not sufficient by themselves; transverse SOPs such as business rules, projection test data and review finalisation are mandatory when their phase appears.
5. Never load the other edition folder on the same run.

## Expected work spine

Follow this spine for any new GhostCrab / MindBrain workspace, unless the user explicitly asks for a narrower repair. Open the referenced SOP / README before writing artifacts for that phase.

| Order | Phase | Agent must answer | Read first | Expected artifact / gate |
|-------|-------|-------------------|------------|--------------------------|
| 0 | A environment | Which runtime, DB and workspace are targeted? | `SOP4` + `EDITIONS.md` | `ghostcrab_status` OK; DB/workspace explicit |
| 1 | B0 import path | Which route applies: LinkML, MCP incremental, structured import, documents, API? | `SOP0` | `import_path_choices.yaml` filled |
| 2 | B model | Which classes, facets, edges, LinkML modules, schemas, import paths and source contracts are required? | `SOP1`, `SOP2` | model contract + LinkML/MCP schema path validated |
| 3 | B1 projections | Which manager questions must be answerable, and through which proof chains? | `ROUTE_MAP` route projections + `../scripts/README_projection_tools.md` | `projection_model_validation.md`; `artifact_kind` and `proj_type` confirmed |
| 4 | B1.5 business rules | Which assertions, calculations, transitions, deadlines, forbidden states and evidence chains complete those projections? | `SOP_business_rules_catalog.md` | `rules/business_rules_catalog.yaml` + rule-to-projection coverage matrix |
| 5 | B2 fake-data | Which scenarios prove the questions and rules, including edge cases and exceptions? | `../scripts/README_fake_business_data.md` | `fake_data/`, `import_ready/`, dry-run gates clean |
| 6 | B2.5 projection test data | Which manager snapshots, claims, evidence entities, edges and assertions prove the answers? | `SOP_projection_test_data_levels.md` | `manager_answer_snapshots.*` + `snapshot_claims_evidence_matrix.*` |
| 7 | Review finalisation | Which documents need human validation, in which order? | `SOP_review_finalisation_dossier.md` | `finalisation/<ws>/current/00_INDEX.md` and optional review round |
| 8 | Import | Which import path applies for this edition and source type? | `SOP5` for tabular, `SOP3`/`SOP6` for vault/docs | apply/import/reindex completed against the active DB |
| 9 | Post-import audit | Do projections and snapshots really answer through current facts, graph, facets and artifacts? | projection audit route + import gates | search, pack, combined search, projection_get, artifact audit OK |

Do not jump from ontology work directly to fake-data or import. B1, B1.5 and B2.5 are gates: fake-data must cover selected business questions, business rules, and manager-oriented answer evidence.

## Rules

- personal-mcp (default): no mindCLI, no COPY, no `generate_copy_migrations.mjs`.
- pro-mcp: no `gcp brain structured-import` as sole bulk path; mindCLI for pragma audit.
- `ghostcrab_status` before modeling; `edition` in `import_manifest.yaml`.

## Complete SOP set and transverse SOPs

| Family | personal-mcp | pro-mcp |
|-----|--------------|---------|
| Main SOP0–SOP6 | all in `personal-mcp/` | all in `pro-mcp/` |
| Business rules | `personal-mcp/SOP_business_rules_catalog.md` | phase B1.5 in `pro-mcp/SOP_SEQUENCE.md` |
| Projection test data | `personal-mcp/SOP_projection_test_data_levels.md` | phase B2.5 in `pro-mcp/SOP_SEQUENCE.md` |
| Review finalisation | `personal-mcp/SOP_review_finalisation_dossier.md` | use equivalent review phase when added |

Root stubs default to personal-mcp.
