# SOP — Catalogue des règles métier (personal-mcp)

**Edition :** GhostCrab Personal — SQLite, `gcp brain ...`, MCP `ghostcrab_*`.

**Phase :** B1.5 — après préparation ontologie/schémas/projections, avant fake-data et structured-import.

**Template :** [../templates/business_rules_catalog.yaml](../templates/business_rules_catalog.yaml)

---

## 1. Objectif

Cette SOP crée le contrat explicite des règles métier entre le modèle ontologique et les données générées ou importées.

First principles :

- Une ontologie nomme les objets, relations, états et valeurs autorisées.
- LinkML rend ce vocabulaire importable.
- Les schémas et facettes GhostCrab rendent ce vocabulaire lisible par les agents MCP et les gates d'import.
- Un catalogue de règles métier dit ce qui doit être vrai, calculé, déclenché, interdit ou explicable dans les situations réelles.
- Les fake-data et read tests prouvent que ces règles sont couvertes.

**Artefact obligatoire :**

```text
rules/business_rules_catalog.yaml
```

Pour les workspaces générés, copier aussi dans :

```text
generated/<workspace_id>/rules/business_rules_catalog.yaml
```

---

## 2. Quand cette SOP est obligatoire

Créer ou mettre à jour `rules/business_rules_catalog.yaml` dès qu'une condition est vraie :

- les Markdown domaine contiennent des règles, calculs, workflows, obligations, décisions, exceptions ou exemples de scénarios ;
- des données fictives vont valider le modèle avant l'arrivée de sources réelles ;
- des applications/API externes exposent des objets génériques qui nécessitent un `mappingProfile` ;
- les projections doivent répondre à "pourquoi", "combien", "qui paie", "qu'est-ce qui est en retard", "qu'est-ce qui a changé" ou "que doit-il se passer ensuite" ;
- des graph gap rules sont nécessaires mais ne couvrent pas toute la logique métier.

Ne pas sauter cette SOP parce que LinkML valide. LinkML prouve que le vocabulaire est bien formé ; il ne prouve pas que le comportement métier est représenté.

---

## 3. Familles MECE de règles

Classer chaque règle dans une seule famille primaire. Ajouter des tags secondaires seulement si utile.

| Famille | Rôle | Sortie |
|---------|------|--------|
| `structural` | Relations graphe obligatoires, cardinalités, topologies impossibles | candidate `gap_rules` |
| `business` | Montants, obligations, éligibilité, échéances, effets de décision | `business_rules_catalog.yaml` |
| `workflow` | Transitions d'état, déclencheurs, cycles de vie | `business_rules_catalog.yaml` |
| `mapping` | Champs API génériques reliés au sens métier canonique | section `mappingProfile` |
| `scenario` | Cas smoke/mini/scale à générer et tester | fake-data |
| `projection` | Questions métier que les agents doivent répondre avec preuves | projection catalog / answer artifacts |

**Règle :** si une règle peut changer un montant, un statut, une échéance, une obligation ou un objet aval, elle appartient au catalogue métier même si elle suggère aussi une graph gap rule.

---

## 4. Format JTBD d'une règle

Chaque règle doit être compréhensible par un responsable métier, un agent IA et un script générateur.

Forme recommandée :

```yaml
- rule_id: ag_vote_budget_travaux_repartition_quotites
  family: business
  title: "AG vote un budget travaux et repartit les appels selon les quotites"
  job_to_be_done: >
    Quand une assemblee generale vote un budget travaux, MindBrain doit expliquer
    quels coproprietaires doivent quels montants selon leurs quotites.
  actor: syndic
  trigger: decision_ag_votee
  outcome: appels_de_fonds_generes
  ontology_refs:
    classes:
      - decisionnel.assemblee_generale
      - decisionnel.decision
      - comptabilite.appel_de_fonds
    slots:
      - decisionnel.montant_vote
      - administrative.quotite
    edges:
      - decision_vote_budget
      - appel_fonds_concerne_lot
  assertions:
    - assertion_id: total_calls_equal_voted_budget
      expression: "sum(appels_de_fonds.montant) == decision.montant_vote"
      severity: error
  scenarios:
    smoke:
      min_examples: 1
      required_variants:
        - budget_voted_and_calls_generated
    mini:
      min_examples: 3
      required_variants:
        - mixed_quotites
        - partial_payment
        - unpaid_call
    scale:
      min_examples: 25
      required_variants:
        - many_lots
        - multiple_budget_lines
        - overdue_reminders
```

---

## 5. Blind spots obligatoires

Avant d'accepter le catalogue, vérifier chaque point :

