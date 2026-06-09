# SOP 0 — Import path choices (pro-mcp)

**Edition:** pro-mcp only. Voir [EDITIONS.md](../EDITIONS.md) pour changer de piste.

Fill [`../templates/import_path_choices.yaml`](../templates/import_path_choices.yaml) with `edition: pro-mcp`.

---

## Defaults

```yaml
edition: pro-mcp
ontology_path: linkml_or_sql
ontology_path_alt: mcp_incremental
tabular_path: sop5_voie_a_copy
document_path: sop3_copy   # vault; optional flat corpus → SOP6
projection_audit: mindcli
```

**Forbidden as sole bulk path:** `gcp brain structured-import` (Personal operator).

---

## Decision guide

| Question | pro-mcp |
|----------|---------|
| Stable LinkML | compile + SQL import |
| CSV / API | SOP5 scripts + COPY |
| Obsidian vault | [SOP3](SOP3_parsing_pipeline.md) |
| Flat document corpus | [SOP6](SOP6_document_import.md) |
| Projection audit | mindCLI + MCP |

---

## Next

[SOP_SEQUENCE.md](SOP_SEQUENCE.md)
