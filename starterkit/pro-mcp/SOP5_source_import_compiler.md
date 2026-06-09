# SOP 5 — Source import compiler (pro-mcp)

**Edition:** pro-mcp only. Voir [EDITIONS.md](../EDITIONS.md) pour changer de piste.

**Version :** 0.1  
**Statut :** Draft exploitable  
**Perimetre :** CSV/API/JSON → PostgreSQL via scripts, COPY, MCP upsert, mindCLI audit from `../mindbot/cmd/mindcli`.

---

## Section 1 — Objectif

Cette SOP generalise SOP2/SOP3 au-dela d'un vault Obsidian.

Elle sert quand la source initiale est:

- un CSV exporte depuis une application;
- un JSON ou JSONL;
- une API REST;
- un export CRM/ERP/support;
- un dossier mixte dont les conventions ne sont pas celles d'Obsidian.

Le principe est de traiter l'import comme une compilation deterministe:

```text
source brute
  -> profil de source
  -> modele cible exporte ou versionne
  -> mapping source -> canonique
  -> JSONB intermediaire SOP2
  -> pending_review / pending_ddl
  -> import facets
  -> graph native si requis
  -> projections
  -> tests consommateurs
```

Cette SOP ne remplace pas SOP2/SOP3. Elle ajoute la couche manquante pour mapper des sources non-Obsidian.

---

## Section 2 — Position dans le starterkit

Ordre canonique:

