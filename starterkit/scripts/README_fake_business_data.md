# Fake business data — génération déterministe (StarterKit)

Génère des **données fictives métier** alignées sur le contrat de modèle (Phase B), **avant** l'import bulk (SOP5 / structured-import). Pattern validé sur le projet Serenity (ontologies Markdown → contrat → CSV → import → projections).

**Route maps:** [personal-mcp/ROUTE_MAP.md § B2](../personal-mcp/ROUTE_MAP.md#route-donnees-fictives-metier) · [pro-mcp/ROUTE_MAP.md § B2](../pro-mcp/ROUTE_MAP.md#route-donnees-fictives-metier)

**Projection validation:** when generated data is used to test `analysis_plan`, `answer_snapshot`, `live_answer_view`, or `evidence_pack`, also apply [../personal-mcp/SOP_projection_test_data_levels.md](../personal-mcp/SOP_projection_test_data_levels.md). Fake-data must cover structural data, business rules, manager answer payloads, and evidence links according to the artifact kind.

**Review dossier:** when fake-data creates strategic evidence for humans, collect the generated reports with [../personal-mcp/SOP_review_finalisation_dossier.md](../personal-mcp/SOP_review_finalisation_dossier.md).

---

## Quand l'utiliser

| Situation | Fake data |
|-----------|-----------|
| Pas encore de source CRM/ERP/API | **Oui** — valider modèle + import + projections |
| Vault Obsidian seul (SOP3/SOP6) | Optionnel — compléter avec tabulaire synthétique |
| Production | **Non** — remplacer par sources réelles |

Phase **B2** : après contrat ontologique (B), catalogue projections (B1), et **catalogue des règles métier (B1.5)**, **avant** `gcp brain structured-import` ou COPY (C2).

Gate obligatoire : produire `rules/business_rules_catalog.yaml` avec [personal-mcp/SOP_business_rules_catalog.md](../personal-mcp/SOP_business_rules_catalog.md). Les fake-data doivent couvrir les règles et scénarios déclarés ; elles ne doivent pas deviner les cas critiques à la place du catalogue.

Gate projection : produire ou vérifier les niveaux de données décrits dans [personal-mcp/SOP_projection_test_data_levels.md](../personal-mcp/SOP_projection_test_data_levels.md) avant de considérer un snapshot ou une live view comme validé métier. Une couverture de règles verte ne suffit pas si les métriques, alertes, conclusions ou preuves ne sont pas matérialisées.

**Facettes enum :** pour les domaines multi-modules, les valeurs générées et les clés de facettes dans `facets` JSON / CSV doivent respecter `<module>.<slot_snake_case>` — voir `ghostcrab-shared/ENUM_BUSINESS_FACETS.md` après `gcp brain setup`. Les clés ingest Obsidian courtes (`status`, `tags`) ne remplacent pas cette règle pour les enums LinkML.

---

## Entrées requises

| Artefact | Rôle |
|----------|------|
| `../templates/jtbd.yaml` | volumes et familles métier |
| `../templates/mvp_core_contract.yaml` ou export MCP | `schema_id`, enums, edges fermés |
| `../templates/business_rules_catalog.yaml` ou `rules/business_rules_catalog.yaml` | règles métier, assertions et scénarios smoke/mini/scale |
| `../templates/ontology_core_provisioning.yaml` | types et facettes obligatoires |
| `../templates/mapping_external_to_canonical.yaml` | clés source → canonique |
| Ontologie Markdown (optionnel) | sections `## Projections / rapports types` |

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
├── rules/
│   └── business_rules_catalog.yaml  # B1.5 — règles, assertions, scénarios
├── reports/
│   ├── fake_data_coverage.json      # couverture règles/scénarios
│   ├── fake_data_coverage.md        # lecture humaine
│   ├── manager_answer_snapshots.json
│   ├── manager_answer_snapshots.md
│   ├── snapshot_claims_evidence_matrix.json
│   ├── snapshot_claims_evidence_matrix.csv
│   └── snapshot_claims_evidence_matrix.md
└── import_manifest.yaml             # counts, paths, edition (runtime: generated/<ws>/import_manifest.yaml)
```

**Personal :** alimenter `gcp brain structured-import` (SOP5).  
**Pro :** alimenter COPY / `generate_copy_migrations.mjs` (SOP5 Voie A).

---

## Règles de qualité métier

1. **`schema_id` namespacé** — `<workspace_id>:<family>:<type>` (SOP2 §6).
2. **Enums du modèle** — pas de valeurs hors liste ; clés enum LinkML en `<module>.<slot_snake_case>` (ex. `administrative.formule_service`, pas `formule_service` seul).
3. **Ordre de génération** — entités pivots avant dépendantes (Serenity : copropriétés avant équipes).
4. **Graphe cohérent** — arêtes uniquement entre `source_ref` existants ; labels dans la liste fermée SOP2.
5. **Volume minimal projections** — assez de lignes pour tester les scopes B1 retenus (ex. ≥3 lignes par projection « core »).
6. **Idempotence** — seed fixe (`--seed 42`) pour reproductibilité CI.
7. **Couverture règles métier** — chaque règle critique du catalogue a au moins un scénario smoke et un scénario mini normal ou exception.

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

1. Lit les Markdown d'ontologie + templates YAML + `rules/business_rules_catalog.yaml`.
2. Émet le contrat JSON et les CSV `fake_data/`.
3. Produit `import_ready/facets_import.csv` + `edges_import.csv` au format structured-import.
4. Valide enums / `schema_id` / ordre de dépendance avant écriture.
5. Vérifie que les scénarios smoke/mini/scale du catalogue ont été matérialisés.
6. Produit les payloads manager-oriented attendus par les projections (`manager_answer_snapshots.*`) quand des `answer_snapshot` ou `live_answer_view` sont prévus.
7. Produit une matrice `snapshot_claims_evidence_matrix.*` reliant :
   `answer_snapshot` / projection → claim → règle métier → variante → evidence refs → assertions.

Référence réelle : `MVP_Serenity_2/scripts/build_serenity_v3_ontology.py` (632 facts, 152 edges, `projection_catalog.json`).

### Claims auditables pour answer_snapshot

Un jeu fake-data prêt pour les snapshots doit distinguer :

| Statut claim | Sens |
|--------------|------|
| `supported` | preuve positive complète dans les facts/edges générés |
| `supported_expected_violation` | cas d'exception généré volontairement, violation attendue observée |
| `supported_with_model_gap_note` | preuve exploitable, mais gap modèle à garder visible |
| `deferred` | règle reportée, typiquement `mappingProfile` off |

Gate recommandé avant de matérialiser les preuves :

- chaque `answer_snapshot` actif a au moins un claim ;
- chaque claim a au moins un `evidence_ref` primaire ;
- les assertions du catalogue sont reprises dans `assertion_results` ;
- seuls les cas explicitement différés restent `deferred` ;
- `smoke`, `mini` et `scale` utilisent le même contrat de claims, avec volumes différents.

---

## Après import — lier aux projections

Les fake-data **seules** ne matérialisent pas les projections. Enchaînement :

1. B1 — catalogue / candidats validés  
2. B1.5 — `rules/business_rules_catalog.yaml` confirmé
3. **B2 — fake data**  
4. B2.5 — projection test data levels ([../personal-mcp/SOP_projection_test_data_levels.md](../personal-mcp/SOP_projection_test_data_levels.md))
5. C2 — import  
6. Matérialiser ou rafraîchir : `ghostcrab_project` (`analysis_plan`) + seed `live_answer_view` + `gcp brain artifact refresh`  
7. `audit_ghostcrab_projections.py` + gate 7 SOP5  

Voir [README_projection_tools.md](README_projection_tools.md).

---

## Checklist B2 « done »

- [ ] `model_contract.json` cohérent avec templates  
- [ ] CSV `import_ready/` parseables ; counts documentés dans `import_manifest.yaml`  
- [ ] Enums et edges validés (dry-run gates 2–4 sans erreur bloquante)  
- [ ] Au moins une projection B1 « core » a assez de lignes source pour un smoke test post-import  
- [ ] Les projections attendues ont les niveaux B2.5 nécessaires : données structurelles, couverture métier, réponse manager et preuves
- [ ] `GHOSTCRAB_SQLITE_PATH` / DSN Pro = **même base** que le MCP actif (éviter le piège multi-SQLite Serenity)
