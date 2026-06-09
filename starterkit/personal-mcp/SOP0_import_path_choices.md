# SOP 0 — Import path choices (personal-mcp)

**Edition:** personal-mcp only. Pro → [../pro-mcp/SOP0_import_path_choices.md](../pro-mcp/SOP0_import_path_choices.md).

**Phases:** B0 (ontology) · C2.0 (tabular)

Fill [`../templates/import_path_choices.yaml`](../templates/import_path_choices.yaml) with `edition: personal-mcp`.

---

## Defaults

```yaml
edition: personal-mcp
ontology_path: linkml
ontology_path_alt: mcp_incremental
tabular_path: gcp_structured_import
document_path: gcp_document
```

**Forbidden:** `sop3_copy`, `sop5_voie_a_copy`, `mindcli_audit`, `generate_copy_migrations.mjs`.

---

## Agent prompt (FR) — ontologie (B0)

```
Pour enregistrer l'ontologie de ce workspace, deux voies sont disponibles :

1. Voie LinkML (recommandée)
   — ontology/core.yaml + gcp brain ontology compile (dry-run puis --import-db)
   — Voir [SOP2_obsidian_ontologie.md](SOP2_obsidian_ontologie.md) section 6 bis

2. Voie MCP incrémentale
   — ghostcrab_schema_register, remember, upsert, learn
   — Voir [SOP2_obsidian_ontologie.md](SOP2_obsidian_ontologie.md) section 7

Quelle voie ? (1 ou 2)
```

| Choix | Next |
|-------|------|
| `linkml` | SOP2 §6 bis + `../templates/linkml_ontology.stub.yaml` |
| `mcp_incremental` | SOP2 §7 |

Références : `ghostcrab-personal-mcp/ontologies/immeuble-demo/core.yaml`, `examples/ghostcrab-docs/import_path_choices.yaml`, `docs/explanation/ontology/README.md`.

---

## Agent prompt (FR) — tabulaire (C2.0)

```
1. structured-import CLI (recommandé) — SOP5_structured_import.md
2. Scripts StarterKit dry-run seulement — profiling/mapping, pas COPY

Quelle voie ? (1 ou 2)
```

| Choix | Next |
|-------|------|
| `structured_import_cli` | [SOP5_structured_import.md](SOP5_structured_import.md) |
| `sop5_compiler` | dry-run scripts only on Personal — **no** `generate_copy_migrations.mjs` |

---

## LinkML loop

See [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase B ontology + product `docs/setup/structured-import.md`.

---

## Next

[SOP_SEQUENCE.md](SOP_SEQUENCE.md)
