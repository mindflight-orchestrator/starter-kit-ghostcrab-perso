# SOP — Projection test data levels (personal-mcp)

**Edition:** GhostCrab Personal — SQLite, `gcp brain ...`, MCP `ghostcrab_*`.

**Phase:** B2.5 — after B1/B1.5/B2 preparation, before accepting `answer_snapshot`, `live_answer_view`, or `evidence_pack` artifacts as business-ready.

**Related SOPs:**

- [SOP_business_rules_catalog.md](SOP_business_rules_catalog.md)
- [SOP5_structured_import.md](SOP5_structured_import.md)
- [SOP_review_finalisation_dossier.md](SOP_review_finalisation_dossier.md)
- [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md)
- [../scripts/README_projection_tools.md](../scripts/README_projection_tools.md)

---

## 1. Objective

This SOP defines the data levels required to test and validate GhostCrab/MindBrain projections.

First principles:

- An ontology says which objects, facets, enums, and graph edges may exist.
- A business rules catalog says which situations must be true, false, blocked, calculated, or explained.
- Fake-data proves that representative situations can be imported.
- A projection proves that an agent or manager can retrieve, calculate, explain, and audit an answer.

Do not assume that valid fake-data automatically creates a valid manager answer. A dataset can cover rules while still lacking the metrics, alerts, summaries, and evidence links expected by `answer_snapshot` or `live_answer_view` artifacts.

---

## 2. When this SOP is mandatory

Run this SOP whenever at least one of these artifacts will be created, audited, or accepted:

- `analysis_plan`
- `answer_snapshot`
- `live_answer_view`
- `evidence_pack`

It is mandatory before declaring projection validation green when:

- the project uses synthetic smoke/mini/scale datasets;
- manager questions were extracted from ontology Markdown;
- `business_rules_catalog.yaml` drives fake-data generation;
- snapshots must be readable with `ghostcrab_projection_get(..., include_evidence=true)`;
- live views must be refreshable and decision-ready;
- evidence must survive audit by another human or agent.

---

## 3. MECE data levels

Prepare and validate four distinct data levels. They are cumulative.

| Level | Name | Purpose | Typical artifacts |
|-------|------|---------|-------------------|
| L1 | Structural data | Prove the model imports and graph edges exist | classes, facets, enums, entities, edges |
| L2 | Business coverage data | Prove rules and scenarios are represented | rule variants, assertions, expected violations |
| L3 | Manager answer data | Prove answers contain metrics, alerts, conclusions, priorities | KPI facts, summary payloads, status rollups |
| L4 | Evidence data | Prove every claim can be audited | `claim -> evidence entity -> edge -> assertion` matrix |

### L1 — Structural data

Minimum required to validate ontology and import mechanics.

Must include:

- at least one entity for each required schema or class;
- required enum values used by smoke scenarios;
- graph edges declared by the projection contract;
- stable `source_ref` values;
- import-ready facets and edges.

Passes when:

- `structured-import apply` and `reindex` succeed;
- `ghostcrab_search` finds representative facts;
- `ghostcrab_combined_search` can retrieve graph + facets;
- critical graph edges exist.

L1 is not enough for `answer_snapshot`.

### L2 — Business coverage data

Minimum required to validate `rules/business_rules_catalog.yaml`.

Must include:

- each critical `rule_id`;
- declared smoke/mini/scale variants;
- happy-path and exception cases;
- assertion inputs and outputs;
- explicit status for blocked or deferred rules.

Passes when:

- `fake_data_coverage.json` maps every generated scenario to a known `rule_id`;
- no generated variant is undeclared;
- expected violations are marked as expected;
- non-covered rules are either `blocked_by_model_gap` or `deferred`.

L2 proves the model can represent the business. It still does not prove a manager can read an answer.

### L3 — Manager answer data

Minimum required to validate manager-facing `answer_snapshot` and `live_answer_view` outputs.

Must include:

- an explicit business question;
- an answer payload with human-readable summary;
- key metrics and counts;
- attention points, risks, or next actions;
- status and priority values;
- provenance fields linking the answer to generated scenarios or real sources.

Recommended payload shape:

```yaml
projection_id: copropriete_360
artifact_kind: answer_snapshot
answer_type: manager_summary
business_question: "Quelle est la situation complete d'une copropriete ?"
subject:
  source_ref: production:copropriete:copro-aurora
  label: ACP Aurora
executive_summary:
  headline: "ACP Aurora est active avec 5 lots et une mission travaux ouverte."
  status: attention_required
key_metrics:
  - metric_id: lots_count
    value: 5
    evidence_refs:
      - administrative:lot:lot-001
attention_points:
  - severity: high
    title: "Travaux ascenseur"
    evidence_refs:
      - decisionnel:decision:decision-lift-budget
```

Passes when:

- `ghostcrab_projection_get(projection_id, include_evidence=true)` returns the payload;
- a human can understand the answer without reconstructing the graph manually;
- each metric or alert has evidence references.

### L4 — Evidence data

Minimum required to make projections auditable.

Must include a matrix:

```text
projection -> claim -> rule_id -> scenario_variant -> evidence entities -> edges -> assertions
```

Recommended files:

```text
generated/<workspace_id>/reports/snapshot_claims_evidence_matrix.json
generated/<workspace_id>/reports/snapshot_claims_evidence_matrix.csv
generated/<workspace_id>/reports/snapshot_claims_evidence_matrix.md
```

Passes when:

- every active snapshot has at least one claim;
- every claim has a primary `evidence_ref`;
- every `evidence_ref` resolves to an imported fact or graph entity;
- support edges such as `supported_by` are materialized;
- assertions are linked back to `business_rules_catalog.yaml`.

---

## 4. Projection artifact requirements

