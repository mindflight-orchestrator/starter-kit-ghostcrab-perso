# GhostCrab MCP StarterKit — Codex Skill

**Trigger:** GhostCrab, mindBrain, ontology, vault ingestion, new GhostCrab project.

## How to use

1. Read `../EDITIONS.md`.
2. Resolve paths: `../personal-mcp/STARTERKIT_PATHS.md`
3. **Default:** `../personal-mcp/ROUTE_MAP.md` + `../personal-mcp/SOP_SEQUENCE.md` + `../personal-mcp/SKILL_ROUTE_MAP.md` (full matrix)
4. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`
5. Use SOP0–SOP6 **inside the chosen folder** + `../templates/` + `../scripts/`.
6. Never load the other edition folder on the same run.

## GhostCrab skills

```bash
gcp brain setup codex
```

- **Routine routing:** `~/.codex/skills/ghostcrab-shared/SKILL_ROUTE_MAP_ESSENTIALS.md`
- **Contracts:** `~/.codex/skills/ghostcrab-shared/` — enum facets `<module>.<slot_snake_case>` per `ENUM_BUSINESS_FACETS.md`; ingest facets per `PATH_CONTENT_FACETS.md`

## Rules

- personal-mcp (default): no mindCLI, no COPY, no `generate_copy_migrations.mjs`.
- pro-mcp: no `gcp brain structured-import` as sole bulk path; mindCLI for pragma audit.
- `ghostcrab_status` before modeling; `edition: personal-mcp` in `import_path_choices.yaml`.
- Multi-module LinkML or JSON ontology sources: require a project-local central ontology contract (`ontology/<workspace>-contract.yaml`) and run `starterkit/scripts/validate_ontology_json_vs_linkml.py` before any ontology import.

## Complete SOP set (each folder)

| SOP | personal-mcp | pro-mcp |
|-----|--------------|---------|
| SOP0–SOP6 | all in `personal-mcp/` | all in `pro-mcp/` |

Root stubs default to personal-mcp.
