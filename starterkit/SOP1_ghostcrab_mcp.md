# SOP 1 — GhostCrab MCP : Surface serveur et interfaçage avec la base de données pour modéliser une ontologie

**Version :** 1.0  
**Statut :** Draft technique  
**Périmètre :** Architecture GhostCrab MCP — modélisation, requête, persistance ontologique  

---

> **⚠ Prérequis — Phase A obligatoire avant d'exécuter cette SOP**
>
> Cette SOP couvre la Phase B (modélisation ontologique) et la Phase C (ingestion). Elle suppose que GhostCrab MCP est **déjà déployé et opérationnel**.
>
> Avant de commencer : charger **SOP4_environment_bootstrap.md** et valider tous les checkpoints Phase A :
> - Docker PostgreSQL en bonne santé (`ghostcrab_postgres_native` ou `ghostcrab_postgres`)
> - Migrations appliquées (`npm run migrate` réussi)
> - Smoke test passant (`npm run smoke:mcp`)
> - `ghostcrab_status` retourne `native_readiness: true` (mode natif) ou `native_readiness: false` (mode fallback accepté)
> - MCP client connecté (outils `ghostcrab_*` visibles dans l'agent)
>
> Référence de contrat initial : `specs/mvp_core_contract.yaml` dans le repo `ghostcrab-mcp`.

---

## Section 1 — Vue d'ensemble : rôle de GhostCrab MCP dans l'architecture

### 1.1 Positionnement dans la stack

GhostCrab MCP est une **surface de modélisation et de requête** exposant 24 outils `ghostcrab_*` via le Model Context Protocol. Il permet à un agent ou à un humain de concevoir, interroger et auditer une ontologie stockée dans PostgreSQL, sans jamais servir de chemin d'ingestion de données en volume.

| Fonction | Responsable | Chemin |
|---|---|---|
| Modélisation du schéma ontologique | GhostCrab MCP | `ghostcrab_ddl_propose` → approbation → `ghostcrab_ddl_execute` |
| Requête et lecture des faits | GhostCrab MCP | Outils `ghostcrab_search`, `ghostcrab_traverse`, `ghostcrab_pack` |
| Persistance de faits unitaires | GhostCrab MCP (SQL) | `ghostcrab_remember`, `ghostcrab_learn`, `ghostcrab_project` |
| **Ingestion hot-path (bulk/streaming)** | **SQL direct — jamais MCP** | pgx (Go) ou psycopg2 (Python) → écriture directe PostgreSQL |

### 1.2 Règle fondamentale — MCP ≠ hot-path

> **Le MCP n'est pas une voie d'ingestion.** Toute écriture en volume ou en temps réel passe directement en SQL via le DSN PostgreSQL. Le MCP intervient avant (conception du modèle) et après (requête, audit) l'ingestion.

### 1.3 Extensions natives sous-jacentes

| Extension | Rôle |
|---|---|
| `pg_facets` | Recherche facettée, BM25, agrégats, hiérarchies |
| `pg_dgraph` | Graphe de connaissance, traversal multi-hop, scoring de confiance |
| `pg_pragma` | Contexte opérationnel, projections, snapshots |

Autres composants : PostgreSQL 17, pgvector, roaringbitmap, PGMQ, pg_cron.

---

## Section 2 — Inventaire des 24 outils par fonction ontologique

### 2.1 Subsystème Workspace (7 outils)

| Outil | Fonction ontologique | Chemin | Écrit / Lit dans DB | Quand l'utiliser |
|---|---|---|---|---|
| `ghostcrab_workspace_create` | Initialise un espace de modélisation isolé | SQL (idempotent) | Crée `mindbrain.workspaces` + schéma PostgreSQL dédié (Layer 1) | Premier acte avant toute modélisation |
| `ghostcrab_workspace_list` | Inventaire des espaces actifs | SQL | Lit `mindbrain.workspaces` + stats live | Audit, découverte |
| `ghostcrab_workspace_inspect` | Introspection Layer 1 + sémantiques | SQL | Lit `table_semantics`, `column_semantics`, `relation_semantics` | Vérification de cohérence du modèle |
| `ghostcrab_workspace_export_model` | Export du modèle en JSON contractualisé | SQL | Lit ensemble des sémantiques du workspace | Contractualisation inter-équipes, versioning |
| `ghostcrab_ddl_propose` | Propose une migration DDL (DDL + triggers sync) | SQL | Écrit dans `pending_migrations` ; génère trigger Layer 1→2 si `sync_spec` fourni | Évolution du schéma ontologique |
| `ghostcrab_ddl_list_pending` | Liste les migrations en attente / approuvées / exécutées | SQL | Lit `pending_migrations` | Suivi du cycle de vie DDL |
| `ghostcrab_ddl_execute` | Exécute une migration approuvée (atomique) | SQL (transaction) | Exécute DDL + triggers en une transaction sur le workspace | Après approbation humaine |

### 2.2 Subsystème Facettes (8 outils)

| Outil | Fonction ontologique | Chemin | Écrit / Lit dans DB | Quand l'utiliser |
|---|---|---|---|---|
| `ghostcrab_remember` | Insère un fait dans le fact store | SQL | INSERT `mfo_facets` (`content`, `facets`, `schema_id`, `workspace_id`, `source_ref`, `embedding` optionnel) | Persistance unitaire d'un fait ontologique |
| `ghostcrab_upsert` | Met à jour ou crée un fait état-courant | SQL | UPDATE/INSERT `mfo_facets` | Mise à jour d'un fait dont l'état courant prime |
| `ghostcrab_search` | Recherche de faits | Natif BM25 (`mode: "bm25"`) si pg_facets ready ; SQL sinon | Lit `mfo_facets` | Interrogation de l'ontologie en langage naturel ou filtres |
| `ghostcrab_count` | Agrégats sur les facettes | Natif si dimensions enregistrées + pas de JSONB filters ; SQL sinon | Lit `mfo_facets` | Métriques de couverture, distribution |
| `ghostcrab_facet_tree` | Hiérarchie des facettes | Natif si pg_facets ready ; SQL sinon | Lit `mfo_facets` + structures pg_facets | Navigation arborescente de l'ontologie |
| `ghostcrab_schema_register` | Enregistre un schéma de facettes (metadata uniquement, pas DDL) | SQL | Écrit dans `mindbrain` (metadata schéma) | Déclaration d'un nouveau type d'entité |
| `ghostcrab_schema_list` | Liste les schémas enregistrés | SQL | Lit metadata schémas | Audit des types d'entités déclarés |
| `ghostcrab_schema_inspect` | Inspecte un schéma | SQL | Lit metadata schéma + sémantiques associées | Vérification avant écriture de faits |

### 2.3 Subsystème Graphe (5 outils)

| Outil | Fonction ontologique | Chemin | Écrit / Lit dans DB | Quand l'utiliser |
|---|---|---|---|---|
| `ghostcrab_learn` | Upsert nœud et/ou arête | SQL | Écrit `graph.entity` et/ou `graph.relation` | Enrichissement du graphe de connaissance |
| `ghostcrab_traverse` | Traversal du graphe | Natif depth=1 sans target via `entity_neighborhood` ; SQL CTE récursive sinon | Lit `graph.entity`, `graph.relation` | Navigation multi-hop dans l'ontologie |
| `ghostcrab_marketplace` | Recherche marketplace sur le graphe | Natif (pg_dgraph requis) | Lit `graph.entity`, `graph.entity_degree` | Découverte d'entités par scoring de confiance |
| `ghostcrab_patch` | Écriture/opération graphe native | Natif | Écrit `graph.entity` / `graph.relation` | Mises à jour atomiques nécessitant pg_dgraph |
| `ghostcrab_coverage` | Couverture ontologie + confidence decay | SQL / natif | Lit `graph.entity`, `graph.relation` | Audit qualité : trous et dégradation de confiance |

### 2.4 Subsystème Pragma (3 outils)

| Outil | Fonction ontologique | Chemin | Écrit / Lit dans DB | Quand l'utiliser |
|---|---|---|---|---|
| `ghostcrab_project` | Crée ou met à jour une projection (trace opérationnelle) | SQL | INSERT/UPDATE `mfo_projections` (`scope`, `content`, `proj_type`, `status`, `agent_id`) | Audit trail, matérialisation d'une vue ontologique |
| `ghostcrab_pack` | Lecture contexte courant | Natif si pg_pragma ready + pas de `scope` en argument ; SQL sinon | Lit `mfo_projections` + contexte runtime | Restitution d'un contexte opérationnel à l'agent |
| `ghostcrab_status` | Snapshot cross-cutting | SQL + probe native | Lit `runtime.native_readiness`, `runtime.capabilities`, `runtime.backends` | Vérification santé avant opération critique |

### 2.5 Subsystème Geo (1 outil — optionnel)

| Outil | Fonction ontologique | Chemin | Écrit / Lit dans DB | Quand l'utiliser |
|---|---|---|---|---|
| `ghostcrab_query_geo` | Requête géographique | SQL (PostGIS requis) | Lit `geo_entities` | Ontologies à dimension spatiale |

---

## Section 3 — Contrat d'interfaçage DB

### 3.1 Création d'un workspace

**Action :** `ghostcrab_workspace_create`

**Ce que PostgreSQL reçoit :**

| Artefact créé | Détail |
|---|---|
| Record dans `mindbrain.workspaces` | Identifiant unique, nom, statut, timestamps |
| Schéma PostgreSQL dédié | Ex : `ws_prod_eu` — isolé des autres workspaces (Layer 1) |

Le workspace est idempotent : un second appel avec le même identifiant ne crée pas de doublon.

**Après création :** le schéma Layer 1 est vide. Les tables typées y seront créées via le cycle DDL (Section 3.2).

---

### 3.2 Couplage Layer 1 ↔ Layer 2 via triggers

**Layer 1** = tables typées dans le schéma du workspace (ex : `ws_prod_eu.product`, `ws_prod_eu.supplier`).  
**Layer 2** = `mfo_facets` — fact store centralisé, structuré pour la recherche.

**Mécanisme de couplage :**

```
ghostcrab_ddl_propose (avec sync_spec)
  → génère automatiquement un trigger AFTER INSERT/UPDATE/DELETE
  → le trigger sync les rows Layer 1 vers mfo_facets
  → idempotence garantie par : source_ref + partial unique index sur mfo_facets
```

**Flux de synchronisation :**

```
INSERT INTO ws_prod_eu.product (...)
  → Trigger AFTER INSERT
    → INSERT INTO mfo_facets (workspace_id, source_ref, content, facets, schema_id)
    → ON CONFLICT (source_ref, workspace_id) DO UPDATE  ← partial unique index
```

**Points critiques du couplage :**

| Point | Règle |
|---|---|
| `source_ref` | Obligatoire. Format recommandé : `<table>:<pk>`. Garantit l'idempotence. |
| `workspace_id` | Doit correspondre exactement à l'ID du workspace créé. |
| `schema_id` | Doit être namespacé `<workspace-id>:<entity-type>`. |
| Trigger | Auto-généré par `ghostcrab_ddl_propose` avec `sync_spec`. Ne jamais écrire à la main. |
| Atomicité | DDL + triggers exécutés en une seule transaction via `ghostcrab_ddl_execute`. |

---

### 3.3 Articulation Graphe ↔ Facettes

Le graphe (`graph.entity`, `graph.relation`) et le fact store (`mfo_facets`) sont **deux représentations complémentaires** d'une même ontologie :

| Dimension | Facettes (`mfo_facets`) | Graphe (`graph.*`) |
|---|---|---|
| Modèle | Documents + JSONB | Nœuds + arêtes typés |
| Usage | Recherche, agrégats, hiérarchies | Traversal, relations, scoring |
| Identifiant partagé | `source_ref` | `entity_id` / `alias` |
| Workspace | `workspace_id` | `workspace_id` = `GRAPH_WORKSPACE` (constante) |
| Écriture MCP | `ghostcrab_remember`, `ghostcrab_upsert` | `ghostcrab_learn`, `ghostcrab_patch` |

**Articulation :** une entité ontologique peut exister simultanément dans `mfo_facets` (pour la recherche facettée) et dans `graph.entity` (pour le traversal relationnel). Le `source_ref` dans `mfo_facets` peut référencer le `entity_id` dans `graph.entity` pour maintenir la traçabilité.

---

### 3.4 Projections comme trace d'audit

`mfo_projections` est le mécanisme de trace opérationnelle. Il enregistre les décisions, contextes et vues matérialisées produits par les agents.

| Champ | Contenu |
|---|---|
| `scope` | Périmètre de la projection (workspace, domaine fonctionnel) |
| `content` | Contenu de la projection (JSON libre ou structuré) |
| `proj_type` | Type enum — valeurs définies dans `mvp_core_contract.yaml`. Hors-enum → transaction en échec. |
| `status` | État de la projection |
| `agent_id` | Identifiant de l'agent producteur |

**Usage audit :** après chaque action ontologique significative, l'agent appelle `ghostcrab_project` pour matérialiser une trace lisible par un humain ou un autre agent.

---

## Section 4 — Invariants à respecter obligatoirement

| # | Invariant | Raison | Conséquence en cas de violation |
|---|---|---|---|
| 1 | Chaque INSERT dans `mfo_facets` porte `workspace_id` + `source_ref` | Garantit l'idempotence via le partial unique index | Doublons de faits, requêtes retournant des résultats corrompus |
| 2 | Chaque `schema_id` est namespacé `<workspace-id>:<entity-type>` | Évite les collisions entre workspaces dans le registre de schémas | Un schéma non-préfixé est ambigu et peut écraser un schéma d'un autre workspace |
| 3 | `graph.workspace_id` == `GRAPH_WORKSPACE` (constante partagée) — jamais `"default"` hardcodé | L'identifiant du workspace graphe doit être cohérent avec `mindbrain.workspaces` | Rupture de jointure entre facettes et graphe ; données graphe orphelines |
| 4 | Une seule source DDL canonique, déclarée dans `mvp_core_contract.yaml` (`ghostcrab_mcp` recommandé) | Évite le DDL drift entre environnements | Le côté non-canonique (ex : `postgres/init/*.sql`) diverge silencieusement ; migrations impossibles à rejouer |
| 5 | Même DSN pour MCP et agents dans le même environnement | Les deux doivent voir le même état transactionnel | Décalages invisibles ; un agent lit des données que le MCP ne voit pas (ou inversement) |
| 6 | `proj_type` n'accepte que les valeurs de l'enum défini dans les specs YAML | Les valeurs hors-enum font échouer la transaction PostgreSQL | Perte de la projection ; échec silencieux si non monitoré |
| 7 | BM25 disponible immédiatement après bootstrap ; semantic search nécessite un batch séparé | L'indexation d'embeddings n'est pas synchrone avec l'INSERT | Requêtes semantic search retournant 0 résultats sur des données fraîches si le batch n'a pas tourné |

---

## Section 5 — Séquence d'onboarding d'une nouvelle ontologie (étapes MCP)

### Étape 1 — Créer le workspace

| Élément | Détail |
|---|---|
| **Action** | Appeler `ghostcrab_workspace_create` avec le nom et la configuration du workspace |
| **Outil MCP** | `ghostcrab_workspace_create` |
| **Artefact PostgreSQL** | Record dans `mindbrain.workspaces` + schéma PostgreSQL dédié (ex : `ws_prod_eu`) |
| **Validation** | `ghostcrab_workspace_list` → le workspace apparaît avec statut actif |

### Étape 2 — Déclarer les schémas de facettes (types d'entités)

| Élément | Détail |
|---|---|
| **Action** | Appeler `ghostcrab_schema_register` pour chaque type d'entité de l'ontologie. Namespacer : `<workspace-id>:<entity-type>` |
| **Outil MCP** | `ghostcrab_schema_register` |
| **Artefact PostgreSQL** | Metadata schéma dans `mindbrain` (pas de DDL physique) |
| **Validation** | `ghostcrab_schema_list` → chaque schéma listé avec son namespace correct |

### Étape 3 — Proposer la migration DDL avec sync_spec

| Élément | Détail |
|---|---|
| **Action** | Appeler `ghostcrab_ddl_propose` avec le payload DDL des tables Layer 1 + `sync_spec` pour chaque table à synchroniser vers `mfo_facets` |
| **Outil MCP** | `ghostcrab_ddl_propose` |
| **Artefact PostgreSQL** | Entrée dans `pending_migrations` (statut : pending) + définition des triggers auto-générés |
| **Validation** | `ghostcrab_ddl_list_pending` → migration visible avec statut `pending` |

### Étape 4 — Approbation humaine de la migration

| Élément | Détail |
|---|---|
| **Action** | Un humain valide la migration via CLI |
| **Outil MCP** | N/A — CLI uniquement : `ghostcrab maintenance ddl-approve --id <uuid> --by <name>` |
| **Artefact PostgreSQL** | Statut de la migration passe à `approved` dans `pending_migrations` |
| **Validation** | `ghostcrab_ddl_list_pending` → migration avec statut `approved` |

### Étape 5 — Exécuter la migration (DDL + triggers)

| Élément | Détail |
|---|---|
| **Action** | Appeler `ghostcrab_ddl_execute` avec l'UUID de la migration approuvée |
| **Outil MCP** | `ghostcrab_ddl_execute` |
| **Artefact PostgreSQL** | Tables Layer 1 créées dans le schéma workspace + triggers AFTER INSERT/UPDATE/DELETE installés + migration marquée `executed` |
| **Validation** | `ghostcrab_workspace_inspect` → tables et sémantiques visibles ; `ghostcrab_status` → readiness OK |

### Étape 6 — Enregistrer les entités et relations dans le graphe

| Élément | Détail |
|---|---|
| **Action** | Pour chaque entité et relation ontologique connue, appeler `ghostcrab_learn` |
| **Outil MCP** | `ghostcrab_learn` |
| **Artefact PostgreSQL** | Nœuds dans `graph.entity`, arêtes dans `graph.relation` avec `workspace_id` = `GRAPH_WORKSPACE` |
| **Validation** | `ghostcrab_traverse` sur une entité connue → voisins retournés ; `ghostcrab_coverage` → couverture > 0% |

### Étape 7 — Vérifier la cohérence globale

| Élément | Détail |
|---|---|
| **Action** | Inspecter le workspace, vérifier le statut runtime, effectuer une recherche test |
| **Outil MCP** | `ghostcrab_workspace_inspect` + `ghostcrab_status` + `ghostcrab_search` |
| **Artefact PostgreSQL** | Aucun artefact créé (lecture seule) |
| **Validation** | `ghostcrab_status` → `native_readiness` conforme au mode configuré ; `ghostcrab_search` → résultats cohérents avec les faits insérés ; BM25 opérationnel |

---

## Section 6 — Modes d'exécution et configuration

### 6.1 Tableau des 3 modes runtime

| Mode | Comportement | Quand l'utiliser | Risque |
|---|---|---|---|
| `sql-only` | SQL portable uniquement. Aucune probe des extensions natives. Pas de BM25 natif, pas de traversal natif. | Environnements sans extensions custom (CI léger, dev local sans pg_facets/pg_dgraph/pg_pragma) | Performances dégradées sur recherche et traversal ; features native indisponibles |
| `auto` | Probe des extensions au démarrage. Natif si chargé + readiness. Fallback SQL automatique sur erreur. | Environnements hybrides ou incertains. Acceptable pour staging. | Le fallback peut masquer des problèmes d'installation des extensions |
| `native` | Fail fast si extensions absentes ou si le bootstrap natif échoue. Aucun fallback. | **Production GhostCrab réel.** Mode recommandé pour garantir les performances et le comportement attendu. | Démarrage en échec si extensions mal installées — c'est le comportement voulu |

### 6.2 Variables d'environnement clés

| Variable | Rôle | Valeur type |
|---|---|---|
| `MFO_NATIVE_EXTENSIONS` | Sélectionne le mode runtime | `sql-only` / `auto` / `native` |
| `DATABASE_URL` (DSN) | URL de connexion PostgreSQL — identique pour MCP et agents | `postgresql://user:pass@host:port/db` |
| `GRAPH_WORKSPACE` | Identifiant du workspace graphe (constante partagée) | **Retourné par `ghostcrab_workspace_create` lors de l'onboarding — ne pas pré-configurer manuellement.** L'UUID généré par le serveur MCP est propagé aux agents d'ingestion après création. |
| `PG_PORT` | Port PostgreSQL (override pour tests) | `55432` (tests), `5432` (prod) |

---

## Section 7 — Points de vigilance et erreurs classiques

### Piège 1 — `workspace_id` incohérent entre facettes et graphe

**Symptôme :** `ghostcrab_traverse` retourne des entités non retrouvables via `ghostcrab_search`.  
**Cause :** `graph.workspace_id` hardcodé à `"default"` au lieu de la valeur `GRAPH_WORKSPACE`.  
**Correction :** `GRAPH_WORKSPACE` n'est pas une variable à pré-configurer — elle est retournée par `ghostcrab_workspace_create` lors de l'onboarding. L'agent Claude Code joue le rôle de médiateur entre l'humain et le serveur MCP ; l'UUID retourné devient la constante partagée pour la session et doit être propagé aux agents d'ingestion. Ne jamais hardcoder cette valeur dans `.env` avant la création du workspace.

---

### Piège 2 — DDL drift entre canonique et non-canonique

**Symptôme :** Les tables Layer 1 en prod ne correspondent pas au modèle exporté par `ghostcrab_workspace_export_model`.  
**Cause :** Le fichier `postgres/init/*.sql` a été édité à la main au lieu d'être généré depuis la source canonique.  
**Correction :** Toute modification DDL passe par `ghostcrab_ddl_propose` → approbation → `ghostcrab_ddl_execute`. Le non-canonique est regénéré, jamais édité.

---

### Piège 3 — Facet sync non-fatal masquant des données manquantes

**Symptôme :** `mfo_facets` est sous-alimenté ; les recherches retournent moins de résultats qu'attendu.  
**Cause :** Le trigger de sync Layer 1→2 a échoué silencieusement (erreur non-propagée depuis le trigger).  
**Correction :** Monitorer les erreurs de trigger PostgreSQL. Après bulk write, exécuter `ghostcrab maintenance merge-facet-deltas` pour forcer la réconciliation.

---

### Piège 4 — `source_ref` absent sur les INSERTs manuels

**Symptôme :** Doublons dans `mfo_facets` après des ré-exécutions ou des relances d'ingestion.  
**Cause :** INSERTs directs en SQL (hot-path) sans `source_ref`, contournant l'idempotence du partial unique index.  
**Correction :** Tout INSERT dans `mfo_facets` — qu'il passe par MCP ou SQL direct — doit porter un `source_ref` stable et déterministe (ex : `<table>:<pk>`).

---

### Piège 5 — Confusion BM25 vs semantic search (embeddings)

**Symptôme :** Les recherches sémantiques retournent 0 résultat sur des données fraîchement insérées.  
**Cause :** BM25 est disponible immédiatement après bootstrap. Les embeddings nécessitent un batch d'indexation séparé qui n'a pas encore tourné.  
**Correction :** Ne pas supposer que `mode: "semantic"` fonctionne sans batch préalable. Utiliser `mode: "bm25"` pour les données récentes. Planifier le batch embedding via pg_cron.

---

### Piège 6 — `schema_id` non-namespacé

**Symptôme :** Un schéma d'entité d'un workspace écrase ou entre en conflit avec un schéma d'un autre workspace.  
**Cause :** `ghostcrab_schema_register` appelé avec un `schema_id` sans préfixe `<workspace-id>:`.  
**Correction :** Appliquer systématiquement le format `<workspace-id>:<entity-type>`. Contrôler via `ghostcrab_schema_list`.

---

### Piège 7 — `proj_type` hors enum

**Symptôme :** `ghostcrab_project` retourne une erreur de contrainte PostgreSQL ; la projection est perdue.  
**Cause :** La valeur `proj_type` passée ne figure pas dans l'enum défini dans `mvp_core_contract.yaml`.  
**Correction :** Vérifier les valeurs autorisées avant l'appel. Toute nouvelle valeur nécessite une mise à jour du YAML et une migration de l'enum PostgreSQL.

---

### Piège 8 — MCP utilisé comme hot-path d'ingestion

**Symptôme :** Latences élevées, timeouts MCP, données partiellement insérées lors de volumes importants.  
**Cause :** Usage de `ghostcrab_remember` en boucle pour ingérer des milliers de faits.  
**Correction :** L'ingestion bulk passe toujours par SQL direct (pgx/psycopg2). Le MCP ne gère que les faits unitaires (configuration, métadonnées, corrections ponctuelles).

---

## Section 8 — Validation et sanity checks

### 8.1 Chaîne de validation complète

| Commande | Ce qu'elle vérifie réellement |
|---|---|
| `npm run lint` | Syntaxe TypeScript, règles ESLint sur le code MCP serveur |
| `npm run build` | Compilation sans erreur ; dépendances résolues |
| `npm run test` | Tests unitaires : logique des outils, parsing payloads, gestion des modes runtime |
| `PG_PORT=55432 npm run migrate` | Application des migrations DB sur l'instance de test ; cohérence du schéma PostgreSQL |
| `PG_PORT=55432 npm run test:integration` | Tests avec DB réelle : écriture/lecture `mfo_facets`, `graph.*`, `mfo_projections` ; triggers actifs |
| `PG_PORT=55432 npm run smoke:mcp` | Smoke test de la surface MCP : chaque outil répond sans erreur critique |
| `PG_PORT=55432 npm run verify:e2e` | Scénario complet end-to-end : workspace → DDL → sync → search → traverse → projection |

### 8.2 Commandes de maintenance et leur fonction réelle

| Commande CLI | Ce qu'elle vérifie / corrige |
|---|---|
| `ghostcrab maintenance register-pg-facets` | Enregistrement idempotent de `mfo_facets` avec pg_facets. À rejouer si pg_facets est réinstallé ou si la readiness native est perdue. |
| `ghostcrab maintenance merge-facet-deltas` | Réconcilie les deltas de `mfo_facets` accumulés depuis les derniers bulk writes. Corrige les écarts sync trigger/fait réel. |
| `ghostcrab maintenance refresh-entity-degree` | Recalcule `graph.entity_degree` — nécessaire pour `ghostcrab_marketplace` et les analytics de couverture. À planifier après ingestion massive de relations. |
| `ghostcrab maintenance ddl-approve --id <uuid> --by <name>` | Valide humainement une migration pending. Bloquant : sans cette approbation, `ghostcrab_ddl_execute` refuse d'agir. |
| `ghostcrab maintenance ddl-execute --id <uuid>` | Exécute atomiquement DDL + triggers pour une migration approuvée. Équivalent CLI de `ghostcrab_ddl_execute`. |

### 8.3 Sanity checks post-onboarding (MCP)

| Vérification | Outil | Signal attendu |
|---|---|---|
| Workspace visible et actif | `ghostcrab_workspace_list` | Workspace avec statut actif, stats > 0 |
| Layer 1 correct | `ghostcrab_workspace_inspect` | Tables typées listées avec sémantiques attachées |
| Readiness native | `ghostcrab_status` | `native_readiness: true` (si mode `native` ou `auto` avec extensions) |
| Faits retrouvables | `ghostcrab_search` | Résultats cohérents avec les faits insérés |
| BM25 opérationnel | `ghostcrab_search` avec `mode: "bm25"` | Résultats scorés retournés |
| Graphe cohérent | `ghostcrab_coverage` | Couverture > 0%, pas de decay anormal |
| Projections tracées | `ghostcrab_pack` | Contexte opérationnel retourné sans erreur |

---

*FIN SOP 1 — GhostCrab MCP v1.0*
