# SOP 7 — mb_process runtime workflows (Pro)

**Edition:** GhostCrab Pro — PostgreSQL, `mb_process`, MCP `ghostcrab_process_*`.

**Phase:** B1.6, after validated projections and business rules, before fake
data and import scenarios.

**Related files:**

- [SOP_SEQUENCE.md](SOP_SEQUENCE.md)
- [ROUTE_MAP.md](ROUTE_MAP.md#route-mb_process-workflows-b16)
- [../templates/business_rules_catalog.yaml](../templates/business_rules_catalog.yaml)
- [../templates/process_workflow_catalog.yaml](../templates/process_workflow_catalog.yaml)
- [../scripts/README_fake_business_data.md](../scripts/README_fake_business_data.md)
- `ghostcrab-mcp/docs/mb_process-architecture.md`

---

## 1. Objective

Promote selected validated business rules into auditable runtime workflows.

Personal levels 1-3 answer business questions from facets, graph edges and
projections. Pro levels 4-5 add action and orchestration:

```text
facets -> graph -> projection answer -> actionable rule -> process workflow
```

This SOP is only for rules whose action, owner, idempotency, provenance and stop
condition are explicit. Do not promote every business rule.

---

## 2. Inputs

| Input | Purpose |
|---|---|
| `projection_model_validation.md` | Confirms the business question and evidence chain |
| `rules/business_rules_catalog.yaml` | Provides assertions, triggers, forbidden states and scenarios |
| Graph rule evaluations or equivalent evidence | Provides runtime provenance such as `graph_rule_state` |
| Process owner / consumer contract | Defines who consumes emitted events |
| PostgreSQL feature probe | Confirms `mb_process` functions and tables exist |

---

## 3. Output

Recommended project-local output:

```text
process_workflow_catalog.yaml
```

Recommended shape:

```yaml
workflows:
  - id: billing.invoice_overdue_escalation
    source_rule_id: comptabilite.invoice_overdue
    projection_refs: [accounting_closeout]
    process_key: billing
    process_version: v0
    process_rule:
      rule_id: rule.invoice.escalate
      trigger_kind: rule_state
      operation_kind: emit_event
      event_type: invoice.escalation_requested
      idempotency_key: invoice_overdue_escalation
    trigger:
      trigger_id: billing.invoice.overdue
      provenance_kind: graph_rule_state
      provenance:
        workspace_id: "<workspace_id>"
        rule_id: comptabilite.invoice_overdue
        state: invalid
      scope:
        workspace_id: "<workspace_id>"
      source: operator
    safety:
      firing_mode: explicit_or_scheduled
      owner: accounting_manager
      stop_condition: graph_rule_state no longer invalid
      managed_dispatch: false
    tests:
      smoke: [invoice_overdue_emits_escalation_event]
      reconcile: [invoice_paid_marks_trigger_stale]
```

---

## 4. Design sequence

1. Start from a validated projection or business rule.
2. Decide whether the rule should answer only, alert a human, or emit an event.
3. Define the process: `process_key`, version and event types.
4. Define the process rule: condition binding, operation kind and idempotency key.
5. Define trigger provenance: why the trigger exists and when it disappears.
6. Define lifecycle: active, stale, disabled, reactivation and GC behavior.
7. Define consumer contract: who reads `events_outbox` and what happens next.
8. Add fake-data scenarios that prove fire, skip, stale and reactivation cases.

---

## 5. Runtime boundary

Tranches 1-2 are explicit or scheduled. They do not automatically react to every
row write. Automatic on-DML dispatch belongs to the experimental managed
dispatch layer and must be opt-in, whitelisted and reviewed.

Use this distinction in user-facing docs:

- business rules catalog trigger = descriptive modeling/test field;
- `mb_process.process_triggers` = runtime reactive binding with provenance;
- managed PostgreSQL AFTER trigger = experimental dispatch mechanism.

---

## 6. MCP surfaces

Use feature-probed MCP tools when available:

| Need | Tool |
|---|---|
| Import/list process rules | `ghostcrab_process_rules_import`, `ghostcrab_process_rules_list` |
| Evaluate rules explicitly | `ghostcrab_process_rules_evaluate` |
| Register/list triggers | `ghostcrab_process_triggers_register`, `ghostcrab_process_triggers_list` |
| Reconcile trigger lifecycle | `ghostcrab_process_triggers_reconcile` |
| Fire active triggers | `ghostcrab_process_triggers_fire` |

All calls must be scoped to a workspace. Never run a process operation across
all workspaces by default.

---

## 7. Done when

- each promoted workflow has a source projection or business rule;
- process rule, event type, trigger provenance and scope are explicit;
- idempotency and reactivation behavior are documented;
- outbox consumer or human owner is named;
- fake-data includes positive, stale/skip and reactivation scenarios;
- audit can list rules, list triggers, fire/reconcile in scope and inspect
  emitted outbox events.
