# MindBrain Project Runner

This is the shared execution contract for GhostCrab / MindBrain projects. Agent
adapters such as Codex, Claude Code, Cursor, or other IDE assistants should point
to this file instead of re-implementing the workflow.

The runner exists to prevent incomplete runs: missing projections, weak fake
data, business rules disconnected from the graph, and answers that cannot be
proven from current facts.

It has two control loops:

- Upstream analysis: use
  `../../ghostcrab-skills/mindbrain-ontology-definition/skill_mindbrain_ontology_explorer_v1.md`
  and the 5-act ontology skills before creating the formal model.
- Visual modeling: keep Mermaid diagrams under `docs/visuals/` so humans can
  inspect the domain, process, graph and projection coverage before import.
- Downstream remediation: when an audit fails, create an explicit remediation
  plan that maps each finding to a model, rule, fake-data, import, or projection
  fix.

## Completion Rule

A MindBrain project run is not complete until every required phase has a
machine-readable PASS/WARN/FAIL result and no hard gate is in FAIL.

Agents may explain partial progress, but they must not say the run is done when
any hard gate is failing or untested.

## Edition Routing

1. Read `../EDITIONS.md`.
2. Select exactly one edition for the run:
   - `personal-mcp` for GhostCrab Personal / SQLite.
   - `pro-mcp` for GhostCrab Pro / PostgreSQL.
3. Read only the selected edition folder's `ROUTE_MAP.md` and
   `SOP_SEQUENCE.md`.
4. Do not mix Personal and Pro operators in the same run.

## Required Phases

| Order | Phase | Required output | Hard gate |
|-------|-------|-----------------|-----------|
| 0 | Environment | Runtime, DB, workspace, edition | `ghostcrab_status` or edition-specific equivalent is OK |
| 0.5 | Ontology exploration | `analysis/ontology-exploration.yaml` | First-principles/JTBD analysis, MECE domains, 5 acts, and clarification decisions captured |
| 1 | Import path | `import_path_choices.yaml` | One route selected and compatible with edition |
| 2 | Model | Ontology/model contract | Main classes, facets, edges, statuses and source contracts declared |
| 3 | Projections | Projection catalog | Every manager question maps to at least one projection and proof chain |
| 3.5 | Visual modeling | `docs/visuals/*.mmd` | Domain, process, graph and projection coverage are visible to humans |
| 4 | Business rules | Rules catalog + rule/projection matrix | Critical rules have triggers, evidence, severity and expected failing cases |
| 5 | Fake data | Scenarios and import-ready data | Nominal, blocked, incomplete and routed cases are present |
| 6 | Projection test data | Manager snapshots + evidence matrix | Each expected answer has claims and evidence references |
| 7 | Review finalisation | Human review dossier | Review order and unresolved decisions are explicit |
| 8 | Import | Applied facts/graph/projections/artifacts | Import, reconciliation and reindex completed against the active DB |
| 9 | Post-import audit | Validation report | Facts, graph, projections, artifacts and business questions pass |
| 10 | Audit remediation | `remediation/audit-remediation-plan.yaml` when audit fails | Every blocking finding has an owner, fix target, expected artifact, and re-test command |

## Upstream Ontology Exploration

Before writing `ontology/core.yaml`, projections, rules, or fake data, agents
must capture an exploration brief based on the ontology explorer skill:

- canonical reformulation of the request
- core problem the model must solve
- actors and JTBD, including operators, users, and AI agents
- MECE ontology domains and their boundaries
- 3-5 clarification questions and decisions
- the 5 acts: NOMS, VERBES, QUALIFICATIFS, CONDITIONS, RECHERCHE
- a 4-column canvas: who/what, known properties, linked to, can do/suffer

This brief is the contract that the formal ontology must satisfy. If the model
contains classes, relations, rules, or projections that cannot be traced back to
this exploration, the agent must either update the brief or remove the drift.

