# Plan de routes — personal-mcp (SOP 0→6)

**Édition par défaut du StarterKit.** SQLite, `gcp brain ...`, MCP `ghostcrab_*`.

**Rester dans ce dossier** + `../templates/` + `../scripts/`. Pro → [../pro-mcp/ROUTE_MAP.md](../pro-mcp/ROUTE_MAP.md) via [../EDITIONS.md](../EDITIONS.md).

**Séquence canonique:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md)

---

## Je suis à l'étape X → prochain fichier

| Où vous en êtes | Prochaine action | Fichier |
|-----------------|------------------|---------|
| Début | Confirmer édition Personal | [../EDITIONS.md](../EDITIONS.md) → ce dossier |
| Phase A | Bootstrap SQLite + MCP | [SOP4](SOP4_environment_bootstrap.md) |
| `ghostcrab_status` OK | Choix de voies d'import | [SOP0](SOP0_import_path_choices.md) + `../templates/import_path_choices.yaml` |
| B0 done | Modéliser workspace | [SOP1](SOP1_ghostcrab_mcp.md) + [SOP2](SOP2_obsidian_ontologie.md) |
| LinkML (SOP0) | Ontologie formelle | SOP2 §6 bis + `../templates/linkml_ontology.stub.yaml` |
| MCP incrémental (SOP0) | Seed unitaire | SOP2 §7 |
| Phase B — specs OK | **Préparer projections** | [§ Route projections](#route-projections) + `../scripts/README_projection_tools.md` |
| Projections validées | Matérialiser catalogue | `ghostcrab_project` + confirmation utilisateur |
| Phase B done | Vault Obsidian à parser | [SOP3](SOP3_parsing_pipeline.md) |
| Corpus documents | Bulk `gcp brain document` | [SOP6](SOP6_gcp_document_import.md) |
| CSV/API/tabulaire | structured-import | [SOP5](SOP5_structured_import.md) |
| Import terminé | Audit projections + pipeline | `audit_ghostcrab_projections.py` + gate 9 |

---

## Phases

```mermaid
flowchart LR
  SOP4[Phase A SOP4] --> SOP0[Phase B0 SOP0]
  SOP0 --> SOP1B[Phase B SOP1+SOP2]
  SOP1B --> SOP1proj[Phase B1 projections]
  SOP1proj --> SOP3[Phase C opt SOP3]
  SOP1B --> SOP6[Phase C SOP6]
  SOP1B --> SOP5[Phase C2 SOP5]
  SOP3 --> SOP6
```

| Phase | SOP | Opérateur | Done when |
|-------|-----|-----------|-----------|
| A | SOP4 | `gcp smoke`, `gcp brain up`, `ghostcrab_status` | SQLite OK, outils MCP visibles |
| B0 | SOP0 | `import_path_choices.yaml` | choix enregistrés |
| B | SOP1 + SOP2 | MCP + LinkML ou incrémental | `ghostcrab_coverage` baseline |
| **B1** | scripts projections | candidats + validation humaine | catalogue déclaré prêt |
| C (opt.) | SOP3 | parsing vault → JSONB | validator OK |
| C | SOP6 | `gcp brain document` | pipeline document OK |
| C2 | SOP5 | `gcp brain structured-import` | facets + reindex |
| Audit | SOP5 gates 8–9 | MCP pack + `audit_ghostcrab_projections.py` | manifest + consumers |

---

## Route projections

Les projections sont le **contrat de retrieval** agent (questions métier → scope → schémas/facettes/arêtes requis). Elles se préparent en Phase B, se matérialisent avant ou juste après l'import, et s'auditent en clôture.

**Doc outils:** [../scripts/README_projection_tools.md](../scripts/README_projection_tools.md)

### Deux modes GhostCrab

| Mode | Stockage Personal | Lecture agent |
|------|-------------------|---------------|
| **Type A — catalogue déclaré** | table `projections` | `ghostcrab_pack`, `ghostcrab_project` |
| **Type B — snapshot calculé** | `graph_entity` (`ProjectionResult`) | `ghostcrab_projection_get` |

Un catalogue Type A sain suffit pour démarrer ; Type B = rapport matérialisé avec preuves graphe.

### Phase B1 — Préparer (avant import massif)

1. Déclarer `projection_types_allowed` dans `../templates/ontology_core_provisioning.yaml` (SOP2).
2. Extraire les candidats depuis l'ontologie / vault Markdown :

```bash
python3 ../scripts/analyze_projection_candidates.py \
  --source-dir ./specs \
  --db "$GHOSTCRAB_SQLITE_PATH" \
  --workspace <workspace_id> \
  --model-contract ../templates/mvp_core_contract.yaml \
  --write-agent-context
```

3. Revue humaine : `generated/projection_candidates/projection_model_validation.md` — valider scope, `proj_type`, jobs de retrieval.
4. **Gate freeze :** pas de matérialisation sans confirmation utilisateur (aligné SOP2 Model Proposal).

Artefacts : `projection_candidates.json`, `projection_model_validation.md`, optionnel `specs/projection_catalog.yaml`.

### Matérialiser — écrire le catalogue

Par projection retenue, via MCP (unitaire) :

```json
// ghostcrab_project
{
  "workspace_id": "<ws>",
  "source_ref": "note:decisions-cms-choice",
  "proj_type": "AUDIT_DECISION",
  "scope": "<ws>:refonte-acme",
  "status": "active",
  "metadata": { "retrieval_jobs": ["summary", "monitor"] }
}
```

Pendant parsing (SOP3/SOP6), le JSONB SOP2 §4.3 peut porter un `projection_signal` — validator obligatoire avant injection.

En bulk tabulaire (SOP5 gate 7) : vérifier `ghostcrab_pack` et `ghostcrab_projection_get` sur les scopes déclarés.

### Travailler — runtime agent

| Besoin | Outil |
|--------|-------|
| Contexte opérationnel courant | `ghostcrab_pack(scope="<ws>:<scope>")` |
| Rapport calculé (Type B) | `ghostcrab_projection_get` |
| Recherche preuves | `ghostcrab_search`, `ghostcrab_count` |
| Couverture | `ghostcrab_coverage` |

Configurer les smoke tests dans `../templates/consumer_contract.yaml` (`requires.projections: true`, check `ghostcrab_pack`).

### Auditer — post-import

```bash
python3 ../scripts/audit_ghostcrab_projections.py \
  --db "$GHOSTCRAB_SQLITE_PATH" \
  --workspace <workspace_id> \
  --model generated/<ws>/model_contract.json
```

Rapports : `generated/projection_audits/projection_audit_<ws>.md` — gaps Type A/B, qualité graphe, types non enregistrés.

Puis gate 9 : `../scripts/audit_import_pipeline.mjs` + `validate_consumer_contract.mjs`.

---

## Bifurcations SOP0

```yaml
edition: personal-mcp
ontology_path: linkml          # ou mcp_incremental
tabular_path: gcp_structured_import
document_path: gcp_document
```

| Question | Route |
|----------|-------|
| Ontologie LinkML | SOP2 §6 bis → `gcp brain ontology compile` |
| Ontologie MCP | SOP2 §7 |
| Vault Obsidian | SOP3 → SOP6 |
| Tabulaire | SOP5 |
| Documents seuls | SOP6 (LinkML si qualify) |

---

## Opérateurs autorisés

| Besoin | Surface |
|--------|---------|
| Bootstrap | `gcp authorize`, `gcp smoke`, `gcp brain up` |
| Modélisation | `ghostcrab_*` (status, workspace, schema, coverage) |
| **Projections — préparer** | `analyze_projection_candidates.py` (read-only) |
| **Projections — écrire** | `ghostcrab_project` (unitaire) |
| **Projections — lire** | `ghostcrab_pack`, `ghostcrab_projection_get` |
| **Projections — auditer** | `audit_ghostcrab_projections.py` |
| Ontologie formelle | `gcp brain ontology compile` |
| Documents bulk | `gcp brain document` (SOP6) |
| Tabulaire bulk | `gcp brain structured-import` (SOP5) |
| Audit agent | MCP search, pack, coverage |

**Interdit:** mindCLI, COPY, `generate_copy_migrations.mjs`, `DATABASE_URL` Pro.

---

## Artefacts YAML (ordre SOP2)

1. `../templates/jtbd.yaml`
2. `../templates/mvp_core_contract.yaml`
3. `../templates/ontology_core_provisioning.yaml`
4. `../templates/initial_referential.yaml`
5. `../templates/mapping_external_to_canonical.yaml`
6. `../templates/disambiguation.yaml`

Clôture : `../templates/import_manifest.yaml` (`edition: personal-mcp`).

---

## Checklist condensée

1. [SOP4](SOP4_environment_bootstrap.md)
2. [SOP0](SOP0_import_path_choices.md)
3. [SOP1](SOP1_ghostcrab_mcp.md) + [SOP2](SOP2_obsidian_ontologie.md)
4. **Projections :** candidats → validation → `ghostcrab_project` → [§ Route projections](#route-projections)
5. Optionnel : [SOP3](SOP3_parsing_pipeline.md) → [SOP6](SOP6_gcp_document_import.md)
6. Optionnel : [SOP5](SOP5_structured_import.md)
7. Audit : `audit_ghostcrab_projections.py` + gate 9

---

## Index SOP (ce dossier)

| SOP | Fichier | Phase |
|-----|---------|-------|
| SOP0 | [SOP0_import_path_choices.md](SOP0_import_path_choices.md) | B0 |
| SOP1 | [SOP1_ghostcrab_mcp.md](SOP1_ghostcrab_mcp.md) | B |
| SOP2 | [SOP2_obsidian_ontologie.md](SOP2_obsidian_ontologie.md) | B |
| SOP3 | [SOP3_parsing_pipeline.md](SOP3_parsing_pipeline.md) | C (opt.) |
| SOP4 | [SOP4_environment_bootstrap.md](SOP4_environment_bootstrap.md) | A |
| SOP5 | [SOP5_structured_import.md](SOP5_structured_import.md) | C2 |
| SOP6 | [SOP6_gcp_document_import.md](SOP6_gcp_document_import.md) | C |

Les stubs racine `../SOP*.md` pointent ici par défaut.
