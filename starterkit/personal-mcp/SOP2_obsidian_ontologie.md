# SOP 2 — Préparation du matériel ontologique depuis un vault Obsidian (personal-mcp)

**Edition:** personal-mcp only — `ghostcrab-personal-mcp`, SQLite, **`gcp brain ...`** + MCP **`ghostcrab_*`**.

**Version :** 1.0  
**Statut :** Draft exploitable  
**Périmètre :** De la structure brute d'un vault Obsidian à l'injection validée dans GhostCrab Personal.

| Concept | Personal SQLite |
|---------|-----------------|
| Runtime | `ghostcrab-personal-mcp` |
| CLI bulk | `gcp brain structured-import`, `gcp brain document`, `gcp brain ontology compile` |
| Fact store | SQLite `agent_facts`, `graph_entity`, `projections`, `ontology_*` |
| MCP unit writes | `ghostcrab_remember`, `ghostcrab_upsert`, `ghostcrab_learn`, `ghostcrab_project` |
| **Interdit** | mindCLI, PostgreSQL COPY, `generate_copy_migrations.mjs`, `DATABASE_URL` Pro |

Les tableaux ci-dessous utilisent les noms logiques (`schema_id`, `content`, `facets`, relations). La persistance cible est **`agent_facts`** et les tables SQLite du produit Personal — pas `mfo_facets` / `mfo_projections` Pro.

---

## Section 1 — Objectif et périmètre

### 1.1 Ce que cette SOP couvre

- Le choix de voie d'import ontologique (voir `SOP0_import_path_choices.md` : LinkML défaut vs MCP incrémental).
- L'analyse d'un vault Obsidian (`.md` + `.pdf`) pour en extraire le matériel ontologique.
- La formalisation des JTBD du vault en ontologies candidates.
- La stratégie de parsing, de chunking et d'enrichissement LLM.
- La production du JSONB intermédiaire structuré.
- La séquence d'injection dans GhostCrab MCP (schémas, facettes, graphe, projections).
- Les conventions de nommage obligatoires.
- La gestion des cas complexes (collisions, mises à jour, multi-projets).

### 1.2 Ce que cette SOP ne couvre pas

- Le code d'implémentation des scripts de parsing (périmètre SOP 3).
- Le déploiement de GhostCrab MCP ou de PostgreSQL.
- La configuration du LLM (choix du modèle, coûts, rate limits).
- La gestion des droits d'accès Obsidian ou des secrets.
- La maintenance des ontologies après la phase initiale de seeding.

### 1.3 Le vault Obsidian comme entrée multi-ontologies

Un vault Obsidian est une collection de fichiers Markdown et PDF organisés librement. Il n'a pas de schéma imposé. Sa structure (dossiers, tags, frontmatter, wikilinks) encode implicitement une ontologie que cette SOP vise à rendre explicite.

**Principe fondamental :** Un vault = un workspace GhostCrab par défaut. Plusieurs ontologies peuvent coexister dans ce workspace via des familles de `schema_id` distinctes, mais cette découpe doit être décidée à partir des JTBD, des besoins de retrieval, et des cycles de vie du vault, pas uniquement à partir de l'arborescence des dossiers.

| Entrée vault | Artefact GhostCrab | Couche cible |
|---|---|---|
| Fichier `.md` | Entité + facettes | `agent_facts` |
| PDF (section/page) | Source documentaire | `agent_facts` / pipeline [SOP6](SOP6_gcp_document_import.md) |
| Tag Obsidian | Axe de facette | Facette indexable |
| `[[wikilink]]` | Edge de graphe | `graph_entity` / relations SQLite |
| Frontmatter YAML | Facettes structurées | `agent_facts.facets` |
| Section logique | `source_ref` distinct | Unité d'extraction |
| Décision/tâche | Projection + entité typée | `projections` + schémas MCP |

---

## Section 2 — Analyse JTBD du vault

### 2.1 Formaliser le JTBD principal du vault

Avant tout parsing, le JTBD du vault doit être formalisé. Ce document pilote toutes les décisions ontologiques suivantes.

**Questions à répondre :**

1. Qui utilise ce vault ? (rôle, contexte)
2. Quel est le déclencheur principal d'usage ?
3. Quel est le résultat attendu (outcome) ?
4. Quelles sont les sous-activités récurrentes ?

### 2.2 Template `jtbd.yaml`

À produire en **premier**, avant toute action technique. Ce fichier est la source de vérité pour dériver les ontologies candidates.

```yaml
# jtbd.yaml — À compléter pour chaque vault
workspace_id: "<kebab-case-slug>"  # ex: web-project-acme

jtbd:
  main_job: "<Phrase infinitive décrivant l'objectif principal>"
  actor: "<Rôle de l'utilisateur principal>"
  trigger: "<Événement déclencheur>"
  outcome: "<Résultat mesurable attendu>"

  sub_jobs:
    - id: SJ1
      job: "<Sous-activité 1>"
      ontology_candidate: "<slug>"         # ex: client-knowledge
      schema_family: "<workspace_id>:<ontology_candidate>"
      primary_object_types:               # types d'entités attendus
        - "<type_1>"
        - "<type_2>"
      source_patterns:                    # patterns de fichiers concernés
        - "clients/*.md"
        - "briefs/*.pdf"

    - id: SJ2
      job: "<Sous-activité 2>"
      ontology_candidate: "<slug>"
      schema_family: "<workspace_id>:<ontology_candidate>"
      primary_object_types: []
      source_patterns: []

  # Répéter pour chaque sous-job identifié
```

### 2.3 Dériver les sous-jobs → ontologies candidates

**Processus :**

1. Lister toutes les grandes catégories de dossiers ou de notes du vault.
2. Vérifier si ces catégories correspondent a de vrais jobs distincts ou seulement a une organisation pratique du meme job.
3. Pour chaque job distinct : formuler le sous-job en phrase infinitive.
4. Nommer l'`ontology_candidate` en kebab-case (sera le suffixe du `schema_family`).
5. Identifier les types d'objets attendus (entités, décisions, tâches...).
6. Identifier les patterns de fichiers sources.

### 2.4 Tableau des JTBD-types courants et leurs ontologies candidates