## Visual Modeling

Mermaid diagrams are validation artifacts, not decoration. They are required
because most humans cannot reliably review a MindBrain project from YAML,
facets and graph rows alone.

Create and maintain:

- `docs/visuals/domain-map.mmd`: domains, actors and JTBD boundaries.
- `docs/visuals/process-flow.mmd`: real workflow, branches, exceptions and
  blocked states.
- `docs/visuals/knowledge-graph.mmd`: main model classes and relationships.
- `docs/visuals/projection-coverage.mmd`: business questions mapped to
  projections, rules and evidence.

When an audit fails, also create:

- `docs/visuals/audit-remediation-map.mmd`: every blocking finding mapped to
  its target fix and retest route.

Diagrams must reference real classes, relations or projections from the current
project. If a diagram introduces a business branch that is not represented in
the model, rules, fake data or projections, either update those artifacts or
mark the branch as an accepted future gap.

## Hard Gates

The following failures block completion:

- Edition, runtime, DB, or workspace is unknown.
- The upstream ontology exploration brief is missing.
- The ontology exploration brief has no canonical reformulation, actors/JTBD,
  MECE domains, 5-act capture, or clarification decisions.
- A required phase is skipped.
- A projection exists only as prose and is not represented in the projection
  catalog or answer artifact registry expected by the edition.
- A business question has no projection, snapshot, or evidence chain.
- Required Mermaid diagrams are missing, invalid, or stale against the model.
- A business rule has no trigger or cannot be tested with fake data.
- Fake data has no nominal case, no blocked case, no incomplete case, or no
  routed-next-action case.
- An edge references a missing node.
- A graph relation is orphaned after import.
- A critical entity type has fewer than three business facets unless the model
  explicitly justifies it as a technical leaf.
- A critical entity type has no incoming and no outgoing relationship.
- Required facets from projections are absent from model and scenario data.
- Post-import audit shows zero facts, zero expected projections, or zero
  expected answer artifacts for a workspace that claims to be ready.
- The final business questions cannot be answered from current facts, graph,
  facets, projections and artifacts.
- A failed audit has no remediation plan that maps findings to concrete fixes
  and re-test commands.
- A failed audit has no visual remediation map for human review.

## Audit Remediation Loop

When a post-import audit is FAIL, do not restart from scratch. Create
`remediation/audit-remediation-plan.yaml` with:

- audit report path and date
- blocking findings copied or normalized from the audit
- classification of each finding:
  - `analysis_gap`
  - `model_gap`
  - `rule_gap`
  - `fake_data_gap`
  - `import_gap`
  - `projection_gap`
  - `answer_artifact_gap`
  - `graph_gap`
- target files or MCP/DB artifacts to update
- expected validation command
- acceptance criteria

After applying fixes, rerun the validator with the new audit report. The run is
complete only when the audit and remediation phases both pass.

## Recommended Validator

Use the shared validator before import and after import:

```bash
python starterkit/scripts/validate_mindbrain_project.py \
  --project <project-dir> \
  --workspace <workspace-id> \
  --edition personal-mcp
```

For GhostCrab Pro, also pass the projection audit JSON generated by
`scripts/audit_ghostcrab_projections.py`:

```bash
python starterkit/scripts/validate_mindbrain_project.py \
  --project <project-dir> \
  --workspace <workspace-id> \
  --edition pro-mcp \
  --projection-audit <projection_audit_workspace.json>
```

The validator must return JSON with:

- `status`: `PASS`, `WARN`, or `FAIL`
- `blocking_errors`
- `warnings`
- `phase_results`
- `next_required_actions`

## Final Answer Discipline

When reporting a run, agents must include:

- active edition and workspace
- validation status
- blocking errors, if any
- files or DB artifacts created
- commands or MCP calls used for validation
- next required action when status is not PASS

Do not describe a run as complete when the validator status is FAIL.
