# GhostCrab StarterKit

Companion kit for GhostCrab MCP. **Default edition: personal-mcp.** Pro is a separate independent folder.

---

## Start here

1. [EDITIONS.md](EDITIONS.md) — confirm `personal-mcp` (default) or switch to `pro-mcp`
2. **Default:** [personal-mcp/ROUTE_MAP.md](personal-mcp/ROUTE_MAP.md) + [personal-mcp/SOP_SEQUENCE.md](personal-mcp/SOP_SEQUENCE.md)
3. **Pro:** [pro-mcp/ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md) + [pro-mcp/SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md)
4. [QUICKSTART.md](QUICKSTART.md) — short router

```bash
git clone git@github.com:mindflight-orchestrator/starter-kit-ghostcrab-perso.git ~/mindbrain-starterkit
```

| Edition | Product repo |
|---------|----------------|
| personal-mcp (default) | `ghostcrab-personal-mcp` |
| pro-mcp | `ghostcrab-mcp` |

---

## Layout

```text
starterkit/
├── EDITIONS.md
├── ROUTE_MAP.md           ← stub → personal-mcp/ROUTE_MAP.md
├── QUICKSTART.md
├── templates/             # shared YAML (set edition:)
├── scripts/               # shared gate scripts
├── personal-mcp/            # DEFAULT — SOP0–SOP6 + ROUTE_MAP
├── pro-mcp/                 # INDEPENDENT — SOP0–SOP6 + ROUTE_MAP
├── shared/SOP2_...          # stub → personal-mcp/SOP2
└── SOP*.md                  # stubs → personal-mcp/* by default
```

---

## IDE entrypoints

| Agent | File |
|-------|------|
| Codex | `codex/SKILL.md` |
| Cursor | `cursor/starterkit.mdc` |
| Claude Code | `claude-code/CLAUDE.md` |

Default load path: `personal-mcp/SOP_SEQUENCE.md`. Pro: explicit `pro-mcp/` folder.

---

## Product docs (personal-mcp)

Sibling clone `ghostcrab-personal-mcp`: glossary, [operator-catalog](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp/blob/main/docs/reference/operator-catalog.md), ontology hub, setup runbooks.