| Type de vault | Main job | Ontologies candidates typiques |
|---|---|---|
| **Projet web** | Piloter la refonte d'un site de A à Z | `client-knowledge`, `project-history`, `project-plan`, `site-content`, `design-decisions` |
| **Base de connaissances technique** | Capitaliser et retrouver les décisions d'architecture | `architecture-decisions`, `technology-catalog`, `incident-log`, `runbook`, `glossary` |
| **Veille réglementaire** | Monitorer et appliquer les évolutions légales | `regulation-catalog`, `impact-assessment`, `compliance-actions`, `legal-references` |
| **CRM léger** | Gérer les relations avec les contacts et comptes | `contact-profile`, `account-history`, `opportunity-pipeline`, `interaction-log` |
| **Roadmap produit** | Planifier et arbitrer les évolutions produit | `feature-backlog`, `user-research`, `release-plan`, `feedback-log`, `competitor-intel` |
| **Recherche académique** | Synthétiser un corpus bibliographique | `paper-catalog`, `concept-map`, `citation-network`, `research-notes`, `hypothesis-log` |
| **Documentation juridique** | Structurer et retrouver les documents contractuels | `contract-catalog`, `clause-library`, `party-registry`, `obligation-tracker` |
| **Wiki personnel** | Organiser et retrouver les connaissances durables | `reference-notes`, `how-to-catalog`, `concept-index`, `resource-links` |

**Important :** La présence d'un client ne suffit pas a classer un vault comme CRM. Un projet web pour un client est souvent plus proche d'un mix `workflow-tracking` + `software-delivery` + `knowledge-base` qu'un pipeline commercial.

---

## Section 3 — Inventaire et classification des objets du vault

### 3.1 Processus d'identification

Pour un vault donné, parcourir les fichiers et classer chaque type d'objet selon la couche GhostCrab cible :

| Question | → Couche |
|---|---|
| Est-ce une entité stable avec identité propre ? | Référentiel stable |
| Est-ce un attribut / axe de classification ? | Facette indexable |
| Est-ce une relation entre deux entités ? | Graphe |
| Est-ce une trace d'événement ou de décision ? | Projection |
| Est-ce un objet opérationnel fortement typé ? | Layer 1 (DDL typé) |
| Est-ce un fragment temporaire de traitement ? | Runtime (ne pas persister tel quel) |

### 3.2 Tableau des objets canoniques

| Objet Obsidian | Couche GhostCrab | `node_type` / rôle | Table cible | Notes |
|---|---|---|---|---|
| Note `.md` (document complet) | Référentiel stable | `document` | `agent_facts` | `source_ref` = `note:<path-hash>` |
| Section logique d'une note | Référentiel stable | `section` | `agent_facts` | `source_ref` = `note:<path-hash>#<section-slug>` |
| Page / section PDF | Référentiel stable | `document-page` | `agent_facts` | `source_ref` = `pdf:<filename>#p<n>` |
| Concept / entité métier | Référentiel stable | `concept` | `agent_facts` + `graph.entity` | Nœud central du graphe |
| Relation sémantique | Graphe | edge | `graph.relation` | Dérivée des wikilinks ou inférée par LLM |
| Tag Obsidian | Facette ingest | facette | `agent_facts.facets` (clé) | Vocabulaire path/content — voir ci-dessous |
| Frontmatter clé-valeur | Facette ingest | facette | `agent_facts.facets` | Mapping direct YAML → JSONB |
| Citation / référence externe | Référentiel stable | `reference` | `agent_facts` | URL ou identifiant externe |
| Décision | Projection | `decision` | `projections` + Layer 1 | Trace d'audit horodatée |
| Tâche | Layer 1 typé | `task` | `agent_facts` (+ schéma dédié si besoin) | Statut, assignee, deadline |
| Événement | Layer 1 typé | `event` | `agent_facts` (+ schéma dédié si besoin) | Occurrence temporelle |
| Wikilink `[[X]]` | Graphe | edge `REFERENCES` | `graph.relation` | Arête source→cible |

### 3.3 Coexistence de plusieurs ontologies dans un workspace

**Règle :** Chaque ontologie candidate = une famille de `schema_id`. Les entités peuvent appartenir à plusieurs familles si elles sont des **pivot objects** (partagés entre ontologies).

**Pivot objects :** Entités référencées par plusieurs ontologies (ex : un `client` référencé dans `client-knowledge` ET dans `project-plan`).

| Situation | Stratégie |
|---|---|
| Entité appartenant à une seule ontologie | `schema_id` = `<workspace>:<ontology>:<type>` |
| Pivot object partagé | Déclarer une famille neutre ex: `<workspace>:shared:<type>` |
| Relation entre deux ontologies | Edge graphe avec `label` fermé + attribut `cross_ontology: true` |
| Conflit de définition d'un même concept | Désambiguïsation via `source_ref` distinct + note de dérivation |

---

## Section 4 — Stratégie de parsing et d'extraction

### 4.1 Choix de la granularité

**Décision à prendre avant tout parsing.** La granularité conditionne la qualité des entités extraites et le volume de `source_ref` créés.

| Granularité | Quand choisir | Avantages | Risques |
|---|---|---|---|
| **Fichier entier** | Notes courtes (<500 tokens), structure homogène | Simple, peu de `source_ref` | Contexte dilué, entités mélangées |
| **Section logique** | Notes structurées avec `##` headings | Granularité naturelle, alignée sur le sens | Nécessite détection de structure |
| **Chunk fixe** (512 tokens) | Corpus dense, PDF longs, sans structure markdown | Reproductible, parallélisable | Coupe les phrases, perd le contexte |
| **Bloc logique** | Frontmatter + premier paragraphe | Rapide pour le référentiel stable | Ignore le corps de la note |

**Recommandation pour un vault projet web :**
- Notes structurées avec headings → **section logique**
- PDFs longs (brief, spec) → **chunk fixe 512 tokens** avec overlap 50 tokens
- Notes courtes (log de décision, tâche) → **fichier entier**

**La granularité est fixée dans `mvp_core_contract.yaml` avant de commencer.**

### 4.2 Rôle du LLM à chaque étape

| Étape | Input LLM | Output attendu | Contraintes |
|---|---|---|---|
| **Extraction** | Chunk texte brut + contexte vault | Entities brutes, edges bruts | Ne pas halluciner des entités absentes du texte |
| **Normalisation** | Entities brutes + ontologie existante | Facets JSONB normalisé, désambiguïsation | Mapper vers `schema_id` existants si possible |
| **Typage** | Entité brute + liste des `node_type` autorisés | `schema_id`, `node_type` | Liste fermée de types — pas de nouveau type sans DDL |
| **Génération d'arêtes** | Entities + chunk contexte | Edges avec `label` de la liste fermée | Interdiction d'inventer des verbes hors liste |
| **Consolidation** | Tout ce qui précède | JSONB complet validable | Format strict (cf. 4.3) |
| **Assistance DDL** | Schema manquant détecté | Payload `ghostcrab_ddl_propose` | Soumis à validation humaine avant exécution |

