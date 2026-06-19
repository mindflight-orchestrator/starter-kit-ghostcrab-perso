# Projection audit and candidate tools

These Python helpers support the GhostCrab projection workflow around SOP1, SOP2, SOP3, SOP5 and the B2.5 projection test-data phase.

When projection audits, snapshots, or evidence matrices need human validation, collect them into a numbered review dossier with [../personal-mcp/SOP_review_finalisation_dossier.md](../personal-mcp/SOP_review_finalisation_dossier.md).

B2.5 reference: [../personal-mcp/SOP_projection_test_data_levels.md](../personal-mcp/SOP_projection_test_data_levels.md). Use it when projections must be tested as manager-facing answers, not only as schema-valid imported data.

They cover two different moments:

1. **Audit existing answer artifacts and projections** already stored in a GhostCrab SQLite or PostgreSQL database.
2. **Analyze upstream ontology notes** to extract projection candidates before materialization.

The scripts are intentionally read-only. They do not write projections or artifacts to GhostCrab.

## Companion skills

Pair these StarterKit scripts with GhostCrab agent skills ([../personal-mcp/SKILL_ROUTE_MAP.md](../personal-mcp/SKILL_ROUTE_MAP.md)):

| Script moment | Companion skill |
|---------------|-----------------|
| `analyze_projection_candidates.py` (pre-import, read-only) | `ghostcrab-projection-reviewer` — human validation of `projection_model_validation.md` |
| `audit_ghostcrab_projections.py` (post-import, read-only) | `ghostcrab-gap-auditor` — remediation narrative and `adjustments[]` |
| SOP5 gate 7 (`ghostcrab_pack`, `ghostcrab_projection_get`) | `ghostcrab-operator` + `ghostcrab-json-answer-builder` |

Install skills: `gcp brain setup cursor|claude|codex|generic` from `ghostcrab-personal-mcp`.

## Answer artifact taxonomy (canonical)

GhostCrab Personal routes agents by **`artifact_kind`**, not by legacy Type A/B labels. Use this vocabulary first; legacy labels appear only as compatibility footnotes.

| `artifact_kind` | Role | Storage (Personal SQLite) | MCP / operator read |
|-----------------|------|---------------------------|---------------------|
| `analysis_plan` | Stable retrieval contract (business question, required schemas/facets/edges) | `projections` | `ghostcrab_project`, `ghostcrab_pack` |
| `live_answer_view` | Dynamic, refreshable dashboard / live answer | `mindbrain_answer_artifacts` | `ghostcrab_live_refresh`, `gcp brain artifact refresh` |
| `answer_snapshot` | Frozen calculated report with evidence | `graph_entity` (`ProjectionResult`) | `ghostcrab_projection_get` |
| `evidence_pack` | Evidence bundle linked to a parent artifact | `mindbrain_answer_artifacts` | `ghostcrab_artifact_get` |

**Lifecycle** on registry artifacts: `draft` | `active` | `frozen` | `stale` | `archived` | `deleted`. After bulk import, `live_answer_view` rows are often **`stale`** until refreshed — expected, not a hard failure.

**Legacy compatibility** (wire overlays only — do not use as primary routing):

| Legacy | Maps to |
|--------|---------|
| Type A / `projection_type_a` | `analysis_plan` |
| Type B / `projection_type_b` | `answer_snapshot` |

**Important:** zero `answer_snapshot` rows does **not** mean the catalogue is missing when `analysis_plan` rows exist. **`live_answer_view` is not Type B** — it is a separate registry artifact.

**`proj_type`** (semantic type inside `analysis_plan` rows, written by `ghostcrab_project`): `FACT` | `GOAL` | `STEP` | `CONSTRAINT`. The `projection_types` table also seeds `NOTE` for pack ranking, but **`ghostcrab_project` does not accept `NOTE`**.

Product reference: `ghostcrab-personal-mcp/docs/explanation/renommage.md`, `vendor/mindbrain/docs/artifacts/artifact-model.md`.

---

## 1. Audit materialized projections and answer artifacts

Use `audit_ghostcrab_projections.py` when you want to inspect what is already stored and, when a model contract is supplied, whether the graph and facets can support the planned projections.

```bash
python3 starterkit/scripts/audit_ghostcrab_projections.py \
  --db data/ghostcrab.sqlite \
  --workspace my-workspace \
  --model generated/my_model/model_contract.json
```

Optional: compare planned `live_answer_view` entries from a seed file:

```bash
python3 starterkit/scripts/audit_ghostcrab_projections.py \
  --db data/ghostcrab.sqlite \
  --workspace my-workspace \
  --answer-artifacts-seed generated/my-workspace/answer-artifacts.seed.jsonl
```

For GhostCrab Pro PostgreSQL:

```bash
python3 starterkit/scripts/audit_ghostcrab_projections.py \
  --db-kind postgres \
  --postgres-dsn "$GHOSTCRAB_DSN" \
  --workspace tp-chantier-full \
  --model artifacts/model_contract.json
```

