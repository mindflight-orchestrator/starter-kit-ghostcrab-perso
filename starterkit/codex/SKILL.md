# GhostCrab MCP StarterKit — Codex Skill

**Trigger:** GhostCrab, mindBrain, ontology, vault ingestion, new GhostCrab project.

## How to use

1. Read `../EDITIONS.md`.
2. **Default:** `../personal-mcp/ROUTE_MAP.md` + `../personal-mcp/SOP_SEQUENCE.md`
3. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`
4. Use SOP0–SOP6 **inside the chosen folder** + `../templates/` + `../scripts/`.
5. Never load the other edition folder on the same run.

## Rules

- personal-mcp (default): no mindCLI, no COPY, no `generate_copy_migrations.mjs`.
- pro-mcp: no `gcp brain structured-import` as sole bulk path; mindCLI for pragma audit.
- `ghostcrab_status` before modeling; `edition` in `import_manifest.yaml`.

## Complete SOP set (each folder)

| SOP | personal-mcp | pro-mcp |
|-----|--------------|---------|
| SOP0–SOP6 | all in `personal-mcp/` | all in `pro-mcp/` |

Root stubs default to personal-mcp.