**Prompt engineering clé :**
- Fournir au LLM la liste des `schema_id` existants à chaque appel.
- Fournir la liste fermée des `edge labels` autorisés.
- Exiger un JSON valide en sortie (mode JSON si disponible).
- Inclure le `workspace_id` et le contexte JTBD dans le system prompt.

### 4.3 Structure JSONB intermédiaire obligatoire

Le LLM **doit produire exactement** cette structure. Pas de champ supplémentaire, pas de champ manquant.

```json
{
  "source_ref": "<entity-type>:<stable-key>",
  "schema_id": "<workspace-id>:<entity-type>",
  "content": "<texte principal extrait ou résumé>",
  "facets": {
    "title": "<titre de l'entité>",
    "tags": ["<tag1>", "<tag2>"],
    "<clé_frontmatter>": "<valeur>"
  },
  "entities": [
    {
      "id": "ent:<natural-key>",
      "node_type": "<type fermé>",
      "label": "<label lisible>"
    }
  ],
  "edges": [
    {
      "source": "<source_ref ou ent:id>",
      "target": "<source_ref ou ent:id>",
      "label": "<LABEL_LISTE_FERMÉE>"
    }
  ],
  "projection_signal": {
    "proj_type": "<SCREAMING_SNAKE_CASE>",
    "scope": "<workspace_id>:<scope_slug>",
    "status": "active | archived | draft"
  }
}
```

**Champs obligatoires :** `source_ref`, `schema_id`, `content`, `facets`.  
**Champs optionnels :** `entities` (si aucune entité extraite), `edges` (si aucune relation), `projection_signal` (si pas de projection).

### 4.4 Règles de validation du JSONB avant injection

Un script de validation **doit s'exécuter entre la sortie LLM et l'injection GhostCrab**.

| Règle | Vérification | Action si échec |
|---|---|---|
| `source_ref` unique et stable | Hash du path ou UUID stable, pas le titre | Rejeter et loguer |
| `schema_id` namespacé | Préfixé par `workspace_id:` | Rejeter |
| `edge.label` dans liste fermée | Vérifier contre la liste des 8 labels | Remplacer par `ASSOCIATED_WITH` ou rejeter |
| `node_type` dans liste autorisée | Vérifier contre les types déclarés | Rejeter, demander DDL |
| `content` non vide | `len(content) > 10` | Logguer, injecter avec flag `low_quality` |
| `projection_signal.proj_type` en SCREAMING_SNAKE_CASE | Regex `^[A-Z][A-Z_]+$` | Rejeter |
| JSON valide | `json.parse()` sans erreur | Rejeter, loguer le chunk source |
| Pas d'entité dupliquée dans `entities[]` | `ent.id` unique dans le tableau | Dédupliquer |

---

## Section 5 — Mapping Obsidian → GhostCrab MCP

> **Deux familles de facettes (ne pas mélanger).** Les exemples de cette section utilisent le **vocabulaire Obsidian brut** (`status`, `priority`, `tags`) pour le mapping vault → JSONB ingest. Ce sont des clés **provisoires / ingest**, pas la règle finale pour les enums LinkML métier.
>
> | Famille | Quand | Règle | Doc installée |
> |---------|-------|-------|----------------|
> | Ingest vault / repo | Tags, frontmatter, sections Obsidian | Clés courtes dans `agent_facts.facets` | `ghostcrab-shared/PATH_CONTENT_FACETS.md` |
> | Enums LinkML / domaine | Après compile LinkML par module | `<module>.<slot_snake_case>` | `ghostcrab-shared/ENUM_BUSINESS_FACETS.md` |
>
> Voir aussi `ghostcrab-shared/SCHEMA_DESIGN.md` pour le design de schémas avant freeze.

### 5.1 Tags Obsidian → axes de facettes

Les tags Obsidian (`#cms`, `#décision`, `#urgent`) deviennent des clés dans le JSONB `facets`.

| Tag Obsidian | Transformation | Résultat dans `facets` |
|---|---|---|
| `#cms` | Clé `tags[]` | `"tags": ["cms"]` |
| `#status/validée` | Clé `status` (parsing du suffixe) | `"status": "validée"` |
| `#priority/high` | Clé `priority` | `"priority": "high"` |
| `#projet/acme` | Clé `project` | `"project": "acme"` |

**Règle :** Les tags hiérarchiques (`#parent/enfant`) sont parsés pour créer des clés structurées. Les tags plats sont ajoutés au tableau `tags`.

### 5.2 Wikilinks `[[X]]` → edges de graphe

| Wikilink | Edge créé | Label assigné |
|---|---|---|
| `[[Note-A]]` dans Note-B | `source: note:B → target: note:A` | `REFERENCES` |
| `[[Client ACME]]` dans une décision | `source: note:décision → target: ent:acme-corp` | `ASSOCIATED_WITH` |
| `[[Tâche#section]]` | `source: note:parent → target: note:tâche#section` | `PART_OF` |
| `[[Technologie X\|dépend de X]]` | `source: note:parent → target: ent:techno-x` | `DEPENDS_ON` (si alias évocateur) |

**Stratégie :** Par défaut, un wikilink simple génère un edge `REFERENCES`. Le LLM peut affiner le label en contexte lors de l'étape d'extraction.

### 5.3 Frontmatter YAML → `facets` JSONB

Le frontmatter est le mapping le plus direct. Toutes les clés sont préservées.

```yaml
# Frontmatter Obsidian
---
title: "Décision : choix CMS headless"
date: 2024-11-15
status: validée
tags: [cms, technique, décision]
client: acme-corp
phase: conception
---
```

```json
// Résultat dans facets JSONB
{
  "title": "Décision : choix CMS headless",
  "date": "2024-11-15",
  "status": "validée",
  "tags": ["cms", "technique", "décision"],
  "client": "acme-corp",
  "phase": "conception"
}
```

**Règle :** Les clés frontmatter sont préservées telles quelles, sans transformation, sauf normalisation de casse (lowercase).

### 5.4 Sections logiques → `source_ref` distincts

Chaque section `##` d'une note peut devenir un `source_ref` séparé si la granularité choisie est "section logique".

