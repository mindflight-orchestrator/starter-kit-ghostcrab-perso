---
name: ghostcrab-process-workflow-designer
description: Design GhostCrab Pro / MindBrain mb_process runtime workflows from validated projections, business rules, graph rule states, or action scenarios. Use when Codex must turn business questions and rules into process rules, dynamic trigger provenance, events outbox contracts, idempotency strategy, reconciliation/GC behavior, safety gates, fake-data trigger scenarios, or autonomy-ready workflow designs. Do not use for GhostCrab Personal-only retrieval/projection work unless planning a future Pro migration.
---

# GhostCrab Process Workflow Designer

Use this skill to promote selected GhostCrab Pro rules into auditable runtime
workflows. The skill's job is design and review, not bulk import.

## Core Boundary

Use the five-layer model:

1. dimensions / facets;
2. semantic graph edges;
3. business questions -> projections -> answers;
4. business rules -> actionable states -> process events;
5. workflows -> chained actions -> controlled autonomy.

GhostCrab Personal stops at levels 1-3. Personal can model rules as evidence
and scenarios, but it does not install `mb_process` triggers or autonomous
workflows. GhostCrab Pro / PostgreSQL covers levels 1-5.

## Required Inputs

Before designing a workflow, collect:

- validated projection ids or `projection_model_validation.md`;
- source rules from `rules/business_rules_catalog.yaml`;
- required graph/facet evidence and expected rule state;
- human or agent owner for the action;
- consumer of the outbox event;
- stop condition and idempotency expectation.

If any of action, owner, provenance, stop condition or consumer is missing,
return a design gap instead of inventing a workflow.

## Design Workflow

1. Identify the actionable state.
   Start from a validated projection or business rule. Decide whether the rule
   should only answer, alert a human, or emit an event.

2. Map evidence to provenance.
   Prefer `graph_rule_state` when graph/rule evaluation is the reason the
   trigger exists. Use `entity_exists`, `process_rule_enabled`, `always` or
   `never` only when they are semantically exact.

3. Define the process contract.
   Produce `process_key`, `process_version`, `event_type`, event payload
   expectations, consumer, and owning role.

4. Define the process rule.
   Specify `rule_id`, `trigger_kind`, `operation_kind`, idempotency key and
   expected event emission.

5. Define trigger lifecycle.
   Specify `trigger_id`, provenance, scope, activation/reactivation behavior,
   stale/disabled behavior, and reconcile/GC expectations.

6. Define safety.
   Default to explicit or scheduled firing. Treat managed PostgreSQL dispatch as
   experimental and require whitelist/operator review.

7. Define tests.
   Include positive fire, stale/skip, reactivation, duplicate/idempotency, and
   no-cross-workspace cases.

## Output Contract

Return a concise design with:

- workflow id and purpose;
- source projection/rule references;
- process rule and event type;
- trigger provenance and scope;
- idempotency and reactivation strategy;
- outbox consumer;
- safety gates;
- fake-data scenarios;
- audit commands or MCP surfaces;
- gaps and non-promoted rules.

When writing artifacts, prefer the StarterKit template
`starterkit/templates/process_workflow_catalog.yaml`.

## MCP Surfaces

Use feature-probed Pro surfaces when available:

- `ghostcrab_process_rules_import`
- `ghostcrab_process_rules_list`
- `ghostcrab_process_rules_evaluate`
- `ghostcrab_process_triggers_register`
- `ghostcrab_process_triggers_list`
- `ghostcrab_process_triggers_reconcile`
- `ghostcrab_process_triggers_fire`

All process operations must be scoped to one workspace. Never design a default
operation that spans every workspace.

## References

Load `references/mb_process-runtime-contract.md` when the task needs exact
`mb_process` concepts, provenance kinds, lifecycle details, or output shapes.
