# SOP 0 — Choix de voie d'import (ontologie et tabulaire)

**Version :** 1.0  
**Statut :** Draft exploitable  
**Périmètre :** Discipline agent pour choisir explicitement la voie d'import ontologique et la voie d'import tabulaire, sans supprimer les workflows historiques.

---

## Section 1 — Objectif

Avant toute écriture Phase B (ontologie) ou Phase C2 (données tabulaires), l'agent doit :

1. présenter **deux options** numérotées pour chaque décision ;
2. recommander la voie par défaut selon l'environnement ;
3. enregistrer le choix utilisateur dans `templates/import_path_choices.yaml` ;
4. suivre **uniquement** la voie choisie, sans mélanger les pipelines.

> Avant d'importer une ontologie ou des données tabulaires, présenter les deux options et demander le choix explicite. Recommandation par défaut : **LinkML** pour l'ontologie, **structured-import CLI** pour le tabulaire en environnement Personal SQLite. Si l'utilisateur choisit la voie existante (MCP incrémental / scripts SOP5), suivre le SOP historique sans modification.

---

## Section 2 — Quand poser chaque question

| Moment | Question | Bloquant si omis |
|--------|----------|------------------|
| Après Phase A validée, **avant** toute écriture Phase B | Choix voie ontologie | Oui |
| Avant Gate 0 SOP5 / début Phase C2 tabulaire | Choix voie tabulaire | Oui |

Ne pas poser les deux questions dans le même message si Phase B n'est pas encore clarifiée. Ordre : ontologie d'abord, tabulaire au moment C2.

---

## Section 3 — Question ontologie (Phase B0)

### 3.1 Texte agent (modèle)

```
Pour enregistrer l'ontologie de ce workspace, deux voies sont disponibles :

1. Voie LinkML (recommandée par défaut)
   — Le LLM génère ontology/core.yaml depuis le Model Proposal
   — Validation : gcp brain ontology compile (dry-run → slice.json)
   — Import après confirmation : compile --import-db
   — Voir SOP2 section 6 bis

2. Voie MCP incrémentale (historique StarterKit)
   — Enregistrement progressif via ghostcrab_schema_register, remember, upsert, learn
   — Voir SOP2 section 7 (Voie A)

Quelle voie choisissez-vous ? (1 ou 2)
```

### 3.2 Enregistrement

Mettre à jour `templates/import_path_choices.yaml` :

```yaml
ontology_path:
  choice: "linkml"          # ou mcp_incremental
  confirmed_at: "<ISO-8601>"
  notes: "<réponse utilisateur>"
```

### 3.3 Routage

| Choix | SOP à suivre |
|-------|--------------|
| `linkml` | `SOP2_obsidian_ontologie.md` section 6 bis |
| `mcp_incremental` | `SOP2_obsidian_ontologie.md` section 7 (Voie A) |

Référence LinkML canonique (Personal) :

- `ghostcrab-personal-mcp/ontologies/immeuble-demo/core.yaml`
- `ghostcrab-personal-mcp/ontologies/ghostcrab/profile.yaml`

Template projet : `templates/linkml_ontology.stub.yaml`

---

## Section 4 — Question tabulaire (Phase C2.0)

### 4.1 Texte agent (modèle)

```
Pour importer les données tabulaires (CSV/JSON/YAML), deux voies sont disponibles :

1. Voie CLI structured-import (recommandée par défaut en Personal SQLite)
   — gcp brain structured-import validate → register-semantics → apply → reindex
   — Voir SOP5 section 1 bis (Voie B)
   — Runbook : ghostcrab-personal-mcp/docs/setup/structured-import.md

2. Voie compiler StarterKit (historique)
   — Scripts starterkit/scripts/ + gates SOP5 section 3 (Voie A)
   — Dry-run JSONL puis plan ghostcrab_upsert

Quelle voie choisissez-vous ? (1 ou 2)
```

### 4.2 Enregistrement

```yaml
tabular_path:
  choice: "structured_import_cli"   # ou sop5_compiler
  confirmed_at: "<ISO-8601>"
  notes: "<réponse utilisateur>"
```

### 4.3 Routage

| Choix | SOP à suivre |
|-------|--------------|
| `structured_import_cli` | `SOP5_source_import_compiler.md` section 1 bis |
| `sop5_compiler` | `SOP5_source_import_compiler.md` section 3 (Voie A) |

Exemple Personal : `ghostcrab-personal-mcp/examples/immeuble/structured-import/`

---

## Section 5 — Boucle LLM LinkML (obligatoire, voie ontologie LinkML)

1. Générer ou réviser `ontology/core.yaml` depuis `jtbd.yaml` + Model Proposal + `linkml_ontology.stub.yaml`.
2. Dry-run compile (sans écriture DB) :
   ```bash
   gcp brain ontology compile \
     --workspace-id <ws> \
     --ontology-id <ws>::core \
     --input ontology/core.yaml \
     --output output/ontology-slice.json
   ```
3. Corriger le YAML jusqu'à exit 0 ; vérifier cohérence avec JTBD (classes, enums, relations).
4. Présenter un résumé lisible à l'utilisateur (classes, enums, edge types).
5. Après confirmation explicite :
   ```bash
   gcp brain ontology compile \
     --workspace-id <ws> \
     --ontology-id <ws>::core \
     --input ontology/core.yaml \
     --import-db --force
   ```
6. Vérification post-import (commune aux deux voies) : `ghostcrab_schema_list`, `ghostcrab_schema_inspect`, `ghostcrab_coverage`.

Variante avancée (non défaut) : OWL/N-Triples via `gcp brain ontology import --materialize-graph`.

---

## Section 6 — Backend et environnement

| Environnement | Ontologie défaut | Tabulaire défaut |
|---------------|------------------|------------------|
| Personal SQLite (`ghostcrab-personal-mcp`) | LinkML | structured-import CLI |
| Pro PostgreSQL (GhostCrab GitLab) | LinkML ou MCP selon volume | sop5_compiler ou structured-import si disponible |

Si QUICKSTART mentionne « PostgreSQL only », lire SOP5 Gate 0 et ce document : le fork SQLite Personal est explicite dans SOP5 et SOP0.

---

## Section 7 — Checklist agent

- [ ] Phase A validée (`ghostcrab_status` OK)
- [ ] Question ontologie posée et réponse enregistrée dans `import_path_choices.yaml`
- [ ] Voie ontologie suivée sans mélange (LinkML **ou** MCP, pas les deux en parallèle)
- [ ] Avant C2 : question tabulaire posée et enregistrée
- [ ] Voie tabulaire suivée sans mélange
- [ ] `import_manifest.yaml` reflète `import_path_choices` et la branche `commands.path`
