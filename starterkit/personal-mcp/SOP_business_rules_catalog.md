# SOP — Business rules catalog (personal-mcp)

**Edition:** GhostCrab Personal — SQLite, `gcp brain ...`, MCP `ghostcrab_*`.

**Phase:** B1.5, between validated projections and fake-data generation.

**Related files:**

- [SOP_SEQUENCE.md](SOP_SEQUENCE.md)
- [ROUTE_MAP.md](ROUTE_MAP.md#route-regles-metier-b15)
- [../templates/business_rules_catalog.yaml](../templates/business_rules_catalog.yaml)
- [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md)
- [SOP_projection_test_data_levels.md](SOP_projection_test_data_levels.md)

---

## 1. Objective

Create a central catalog of business rules before generating fake data or
importing real data.

The ontology defines objects, facets and graph edges. The business rules catalog
defines what must be true, calculated, forbidden, triggered or proven across
those objects.

Without this phase, fake data may look plausible but fail to cover the real
manager questions and operational exceptions.

---

## 2. Inputs

| Input | Purpose |
|---|---|
| Ontology Markdown | Source business rules, legal constraints, exceptions and workflows |
| LinkML / ontology contract | Check that rule objects, facets and edges exist |
| `specs/manager_questions.yaml` | Business questions the rules must support |
| `specs/projection_catalog.yaml` | Projection scopes and artifact kinds |
| `projection_model_validation.md` | Human-validated retrieval needs |

---

## 3. Output

Project-local output:

```text
rules/business_rules_catalog.yaml
```

Recommended shape:

```yaml
rules:
  - id: comptabilite.repartition_travaux_par_quotites
    priority: critical
    domains: [administrative, comptabilite, decisionnel, technique]
    business_question_refs: [accounting_closeout, ag_decision_cycle]
    trigger: decision_ag.resultat == adoptee
    required_objects:
      - cle_de_repartition
      - lot
      - budget
      - appel_de_fonds
    required_facets:
      - quotites
      - montant_total
      - resultat
    required_edges:
      - resulte_de
      - est_calcule_a_partir_de
      - donne_lieu_a
    assertions:
      - sum(lot.quotites) == cle_de_repartition.base
      - sum(appel_de_fonds.montant_total) == budget.montant_total_annuel
    scenarios:
      smoke: [travaux_adoptes_budget_appels]
      mini: [adopte, rejete, prorata_interdit, regularisation]
      scale: [volume_multi_coproprietes]
    model_gaps: []
```

---

## 4. MECE classification

Classify each rule in one primary family:

| Family | Examples |
|---|---|
| `calculation` | sums, repartitions, balances, quotas |
| `eligibility` | voting rights, mandates, ownership date |
| `state_transition` | draft -> approved -> executed -> closed |
| `deadline` | contestation period, reminder timing |
| `forbidden_state` | multi-copro invoice, missing mandate, missing transcription |
| `evidence_required` | PV, expertise, CODA, supplier quote |
| `cross_domain` | AG decision -> budget -> calls -> works -> mission |

If one rule spans several families, keep one primary family and list secondary
families in `tags`.

---

## 5. Required coverage matrix

For every critical or important rule, record:

| Column | Meaning |
|---|---|
| `rule_id` | Stable id from `business_rules_catalog.yaml` |
| `projection_refs` | Projections that must answer or display this rule |
| `required_schemas` | Object types needed |
| `required_facets` | Facets needed for calculations/filtering |
| `required_edges` | Graph relations needed for proof chains |
| `smoke_variants` | Minimal variants generated in first test |
| `mini_variants` | Full business variants and exceptions |
| `scale_variants` | Volume variants |
| `model_gap` | Missing model element, if any |

This matrix is the gate for Phase B2 fake data.

---

## 6. Done when

- each critical rule has a stable `id`;
- each critical rule has at least one assertion;
- each critical rule maps to at least one business question or projection;
- required objects, facets and edges are explicit;
- smoke / mini / scale variants are declared;
- gaps are named as `model_gaps`, not silently ignored;
- the catalog is included in the finalisation review dossier.

---

## 7. Handoff

Next phase:

1. [SOP_projection_test_data_levels.md](SOP_projection_test_data_levels.md) to decide how smoke / mini / scale will prove the rules and snapshots.
2. [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md) to generate deterministic import-ready data.
3. [SOP_review_finalisation_dossier.md](SOP_review_finalisation_dossier.md) to collect the catalog for human validation.
