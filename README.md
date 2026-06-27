# GhostCrab / MindBrain Starter Kit

Start here if you are a human or an agent discovering this repository.

This repo helps you create a GhostCrab / MindBrain project without skipping the
boring-but-critical steps: understand the domain, define the model, prepare test
data, import it, and prove that the resulting views can answer real business
questions.

## In Plain Language

MindBrain can feel cryptic at first. The simple idea is this:

1. Describe the real-world process in normal words.
2. Identify the important things in that process.
3. Describe what connects those things.
4. List the statuses, rules, exceptions, and search angles.
5. Create test examples.
6. Import the model and data into GhostCrab.
7. Check that the system can answer the questions people actually ask.

The goal is not to produce a beautiful theory. The goal is to build an
operational memory that an agent can query, audit, and use to recommend the next
action.

## If You Are An Agent

Read the entrypoint for your runtime first:

| Agent | Start here |
|-------|------------|
| Codex | [starterkit/codex/SKILL.md](starterkit/codex/SKILL.md) |
| Claude Code | [starterkit/claude-code/CLAUDE.md](starterkit/claude-code/CLAUDE.md) |
| Cursor | [starterkit/cursor/starterkit.mdc](starterkit/cursor/starterkit.mdc) |

Then read the shared runner contract:

- [starterkit/core/MINDBRAIN_PROJECT_RUNNER.md](starterkit/core/MINDBRAIN_PROJECT_RUNNER.md)
- [starterkit/core/gates/project_run_checklist.yaml](starterkit/core/gates/project_run_checklist.yaml)

Do not declare a run complete while the validator reports `FAIL`.

## If You Are Human

You do not need to understand every GhostCrab or MindBrain term before starting.
Use this repo as a guided checklist.

The work happens in this order:

1. **Choose the runtime**
   Decide whether the project targets Personal SQLite or Pro PostgreSQL.
   Start with [starterkit/EDITIONS.md](starterkit/EDITIONS.md).

2. **Explore the domain**
   Before writing schemas, capture the business story: who acts, what they need,
   what can go wrong, and what questions must be answered.
   Use [ghostcrab-skills/mindbrain-ontology-definition/skill_mindbrain_ontology_explorer_v1.md](ghostcrab-skills/mindbrain-ontology-definition/skill_mindbrain_ontology_explorer_v1.md).

3. **Build the model**
   Turn the business story into objects, relationships, statuses, rules, and
   search facets.
   Use the 5-act ontology skills:
   - [SKILL-Onto-mindBrain-QuickRef.md](ghostcrab-skills/mindbrain-ontology-definition/SKILL-Onto-mindBrain-QuickRef.md)
   - [SKILL-Onto-mindBrain.md](ghostcrab-skills/mindbrain-ontology-definition/SKILL-Onto-mindBrain.md)

4. **Define the business questions**
   A model is not ready until it knows which views must answer which questions.
   Example: "What is blocked?", "What is the next action?", "Which records are
   ready to import into another system?"

5. **Create fake data**
   Good fake data must include at least:
   - one normal case
   - one blocked case
   - one incomplete case
   - one case that routes to a next action

6. **Import and reindex**
   Follow the SOP for the selected edition only. Do not mix Personal and Pro
   commands on the same run.

7. **Audit**
   Run the validator and projection audit. If anything fails, create a
   remediation plan and fix the specific gap instead of restarting from scratch.

## Edition Choice

| Edition | Use when | Main folder |
|---------|----------|-------------|
| Personal MCP | You target the standard local SQLite GhostCrab/MindBrain runtime. | [starterkit/personal-mcp](starterkit/personal-mcp) |
| Pro MCP | You target the PostgreSQL/Docker GhostCrab Pro runtime. | [starterkit/pro-mcp](starterkit/pro-mcp) |

Read [starterkit/EDITIONS.md](starterkit/EDITIONS.md) before choosing commands.

## Required Validator

The shared validator is the safety rail. It checks that the work is not just
described, but actually prepared.

```bash
python starterkit/scripts/validate_mindbrain_project.py \
  --project <project-dir> \
  --workspace <workspace-id> \
  --edition <personal-mcp|pro-mcp>
```

For GhostCrab Pro, also pass the projection audit JSON:

```bash
python starterkit/scripts/validate_mindbrain_project.py \
  --project <project-dir> \
  --workspace <workspace-id> \
  --edition pro-mcp \
  --projection-audit <projection_audit_workspace.json>
```

Expected result:

- `PASS`: the run can be considered ready.
- `WARN`: the run may continue, but the warnings must be accepted explicitly.
- `FAIL`: the run is not complete.

## Important Rule

Do not jump directly from "we have an ontology idea" to "let's import data".

The normal path is:

```text
exploration -> model -> projections -> business rules -> fake data
-> projection test data -> import -> audit -> remediation if needed
```

That is the difference between a graph that looks plausible and a MindBrain
workspace that can actually support an agent.
