# GhostCrab MCP StarterKit — Claude Code Entrypoint

## Runner contract

Read `../core/MINDBRAIN_PROJECT_RUNNER.md` and
`../core/gates/project_run_checklist.yaml` before starting a new GhostCrab /
MindBrain workspace. This file is only the Claude Code adapter; the shared
runner is the source of truth for hard gates.

Before declaring completion, run:

```bash
python ../scripts/validate_mindbrain_project.py \
  --project <project-dir> \
  --workspace <workspace-id> \
  --edition <personal-mcp|pro-mcp>
```

For GhostCrab Pro, include the projection audit JSON with `--projection-audit`.

## Default: personal-mcp

1. Read `../EDITIONS.md` (Pro only if user asks)
2. **Default load:**
   - `../personal-mcp/ROUTE_MAP.md`
   - `../personal-mcp/SOP_SEQUENCE.md`
3. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`

Do not mix operators between tracks.

## Execute sequence

Follow the chosen folder's `SOP_SEQUENCE.md` from Phase A through C/C2 and audit. SOP0–SOP6 are the main operational SOPs, but not the whole workflow. Also load the transverse SOPs when reached: business rules B1.5, projection test data B2.5, and review finalisation.

**Phase B0:** local `SOP0` + `../templates/import_path_choices.yaml`

**Ontology:** local `SOP2_obsidian_ontologie.md` in the active edition folder.

**Business validation gates:**

- B1 projections before fake-data.
- B1.5 `SOP_business_rules_catalog.md` before fake-data scenarios.
- B2.5 `SOP_projection_test_data_levels.md` before manager snapshot validation.
- Review dossier before declaring the model ready for human validation.

## Templates

`../templates/` — set `edition` in `import_manifest.yaml`