| Note | Section | `source_ref` généré |
|---|---|---|
| `decisions/cms-choice.md` | (fichier entier) | `note:decisions-cms-choice` |
| `decisions/cms-choice.md` | `## Contexte` | `note:decisions-cms-choice#contexte` |
| `decisions/cms-choice.md` | `## Alternatives évaluées` | `note:decisions-cms-choice#alternatives-evaluees` |
| `briefs/client-acme.pdf` | Page 3 | `pdf:brief-client-acme#p3` |

**Règle sur la stabilité :** Le `source_ref` est dérivé du **path de fichier** (pas du titre) + slug de section. Si un fichier est renommé, mettre à jour le `source_ref` via un script de migration, pas à la main.

### 5.5 Fichier `mapping_external_to_canonical.yaml`

Ce fichier traduit les conventions du vault vers les conventions GhostCrab.

```yaml
# mapping_external_to_canonical.yaml
workspace_id: "web-project-acme"

tag_to_facet_key:
  # Tags plats → clés de facettes
  - obsidian_tag: "décision"
    facet_key: "tags"
    facet_value: "decision"
  - obsidian_tag: "tâche"
    facet_key: "tags"
    facet_value: "task"
  
  # Tags hiérarchiques → clés structurées
  - obsidian_tag_prefix: "status/"
    facet_key: "status"
    extract_suffix: true
  - obsidian_tag_prefix: "priority/"
    facet_key: "priority"
    extract_suffix: true
  - obsidian_tag_prefix: "phase/"
    facet_key: "project_phase"
    extract_suffix: true

frontmatter_to_facet:
  # Renommages explicites (si la clé frontmatter ≠ clé facette cible)
  - fm_key: "client"
    facet_key: "client_id"
  - fm_key: "assignee"
    facet_key: "owner"
  # Clés identiques (passthrough) — lister pour documentation
  - fm_key: "title"
    facet_key: "title"
  - fm_key: "date"
    facet_key: "date"
  - fm_key: "status"
    facet_key: "status"

folder_to_schema_family:
  # Dossiers Obsidian → familles de schema_id
  - folder_pattern: "decisions/**"
    schema_family: "web-project-acme:design-decisions"
  - folder_pattern: "clients/**"
    schema_family: "web-project-acme:client-knowledge"
  - folder_pattern: "tasks/**"
    schema_family: "web-project-acme:project-plan"
  - folder_pattern: "content/**"
    schema_family: "web-project-acme:site-content"
  - folder_pattern: "history/**"
    schema_family: "web-project-acme:project-history"

wikilink_to_edge_label:
  # Règles de déduction du label selon le contexte (optionnel — LLM peut affiner)
  - source_schema_family: "web-project-acme:design-decisions"
    target_schema_family: "web-project-acme:client-knowledge"
    default_label: "OWNED_BY"
  - source_schema_family: "web-project-acme:project-plan"
    target_schema_family: "web-project-acme:design-decisions"
    default_label: "DEPENDS_ON"
  - default_label: "REFERENCES"  # fallback universel
```

---

## Section 6 — Convention de nommage (appliquée au vault Obsidian)

### 6.1 Tableau complet des conventions

| Élément | Format | Exemples (projet web) | Règles |
|---|---|---|---|
| `workspace_id` | `kebab-case` | `web-project-acme`, `kb-technique-infra`, `crm-2025` | Pas de majuscules, pas d'espaces, pas de `_` |
| `schema_id` | `<workspace_id>:<entity-type>` | `web-project-acme:decision`, `web-project-acme:task`, `web-project-acme:concept` | Toujours préfixé par workspace |
| `source_ref` | `<entity-type>:<natural-key>` | `note:decisions-cms-choice`, `pdf:brief-acme#p3`, `ent:acme-corp` | Stable, dérivé du path, jamais du titre |
| `proj_type` | `SCREAMING_SNAKE_CASE` | `AUDIT_DECISION`, `AUDIT_TASK_COMPLETION`, `AUDIT_MILESTONE_REACHED` | Préfixe par stage : `AUDIT_`, `SIGNAL_`, `REVIEW_` |
| `node_type` | `lowercase-kebab` | `concept`, `client`, `decision`, `task`, `document`, `reference` | Liste fermée, déclarée dans specs |
| Edge labels | `SCREAMING_SNAKE_CASE` (liste fermée) | `REFERENCES`, `DEPENDS_ON`, `ASSOCIATED_WITH`, `OBSERVED_ON`, `OWNED_BY`, `LOCATED_IN`, `PART_OF`, `CONNECTED_TO` | 8 labels maximum, aucun ajout sans DDL |
| `ent:id` | `ent:<natural-key>` | `ent:cms-headless`, `ent:acme-corp`, `ent:phase-conception` | Kebab-case, unique dans le workspace |

### 6.2 Exemples concrets (projet web ACME)

```
workspace_id    → web-project-acme
schema_id       → web-project-acme:decision
                → web-project-acme:client
                → web-project-acme:task
                → web-project-acme:milestone

source_ref      → note:decisions-cms-choice
                → note:decisions-cms-choice#alternatives-evaluees
                → pdf:brief-client-acme
                → pdf:brief-client-acme#p3
                → ent:acme-corp
                → ent:cms-headless

proj_type       → AUDIT_DECISION
                → AUDIT_TASK_COMPLETION
                → SIGNAL_MILESTONE_REACHED
                → REVIEW_CLIENT_APPROVAL

edge labels     → note:decisions-cms-choice DEPENDS_ON ent:cms-headless
                → ent:acme-corp OWNS note:decisions-cms-choice   [OWNED_BY inversé]
                → note:task-001 PART_OF note:phase-conception
                → note:decisions-cms-choice REFERENCES pdf:brief-client-acme#p3
```

---

## Section 6 bis — Voie LinkML (`ontology_path.choice: linkml`, format par défaut)

> **Prérequis :** Phase B0 complétée — choix `linkml` enregistré dans `{starterkit}/templates/import_path_choices.yaml` (voir [SOP0](SOP0_import_path_choices.md)). Ne pas utiliser cette section si l'utilisateur a choisi la voie MCP incrémentale (section 7, `mcp_incremental`).

Cette voie enregistre l'ontologie comme artefact LinkML versionné, compilé et importé via le CLI MindBrain. Le LLM **génère** et **valide** le fichier ; l'import DB n'a lieu qu'après confirmation explicite.

### 6 bis.1 Artefacts

