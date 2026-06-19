# SOP — Review finalisation dossier (personal-mcp)

**Edition:** GhostCrab Personal — SQLite, `gcp brain ...`, MCP `ghostcrab_*`.

**Phase:** Cross-phase supervision after B1 starts producing human-review artifacts.

**Related SOPs:**

- [SOP_SEQUENCE.md](SOP_SEQUENCE.md)
- [SOP_business_rules_catalog.md](SOP_business_rules_catalog.md)
- [SOP_projection_test_data_levels.md](SOP_projection_test_data_levels.md)
- [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md)
- [../scripts/README_projection_tools.md](../scripts/README_projection_tools.md)

---

## 1. Objective

Use a finalisation dossier to collect copies of the documents that humans and
agents must review before a workspace is considered business-valid.

The dossier is not the source of truth. Source files stay in their original
locations. The dossier gives reviewers a numbered reading order, validation
questions, statuses, and stable review rounds.

---

## 2. Required layout

Recommended project-local layout:

```text
finalisation/<workspace_id>/
├── README.md
├── review_manifest.json
├── review_status.json
├── current/
│   ├── 00_INDEX.md
│   └── ...
└── review_rounds/
    └── <YYYY-MM-DD>/
        ├── 00_INDEX.md
        └── ...
```

- `current/` is a regenerated mirror.
- `review_rounds/<name>/` is stable and may be annotated by humans.
- `review_manifest.json` lists the sources and their reading order.
- `review_status.json` records optional human validation statuses.

---

## 3. What to collect

At minimum, collect:

- source ontology Markdown;
- central ontology contract and LinkML validation reports;
- schema/facet activation plans;
- manager questions and projection catalogs;
- business rules catalogs and rule/projection matrices;
- fake-data coverage reports;
- projection test data B2.5 reports, including manager snapshots and
  `claim -> evidence -> assertion` matrices;
- import/read-test/projection audits;
- smoke, mini and scale profile reports;
- scenario comparison contracts when validating a second workspace.

---

## 4. Review statuses

Use these statuses:

| Status | Meaning |
|---|---|
| `required` | Must be reviewed but no decision recorded yet |
| `context` | Useful background, not a blocking gate |
| `machine` | Machine-readable evidence, reviewed through summary reports |
| `appendix` | Optional support material |
| `to_validate` | Human validation explicitly pending |
| `validated` | Accepted by reviewer |
| `needs_fix` | Corrections must be made in source files |

Corrections must be made in the source files, not only in finalisation copies.

---

## 5. Procedure

1. Update `review_manifest.json` when new strategic documents appear.
2. Regenerate `current/`:

```bash
python3 scripts/collect_serenity_v4_review_docs.py --mode current
```

3. Create a stable review round:

```bash
python3 scripts/collect_serenity_v4_review_docs.py \
  --mode review-round \
  --review-round <YYYY-MM-DD>
```

4. Reviewers annotate files in the review round.
5. Record decisions in `review_status.json` when useful.
6. Apply real corrections to source files.
7. Regenerate `current/` and rerun project audits.

---

## 6. Scenario comparison

For a second scenario:

- keep the same ontology, business rules and projection contracts;
- create a separate scenario contract;
- generate data into a separate output folder;
- import into a separate workspace;
- compare coverage, snapshots, evidence matrices and projection audits.

The scenario workspace must be explicit in every command. Do not reimport a
scenario into the baseline workspace.

---

## 7. Done when

This SOP is complete when:

- `current/00_INDEX.md` lists all strategic review documents;
- a stable review round exists for human annotations;
- required documents have `validated` or `needs_fix` status;
- source corrections have been applied and regenerated;
- scenario comparison reports distinguish model gaps, data gaps, projection gaps
  and runtime gaps.