| Artifact kind | Required data levels | Acceptance gate |
|---------------|----------------------|-----------------|
| `analysis_plan` | L1 contract, optional L2 references | `ghostcrab_artifact_get` or `ghostcrab_pack` can expose the retrieval contract |
| `answer_snapshot` | L1 + L2 + L3 + L4 | `ghostcrab_projection_get(..., include_evidence=true)` returns answer payload + linked evidence |
| `live_answer_view` | L1 + L2 + L3 + refresh inputs | `ghostcrab_live_refresh` or artifact refresh recomputes current metrics |
| `evidence_pack` | L4 | `ghostcrab_artifact_get` returns stable evidence bundle linked to parent question/artifact |

Important:

- `analysis_plan` is a retrieval contract, not a calculated answer.
- `answer_snapshot` is frozen. It must carry the answer shape and evidence at the time of creation.
- `live_answer_view` is dynamic. It needs refreshable metrics and current-state records.
- `evidence_pack` is not a substitute for a manager answer. It supports the answer.

---

## 5. Smoke, mini, scale expectations

Use the same rule and claim contracts across profiles. Only volumes and variant breadth change.

| Profile | Purpose | Minimum expectation |
|---------|---------|---------------------|
| `smoke` | Fast import and first read tests | One complete transversal chain, manager payloads for active projections, evidence refs for critical claims |
| `mini` | Realistic business validation | All critical rule variants, normal + exception cases, manager answer quality review |
| `scale` | Retrieval and graph robustness | Larger volumes while preserving assertions, evidence links, and projection response shape |

Smoke is allowed to be small. It is not allowed to be structurally silent. If a snapshot is expected, smoke must include at least a minimal manager summary and evidence.

---

## 6. Required generated outputs

For projects that generate synthetic data, B2/B2.5 should produce:

```text
generated/<workspace_id>/
├── fake_data/
├── import_ready/
│   ├── facets_import.csv
│   └── edges_import.csv
├── rules/
│   └── business_rules_catalog.yaml
├── reports/
│   ├── fake_data_coverage.json
│   ├── fake_data_coverage.md
│   ├── manager_answer_snapshots.json
│   ├── manager_answer_snapshots.md
│   ├── snapshot_claims_evidence_matrix.json
│   ├── snapshot_claims_evidence_matrix.csv
│   └── snapshot_claims_evidence_matrix.md
└── import_manifest.yaml
```

The names may differ by project, but the information must exist.

---

## 7. Validation sequence

1. Validate B1 projections:
   - `specs/manager_questions.yaml`
   - `specs/projection_catalog.yaml`
   - `projection_model_validation.md`

2. Validate B1.5 rules:
   - `rules/business_rules_catalog.yaml`
   - rule coverage by profile
   - model gaps and deferred mapping rules

3. Generate B2 data:
   - `fake_data/`
   - `import_ready/`
   - `fake_data_coverage.*`

4. Generate B2.5 projection answer data:
   - manager answer payloads
   - claim/evidence/assertion matrix
   - snapshot support relations

5. Import and reindex:

```bash
gcp brain structured-import apply \
  --workspace-id <workspace_id> \
  --facets generated/<workspace_id>/import_ready/facets_import.csv \
  --edges generated/<workspace_id>/import_ready/edges_import.csv

gcp brain structured-import reindex \
  --workspace-id <workspace_id> \
  --scope all
```

6. Materialize or refresh projection artifacts.

7. Read-test:

```text
ghostcrab_artifact_get      # analysis_plan / evidence_pack
ghostcrab_pack              # working context
ghostcrab_projection_get    # answer_snapshot
ghostcrab_live_refresh      # live_answer_view
ghostcrab_combined_search   # graph + facts retrieval
ghostcrab_graph_path        # critical reasoning chains
```

---

## 8. Acceptance checklist

- [ ] Every active projection declares its required schemas, facets, edges, and business question.
- [ ] Every critical business rule is covered, blocked with reason, or deferred by policy.
- [ ] Every expected snapshot has an explicit manager answer payload.
- [ ] Every metric, alert, conclusion, or recommendation has evidence refs.
- [ ] Every evidence ref resolves after import and reindex.
- [ ] Every claim is linked to at least one evidence entity or an explicit model gap.
- [ ] `ghostcrab_projection_get(..., include_evidence=true)` is non-empty for snapshots.
- [ ] `live_answer_view` artifacts are refreshed after import before being accepted.
- [ ] Audit reports distinguish runtime issues, model gaps, data gaps, and projection gaps.

---

## 9. Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Snapshot is readable but not useful | L3 missing | Generate manager answer payloads |
| Snapshot has answer text but no evidence | L4 missing | Build claim/evidence matrix and `supported_by` links |
| Fake-data coverage is green but manager asks cannot be answered | L2 exists, L3 missing | Add metrics, rollups, alerts, priorities |
| `analysis_plan` exists but `answer_snapshot` is missing | Only B1 was done | Generate and materialize snapshots after import |
| `live_answer_view` is stale | Artifact seeded but not refreshed | Run refresh after import/reindex |
| Evidence points to broad or wrong entity | Weak evidence resolver | Prefer exact `source_ref`/entity name before relation metadata matches |
| Scale data breaks assertions | Volume multiplier bypassed rules | Re-run rule assertion checks after scaling |

---

## 10. Done when

This SOP is complete when:

- generated datasets cover L1/L2/L3/L4 for the intended artifact kinds;
- smoke has at least one complete answerable path per active projection;
- mini covers critical normal and exception variants;
- scale preserves assertions under larger volumes;
- the final audit can say whether each projection is `pass`, `partial`, `blocked`, or `deferred`, with evidence.
- strategic B2.5 reports are collected into the review finalisation dossier when human validation is required.