### Personal operator commands (artifact registry)

```bash
gcp brain artifact list --workspace-id <ws> --kind analysis_plan
gcp brain artifact list --workspace-id <ws> --kind live_answer_view
gcp brain artifact list --workspace-id <ws> --kind answer_snapshot

# After import + seed — refresh stale live views
gcp brain artifact refresh live_answer_view__<slug>
```

### Pro operator commands (mindCLI)

For PostgreSQL projects, the generated Markdown report also reminds agents of the mindCLI commands to use:

```bash
DATABASE_URL="$GHOSTCRAB_DSN" go run ../mindbot/cmd/mindcli --json \
  mb_pragma projections list --workspace tp-chantier-full

DATABASE_URL="$GHOSTCRAB_DSN" go run ../mindbot/cmd/mindcli --json \
  mb_pragma projection get --scope tp-chantier-full:bim:conflits_zone_impact

DATABASE_URL="$GHOSTCRAB_DSN" go run ../mindbot/cmd/mindcli --json \
  mb_pragma inspect --user coordination_bot --query "conflits BIM zone" --limit 8
```

The `--model` argument is optional. When provided, the script compares planned projections in the model contract against materialized `analysis_plan` scopes.

Outputs:

- `generated/projection_audits/projection_audit_<workspace>.json`
- `generated/projection_audits/projection_audit_<workspace>.md`

The audit reports:

- registered `proj_type` values from `projection_types`;
- **`analysis_plan`** rows (`projections` table) by `scope`, `proj_type`, `status`, and `agent_id`;
- **`answer_snapshot`** rows (`ProjectionResult` in graph) by `projection_id`, name, confidence, and metadata;
- **`live_answer_view`** and **`evidence_pack`** rows from `mindbrain_answer_artifacts` (when table exists), grouped by `lifecycle`;
- `stale_live_view_count` (informational — expected post-import until refresh);
- custom `proj_type` values not registered in `projection_types`;
- invalid JSON content in `projections.content`;
- expired projections;
- planned gaps when a model contract or seed file is supplied:
  - **`analysis_plan_gap`** — planned scope missing from `projections`;
  - **`answer_snapshot_gap`** — planned projection missing from graph `ProjectionResult`;
  - **`live_answer_view_gap`** — planned live view missing from registry (when `--answer-artifacts-seed` supplied);
- graph quality when graph tables are available:
  - graph entity and relation counts;
  - orphan relation count;
  - required edge types with no relation;
  - required schemas with no facet records;
  - required facets not observed in imported facet records;
  - a simple `quality_score` out of 100.

Legacy summary keys (`type_a_declared_projection_count`, `type_b_projection_result_count`) are kept as aliases.

---

## 2. Analyze projection candidates from ontology Markdown

Use `analyze_projection_candidates.py` before materializing projections. It scans Markdown files and extracts rows from sections named:

```markdown
## Projections / rapports types
```

Example:

```bash
python3 starterkit/scripts/analyze_projection_candidates.py \
  --source-dir Ontologie_Infrastructure_Administrative \
  --db data/ghostcrab.sqlite \
  --workspace serenity-coproprietes
```

You can also enrich the extracted candidates with deterministic analysis lenses.
This is useful when the source ontology already lists obvious reports, but you
want to search for missing manager-facing projections:

```bash
python3 starterkit/scripts/analyze_projection_candidates.py \
  --source-dir Ontologie_Chantier \
  --projection-catalog specs/projection_catalog.yaml \
  --manager-questions specs/manager_questions.yaml \
  --model-contract artifacts/model_contract.json \
  --workspace tp-chantier-full \
  --db-kind postgres \
  --postgres-dsn "$GHOSTCRAB_DSN" \
  --prompt "utilise patterns Blind Spot toujours pour un rôle de manager qui supervise les opérations : quelles questions manqueraient pour compléter celles déjà identifiées? ajoute les nuances JTBD suivant les rôles humains et agents IA impliqués"
```

Equivalent explicit flags:

```bash
python3 starterkit/scripts/analyze_projection_candidates.py \
  --source-dir Ontologie_Chantier \
  --projection-catalog specs/projection_catalog.yaml \
  --manager-questions specs/manager_questions.yaml \
  --model-contract artifacts/model_contract.json \
  --workspace tp-chantier-full \
  --role manager_operations \
  --lens blind_spot_manager \
  --lens jtbd_human \
  --lens jtbd_ai
```

Known lenses can be listed with:

```bash
python3 starterkit/scripts/analyze_projection_candidates.py --list-lenses
```

Because this script is usually launched by an agent such as Codex, Claude Code,
or Cursor, it can also prepare a compact review pack for that agent to send to
an LLM:

```bash
python3 starterkit/scripts/analyze_projection_candidates.py \
  --source-dir Ontologie_Chantier \
  --projection-catalog specs/projection_catalog.yaml \
  --manager-questions specs/manager_questions.yaml \
  --model-contract artifacts/model_contract.json \
  --workspace tp-chantier-full \
  --include-blind-spots \
  --include-jtbd \
  --write-agent-context
```

