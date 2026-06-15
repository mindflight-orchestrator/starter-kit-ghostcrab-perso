# GhostCrab MCP StarterKit — Claude Code Skill

**Trigger:** GhostCrab, mindBrain, ontology, vault ingestion, new GhostCrab project.

## Default: personal-mcp

1. Read `../EDITIONS.md`.
2. Resolve paths: `../personal-mcp/STARTERKIT_PATHS.md`
3. **Default:** `../personal-mcp/ROUTE_MAP.md` + `../personal-mcp/SOP_SEQUENCE.md` + `../personal-mcp/SKILL_ROUTE_MAP.md` (full matrix)
4. **Pro:** `../pro-mcp/ROUTE_MAP.md` + `../pro-mcp/SOP_SEQUENCE.md`
5. Load SOP0–SOP6 from the active folder only (not root stubs).

## GhostCrab skills

```bash
gcp brain setup claude
```

- **Routine routing:** `~/.claude/skills/ghostcrab-shared/SKILL_ROUTE_MAP_ESSENTIALS.md`
- **Contracts:** `~/.claude/skills/ghostcrab-shared/` — `ENUM_BUSINESS_FACETS.md`, `PATH_CONTENT_FACETS.md`, `SCHEMA_DESIGN.md`

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
