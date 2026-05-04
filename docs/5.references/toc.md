5.2 reference/schema-spec.md
Structure:

File format (YAML, version field)

Entity definition: all fields

Dimension types table: type / description / example / constraints

Relation definition: all fields, cardinality options

Projection definition: all fields, format options (cockpit / raw / summary)

Constraint syntax: rule expressions, severity levels

Versioning and migration

Complete annotated example schema (compliance domain)

5.3 reference/projection-api.md
Structure:

mindCLI invocation

REST API: endpoint, headers, query params

Full cockpit response: every field annotated

Inbound write: PATCH endpoint + response (downstream_effects)

Python SDK: install, client init, project(), update()

TypeScript SDK: install, client init, project(), update()

LangGraph integration: checkpointer + projection node

CrewAI integration: memory tool

Error codes table (MB_001–MB_006)

Rate limits table (Pro / Enterprise / SQLite)