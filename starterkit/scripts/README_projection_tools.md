# Projection audit and candidate tools

These Python helpers support the GhostCrab projection workflow around SOP1, SOP2, SOP3, and SOP5.

They cover two different moments:

1. **Audit existing projections** already stored in a GhostCrab SQLite database.
2. **Analyze upstream ontology notes** to extract projection candidates before materialization.

The scripts are intentionally read-only. They do not write projections to GhostCrab.

## 1. Audit materialized projections

Use `audit_ghostcrab_projections.py` when you want to inspect what is already
stored in the projections table and, when a model contract is supplied, whether
the graph and facets can support the planned projections.

The audit now distinguishes the two GhostCrab projection modes:

- **Type A / declared projections**: rows in `mb_pragma.projections` on
  PostgreSQL, or `projections` on SQLite. This is the JSONB projection contract
  used by `ghostcrab_pack`, `mb_pragma.pragma_pack_context`, and mindCLI. It
  describes the business question, required schemas, facets, edges, and
  retrieval jobs.
- **Type B / graph projection results**: rows in `graph.entity` where
  `type = 'ProjectionResult'`. These are calculated report snapshots with
  evidence links, read by `ghostcrab_projection_get` /
  `mb_ontology.ghostcrab_projection_get`.

A healthy Type A count means the projection catalogue is ready for agents. A
zero Type B count does not mean projections are missing; it means no calculated
graph snapshot has been written for those projections.

```bash
python3 starterkit/scripts/audit_ghostcrab_projections.py \
  --db data/ghostcrab.sqlite \
  --workspace my-workspace \
  --model generated/my_model/model_contract.json
```

For GhostCrab Pro PostgreSQL:

```bash
python3 starterkit/scripts/audit_ghostcrab_projections.py \
  --db-kind postgres \
  --postgres-dsn "$GHOSTCRAB_DSN" \
  --workspace tp-chantier-full \
  --model artifacts/model_contract.json
```

For PostgreSQL projects, the generated Markdown report also reminds agents of
the mindCLI commands to use:

```bash
DATABASE_URL="$GHOSTCRAB_DSN" go run ./cmd/mindcli --json \
  mb_pragma projections list --workspace tp-chantier-full

DATABASE_URL="$GHOSTCRAB_DSN" go run ./cmd/mindcli --json \
  mb_pragma projection get --scope tp-chantier-full:bim:conflits_zone_impact

DATABASE_URL="$GHOSTCRAB_DSN" go run ./cmd/mindcli --json \
  mb_pragma inspect --user coordination_bot --query "conflits BIM zone" --limit 8
```

The `--model` argument is optional. When provided, the script compares planned projections in the model contract against materialized projection scopes.

Outputs:

- `generated/projection_audits/projection_audit_<workspace>.json`
- `generated/projection_audits/projection_audit_<workspace>.md`

The audit reports:

- registered projection types from `projection_types`;
- Type A declared projections by `scope`, `proj_type`, `status`, and `agent_id`;
- Type B `ProjectionResult` rows by `projection_id`, name, confidence, and metadata;
- custom projection types not registered in `projection_types`;
- invalid JSON content in `projections.content`;
- expired projections;
- planned projection gaps when a model contract is supplied.
- separate Type A and Type B gap counts:
  - Type A gap = planned projection missing from `mb_pragma.projections`;
  - Type B gap = planned projection missing from `graph.entity` as a calculated `ProjectionResult`;
- graph quality when graph tables are available:
  - graph entity and relation counts;
  - orphan relation count;
  - required edge types with no relation;
  - required schemas with no facet records;
  - required facets not observed in imported facet records;
  - a simple `quality_score` out of 100.

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
and `--manager-questions` imports natural-language business questions. Use
`--recursive-markdown` only when the source reports are spread across nested
Markdown folders.

Materialization lookup adapts to the environment:

- `--db-kind sqlite --db data/ghostcrab.sqlite` checks the starterkit SQLite
  `projections` table.
- `--db-kind postgres --postgres-dsn "$GHOSTCRAB_DSN"` checks GhostCrab Pro
  PostgreSQL, including `mb_pragma.projections`.
- `--db-kind auto` keeps SQLite compatibility and uses PostgreSQL when
  `--postgres-dsn` is provided.
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
- suggested projection type (`FACT`, `STEP`, or `NOTE`);
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

1. Run `analyze_projection_candidates.py` during Phase B after reading the ontology Markdown.
2. Review candidates with the user and select the projections worth materializing.
3. Materialize only projections that have a clear retrieval job and enough data.
4. Run `audit_ghostcrab_projections.py` after materialization to verify what actually exists in GhostCrab.

This keeps the model provisional until the user has validated the retrieval contract, in line with the GhostCrab data architect freeze policy.