| Fichier | Rôle |
|---------|------|
| `../templates/linkml_ontology.stub.yaml` | Squelette de départ |
| `ontology/core.yaml` | Ontologie domaine mono-module (défaut) |
| `ontology/<module>.yaml` | Ontologie multi-modules (un fichier par module LinkML) |
| `ontology/<workspace>-contract.yaml` | Contrat central multi-ontologies : nommage public/interne, aliases, imports, ordre d'import, mappingProfile, gates |
| `../scripts/generate_linkml_from_ontology_json.py` | Générateur JSON ontologique → YAML LinkML, à utiliser si les JSON existent déjà |
| `../scripts/validate_ontology_json_vs_linkml.py` | Gate read-only JSON ontologique ↔ LinkML avant import |
| `output/ontology-slice.json` | Sortie dry-run compile (inspection) |

Références optionnelles : [ghostcrab-personal-mcp `ontologies/immeuble-demo`](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp/tree/main/ontologies/immeuble-demo) (mono-module).

### 6 bis.2 Séquence

1. Compléter `jtbd.yaml` et obtenir confirmation du Model Proposal (identique voie MCP incrémentale).
2. Copier `../templates/linkml_ontology.stub.yaml` vers `ontology/core.yaml`.
3. Le LLM étend le stub : classes, enums, slots, annotations `ghostcrab.native_entity_type` / `ghostcrab.native_edge_type`.
4. Si le modèle est multi-module, dérivé de JSON, ou contient des renommages/aliases, produire `ontology/<workspace>-contract.yaml` avant tout import. Le contrat central doit figer :
   - `workspace_id`, edition, backend et statut de décision ;
   - ontologies canoniques, labels publics, rôles internes et aliases historiques ;
   - imports attendus, ordre d'import, entrypoints techniques ;
   - règles `mappingProfile` pour API/applications externes ;
   - gates de validation et section `aliases` / `checks` consommée par le validateur.
5. Si des JSON ontologiques existent déjà, générer d'abord une base LinkML complète dans un dossier séparé :
   ```bash
   python3 ../scripts/generate_linkml_from_ontology_json.py \
     --json-dir ontology \
     --manifest ontology/manifest.json \
     --config ontology/<workspace>-contract.yaml \
     --output-dir generated/linkml_from_json \
     --write-entrypoint \
     --report generated/linkml_from_json/generation_report.json
   ```
   Relire les warnings du rapport avant de promouvoir les YAML générés dans `ontology/`.
6. **Validation JSON ↔ LinkML** (obligatoire si des JSON ontologiques existent, sans écriture DB) :
   ```bash
   python3 ../scripts/validate_ontology_json_vs_linkml.py \
     --json-dir ontology \
     --linkml-dir generated/linkml_from_json \
     --manifest ontology/manifest.json \
     --config ontology/<workspace>-contract.yaml \
     --output generated/<workspace_id>/reports/json_vs_linkml.validation.json \
     --markdown-output generated/<workspace_id>/reports/json_vs_linkml.validation.md
   ```
   `ok=false` bloque l'import si le rapport contient des `blocking` réels : classes manquantes, slots manquants, edges absents, enums non préservés, imports divergents. Les aliases validés dans le contrat ne sont pas des erreurs.
7. **Validation dry-run LinkML** (obligatoire, sans écriture DB) :
   ```bash
   gcp brain ontology compile \
     --workspace-id <workspace_id> \
     --ontology-id <workspace_id>::core \
     --input ontology/core.yaml \
     --output output/ontology-slice.json
   ```
8. Corriger `core.yaml` jusqu'à exit 0 ; vérifier cohérence JTBD ↔ classes/enums/relations.
9. Présenter le résumé ontologique à l'utilisateur et obtenir confirmation.
10. **Import** :
   ```bash
   gcp brain ontology compile \
     --workspace-id <workspace_id> \
     --ontology-id <workspace_id>::core \
     --input ontology/core.yaml \
     --import-db --force
   ```
11. Vérification post-import : `ghostcrab_ontology_list`, `ghostcrab_coverage`.

**Multi-module :** générer et valider l'ensemble une fois, puis répéter les étapes 7–11 par module avec `ontology_id: <workspace_id>::<module>`. Ordre de compile recommandé (catalogue Serenity V4) : `production` → `administrative` → `comptabilite` → `decisionnel` → `technique` → `missions` — voir `ghostcrab-shared/ENUM_BUSINESS_FACETS.md` pour la liste complète des enum facets par module. Enregistrer la liste dans `import_path_choices.yaml` → `artefacts.ontology_modules`.

### 6 bis.2a — Contrat central multi-ontologies

Créer ce contrat quand au moins une condition est vraie : plusieurs ontologies, présence d'artefacts JSON en plus des YAML LinkML, renommage public/interne, aliases historiques, entrypoint technique distinct, ou couche `mappingProfile`.

Structure minimale :

```yaml
workspace_id: <workspace_id>
contract_kind: ontology_bundle_contract
edition: personal-mcp
status: draft|confirmed

naming_policy:
  public_labels_are_client_language: true
  internal_roles_are_explicit: true

canonical_domains:
  - id: production
    public_label: Production
    role: shared_client_referential
  - id: mapping-profile
    public_label: mappingProfile
    role: external_app_mapping_layer

aliases:
  ontology:
    core: production
  concepts: {}
  properties: {}
  edges: {}

checks:
  require_all_json_nodes_in_linkml: true
  require_all_json_properties_in_linkml: true
  require_all_json_edges_in_linkml: true
  require_imports_match_manifest: true
  allow_aliases: true
```

Ce fichier est à la fois un contrat humain et la configuration du validateur. Les noms clients restent stables ; les rôles internes servent seulement à désambiguïser les couches techniques.

### 6 bis.2b — Enum facet layer (LinkML → MCP)

