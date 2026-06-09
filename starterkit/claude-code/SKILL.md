# GhostCrab MCP StarterKit — Claude Code Skill

**Trigger:** GhostCrab, mindBrain, ontology, vault ingestion, new GhostCrab project.

## Default: personal-mcp

1. Read `../EDITIONS.md`.
2. **Default:** `../personal-mcp/ROUTE_MAP.md` + `../personal-mcp/SOP_SEQUENCE.md`
3. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`
4. Load SOP0–SOP6 from the active folder only (not root stubs).

## Key rules

- **Never mix tracks** on the same database.
- personal-mcp: `gcp` + MCP; no mindCLI, no COPY.
- pro-mcp: COPY + MCP + mindCLI audit; no `gcp brain structured-import` as sole bulk.
- Local `SOP2_obsidian_ontologie.md` in the edition folder.

## SOP index (complete per folder)

| Phase | personal-mcp | pro-mcp |
|-------|--------------|---------|
| A | SOP4 | SOP4 |
| B0 | SOP0 | SOP0 |
| B | SOP1 + SOP2 | SOP1 + SOP2 |
| C | SOP3 (opt.) + SOP6 | SOP3 + SOP6 (opt.) |
| C2 | SOP5 | SOP5 |
