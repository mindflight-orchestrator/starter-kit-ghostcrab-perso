# mb_process Runtime Contract

Use this reference when designing GhostCrab Pro runtime workflows from
validated projections and business rules.

## Concepts

| Concept | Meaning |
|---|---|
| Process | Versioned runtime behavior: `process_key` + `version`. |
| Event type | Schema-validated event a process can emit into the outbox. |
| Process rule | Process-owned binding of a condition to an operation. |
| Dynamic trigger | Logical reactive binding from provenance to a process rule. |
| Provenance | The reason a trigger exists and the condition used for lifecycle checks. |
| Outbox | Durable emitted operation events consumed downstream. |

## Five-Layer Mapping

```text
facets
  -> graph edges
  -> projection answer
  -> actionable rule state
  -> mb_process workflow
```

Personal models and proves the first three layers. Pro can promote selected
rules into layers four and five.

## Provenance Kinds

| `provenance_kind` | Use when |
|---|---|
| `always` | The trigger is operator-owned and always valid until disabled. |
| `never` | Explicit teardown or tests. |
| `process_rule_enabled` | The trigger exists only while a named rule remains enabled. |
| `graph_rule_state` | A graph/rule evaluation row proves the actionable state. |
| `entity_exists` | The existence of an entity justifies the trigger. |

Unknown provenance is fail-safe keep; do not rely on unknown kinds for product
behavior.

## Lifecycle

Triggers move through:

```text
active -> stale -> removed
```

`disabled` is operator-controlled and should not auto-reactivate.

Reconciliation checks whether provenance still holds:

- holds and stale -> reactivate with new `activation_id`;
- holds and active -> keep;
- gone and hard delete false -> mark stale;
- gone and hard delete true -> remove;
- disabled -> never fire.

The `activation_id` is part of idempotency generation. Reactivation must bump
the activation generation so a returning condition can emit again.

## Design Shape

```yaml
workflows:
  - id: billing.invoice_overdue_escalation
    source_rule_id: comptabilite.invoice_overdue
    projection_refs: [accounting_closeout]
    process:
      process_key: billing
      process_version: v0
    event_type:
      key: invoice.escalation_requested
      consumer: accounting_manager
    process_rule:
      rule_id: rule.invoice.escalate
      trigger_kind: rule_state
      operation_kind: emit_event
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
      stale_or_skip: [invoice_paid_marks_trigger_stale]
      reactivation: [invoice_overdue_again_reemits_once]
```

## Safety Rules

- Prefer explicit or scheduled firing for production design.
- Treat managed automatic dispatch as experimental.
- Require one workspace scope per call.
- Require idempotency for every event-emitting rule.
- Name the owner and consumer before promotion.
- Keep answer-only rules out of `mb_process`.

## Audit Checklist

- List process rules.
- List active and stale triggers.
- Fire selected triggers in workspace scope.
- Reconcile after provenance disappears.
- Verify duplicate fire does not duplicate events.
- Verify reactivation emits once after `activation_id` changes.
- Inspect outbox event payload and consumer readiness.
