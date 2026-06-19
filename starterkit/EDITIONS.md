# GhostCrab editions — choose one track

**Default:** [personal-mcp/](personal-mcp/) — root stubs and [ROUTE_MAP.md](ROUTE_MAP.md) point here.

**Pro (independent):** [pro-mcp/](pro-mcp/) — own [SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md) + [ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md).

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

Each folder contains a runtime-specific `SOP_SEQUENCE.md`. SOP0–SOP6 are the
main operational SOPs, but transverse phases such as business rules, projection
test data and finalisation review must also be followed when listed by the
sequence. Do not load the other edition's folder on the same database.

---

## Product docs (Personal — sibling clone)

| Doc | Path (from `mindflight/` parent) |
|-----|----------------------------------|
| Glossary | `ghostcrab-personal-mcp/docs/explanation/glossary.md` |
| Operator catalog | `ghostcrab-personal-mcp/docs/reference/operator-catalog.md` |
| Ontology LinkML/OWL2 | `ghostcrab-personal-mcp/docs/explanation/ontology/README.md` |
| MECE lab example | `ghostcrab-personal-mcp/examples/ghostcrab-docs/import_path_choices.yaml` |

---

## Entry flow for agents

1. **Default:** open [personal-mcp/ROUTE_MAP.md](personal-mcp/ROUTE_MAP.md) + [personal-mcp/SOP_SEQUENCE.md](personal-mcp/SOP_SEQUENCE.md).
2. **Pro only:** open [pro-mcp/ROUTE_MAP.md](pro-mcp/ROUTE_MAP.md) + [pro-mcp/SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md) — do not use root stubs as checklist.
3. [QUICKSTART.md](QUICKSTART.md) — router only.