Après import LinkML par module, enregistrer la **couche enum métier** (automatiquement — ne pas attendre que l'utilisateur demande le préfixage).

**Règle obligatoire :** `<module>.<slot_snake_case>` (ex. `administrative.formule_service`, `comptabilite.statut_exercice`).

| Famille | Exemples de clés | Doc |
|---------|------------------|-----|
| Ingest Obsidian (tags, frontmatter) | `status`, `tags`, `priority` dans `agent_facts.facets` | Vocabulaire ingest — pas de préfixe module requis |
| Enums LinkML / domaine | `production.statut_copropriete`, `missions.statut_mission` | Installé : `ghostcrab-shared/ENUM_BUSINESS_FACETS.md` |

Workflow MCP (après confirmation utilisateur) :

1. `ghostcrab_ontology_import` (ou `gcp brain ontology compile --import-db`) par module
2. `ghostcrab_schema_register` avec `target: "facets"`, `schema_id: "<workspace_id>:<module>"`, corps avec `facet_keys` + `enum_facets`
3. `ghostcrab_facet_register` pour chaque clé enum
4. Valider : `ghostcrab_facet_inspect("<module>.<slot>")`, `ghostcrab_schema_list(domain="<workspace_id>", target="facets")`

`ghostcrab_workspace_inspect` vide **avant structured-import** n'est pas une erreur.

### 6 bis.3 Variante avancée (non défaut)

OWL/N-Triples normalisés :

```bash
gcp brain ontology import \
  --workspace-id <workspace_id> \
  --ontology-id <workspace_id>::owl \
  --input ./ontology.nt \
  --materialize-graph
```

### 6 bis.4 Alternative historique

Pour l'enregistrement progressif via MCP (`ghostcrab_schema_register`, `remember`, `upsert`, `learn`), voir **section 7 — Voie MCP incrémentale**.

---

## Section 7 — Voie MCP incrémentale (`ontology_path.choice: mcp_incremental`)

> **Prérequis :** Phase B0 complétée — choix `mcp_incremental` enregistré dans `{starterkit}/templates/import_path_choices.yaml`. Pour la voie LinkML par défaut, voir section 6 bis.

### 7.1 Vue d'ensemble

```
Étape 1  → Créer le workspace
Étape 2  → Enregistrer les schémas (un par ontologie candidate)
Étape 3  → Seed le référentiel stable
Étape 4  → Injecter les facettes
Étape 5  → Créer les edges de graphe
Étape 6  → Créer les projections initiales
Étape 7  → Valider
```

### 7.2 Étape 1 — Créer le workspace

```json
// ghostcrab_workspace_create
{
  "workspace_id": "web-project-acme",
  "label": "Refonte site web ACME Corp",
  "description": "Vault Obsidian : pilotage complet de la refonte site ACME",
  "config": {
    "chunking_strategy": "section_logical"
  }
}
```

**Pré-requis :** `workspace_id` unique. Backend SQLite via `ghostcrab-personal-mcp` — pas de DDL PostgreSQL Layer 1.

### 7.3 Étape 2 — Enregistrer les schémas

Un appel par ontologie candidate. L'ordre suit la dépendance (les pivots en premier).

> **Facet keys dans cette voie :** les clés ci-dessous sont **ingest / entité** (Obsidian frontmatter, pas enums LinkML). Pour les enums métier après LinkML, utiliser la voie 6 bis.2b et `<module>.<slot_snake_case>` (`ghostcrab-shared/ENUM_BUSINESS_FACETS.md`). Pour l'ingest documentaire, voir `ghostcrab-shared/PATH_CONTENT_FACETS.md`.

```json
// ghostcrab_schema_register — exemple décision (ingest / entité, pas enum LinkML)
{
  "workspace_id": "web-project-acme",
  "schema_id": "web-project-acme:decision",
  "node_type": "decision",
  "label": "Décision projet",
  "facet_keys": ["title", "date", "status", "tags", "client", "phase"],
  "required_facets": ["title", "date", "status"],
  "projection_types_allowed": ["AUDIT_DECISION", "REVIEW_CLIENT_APPROVAL"]
}
```

Exemple **enum facet LinkML** (voie 6 bis.2b, pas cette étape MCP incrémentale) :

```json
// ghostcrab_schema_register — target: "facets", schema_id: "<workspace_id>:<module>"
{
  "workspace_id": "web-project-acme",
  "schema_id": "web-project-acme:administrative",
  "target": "facets",
  "facet_keys": ["administrative.formule_service", "administrative.statut_contrat"],
  "enum_facets": {
    "administrative.formule_service": ["FDRO", "FDRS", "FDROP"],
    "administrative.statut_contrat": ["actif", "resilie", "en_cours"]
  }
}
```

**Ordre recommandé :**
1. Schémas pivots partagés (`shared:client`, `shared:concept`)
2. Schémas référentiel stable (`design-decisions:decision`, `project-plan:task`)
3. Schémas documentaires (`client-knowledge:document`)
4. Schémas projection (`project-history:milestone`)

### 7.4 Étape 3 — Seed le référentiel stable

Injecter les entités stables identifiées dans `initial_referential.yaml` : liste de clients, types de tâches, phases de projet, personnes.

```json
// ghostcrab_remember — seed entité stable
{
  "workspace_id": "web-project-acme",
  "source_ref": "ent:acme-corp",
  "schema_id": "web-project-acme:client",
  "content": "ACME Corp — client principal du projet de refonte",
  "facets": {
    "title": "ACME Corp",
    "type": "client",
    "status": "active"
  }
}
```

### 7.5 Étape 4 — Injecter les facettes

Pour chaque JSONB validé produit par le LLM :

```json
// ghostcrab_upsert — injection facette principale
{
  "workspace_id": "web-project-acme",
  "source_ref": "note:decisions-cms-choice",
  "schema_id": "web-project-acme:decision",
  "content": "Décision de choisir un CMS headless pour découpler le front...",
  "facets": {
    "title": "Décision : choix CMS headless",
    "date": "2024-11-15",
    "status": "validée",
    "tags": ["cms", "technique", "décision"],
    "client": "acme-corp",
    "phase": "conception"
  }
}
```

**Comportement upsert :** Si `source_ref` existe → mise à jour. Si absent → création. Idempotence via contrainte unique sur `source_ref` dans SQLite `agent_facts`.

**Volume :** pour un vault entier, préférer [SOP3](SOP3_parsing_pipeline.md) → [SOP6](SOP6_gcp_document_import.md) ou `gcp brain structured-import` ([SOP5](SOP5_structured_import.md)) — pas d'injection MCP unitaire en masse.

### 7.6 Étape 5 — Créer les edges de graphe

```json
// ghostcrab_learn — edge de graphe
{
  "workspace_id": "web-project-acme",
  "source": "note:decisions-cms-choice",
  "target": "ent:cms-headless",
  "label": "DEPENDS_ON",
  "attributes": {
    "extracted_by": "llm",
    "confidence": 0.92,
    "chunk_ref": "note:decisions-cms-choice#contexte"
  }
}
```

**Règles :**
- Injecter les edges après les entités qu'ils relient (sinon erreur de référence).
- `confidence` est un attribut informatif, pas un filtre automatique.

### 7.7 Étape 6 — Créer les projections initiales

```json
// ghostcrab_project — projection décision
{
  "workspace_id": "web-project-acme",
  "source_ref": "note:decisions-cms-choice",
  "proj_type": "AUDIT_DECISION",
  "scope": "web-project-acme:refonte-acme",
  "status": "active",
  "metadata": {
    "decision_date": "2024-11-15",
    "validated_by": "client",
    "impact": "high"
  }
}
```

### 7.8 Étape 7 — Valider l'injection

Exécuter dans l'ordre :

| Appel | Vérification attendue |
|---|---|
| `ghostcrab_schema_list` | Tous les schémas enregistrés présents |
| `ghostcrab_coverage` | Taux de couverture des `source_ref` par schéma |
| `ghostcrab_status` | Workspace en état `active`, pas d'erreurs |
| `ghostcrab_search(query="cms")` | Retourne les entités liées au CMS |
| `ghostcrab_traverse(from="ent:acme-corp")` | Retourne le graphe autour du client |
| `ghostcrab_pack(scope="web-project-acme:refonte-acme")` | Pack de projections cohérent |

**Seuil d'acceptation :** Coverage ≥ 80% sur les schémas core. 0 erreur de validation de schéma.

---

## Section 8 — Gestion des cas complexes

### 8.1 Notes modifiées après injection (upsert)

| Situation | Stratégie |
|---|---|
| Frontmatter modifié | Re-parser la note, appeler `ghostcrab_upsert` avec le même `source_ref` |
| Titre modifié | `source_ref` inchangé (dérivé du path, pas du titre) → pas d'impact |
| Note déplacée | `source_ref` change (path nouveau) → **V1 :** pas d'outil `ghostcrab_delete`. Migrer avec `ghostcrab_upsert` sur l'ancien `source_ref` en marquant `facets.status: "deleted"` (tombstone), puis `ghostcrab_remember` / `ghostcrab_upsert` sur le nouveau `source_ref` ; nettoyer le graphe (`graph.relation`) si besoin via re-sync ou SQL ciblé. |
| Note supprimée | **V1 :** même approche — `ghostcrab_upsert` avec tombstone `status: "deleted"` sur le `source_ref` ; suppression définitive des lignes (hard delete) uniquement via SQL manuel sur `agent_facts` / graphe si la politique du workspace l'exige. |
| Contenu réécrit | Re-extraire avec LLM, `ghostcrab_upsert`, re-générer les edges (diff d'edges si nécessaire) |

**Pattern recommandé :** Mantenir un fichier `sync_state.json` avec `{source_ref: last_modified_timestamp}` pour détecter les changements sans re-parser tout le vault.

### 8.2 PDF dont le parsing est bruité

| Problème | Symptômes | Stratégie |
|---|---|---|
| PDF scanné (image) | Texte vide ou charabia | OCR préalable (Tesseract, AWS Textract) avant parsing |
| PDF avec colonnes multiples | Texte mélangé entre colonnes | Extraction par bloc (PyMuPDF `get_text("blocks")`) |
| PDF protégé | Erreur d'extraction | Signaler dans le log, passer — ne pas bloquer le pipeline |
| Tables dans le PDF | Tables parsées comme du texte linéaire | Extraction spécifique des tables (camelot, pdfplumber) |
| PDF très long (>50 pages) | Contexte LLM dépassé | Chunking fixe 512 tokens avec overlap, traiter par batch |

**Règle préventive :** Tester sur 2-3 PDF représentatifs avant de fixer la stratégie de parsing pour tout le vault.

### 8.3 Collisions sémantiques entre fichiers du même vault

Un même concept peut apparaître sous plusieurs formes : `client`, `Customer`, `compte client`, `ACME`, `ACME Corp`.

| Stratégie | Quand utiliser | Implémentation |
|---|---|---|
| **Dictionnaire de synonymes** | Termes connus et stables | `disambiguation.yaml` : `{synonyms: ["client", "Customer", "compte client"] → canonical: "ent:acme-corp"}` |
| **Clustering par LLM** | Corpus large, termes inconnus | Passer une liste d'entités extraites au LLM, lui demander de regrouper |
| **Pivot par `ent:id`** | Relations déjà établies | Forcer le mapping vers `ent:id` canonique lors de la normalisation |
| **Flag `ambiguous: true`** | Incertitude résiduelle | Marquer l'entité, résoudre en post-processing humain |

**Règle :** Le fichier `disambiguation.yaml` est créé et maintenu manuellement pour le vocabulaire core. Le LLM ne peut pas modifier ce fichier.

### 8.4 Vault multi-projets nécessitant plusieurs workspaces

| Situation | Décision |
|---|---|
| Projets indépendants dans le même vault | Un workspace par projet (`web-project-acme`, `web-project-beta`) |
| Entités partagées entre projets | Workspace commun (`shared-referential`) + edges cross-workspace déclarés |
| Vault de veille couvrant plusieurs domaines | Un workspace par domaine si isolation des droits requise |
| Wiki personnel polyvalent | Un seul workspace, plusieurs familles `schema_id` |

**Critère de décision :** Si deux projets ne partagent aucune entité et ont des cycles de vie indépendants → workspaces séparés. Sinon → familles `schema_id` dans un workspace commun.

### 8.5 Dérive du schéma — nouveau type d'entité détecté en cours de parsing

**Processus obligatoire :**

1. Le LLM détecte un type d'entité non reconnu → génère un payload `ghostcrab_ddl_propose`.
2. Le script de validation **bloque l'injection** de cette entité.
3. Le payload DDL est logué dans `pending_ddl.json`.
4. Un humain review le payload, le valide ou le rejette.
5. Si validé → `ghostcrab_ddl_execute` → nouveau schéma disponible → relancer le parsing du chunk concerné.
6. Si rejeté → mapper vers le type existant le plus proche ou créer un type `generic:concept`.

**Anti-pattern à éviter :** Ne jamais laisser le LLM appeler `ghostcrab_ddl_execute` directement sans validation humaine.

---

## Section 9 — Hypothèses à confirmer avant de démarrer

### 9.1 Hypothèses critiques (haute)

| # | Hypothèse | Question à lever | Comment valider |
|---|---|---|---|
| H1 | Le vault a une structure de dossiers représentative des JTBD | Est-ce que les dossiers reflètent les sous-jobs ou sont-ils arbitraires ? | Audit manuel du vault, interview du propriétaire |
| H2 | Les frontmatter sont homogènes entre les notes d'une même catégorie | Les clés frontmatter sont-elles standardisées ou anarchiques ? | `grep -r "^---" vault/ | head -100` + analyse |
| H3 | Le parsing PDF est faisable (pas de scans, pas de protection) | Les PDFs sont-ils extractibles ou nécessitent-ils OCR ? | Tester `pdfplumber` sur 3 PDFs représentatifs |
| H4 | PostgreSQL est disponible avec les extensions GhostCrab | GhostCrab MCP est-il configuré et connecté ? | `ghostcrab_status` call |
| H5 | La granularité "section logique" est applicable | Les notes ont-elles des `##` headings cohérents ? | Audit de 20 notes représentatives |

### 9.2 Hypothèses moyennes

| # | Hypothèse | Question à lever | Comment valider |
|---|---|---|---|
| H6 | Les wikilinks sont maintenus et non brisés | Y a-t-il des wikilinks vers des notes inexistantes ? | `grep -r "\[\[" vault/ + vérification existence` |
| H7 | Les tags Obsidian suivent une convention hiérarchique | La taxonomie `#parent/enfant` est-elle utilisée ? | Extraire tous les tags distincts et analyser |
| H8 | Le volume de notes est traitable en un batch | Combien de notes et de PDF ? Estimation tokens ? | `find vault/ -name "*.md" | wc -l` + taille moyenne |
| H9 | Les ontologies candidates correspondent aux JTBD réels | Le `jtbd.yaml` a-t-il été validé par l'utilisateur du vault ? | Session de revue du JTBD avec le propriétaire |
| H10 | Le `workspace_id` est définitif | Le slug peut-il changer en cours de projet ? | Décision à figer dans `mvp_core_contract.yaml` |

### 9.3 Hypothèses basses

| # | Hypothèse | Question à lever | Comment valider |
|---|---|---|---|
| H11 | Les noms de fichiers sont en ASCII ou UTF-8 sans caractères spéciaux | Y a-t-il des notes avec accents dans le filename ? | `ls vault/**/*.md | grep -P "[^\x00-\x7F]"` |
| H12 | Pas de dépendances circulaires dans les wikilinks | Le graphe de wikilinks est-il acyclique ou cyclique gérable ? | Analyse graphe avec NetworkX |
| H13 | Le LLM cible est accessible et stable | Quotas, latence, mode JSON disponible ? | Test d'un appel de parsing sur un chunk réel |

---

## Section 10 — Acceptance criteria du contexte

Ces critères permettent de juger si la préparation est suffisante avant de passer à l'implémentation.

### 10.1 Setup workspace et schémas

```gherkin
Given un vault Obsidian avec au moins 10 notes structurées
When ghostcrab_workspace_create est appelé avec workspace_id "web-project-acme"
Then le workspace est créé avec statut "active"
  And ghostcrab_schema_list retourne au moins 3 schema_id distincts
  And ghostcrab_status ne retourne aucune erreur
```

### 10.2 Parsing et JSONB

```gherkin
Given une note .md avec frontmatter YAML et 2 sections logiques
When le pipeline de parsing est exécuté sur cette note
Then 2 JSONB distincts sont produits (un par section)
  And chaque JSONB contient source_ref, schema_id, content, facets
  And les source_ref sont stables et distincts
  And le validator ne retourne aucune erreur de schéma
```

### 10.3 Injection et graphe

```gherkin
Given un JSONB validé avec 2 entités et 1 edge
When ghostcrab_upsert est appelé puis ghostcrab_learn
Then ghostcrab_search("cms") retourne l'entité "cms-headless"
  And ghostcrab_traverse(from="ent:acme-corp") retourne au moins 1 voisin
  And l'edge label est dans la liste fermée des 8 labels
```

### 10.4 Couverture ontologique

```gherkin
Given un vault de 50 notes entièrement parsé
When ghostcrab_coverage est appelé
Then le taux de couverture est >= 80% sur les schémas core
  And le nombre de source_ref orphelins (sans schema_id) est < 5%
  And aucun schema_id non-namespacé n'est présent dans la base
```

### 10.5 Résistance aux mises à jour

```gherkin
Given une note déjà injectée avec source_ref "note:decisions-cms-choice"
When le frontmatter est modifié (status: validée → status: archivée)
  And ghostcrab_upsert est rappelé avec le même source_ref
Then la facette status est mise à jour à "archivée"
  And aucun doublon n'est créé dans agent_facts
  And les edges existants sont préservés
```

### 10.6 Rejet des non-conformités

```gherkin
Given un JSONB produit par le LLM avec un edge label inventé "INSPIRED_BY"
When le validator de JSONB s'exécute
Then l'injection est bloquée
  And un message d'erreur précise le label non autorisé
  And le JSONB est logué dans pending_review.json
```

---

## Annexe A — Fichiers specs à produire en premier

Ordre de production obligatoire avant tout parsing :

```
specs/
  jtbd.yaml                           # 1er — JTBD principal + sous-jobs + ontologies candidates
  mvp_core_contract.yaml              # 2e — workspace_id, backend, chunking_strategy, DDL authority
  ontology_core_provisioning.yaml     # 3e — schémas GhostCrab par ontologie (un bloc par JTBD/ontology_candidate)
  initial_referential.yaml            # 4e — entités stables à seeder (clients, types, phases)
  mapping_external_to_canonical.yaml  # 5e — mapping tags/dossiers/frontmatter → schema_id
  disambiguation.yaml                 # 6e — dictionnaire de synonymes et pivots canoniques
ontology/
  <workspace>-contract.yaml           # conditionnel — contrat central multi-ontologies / JSON / aliases / mappingProfile
```

## Annexe B — Liste fermée des edge labels

| Label | Usage | Direction sémantique |
|---|---|---|
| `REFERENCES` | Lien documentaire générique (wikilink par défaut) | source mentionne target |
| `DEPENDS_ON` | Dépendance technique ou logique | source ne peut fonctionner sans target |
| `ASSOCIATED_WITH` | Association sémantique non directionnelle | source est lié à target |
| `OBSERVED_ON` | Événement ou mesure temporelle | source observé à target (date/contexte) |
| `OWNED_BY` | Appartenance / responsabilité | source appartient à target |
| `LOCATED_IN` | Localisation (géo, projet, phase) | source se trouve dans target |
| `PART_OF` | Composition / appartenance structurelle | source est une partie de target |
| `CONNECTED_TO` | Connexion réseau ou système | source est connecté à target |

**Règle absolue :** Aucun label hors de cette liste. Le LLM doit mapper vers le label le plus proche. En dernier recours : `ASSOCIATED_WITH`.

---

*Fin de SOP 2 — Version 1.0*
