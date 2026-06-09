# SOP 6 — Document import via `gcp brain document` (Personal)

**Version:** 0.1  
**Statut:** Draft exploitable  
**Perimetre:** Corpus PDF/HTML/Markdown → MindBrain SQLite via GhostCrab Personal.

> **Edition: personal-mcp only.** Pro vault COPY → [../pro-mcp/SOP3_parsing_pipeline.md](../pro-mcp/SOP3_parsing_pipeline.md). No mindCLI on this SOP.

---

## Objectif

Ingest unstructured documents after Phase B ontology (LinkML) or MCP schemas exist. This SOP is the StarterKit companion to the product runbook:

→ [`ghostcrab-personal-mcp` document-import.md](https://gitlab.com/webigniter/ghostcrab-personal-mcp/-/blob/main/docs/setup/document-import.md)

---

## Prerequisites

- Phase A complete (`ghostcrab_status` OK)
- LinkML slice imported when using `document-qualify` taxonomies (`gcp brain ontology compile --import-db`)
- **Stop MCP** before database-backed `gcp brain document` subcommands

---

## Gates (minimal)

| Gate | Command / check | Impact |
|------|-----------------|--------|
| 0 | `ghostcrab_status` | workspace + SQLite path |
| 1 | `document-normalize` | files on disk |
| 2 | `document-profile` or worker queue | LLM or deterministic profile |
| 3 | `document-ingest` | `documents_raw`, `chunks_raw` |
| 4 | `qualification-vocab-list` | read `ontology_*` |
| 5 | `document-qualify` | `facet_assignments_raw` |
| 6 | `ghostcrab_collection_reindex` or engine reindex | search + graph derivation |
| 7 | `consumer_contract.yaml` | MCP smoke |

---

## Example commands

```bash
gcp brain document document-normalize --input ./paper.pdf --output-dir ./out
gcp brain document document-qualify \
  --workspace-id my_ws --collection-id my_ws::docs \
  --taxonomies my_ws::core --facets topic.category
```

Full catalogue: product [`operator-catalog.md`](https://gitlab.com/webigniter/ghostcrab-personal-mcp/-/blob/main/docs/reference/operator-catalog.md).

---

## Relation SOP2 / SOP3

- **SOP2 LinkML** supplies taxonomies for qualification (formal ontology — not `ghostcrab:note` schemas).
- **SOP3** prepares vault parsing before bulk [SOP6](SOP6_gcp_document_import.md).
- **COPY PostgreSQL** is out of scope on Personal.