1. `SOP4_environment_bootstrap.md` — verifier l'environnement.
2. `SOP0_import_path_choices.md` — enregistrer les voies d'import.
3. `SOP1_ghostcrab_mcp.md` — comprendre le contrat MCP / DB.
4. [SOP2_obsidian_ontologie.md](SOP2_obsidian_ontologie.md) — modeliser le workspace et ses ontologies.
5. Phase **B1** projections — [ROUTE_MAP § projections](ROUTE_MAP.md#route-projections).
6. Phase **B2** fake-data metier — [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md) (recommande avant premier bulk COPY).
7. `SOP3_parsing_pipeline.md` — parser un vault documentaire (optionnel).
8. `SOP5_source_import_compiler.md` — compiler une source externe generique vers le modele.

Templates utilises:

- `templates/jtbd.yaml`
- `templates/mvp_core_contract.yaml`
- `templates/ontology_core_provisioning.yaml`
- `templates/initial_referential.yaml`
- `templates/mapping_external_to_canonical.yaml`
- `templates/disambiguation.yaml`
- `templates/source_profile.yaml`
- `templates/consumer_contract.yaml`
- `templates/import_manifest.yaml`

---

## Voie A — pro-mcp (scripts + COPY + mindCLI audit)

**Edition:** GhostCrab Pro (`ghostcrab-mcp`, PostgreSQL).

**Sequence:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase C2.

**Prerequisite B2:** when no real CRM/ERP export exists yet, generate deterministic fake rows into `generated/<ws>/import_ready/` — see [ROUTE_MAP § B2](ROUTE_MAP.md#route-donnees-fictives-metier). Record `fake_data.choice` in `../templates/import_path_choices.yaml`.

| Gate | Operator surface |
|------|------------------|
| 0–3 | StarterKit `.mjs` dry-run (profile, mapping, transform) |
| 4–6 | JSONB intermediate + `import_facets.mjs` plan → MCP `ghostcrab_upsert`; graph scripts; optional **COPY** via SOP3 / `generate_copy_migrations.mjs` |
| 7–8 | MCP `ghostcrab_pack`, consumers; **mindCLI** for projection contract audit |
| 9 | `audit_import_pipeline.mjs` |

**mindCLI (Pro):** after data import, validate projection catalogue:

```bash
export DATABASE_URL="$GHOSTCRAB_DSN"
go run ../mindbot/cmd/mindcli --json mb_pragma projections list --workspace <workspace_id>
go run ../mindbot/cmd/mindcli --json mb_pragma projection get --scope <scope>
```

---


## Section 3 — Gates deterministes (Voie A detail)

### Gate 0 — Autorisation et runtime

Avant tout import:

- confirmer le `workspace_id`;
- identifier le backend actif: PostgreSQL, SQLite PERSO, ou autre;
- verifier que le modele est deja valide ou que la proposition de modele a ete approuvee;
- ne pas freezer de schema sans confirmation explicite.

Sortie:

- section `runtime` dans `import_manifest.yaml`.

### Gate 1 — Modele cible

Source preferee:

- `ghostcrab_workspace_export_model(workspace_id, depth=full)`

Fallback:

- contrat local versionne, par exemple `mvp_core_contract.yaml` + `ontology_core_provisioning.yaml`.

Le modele cible doit exposer:

- `workspace_id`;
- `schema_id` autorises;
- facets requises;
- valeurs fermees / enums;
- node types;
- edge labels;
- contraintes source/target des edges quand disponibles;
- projection scopes;
- consommateurs attendus.

Sortie:

- `target_model_contract` reference dans le manifest.

### Gate 2 — Profil de source

Produire `source_profile.yaml`.

Pour CSV:

- chemin du fichier;
- delimiter, encoding;
- headers;
- lignes d'echantillon;
- null rate par colonne;
- candidats d'identifiant stable;
- enums detectees;
- colonnes relationnelles probables;
- colonnes ignorees avec raison.

Pour JSON/API:

- endpoint ou fichier;
- object paths;
- arrays repetes;
- candidats d'identifiant stable;
- chemins de relations;
- champs nullable;
- valeurs enum-like.

Sortie:

- `source_profile.yaml` complete.

### Gate 3 — Mapping source vers canonique

Etendre `mapping_external_to_canonical.yaml` pour definir:

- type de source;
- selecteur de lignes/objets;
- `schema_id` cible;
- formule `record_id`;
- mapping champ -> facet;
- transforms;
- defaults;
- enum maps;
- extraction des relations;
- regles de mise en attente.

Sortie:

- `mapping_external_to_canonical.yaml` complete et relu.

### Gate 4 — Dry run JSONB

Transformer la source en JSONB intermediaire SOP2 section 4.3.

Verifications:

- `source_ref` stable;
- `schema_id` namespaced;
- `record_id` unique;
- facets requises presentes;
- enum values valides;
- edge labels autorises;
- endpoints resolvables.

Sorties:

- `output/normalized_records.jsonl`;
- `output/normalized_edges.jsonl`;
- `output/pending_review.json`;
- `output/pending_ddl.json`.

### Gate 5 — Import facets

Importer les records valides.

Options:

- MCP pour petits volumes;
- SQL/batch pour volumes importants;
- import direct SQLite uniquement dans un clone local maitrise, pas comme raccourci non audite.

Verifications:

- counts attendus;
- `workspace_id` correct partout;
- `record_id` conserve;
- pas de duplicats.

### Gate 6 — Graphe

Si `consumer_contract.yaml` declare `native_graph: true`, le graphe doit etre materialise.

Options:

- `ghostcrab_learn` quand disponible et adapte;
- tables natives PostgreSQL;
- tables natives SQLite PERSO (`graph_entity`, `graph_relation`) dans un clone local;
- materialisation depuis records `semantic-edge`.

Verifications:

- node count attendu;
- edge count attendu;
- endpoints resolus;
- labels autorises;
- type source/target conforme au modele.

### Gate 7 — Projections

Tester les projections declarees:

- `ghostcrab_pack`;
- recherches par status/stage/owner;
- vues compactes;
- detection de bloqueurs;
- next action.

Important:

- une projection qui fonctionne ne prouve pas que le graphe natif est pret.

### Gate 8 — Consommateurs

Chaque consommateur declare dans `consumer_contract.yaml` doit avoir ses smoke tests.

Exemples:

- Sigma/Graphology: `/api/graph/ontologies`, `/api/graph/count`, `/api/graph`;
- agent GhostCrab: `ghostcrab_search`, `ghostcrab_count`, `ghostcrab_pack`;
- reporting: counts par facets;
- traversal: parcours de graphe attendu.

### Gate 9 — Manifest final

Mettre a jour `import_manifest.yaml` avec:

- source;
- target model;
- mapping;
- scripts/commandes executes;
- counts;
- exceptions;
- statut des consommateurs.

---

## Section 4 — Fichiers d'exception

Utiliser les fichiers existants du starterkit:

- `pending_review.json` pour les objets source non importes;
- `pending_ddl.json` pour les vrais gaps de modele;
- `unmatched.log` pour les objets non couverts par le mapping;
- `syncstate.json` pour l'incrementalite.

Codes de raison recommandes:

- `unknown_entity_type`
- `missing_required_facet`
- `invalid_enum_value`
- `unresolved_reference`
- `ambiguous_reference`
- `duplicate_record_id`
- `invalid_edge_label`
- `edge_type_mismatch`
- `unsafe_inference`
- `needs_model_extension`
- `consumer_gap`

Ne pas creer automatiquement un nouveau schema pour une ligne qui echappe aux regles.

---

## Section 5 — Harnais de scripts

Le starterkit fournit un harnais dry-run minimal dans `scripts/`.

Un agent peut les copier dans un projet cible et les specialiser, mais ils doivent deja servir de reference executable:

```text
scripts/profile_source.mjs
scripts/validate_source_profile.mjs
scripts/export_model_contract.mjs
scripts/validate_mapping_contract.mjs
scripts/transform_source_to_jsonb.mjs
scripts/write_pending_files.mjs
scripts/import_facets.mjs
scripts/materialize_graph_from_edges.mjs
scripts/generate_copy_migrations.mjs
scripts/validate_graph_contract.mjs
scripts/validate_consumer_contract.mjs
scripts/update_syncstate.mjs
scripts/audit_import_pipeline.mjs
```

Contrat minimal:

- chaque script doit accepter `--workspace`, `--input`, `--mapping`, `--model`, `--output`;
- chaque script doit ecrire un rapport JSON stable;
- aucun script ne doit ecrire dans GhostCrab sans mode explicite `--write`;
- le mode par defaut est dry-run;
- les scripts doivent echouer sur references non resolues, labels inconnus, ou facets requises manquantes.

Commandes de verification:

```bash
node scripts/profile_source.mjs --help
node scripts/validate_source_profile.mjs --help
node scripts/export_model_contract.mjs --help
node scripts/validate_mapping_contract.mjs --help
node scripts/transform_source_to_jsonb.mjs --help
node scripts/write_pending_files.mjs --help
node scripts/import_facets.mjs --help
node scripts/materialize_graph_from_edges.mjs --help
node scripts/generate_copy_migrations.mjs --help
node scripts/validate_graph_contract.mjs --help
node scripts/validate_consumer_contract.mjs --help
node scripts/update_syncstate.mjs --help
node scripts/audit_import_pipeline.mjs --help
```

---

## Section 6 — Definition of ready

Un import est pret seulement si:

- le modele cible est charge;
- `source_profile.yaml` existe;
- le mapping est complet;
- le dry run n'a pas de blocage;
- `pending_review.json` a ete revu;
- `pending_ddl.json` est vide ou explicitement accepte comme hors-scope;
- les counts facets correspondent;
- les counts graph correspondent quand le graphe est requis;
- les projections passent;
- les consommateurs passent;
- `import_manifest.yaml` documente le resultat.

---

## Section 7 — Regle d'organisation

Le starterkit reste la reference clonable/personnalisable.

Les skills GhostCrab doivent pointer vers ce starterkit quand un agent doit produire:

- des templates de modelisation;
- un pipeline d'import;
- un mapping source vers canonique;
- un consumer contract;
- un audit d'import.

Ne pas dupliquer ces templates dans chaque skill. Les skills doivent rester legers et charger le starterkit quand le travail demande des artefacts concrets.
