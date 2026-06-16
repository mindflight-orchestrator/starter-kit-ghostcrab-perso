# SOP 0 — Import path choices (personal-mcp)

**Edition:** personal-mcp only. Pro → [../pro-mcp/SOP0_import_path_choices.md](../pro-mcp/SOP0_import_path_choices.md).

**Phases:** B0 (ontology) · C2.0 (tabular)

Fill [`../templates/import_path_choices.yaml`](../templates/import_path_choices.yaml) with `edition: personal-mcp` and copy to `{project}/<workspace-slug>/import_path_choices.yaml`.

**Path resolution:** [STARTERKIT_PATHS.md](STARTERKIT_PATHS.md)

**Companion skill:** `ghostcrab-data-architect` ([SKILL_ROUTE_MAP.md](SKILL_ROUTE_MAP.md)) — install via `gcp brain setup <ide>`.

---

## Defaults

```yaml
edition: personal-mcp
ontology_path:
  choice: linkml
tabular_path:
  choice: structured_import_cli
document_path:
  choice: gcp_document
paths:
  starterkit_root: null
```

**Forbidden:** `sop3_copy`, `sop5_voie_a_copy`, `mindcli_audit`, `generate_copy_migrations.mjs`.

---

## Agent prompt (FR) — ontologie (B0)

```
Pour enregistrer l'ontologie de ce workspace, deux voies sont disponibles :

1. Voie LinkML (recommandée)
   — ontology/core.yaml (module unique) ou ontology/<module>.yaml (multi-modules)
   — si multi-modules / JSON source / aliases : ontology/<workspace>-contract.yaml + validation JSON ↔ LinkML
   — gcp brain ontology compile (dry-run puis --import-db)
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

**Multi-module / JSON source:** list modules in `artefacts.ontology_modules` and create a project-local central contract (`ontology/<workspace>-contract.yaml`) before import. The contract records canonical ontology ids, public/internal naming, aliases, accepted renames, import order, `mappingProfile` rules, and the config consumed by `../scripts/validate_ontology_json_vs_linkml.py`. After LinkML import, register enum facets as `<module>.<slot_snake_case>` — see installed `ghostcrab-shared/ENUM_BUSINESS_FACETS.md`.

Optional single-module reference: [ghostcrab-personal-mcp `ontologies/immeuble-demo`](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp/tree/main/ontologies/immeuble-demo).

---

## Agent prompt (FR) — fake-data métier (B2)

```
Avant le premier import bulk tabulaire (SOP5), le gate B1.5 doit produire
rules/business_rules_catalog.yaml selon SOP_business_rules_catalog.md.

Ensuite, souhaitez-vous :

1. Générer des données fictives métier (recommandé sans source CRM/API)
   — couvre les règles, assertions et scénarios smoke/mini/scale du catalogue
   — ../scripts/README_fake_business_data.md + ROUTE_MAP § B2

2. Passer B2 (sources réelles déjà profilées et mappées)
   — documenter pourquoi le catalogue n'est pas nécessaire ou comment les sources réelles couvrent les règles

Choix ? (1 ou 2)
```

Enregistrer dans `import_path_choices.yaml` → `fake_data.choice`: `generate` | `skip`.
Enregistrer aussi `business_rules_catalog.choice`: `create` | `skip_with_reason`.

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

See [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase B ontology + [SOP5_structured_import.md](SOP5_structured_import.md) for tabular closure gates (`ghostcrab-shared/IMPORT_CLOSURE_GATES.md`).

---

## Next

[SOP_SEQUENCE.md](SOP_SEQUENCE.md)