- Des règles présentes dans les Markdown manquent dans LinkML, les projections ou les fake-data.
- Un calcul existe en prose mais aucun slot ne porte ses entrées ou sorties.
- Un enum d'état est valide syntaxiquement mais sans transitions métier.
- Une relation existe dans le graphe mais aucun scénario ne prouve pourquoi elle compte.
- Les fake-data ne couvrent que les chemins heureux ; les cas négatifs et exceptions manquent.
- Les API externes fournissent des ids/champs génériques sans règle `mappingProfile` vers le concept canonique.
- Les règles financières oublient paiement partiel, impayé, avoir, annulation ou échéance.
- Les règles décisionnelles oublient résultat de vote, quorum, périmètre, ligne budgétaire ou actifs concernés.
- Les règles techniques/intervention oublient récurrence, sévérité, fournisseur, SLA ou preuve de clôture.
- Les projections retrouvent des faits mais ne peuvent pas expliquer la chaîne de raisonnement.

Si un point est vrai, garder le catalogue en `status: draft` et ne pas passer en B2 fake-data.

---

## 6. Procédure

### 6.1 Entrées

Lire ces sources dans l'ordre :

1. `jtbd.yaml`
2. `ontology/<workspace>-contract.yaml` si présent
3. modules LinkML sous `ontology/` ou `generated/linkml_from_json/`
4. documents Markdown métier
5. projection candidates ou projection catalog
6. analyses `mappingProfile` / OpenAPI quand des applications externes sont dans le périmètre

### 6.2 Extraire les règles candidates

Pour chaque source Markdown, collecter :

- mentions explicites de règle, obligation, interdiction, condition, calcul, échéance, statut, vote, montant, répartition, paiement, exception ;
- règles implicites dans les exemples, rapports ou scénarios ;
- ambiguïtés non résolues sous `open_questions`.

Conserver la référence source :

```yaml
source_refs:
  - path: Ontologies-14-06-2026/Ontologie_Infrastructure_Comptabilite.md
    heading: "Appels de fonds"
    evidence_type: markdown_section
```

### 6.3 Normaliser chaque règle

Pour chaque règle :

- assigner un `rule_id` stable en snake_case ;
- choisir une famille MECE primaire ;
- écrire la phrase JTBD ;
- relier classes, slots, enum slots et arêtes ;
- lister préconditions, entrées de calcul, sorties et états interdits ;
- définir les assertions ;
- mapper les scénarios smoke/mini/scale requis ;
- marquer le statut.

### 6.4 Séparer les gap rules structurelles

Si une règle est purement structurelle, dupliquer seulement la partie structurelle dans un futur pack de gap rules.

Exemple :

- catalogue métier : "Un lot non vacant doit avoir un propriétaire pour calculer les appels."
- gap rule : un lot exige au moins une relation `owned_by`.

Relier les deux avec `derived_gap_rule_ids`.

### 6.5 Préparer la couverture fake-data

Chaque règle critique doit déclarer :

- au moins un scénario smoke ;
- au moins un scénario mini normal ;
- au moins un scénario mini exception ou négatif ;
- des volumes scale optionnels.

La génération B2 consomme le catalogue. Elle ne doit pas inventer les cas importants absents de ce fichier.

---

## 7. Gates d'acceptation

`rules/business_rules_catalog.yaml` est accepté seulement quand :

- `workspace_id`, `edition`, `status` et `source_documents` sont remplis ;
- chaque règle critique a `rule_id`, `family`, `job_to_be_done`, `trigger`, `outcome`, `ontology_refs`, `assertions` et `scenarios` ;
- chaque classe, slot, enum slot et arête référencé existe dans LinkML ou figure dans `model_gaps` ;
- les règles de mapping référencent un `mappingProfile` ou expliquent pourquoi aucune source externe n'est encore nécessaire ;
- les règles structurelles sont marquées comme candidates gap rules ;
- la couverture smoke/mini/scale est explicite ;
- les questions ouvertes ont un owner et un statut bloquant/non bloquant.

**Done when :** le statut peut passer à `confirmed` et le générateur B2 peut produire les fake-data sans deviner les situations métier centrales.

---

## 8. Relation aux autres artefacts

| Artefact | Relation |
|----------|----------|
| LinkML | Fournit classes, slots, enums et labels d'arêtes référencés par les règles |
| Schémas/facettes GhostCrab | Rendent les éléments modèle visibles par MCP et les gates d'import |
| `gap_rules` | Reçoit le sous-ensemble structurel/cardinalité, pas les calculs ni workflows |
| `mappingProfile` | Reçoit les règles d'interprétation des champs d'applications externes |
| fake-data | Consomme les scénarios et assertions du catalogue |
| projections | Consomment les questions, chaînes de preuve et besoins d'explicabilité |
| import manifest | Enregistre chemin du catalogue, statut et compteurs de couverture |

