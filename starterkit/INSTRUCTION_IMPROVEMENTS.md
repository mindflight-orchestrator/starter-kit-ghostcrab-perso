# Instruction Improvements

This note captures the main ambiguities found while reviewing the starterkit instructions.

## Proposed canonical interpretation

The instructions become much clearer if they distinguish:

- the logical ontology model
- the physical storage backend

Recommended canonical rule:

- `workspace_id` is the logical project or domain container
- `schema_id` is the logical ontology or entity namespace inside a workspace
- `GRAPH_WORKSPACE` is the runtime graph identifier returned by GhostCrab MCP for PostgreSQL-backed execution

Backend-specific interpretation:

- PostgreSQL:
  - one `workspace_id` may contain several `schema_id`
  - this is how several ontologies can coexist in the same project workspace
  - `GRAPH_WORKSPACE` is a server-returned runtime UUID or graph identifier and must stay aligned with the created workspace
- SQLite:
  - no PostgreSQL schema layer exists
  - ontology separation is still logical, but implemented as fields in tables rather than as PostgreSQL schema semantics
  - `schema_id` remains a classification attribute, not a physical database schema

Practical consequence:

- the ontology design can be backend-agnostic at the logical level
- the execution and ingestion instructions must branch explicitly between PostgreSQL and SQLite

## What the kit already communicates well

- The 3-phase flow is easy to understand.
- The separation between modeling and ingestion is clear.
- The template order is strong and practical.
- PostgreSQL-only and COPY-not-MCP guidance is explicit.

## Improvements recommended

### 1. Resolve the workspace model contradiction

Current tension:
- `ghostcrab-data-architect` says one workspace per ontology domain.
- `SOP2_obsidian_ontologie.md` says one vault equals one workspace and multiple ontologies coexist inside it.

Recommendation:
- pick one canonical rule and state it everywhere
- suggested wording: "One project domain = one workspace. A workspace may contain multiple ontologies through multiple `schema_id` families when they belong to the same project boundary."

### 2. Clarify `workspace_id` versus `GRAPH_WORKSPACE`

Current tension:
- templates and skill examples use a slug-like `workspace_id`
- `claude-code/CLAUDE.md` says `ghostcrab_workspace_create` returns a UUID that becomes `GRAPH_WORKSPACE`

Recommendation:
- define both explicitly:
- `workspace_id`: stable logical namespace chosen by the user and reused in `schema_id`
- `GRAPH_WORKSPACE`: runtime graph identifier returned by GhostCrab for PostgreSQL execution
- explain which tool expects which identifier

### 3. Clarify the canonical `schema_id` pattern

Current tension:
- some instructions imply `<workspace_id>:<entity_type>`
- SOP2 introduces `<workspace>:<ontology>:<type>`

Recommendation:
- document that `schema_id` is a logical namespace, not necessarily a physical PostgreSQL schema
- define whether the canonical pattern is:
- `<workspace_id>:<entity_type>` for compact models
- or `<workspace_id>:<ontology_family>:<entity_type>` for multi-ontology workspaces
- if both are allowed, state when to choose each form

### 4. Separate "offline modeling" from "live MCP execution"

Current tension:
- entrypoints push Phase A first in every session
- but many ontology design tasks can be done before the MCP server is up

Recommendation:
- allow an explicit "design-only mode"
- suggested rule: "You may draft JTBD, contract, ontology families, and seed referential offline. Do not perform GhostCrab writes until Phase A is validated."

### 4bis. Separate backend-neutral design from backend-specific execution

Current tension:
- the starterkit currently states PostgreSQL-only in several places
- some ontology decisions are actually valid for both PostgreSQL and SQLite

Recommendation:
- split each important rule into:
- logical rule
- PostgreSQL execution rule
- SQLite execution rule
- suggested wording: "Model first at the ontology layer, then choose the storage mapping: PostgreSQL uses workspace plus logical schema namespaces; SQLite stores the same distinction through typed records and attributes."

### 5. Make the edge-label policy local to the project

Current tension:
- the starter contract has a fixed list of 8 labels
- real projects may need a different but still closed set

Recommendation:
- say the list is project-local and frozen in `mvp_core_contract.yaml`
- provide a default list, not a universal one

### 6. Loosen the "exact JSON shape" rule slightly

Current tension:
- SOP2 says no extra fields at all
- later enrichment or provenance metadata may become useful

Recommendation:
- keep a required core shape
- permit optional `metadata` or `provenance` blocks when validators allow them

### 7. Add one full worked example

Recommendation:
- include a complete example for a common case such as website delivery
- this reduces ambiguity much faster than more abstract prose
