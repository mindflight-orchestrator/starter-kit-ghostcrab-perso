# GhostCrab MCP StarterKit — Claude Code Entrypoint

## Default: personal-mcp

1. Read `../EDITIONS.md` (Pro only if user asks)
2. Resolve paths: `../personal-mcp/STARTERKIT_PATHS.md`
3. **Default load:**
   - `../personal-mcp/ROUTE_MAP.md`
   - `../personal-mcp/SOP_SEQUENCE.md`
   - `../personal-mcp/SKILL_ROUTE_MAP.md`
4. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`

Do not mix operators between tracks.

## GhostCrab skills (product)

```bash
gcp brain setup claude
```

Contracts: `~/.claude/skills/ghostcrab-shared/`. Skills replaced on each setup.

- **Routine routing:** `ghostcrab-shared/SKILL_ROUTE_MAP_ESSENTIALS.md`
- **Full matrix:** `../personal-mcp/SKILL_ROUTE_MAP.md`

## Execute sequence

Follow the chosen folder's `SOP_SEQUENCE.md` from Phase A through C/C2. Load SOP0–SOP6 **only from that folder** (not root stubs, not the other edition).

**Phase B0:** local `SOP0` + `../templates/import_path_choices.yaml`

**Ontology:** local `SOP2_obsidian_ontologie.md` in the active edition folder. Business enum facets: `<module>.<slot_snake_case>` per `ghostcrab-shared/ENUM_BUSINESS_FACETS.md`.

## Templates

`../templates/` — set `edition: personal-mcp` in `import_path_choices.yaml` and `import_manifest.yaml`
