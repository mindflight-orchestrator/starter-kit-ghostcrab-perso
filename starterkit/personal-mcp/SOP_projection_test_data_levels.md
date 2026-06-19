# SOP — Projection test data levels (personal-mcp)

**Edition:** GhostCrab Personal — SQLite, `gcp brain ...`, MCP `ghostcrab_*`.

**Phase:** B2.5, after fake-data design/generation and before final review,
import, snapshots validation or scenario comparison.

**Related files:**

- [SOP_SEQUENCE.md](SOP_SEQUENCE.md)
- [SOP_business_rules_catalog.md](SOP_business_rules_catalog.md)
- [SOP_review_finalisation_dossier.md](SOP_review_finalisation_dossier.md)
- [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md)
- [../scripts/README_projection_tools.md](../scripts/README_projection_tools.md)

---

## 1. Objective

Define the three levels of data needed to validate projections and snapshots:

- `smoke`: minimal end-to-end chain, quick import and read tests;
- `mini`: complete business variants and exceptions;
- `scale`: larger volumes with the same assertions preserved.

This phase prevents a common failure: importing objects and edges that validate
the schema but do not support manager-oriented answers.

---

## 2. What each level must prove

| Level | Purpose | Must include |
|---|---|---|
| `smoke` | Fast end-to-end proof | one pivot case, cross-domain graph chain, critical assertions, first manager snapshots |
| `mini` | Real business validation | all critical rule variants, exceptions, blocked cases, enough evidence for the 6-10 active projections |
| `scale` | Robustness and retrieval | many entities, repeated rule variants, aggregate counts, search/traversal load |

Do not treat `scale` as random volume. It must replay the declared
`scale.required_variants` from the rules catalog.

---

## 3. Required outputs

Recommended project-local layout:

```text
generated/<workspace_id>-test-<profile>/
├── fake_data/
├── import_ready/
├── reports/
│   ├── fake_data_coverage.md
│   ├── fake_data_coverage.json
│   ├── manager_answer_snapshots.md
│   ├── manager_answer_snapshots.json
│   ├── snapshot_claims_evidence_matrix.md
│   └── snapshot_claims_evidence_matrix.json
└── import_manifest.yaml
```

For a manager-oriented snapshot, each claim must map to evidence:

```yaml
claim:
  id: ag_decision_cycle.claim.budget_travaux_adopte
  projection_id: ag_decision_cycle
  statement: "The elevator works budget was adopted and can trigger calls."
  evidence_entities:
    - decision_ag:decision-lift-budget-001
    - budget:budget-lift-15000
  evidence_edges:
    - resulte_de
    - donne_lieu_a
  assertions:
    - decision.resultat == adoptee
    - budget.montant_total == 15000
```

---

## 4. Gates before import

Before importing a test profile:

- every generated `rule_id` exists in `rules/business_rules_catalog.yaml`;
- every generated scenario variant is declared for the selected profile;
- every active projection has at least one test question;
- every manager snapshot claim has evidence entities or a named gap;
- hard gaps are reported as `blocked_by_model_gap`, not hidden;
- `mappingProfile` remains `deferred` unless explicitly activated.

---

## 5. Gates after import

After import and reindex:

- `ghostcrab_search` finds the pivot objects;
- `ghostcrab_count` returns expected counts by schema/facet;
- `ghostcrab_combined_search` answers representative manager questions;
- `ghostcrab_projection_get(..., include_evidence=true)` returns non-empty evidence for snapshots;
- `audit_ghostcrab_projections.py` distinguishes:
  - `pass`;
  - `partial`;
  - `blocked`;
  - `deferred`.

---

## 6. Scenario comparison

For a second scenario, do not duplicate ontologies. Reuse:

- same LinkML / ontology contract;
- same `business_rules_catalog.yaml`;
- same `projection_catalog.yaml`;
- different scenario values and volumes;
- separate `workspace_id`.

Recommended structure:

```text
scenarios/<workspace_id>.yaml
generated/<workspace_id>/<profile>/
```

The comparison report must separate:

- model gaps;
- rule coverage gaps;
- fake-data gaps;
- projection/snapshot gaps;
- runtime/tooling gaps.

---

## 7. Done when

- smoke profile validates the core graph chain and first snapshots;
- mini profile covers all critical business variants;
- scale profile tests volume without losing assertions;
- manager snapshots are readable and auditable;
- the reports are collected by [SOP_review_finalisation_dossier.md](SOP_review_finalisation_dossier.md).
