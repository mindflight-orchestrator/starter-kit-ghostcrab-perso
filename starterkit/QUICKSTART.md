# GhostCrab StarterKit — QUICKSTART (router)

**Default edition: personal-mcp.** Pro is independent under `pro-mcp/`.

---

## Default path (personal-mcp)

1. [personal-mcp/STARTERKIT_PATHS.md](personal-mcp/STARTERKIT_PATHS.md) — resolve `{starterkit}` and `{project}`
2. [personal-mcp/ROUTE_MAP.md](personal-mcp/ROUTE_MAP.md) — full route SOP 0→6
3. [personal-mcp/SOP_SEQUENCE.md](personal-mcp/SOP_SEQUENCE.md) — canonical checklist
4. [personal-mcp/SKILL_ROUTE_MAP.md](personal-mcp/SKILL_ROUTE_MAP.md) — which GhostCrab skill per phase

Root `SOP*.md` stubs point here by default.

**Skills (product):** `npm install -g @mindflight/ghostcrab-personal-mcp@0.5.0` then `gcp brain setup cursor|claude|codex|generic`.

---

## Pro path (explicit choice)

Read [EDITIONS.md](EDITIONS.md), then:

- [pro-mcp/ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md)
- [pro-mcp/SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md)

Never mix `gcp` bulk operators with Pro COPY/mindCLI on the same database.

---

## Clone

```bash
git clone git@github.com:mindflight-orchestrator/starter-kit-ghostcrab-perso.git
```

| Edition | Product package |
|---------|-----------------|
| personal-mcp (default) | `@mindflight/ghostcrab-personal-mcp` |
| pro-mcp | `ghostcrab-mcp` |

---

## Layout

```text
starterkit/
├── EDITIONS.md
├── ROUTE_MAP.md         ← stub → personal-mcp/
├── personal-mcp/        ← DEFAULT (SOP0–SOP6)
├── pro-mcp/             ← Pro only (SOP0–SOP6)
├── templates/
└── scripts/
```

---

## Global modeling gate

- `ghostcrab_*` tools visible in session; call `ghostcrab_status` before modeling.
- LinkML (`gcp brain ontology compile`) ≠ `ghostcrab_schema_register` (`ghostcrab:*`) on Personal.
- Business enum facets: `<module>.<slot_snake_case>` — see installed `ghostcrab-shared/ENUM_BUSINESS_FACETS.md`.

---

## IDE entrypoints

| Agent | Default load |
|-------|----------------|
| Claude Code | `claude-code/CLAUDE.md` |
| Cursor | `cursor/starterkit.mdc` |
| Codex | `codex/SKILL.md` |
