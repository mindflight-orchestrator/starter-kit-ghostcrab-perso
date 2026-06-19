# GhostCrab StarterKit — QUICKSTART (router)

**Default edition: personal-mcp.** Pro is independent under `pro-mcp/`.

---

## Default path (personal-mcp)

1. [personal-mcp/ROUTE_MAP.md](personal-mcp/ROUTE_MAP.md) — full workflow route
2. [personal-mcp/SOP_SEQUENCE.md](personal-mcp/SOP_SEQUENCE.md) — canonical checklist

Root `SOP*.md` stubs point here by default.

Do not treat SOP0–SOP6 as the complete project sequence. The Personal workflow
also includes mandatory transverse phases when applicable:

- B1.5 — [business rules catalog](personal-mcp/SOP_business_rules_catalog.md)
- B2.5 — [projection test data levels](personal-mcp/SOP_projection_test_data_levels.md)
- Review — [finalisation dossier](personal-mcp/SOP_review_finalisation_dossier.md)

---

## Pro path (explicit choice)

Read [EDITIONS.md](EDITIONS.md), then:

- [pro-mcp/ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md)
- [pro-mcp/SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md)

Never mix `gcp` bulk operators with Pro COPY/mindCLI on the same database.

---

## Clone

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
├── ROUTE_MAP.md         ← stub → personal-mcp/
├── personal-mcp/        ← DEFAULT (SOP_SEQUENCE + SOP0–SOP6 + transverse SOPs)
├── pro-mcp/             ← Pro only (SOP_SEQUENCE + SOP0–SOP6)
├── templates/
└── scripts/
```

---

## Global modeling gate

- `ghostcrab_*` tools visible in session; call `ghostcrab_status` before modeling.
- LinkML (`gcp brain ontology compile`) ≠ `ghostcrab_schema_register` (`ghostcrab:*`) on Personal.

---

## IDE entrypoints

| Agent | Default load |
|-------|----------------|
| Claude Code | `claude-code/CLAUDE.md` |
| Cursor | `cursor/starterkit.mdc` |
| Codex | `codex/SKILL.md` |
