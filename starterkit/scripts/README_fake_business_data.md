# Fake business data — génération déterministe (StarterKit)

Génère des **données fictives métier** alignées sur le contrat de modèle (Phase B), **avant** l'import bulk (SOP5 / structured-import). Pattern validé sur le projet Serenity (ontologies Markdown → contrat → CSV → import → projections).

**Route maps:** [personal-mcp/ROUTE_MAP.md § B2](../personal-mcp/ROUTE_MAP.md#route-donnees-fictives-metier) · [pro-mcp/ROUTE_MAP.md § B2](../pro-mcp/ROUTE_MAP.md#route-donnees-fictives-metier)

**Review dossier:** when fake-data creates strategic evidence for humans, collect the generated reports with [../personal-mcp/SOP_review_finalisation_dossier.md](../personal-mcp/SOP_review_finalisation_dossier.md).

---

## Quand l'utiliser

| Situation | Fake data |
|-----------|-----------|
| Pas encore de source CRM/ERP/API | **Oui** — valider modèle + import + projections |
| Vault Obsidian seul (SOP3/SOP6) | Optionnel — compléter avec tabulaire synthétique |
| Production | **Non** — remplacer par sources réelles |

Phase **B2** : après contrat ontologique (B), catalogue projections (B1) et règles métier (B1.5), **avant** `gcp brain structured-import` ou COPY (C2).

Phase **B2.5** complète B2 : elle vérifie que les données peuvent produire des
réponses manager auditables (`answer_snapshot`, claims, evidence, assertions).
Voir [../personal-mcp/SOP_projection_test_data_levels.md](../personal-mcp/SOP_projection_test_data_levels.md).

---

## Entrées requises

| Artefact | Rôle |
|----------|------|
| `../templates/jtbd.yaml` | volumes et familles métier |
| `../templates/mvp_core_contract.yaml` ou export MCP | `schema_id`, enums, edges fermés |
| `../templates/ontology_core_provisioning.yaml` | types et facettes obligatoires |
| `../templates/mapping_external_to_canonical.yaml` | clés source → canonique |
| Ontologie Markdown (optionnel) | sections `## Projections / rapports types` |
| `rules/business_rules_catalog.yaml` | règles, assertions et variantes à couvrir |
| `specs/projection_catalog.yaml` | projections à tester |

---

## Sorties attendues (layout recommandé)

```text
generated/<workspace_id>/
├── model/
│   └── model_contract.json          # export MCP ou merge templates
├── fake_data/
│   └── <entity_type>.csv            # un CSV par type métier (debug humain)
├── import_ready/
│   ├── facets_import.csv            # source_ref, workspace_id, schema_id, content, facets
│   └── edges_import.csv             # workspace_id, source, target, label
├── contracts/
│   ├── projection_catalog.yaml      # optional — lié B1
│   └── mapping_external_to_canonical.json
├── reports/
│   ├── fake_data_coverage.md
│   ├── manager_answer_snapshots.md  # B2.5 when snapshots are expected
│   └── snapshot_claims_evidence_matrix.md
└── import_manifest.json             # counts, paths, edition
```

**Personal :** alimenter `gcp brain structured-import` (SOP5).  
**Pro :** alimenter COPY / `generate_copy_migrations.mjs` (SOP5 Voie A).

---

## Règles de qualité métier

1. **`schema_id` namespacé** — `<workspace_id>:<family>:<type>` (SOP2 §6).
2. **Enums du modèle** — pas de valeurs hors liste (ex. `FDRO`/`FDRS`/`FDROP`, pas `annuel` générique).
3. **Ordre de génération** — entités pivots avant dépendantes (Serenity : copropriétés avant équipes).
4. **Graphe cohérent** — arêtes uniquement entre `source_ref` existants ; labels dans la liste fermée SOP2.
5. **Volume minimal projections** — assez de lignes pour tester les scopes B1 retenus (ex. ≥3 lignes par projection « core »).
6. **Règles métier couvertes** — chaque `rule_id` généré existe dans `business_rules_catalog.yaml`.
7. **Snapshots auditables** — quand un `answer_snapshot` est attendu, chaque claim doit pointer vers des evidence entities, edges et assertions.
8. **Idempotence** — seed fixe (`--seed 42`) pour reproductibilité CI.

---

## Pipeline StarterKit (sans script Python obligatoire)

Si vous n'avez pas encore de générateur domaine (type `build_*_ontology.py`) :

```bash
# 1. Exporter / valider le contrat
node ../scripts/export_model_contract.mjs \
  --workspace <workspace_id> \
  --exported generated/<ws>/model/model_contract.json

# 2. Profiler le dossier fake_data (une fois les CSV créés)
node ../scripts/profile_source.mjs \
  --source generated/<ws>/fake_data \
  --output generated/<ws>/source_profile.report.json

# 3. Valider mapping
node ../scripts/validate_mapping_contract.mjs \
  --mapping ../templates/mapping_external_to_canonical.yaml \
  --model generated/<ws>/model/model_contract.json

# 4. Dry-run JSONB
node ../scripts/transform_source_to_jsonb.mjs \
  --source generated/<ws>/import_ready/facets_import.csv \
  --mapping ../templates/mapping_external_to_canonical.yaml \
  --output generated/<ws>/dry_run/facets.jsonl
```

Puis SOP5 : `gcp brain structured-import validate` → `apply` → `reindex`.

---

## Générateur Python (recommandé domaine)

Créer un script **projet-local** (hors starterkit) qui :

1. Lit les Markdown d'ontologie + templates YAML.
2. Émet le contrat JSON et les CSV `fake_data/`.
3. Produit `import_ready/facets_import.csv` + `edges_import.csv` au format structured-import.
4. Valide enums / `schema_id` / ordre de dépendance avant écriture.

Référence réelle : `MVP_Serenity_2/scripts/build_serenity_v3_ontology.py` (632 facts, 152 edges, `projection_catalog.json`).

---

## Après import — lier aux projections

Les fake-data **seules** ne matérialisent pas les projections. Enchaînement :

1. B1 — catalogue / candidats validés  
2. **B2 — fake data**  
3. C2 — import  
4. B2.5 — générer les snapshots manager-oriented et matrices `claim -> evidence -> assertion`
5. Matérialiser ou rafraîchir : `ghostcrab_project` (`analysis_plan`) + seed `live_answer_view` + `gcp brain artifact refresh`
6. `audit_ghostcrab_projections.py` + gate 7 SOP5

Voir [README_projection_tools.md](README_projection_tools.md).

---

## Checklist B2 « done »

- [ ] `model_contract.json` cohérent avec templates  
- [ ] CSV `import_ready/` parseables ; counts documentés dans `import_manifest.json`  
- [ ] Enums et edges validés (dry-run gates 2–4 sans erreur bloquante)  
- [ ] Au moins une projection B1 « core » a assez de lignes source pour un smoke test post-import  
- [ ] B2.5 préparé si des `answer_snapshot` ou vues manager sont attendus
- [ ] `GHOSTCRAB_SQLITE_PATH` / DSN Pro = **même base** que le MCP actif (éviter le piège multi-SQLite Serenity)
