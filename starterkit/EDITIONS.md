# GhostCrab editions — choose one track

**Default:** [personal-mcp/](personal-mcp/) — root stubs and [ROUTE_MAP.md](ROUTE_MAP.md) point here.

**Pro (independent):** [pro-mcp/](pro-mcp/) — complete SOP0–SOP6 + own [ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md).

Pick **one** edition before any SOP work. Do not mix operators across tracks.

| Edition | Route map | Sequence | Repo | Primary operators |
|---------|-----------|----------|------|-------------------|
| **personal-mcp** (default) | [personal-mcp/ROUTE_MAP.md](personal-mcp/ROUTE_MAP.md) | [SOP_SEQUENCE.md](personal-mcp/SOP_SEQUENCE.md) | `ghostcrab-personal-mcp` | `gcp brain ...` + MCP `ghostcrab_*` |
| **pro-mcp** | [pro-mcp/ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md) | [SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md) | `ghostcrab-mcp` + mindCLI | Docker Postgres + COPY + MCP + **mindCLI** |

---

## Quick matrix

| Question | personal-mcp | pro-mcp |
|----------|--------------|---------|
| Database | SQLite | PostgreSQL 17 + Docker + `DATABASE_URL` |
| Start MCP | `gcp brain up` | Docker stack + MCP |
| SOP3 | Vault parsing → SOP6 | Vault → COPY |
| SOP5 | `gcp brain structured-import` | Compiler + COPY |
| SOP6 | `gcp brain document` | Corpus docs → COPY + mindCLI |
| Formal ontology | `gcp brain ontology compile` | LinkML + SQL / DDL MCP |
| Projection audit | MCP `ghostcrab_pack` | mindCLI `mb_pragma` (+ MCP) |
| Forbidden cross-use | mindCLI, COPY, `DATABASE_URL` | `gcp brain structured-import` as sole bulk |

Each folder contains **all SOP0–SOP6** adapted to its runtime. Do not load the other edition's folder on the same database.

---

## Product reference (Personal)

Install GhostCrab skills first: `gcp brain setup <ide>` → shared contracts in `ghostcrab-shared/`.

| Topic | Primary source |
| ----- | -------------- |
| Onboarding / gates | `ghostcrab-shared/ONBOARDING_CONTRACT.md` |
| Schema design | `ghostcrab-shared/SCHEMA_DESIGN.md` |
| Enum facet naming | `ghostcrab-shared/ENUM_BUSINESS_FACETS.md` |
| Path/content ingest facets | `ghostcrab-shared/PATH_CONTENT_FACETS.md` |
| Artifact kinds | `ghostcrab-shared/ARTIFACT_KINDS.md` |
| Projection discovery | `ghostcrab-shared/PROJECTIONS_DISCOVERY.md` |
| Operator surface | `ghostcrab-shared/CAPABILITIES.md` |
| Phase × skill (short) | `ghostcrab-shared/SKILL_ROUTE_MAP_ESSENTIALS.md` |
| Path resolution (full) | `ghostcrab-shared/STARTERKIT_PATHS.md` or [personal-mcp/STARTERKIT_PATHS.md](personal-mcp/STARTERKIT_PATHS.md) |

Optional deep docs (GitHub): [ghostcrab-personal-mcp](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp) — glossary, operator catalog, ontology hub, MECE lab example.

---

## Entry flow for agents

1. **Default:** open [personal-mcp/ROUTE_MAP.md](personal-mcp/ROUTE_MAP.md) + [personal-mcp/SOP_SEQUENCE.md](personal-mcp/SOP_SEQUENCE.md).
2. **Pro only:** open [pro-mcp/ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md) + [pro-mcp/SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md) — do not use root stubs as checklist.
3. [QUICKSTART.md](QUICKSTART.md) — router only.
