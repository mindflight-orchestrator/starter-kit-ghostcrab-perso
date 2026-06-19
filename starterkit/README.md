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
├── personal-mcp/            # DEFAULT — SOP_SEQUENCE + SOP0–SOP6 + transverse SOPs
├── pro-mcp/                 # INDEPENDENT — SOP_SEQUENCE + SOP0–SOP6
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

`SOP_SEQUENCE.md` is the canonical checklist. Do not stop at SOP0–SOP6 when the
workflow reaches business rules, projection test data, finalisation review,
snapshots or scenario comparison.

## Canonical workflow summary

| Phase | Goal | Main output |
|---|---|---|
| A | Verify runtime and DB | `ghostcrab_status` OK |
| B0 | Choose import routes | `import_path_choices.yaml` |
| B | Model ontology/schemas | contract, LinkML, schemas/facets |
| B1 | Identify business questions/projections | `projection_model_validation.md`, `projection_catalog.yaml` |
| B1.5 | Normalize business rules | `rules/business_rules_catalog.yaml` |
| B2 | Generate fake/real test data | `fake_data/`, `import_ready/`, coverage reports |
| B2.5 | Test manager answers and evidence | snapshots + claims/evidence/assertions matrix |
| Review | Human supervision dossier | `finalisation/<ws>/current/00_INDEX.md` |
| C/C2 | Import and reindex | structured/document import manifest |
| Audit | Validate answers | projection and snapshot audit reports |

---

## Product docs (personal-mcp)

Sibling clone `ghostcrab-personal-mcp`: glossary, [operator-catalog](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp/blob/main/docs/reference/operator-catalog.md), ontology hub, setup runbooks.
