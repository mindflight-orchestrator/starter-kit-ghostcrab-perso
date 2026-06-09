# GhostCrab MCP StarterKit — Claude Code Entrypoint

## Default: personal-mcp

1. Read `../EDITIONS.md` (Pro only if user asks)
2. **Default load:**
   - `../personal-mcp/ROUTE_MAP.md`
   - `../personal-mcp/SOP_SEQUENCE.md`
3. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`

Do not mix operators between tracks.

## Execute sequence

Follow the chosen folder's `SOP_SEQUENCE.md` from Phase A through C/C2. Load SOP0–SOP6 **only from that folder** (not root stubs, not the other edition).

**Phase B0:** local `SOP0` + `../templates/import_path_choices.yaml`

**Ontology:** local `SOP2_obsidian_ontologie.md` in the active edition folder.

## Templates

`../templates/` — set `edition` in `import_manifest.yaml`
