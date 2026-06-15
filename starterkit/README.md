# GhostCrab StarterKit

Companion kit for GhostCrab MCP. **Default edition: personal-mcp.** Pro is a separate independent folder.

---

## Start here

1. [EDITIONS.md](EDITIONS.md) — confirm `personal-mcp` (default) or switch to `pro-mcp`
2. **Default:** [personal-mcp/STARTERKIT_PATHS.md](personal-mcp/STARTERKIT_PATHS.md) → [personal-mcp/ROUTE_MAP.md](personal-mcp/ROUTE_MAP.md) + [personal-mcp/SOP_SEQUENCE.md](personal-mcp/SOP_SEQUENCE.md) + [personal-mcp/SKILL_ROUTE_MAP.md](personal-mcp/SKILL_ROUTE_MAP.md)
3. **Pro:** [pro-mcp/ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md) + [pro-mcp/SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md)
4. [QUICKSTART.md](QUICKSTART.md) — short router

```bash
git clone git@github.com:mindflight-orchestrator/starter-kit-ghostcrab-perso.git
cd <your-clone>
```

Record the clone root in `{project}/.ghostcrab/starterkit-root` or set `GHOSTCRAB_STARTERKIT_ROOT` when the delivery project is not the clone itself.

| Edition | Product package |
|---------|-----------------|
| personal-mcp (default) | `@mindflight/ghostcrab-personal-mcp` |
| pro-mcp | `ghostcrab-mcp` |

After installing the product: `gcp brain setup cursor|claude|codex|generic` — skills and `ghostcrab-shared/` contracts.

---

## Layout

```text
starterkit/
├── EDITIONS.md
├── ROUTE_MAP.md           ← stub → personal-mcp/ROUTE_MAP.md
├── QUICKSTART.md
├── templates/             # shared YAML (set edition:)
├── scripts/               # shared gate scripts
├── personal-mcp/            # DEFAULT — SOP0–SOP6 + ROUTE_MAP + STARTERKIT_PATHS
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

Default load path: `personal-mcp/SOP_SEQUENCE.md` + `personal-mcp/SKILL_ROUTE_MAP.md`. Pro: explicit `pro-mcp/` folder.

---

## Product reference (personal-mcp)

Runtime contracts: install skills → `ghostcrab-shared/` (`ONBOARDING_CONTRACT.md`, `ENUM_BUSINESS_FACETS.md`, `CAPABILITIES.md`, …).

Optional human docs: [ghostcrab-personal-mcp](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp) (operator catalog, ontology hub, MECE lab).