This writes:

- `projection_candidates_agent_context.json`
- `projection_candidates_agent_prompt.md`

The calling agent can run an LLM review with that prompt, save the JSON answer,
then merge the additional findings back into the candidate report:

```bash
python3 starterkit/scripts/analyze_projection_candidates.py \
  --source-dir Ontologie_Chantier \
  --projection-catalog specs/projection_catalog.yaml \
  --manager-questions specs/manager_questions.yaml \
  --model-contract artifacts/model_contract.json \
  --workspace tp-chantier-full \
  --include-blind-spots \
  --include-jtbd \
  --llm-findings generated/projection_candidates/llm_findings.json
```

For YAML-first projects, `--projection-catalog` imports declared projections
and `--manager-questions` imports natural-language business questions. Catalog entries may override routing:

```yaml
projections:
  - name: pilotage_hebdomadaire
    artifact_kind: live_answer_view   # default: analysis_plan
    proj_type: STEP
    scope: my-workspace:decisionnel:pilotage_hebdomadaire
```

When manager questions become too broad because a projection combines many
facets, add focused review candidates with grouped clusters:

```bash
python3 starterkit/scripts/analyze_projection_candidates.py \
  --source-dir Ontologie_Chantier \
  --projection-catalog specs/projection_catalog.yaml \
  --manager-questions specs/manager_questions.yaml \
  --projection-requirements specs/projection_requirements.yaml \
  --workspace tp-chantier-full \
  --expand-manager-question-clusters
```

The broad question is kept as the strategic candidate. The generated
`manager_question_cluster` rows split the same requirements into shorter human
questions such as responsibility/action, status/risk, deadlines, money,
decision/AG, proof/compliance, source/mapping, and perimeter/object.

Use `--recursive-markdown` only when the source reports are spread across nested Markdown folders.

Materialization lookup adapts to the environment:

- `--db-kind sqlite --db data/ghostcrab.sqlite` checks `projections` (`analysis_plan`) and `mindbrain_answer_artifacts` (`live_answer_view`).
- `--db-kind postgres --postgres-dsn "$GHOSTCRAB_DSN"` checks GhostCrab Pro PostgreSQL, including `mb_pragma.projections`.
- `--db-kind auto` keeps SQLite compatibility and uses PostgreSQL when `--postgres-dsn` is provided.
- `--db-kind none` disables materialization lookup.

The summary reports both row-level `materialized_count` and
`unique_materialized_scope_count`, because several natural-language manager
questions can map to the same materialized projection scope.

Outputs:

- `generated/projection_candidates/projection_candidates.json`
- `generated/projection_candidates/projection_candidates.md`
- `generated/projection_candidates/projection_model_validation.md`

Each candidate includes:

- normalized projection name;
- expected GhostCrab scope;
- ontology family;
- source file and source section;
- **`suggested_artifact_kind`** (`analysis_plan` | `live_answer_view` | `answer_snapshot` | `evidence_pack`);
- **`suggested_proj_type`** (`FACT`, `GOAL`, `STEP`, or `CONSTRAINT` — valid for `ghostcrab_project`);
- **`materialization_target`** (`ghostcrab_project` | `answer_artifact_seed` | `review_only`);
- **`materialization_warning`** when a type cannot be written via MCP;
- retrieval jobs such as `summary`, `monitor`, `aggregate`, `graph_traversal`;
- inferred data dependencies;
- materialization status;
- recommendation (`add`, `review`, or `keep`).

When analysis lenses are active, candidates also include:

- `origin` (`source_table` or `analysis_lens`);
- `lens` (`blind_spot_manager`, `jtbd_human`, `jtbd_ai`);
- `business_question`;
- `required_schemas`, `required_facets`, and `required_edges`;
- `human_jobs` and `ai_agent_jobs`;
- `impact_summary`, explaining what the candidate implies for the model.

`projection_model_validation.md` is the human validation document. It groups
the natural-language questions, declared projections, Blind Spot/JTBD additions,
and the dimensions / semantic edges to confirm. When `--model-contract` is
provided, it also flags schemas, facets, and edges required by proposals but
missing from the contract.

## Recommended workflow

1. Run `analyze_projection_candidates.py` during Phase B1 after reading the ontology Markdown.
2. Review candidates with the user — confirm **`artifact_kind`** and **`proj_type`** per row in `projection_model_validation.md`.
3. Materialize `analysis_plan` rows via `ghostcrab_project`; load `live_answer_view` via `answer-artifacts.seed.jsonl` when needed.
4. When `answer_snapshot` artifacts are expected, generate the B2.5 manager snapshot reports and `claim -> evidence -> assertion` matrices before declaring the projection testable.
5. Run `audit_ghostcrab_projections.py` after import to verify registry + graph; refresh stale `live_answer_view` artifacts.

This keeps the model provisional until the user has validated the retrieval contract, in line with the GhostCrab data architect freeze policy.
