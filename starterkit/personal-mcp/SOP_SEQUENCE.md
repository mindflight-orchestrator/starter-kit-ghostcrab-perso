# personal-mcp — Canonical SOP sequence

**Edition:** GhostCrab Personal — `ghostcrab-personal-mcp`, SQLite, **`gcp`** + MCP **`ghostcrab_*`**.

**Route map:** [ROUTE_MAP.md](ROUTE_MAP.md)

**Skill route map:** [SKILL_ROUTE_MAP.md](SKILL_ROUTE_MAP.md) — which GhostCrab skill to invoke at each SOP phase.

**Do not use:** mindCLI, PostgreSQL COPY, `../pro-mcp/`, `generate_copy_migrations.mjs`.

**Path resolution:** [STARTERKIT_PATHS.md](STARTERKIT_PATHS.md)

**Product references:**

| Doc | Source |
|-----|--------|
| Skill route map (this kit) | [SKILL_ROUTE_MAP.md](SKILL_ROUTE_MAP.md) |
| IDE skills install | `gcp brain setup cursor\|claude\|codex\|generic` → `ghostcrab-shared/` |
| Phase × skill (condensed) | `ghostcrab-shared/SKILL_ROUTE_MAP_ESSENTIALS.md` |
| Enum facet naming | `ghostcrab-shared/ENUM_BUSINESS_FACETS.md` |
| Operator surface | `ghostcrab-shared/CAPABILITIES.md` |
| Optional deep docs | [ghostcrab-personal-mcp on GitHub](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp) |

---

## How to use

1. Phases **in order** (A → B0 → B → **B1** → **B1.5** → **B2** → C / C2).
2. Load **only** files in this folder + `../templates/` + `../scripts/`.
3. `edition: personal-mcp` in `../templates/import_manifest.yaml`.
4. Match each phase to GhostCrab skills via [SKILL_ROUTE_MAP.md](SKILL_ROUTE_MAP.md) (`gcp brain setup cursor|claude|codex|generic` for install).

```mermaid
flowchart LR
  A[Phase A SOP4]
  B0[Phase B0 SOP0]
  B[Phase B SOP1+SOP2]
  B1[Phase B1 projections]
  B15[Phase B1.5 business rules]
  B2[Phase B2 fake-data]
  C3[Phase C opt SOP3]
  C6[Phase C SOP6]
  C2[Phase C2 SOP5]
  A --> B0 --> B --> B1 --> B15 --> B2
  B2 --> C3 --> C6
  B2 --> C6
  B2 --> C2
```

---

## Phase A — Environment

| Step | Document | Operator | Done when |
|------|----------|----------|-----------|
| A | [SOP4](SOP4_environment_bootstrap.md) | `gcp smoke`, `gcp brain up`, `ghostcrab_status` | SQLite OK, tools visible |
| — | [../EDITIONS.md](../EDITIONS.md) | read once | edition confirmed |

---

## Phase B0 — Import path choices

| Step | Document | Done when |
|------|----------|-----------|
| B0 | [SOP0](SOP0_import_path_choices.md) | `../templates/import_path_choices.yaml` filled |

---

## Phase B — Model workspace

| Step | Document | Done when |
|------|----------|-----------|
| B | [SOP1](SOP1_ghostcrab_mcp.md) | baseline `ghostcrab_coverage` |
| B | [SOP2](SOP2_obsidian_ontologie.md) | contracts + LinkML or MCP path |
| B ontology | SOP2 §6 bis + `../templates/linkml_ontology.stub.yaml` | `ontology_*` ready |

---

## Phase B1 — Projections (prepare + materialize)

| Step | Document / tool | Done when |
|------|-------------------|-----------|
| B1 prep | [ROUTE_MAP § projections](ROUTE_MAP.md#route-projections), [../scripts/README_projection_tools.md](../scripts/README_projection_tools.md) | `projection_model_validation.md` reviewed — broad `manager_questions` and focused `manager_question_cluster` rows accepted/rejected; `artifact_kind` + `proj_type` confirmed |
| B1 write | SOP2 §7.6–7.7, `ghostcrab_project` | `analysis_plan` scopes declared; optional `live_answer_view` seed |
| B1 audit (post-import) | `audit_ghostcrab_projections.py`, SOP5 gate 7 | pack + projection_get smoke OK; refresh stale `live_answer_view` if seeded |

---

## Phase B1.5 — Business rules catalog

| Step | Document / tool | Done when |
|------|-------------------|-----------|
| B1.5 | [SOP_business_rules_catalog.md](SOP_business_rules_catalog.md), [../templates/business_rules_catalog.yaml](../templates/business_rules_catalog.yaml) | `rules/business_rules_catalog.yaml` confirmed; critical rules linked to ontology refs, assertions, and smoke/mini/scale scenarios |

Do not start B2 fake-data generation until this catalog exists or the absence of business rules is explicitly documented in `import_path_choices.yaml`.

---

## Phase B2 — Fake business data (before first bulk import)

| Step | Document / tool | Done when |
|------|-------------------|-----------|
| B2 | [ROUTE_MAP § fake-data](ROUTE_MAP.md#route-donnees-fictives-metier), [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md) | `import_ready/` + gates 2–4 dry-run OK |
| B2 gates | `profile_source.mjs`, `validate_mapping_contract.mjs`, `transform_source_to_jsonb.mjs` | JSONL preview clean |

Skip B2 only when real tabular sources are already validated (document in `import_path_choices.yaml`).

---

## Phase C — Vault prep (optional)

| Step | Document | Done when |
|------|----------|-----------|
| C (opt.) | [SOP3](SOP3_parsing_pipeline.md) | JSONB validated, route to SOP6 chosen |

---

## Phase C — Documents

| Step | Document | Done when |
|------|----------|-----------|
| C | [SOP6](SOP6_gcp_document_import.md) | `gcp brain document` pipeline OK |

---

## Phase C2 — Tabular import

| Step | Document | Done when |
|------|----------|-----------|
| C2 | [SOP5](SOP5_structured_import.md) | structured-import + consumers |

---

## Phase audit

| Step | Document | Done when |
|------|----------|-----------|
| 9 | SOP5 + projections audit + `../templates/import_manifest.yaml` | `audit_ghostcrab_projections.py`, `audit_import_pipeline.mjs`, MCP consumers |

---

## SOP index (complete — this folder)

| SOP | File | Phase |
|-----|------|-------|
| SOP0 | [SOP0_import_path_choices.md](SOP0_import_path_choices.md) | B0 |
| SOP1 | [SOP1_ghostcrab_mcp.md](SOP1_ghostcrab_mcp.md) | B |
| SOP2 | [SOP2_obsidian_ontologie.md](SOP2_obsidian_ontologie.md) | B |
| Business rules | [SOP_business_rules_catalog.md](SOP_business_rules_catalog.md) | B1.5 |
| SOP3 | [SOP3_parsing_pipeline.md](SOP3_parsing_pipeline.md) | C (opt.) |
| SOP4 | [SOP4_environment_bootstrap.md](SOP4_environment_bootstrap.md) | A |
| SOP5 | [SOP5_structured_import.md](SOP5_structured_import.md) | C2 |
| SOP6 | [SOP6_gcp_document_import.md](SOP6_gcp_document_import.md) | C |

Root `../SOP*.md` stubs default here. Pro track: [../pro-mcp/SOP_SEQUENCE.md](../pro-mcp/SOP_SEQUENCE.md).
