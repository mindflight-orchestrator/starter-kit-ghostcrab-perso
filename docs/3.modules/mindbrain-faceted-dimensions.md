# Faceted Dimensions

Objects exist at typed coordinates, not in a flat tag cloud.

Facets are the dimensions that make GhostCrab and mindBrain queryable: status, priority, owner, domain, jurisdiction, source, environment, and other stable attributes.

---

## Dimensions vs tags

Tags search. Dimensions navigate.

A tag system answers: *"find everything tagged compliance."* You get a list and then filter it yourself.

A faceted system answers: *"how many compliance tasks are blocked, grouped by priority?"* The backend can count by registered dimensions directly.

The difference is architectural. Tags are loose annotations. Dimensions are typed coordinates in a model.

---

## Common dimension types

| Type | Use for | Examples |
|---|---|---|
| `enum` | Controlled state or category | `todo`, `blocked`, `done` |
| `string` | Names, ids, codes | `GDPR Art. 32`, `team-alpha` |
| `integer` | Counts or ordinal values | `0`, `42` |
| `float` | Scores, percentages, weights | `0.87`, `3.14` |
| `date` | Calendar dates | `2026-05-01` |
| `datetime` | Timestamps | `2026-05-01T09:00:00Z` |
| `boolean` | Binary flags | `true`, `false` |
| `json` | Flexible metadata | `{"source":"odoo"}` |
| `vector` | Semantic proximity when enabled | embedding arrays |

Use the strictest dimension that matches the data. An enum is better than a free string when the values are known.

---

## Querying facets through MCP

For agents, the canonical query surface is MCP.

Search records with filters:

```json
{
  "tool": "ghostcrab_search",
  "arguments": {
    "workspace_id": "compliance",
    "schema_id": "ghostcrab:task",
    "filters": {
      "status": "blocked",
      "domain": "compliance"
    },
    "limit": 20,
    "mode": "bm25"
  }
}
```

Count records grouped by a dimension:

```json
{
  "tool": "ghostcrab_count",
  "arguments": {
    "workspace_id": "compliance",
    "schema_id": "ghostcrab:task",
    "filters": {
      "status": "blocked"
    },
    "group_by": ["priority"]
  }
}
```

Combine facets with graph traversal when the graph tool is available:

```json
{
  "tool": "ghostcrab_traverse",
  "arguments": {
    "workspace_id": "compliance",
    "start": "task:gdpr-art32",
    "edge_labels": ["assigned_to"],
    "depth": 1
  }
}
```

---

## Querying facets through mindCLI

In Pro/operator workflows, mindCLI can expose equivalent deterministic commands or query templates:

```bash
mindcli pg query \
  --template blocked_tasks_by_priority \
  --workspace compliance \
  --format json
```

For high-volume source data, prefer batch ingestion and sync:

```bash
mindcli odoo ingest \
  --workspace compliance \
  --entity project.task \
  --batch-size 500
```

Do not model bulk ingestion as repeated MCP calls when a deterministic ingestion channel exists.

---

## Vector and hybrid search

Vector dimensions and hybrid search are optional capabilities. They are useful when semantic similarity is truly part of the query, such as finding documents similar to "data encryption at rest."

Model as `enum` when:

- values are finite and known;
- exact filtering matters;
- deterministic counts are more important than similarity.

Model as vector or hybrid search when:

- content is free-form;
- similarity is the actual retrieval need;
- the runtime reports embeddings/vector readiness.

Perso may run with BM25-only retrieval or embeddings disabled depending on configuration. Pro can expose stronger native and hybrid paths when readiness checks pass. Use `ghostcrab_status` to see the real mode.

---

## Performance guidance

Performance depends on backend, indexes, data shape, query mix, and native readiness.

| Backend | Good fit | Notes |
|---|---|---|
| SQLite Perso | Local agents, small to medium personal graphs, starter workflows | Fast enough for local work; avoid treating it as a shared high-concurrency server |
| PostgreSQL Pro | Concurrent agents, governed workspaces, larger datasets, native graph/facet workloads | Can use `pg_facets`, `pg_dgraph`, `pg_pragma`, and `pg_mindbrain` when ready |
| Pro with mindCLI | Batch ingest, sync, migrations, query templates | Better fit than MCP for high-volume deterministic operations |

Any fixed latency table is illustrative only. Benchmark with your real workload.

---

## Modeling tips

- Keep status-like values as enums.
- Use stable ids such as `record_id` for upsert matching.
- Put day-to-day state on current-state records, not only in notes.
- Use graph edges for real relations such as `blocks`, `requires`, `assigned_to`, and `validated_by`.
- Add vector fields only when semantic similarity is part of the user story.

---

## Next step

Connect faceted objects with graph relations:

[Semantic Graph](../2.concepts/2.3.semantic-graph.md)

For local setup, see:

[Installation](../0.installation/0.1.mindbrain-installation.md)
