# GhostCrab MCP StarterKit — QUICKSTART

**For agents and humans.** Load this file first to understand which SOP to use at each phase.

---

## Prerequisites: GhostCrab MCP

This starterkit is a **companion repo** to the [GhostCrab MCP server](https://gitlab.com/webigniter/ghostcrab.git). It provides agent-loadable SOPs, templates, and IDE entrypoints for setting up a GhostCrab-backed project.

Download:

```bash
git clone https://gitlab.com/webigniter/starter-kit-ghostcrab-perso.git ~/mindbrain-starterkit
```

**Required before using this starterkit:**

- GhostCrab MCP server installed and running → see [GhostCrab README](../README.md) for full installation steps
- Docker Engine running (Docker Desktop or daemon)
- Node.js ≥ 20
- PostgreSQL container healthy (native or fallback mode)

**Quick verification:**

```bash
# From your GhostCrab MCP repo directory:
cd ~/ghostcrab-mcp
docker inspect --format '{{.State.Health.Status}}' ghostcrab_postgres_native
# Expected: "healthy"

# Verify 24 ghostcrab_* tools are available in your MCP client
```

If any of these prerequisites fail, **stop here** and complete Phase A (SOP4) before continuing.

> **Modeling gate:** before proposing any domain model, entity list, schema family, or ontology structure, the agent must first confirm that GhostCrab MCP is actually reachable from the current session. Minimum check: GhostCrab tools visible in the client, then call `ghostcrab_status`. If the server is configured in settings but not exposed in the current session, do **not** present a model as MCP-validated. Stay in diagnostic mode, explain the gap clearly, and stop before Phase B writes or schema proposals.

> **Storage note:** This workflow targets **PostgreSQL only**. SQLite is not supported in the current GhostCrab MCP stack (`src/` contains no SQLite implementation). Do not generate SQLite migration scripts.

> **Tool limitation — ghostcrab_delete:** The V1 MCP server does not expose a `ghostcrab_delete` tool. To handle note moves or deletions, use the tombstone pattern: call `ghostcrab_upsert` with `facets.status: "deleted"` on the old `source_ref`, then upsert the new record. For hard deletes, use manual SQL `DELETE` statements against the PostgreSQL database.

---

## The 3-Phase Workflow

```
Phase A — Verify GhostCrab MCP    →  SOP4_environment_bootstrap.md
Phase B — Model the project        →  SOP1_ghostcrab_mcp.md + SOP2_obsidian_ontologie.md
Phase C — Parse and ingest files   →  SOP2_obsidian_ontologie.md §7 + SOP3_parsing_pipeline.md or SOP5_source_import_compiler.md
```

---

## Phase A — Verify GhostCrab MCP Setup

**Load:** `SOP4_environment_bootstrap.md`

**Goal:** confirm the stack is running before any modeling.

Quick path (single command if Docker is up):

```bash
cd ~/ghostcrab-mcp
make dev-bootstrap   # starts PostgreSQL + runs migrations
npm run build        # compiles the MCP server
npm run smoke:mcp    # validates all 24 tools respond
```

Then connect your MCP client (see SOP4 §A6) and call `ghostcrab_status`.

**Phase A is done when:** `ghostcrab_status` returns no `database: unreachable` error and 24 `ghostcrab_*` tools are visible in your agent.

---

## Phase B — Model the Project

**Load:** `SOP1_ghostcrab_mcp.md` then `SOP2_obsidian_ontologie.md`

**Goal:** help the user understand what kind of vault they have, which jobs it serves, and whether it should become one ontology or several related ontology families in one workspace.

Sequence:

1. Call `ghostcrab_status` if not already done in Phase A from the current session.
2. Call `ghostcrab_modeling_guidance` with the user's JTBD before proposing a domain model.
3. Understand the vault JTBD: who uses it, what triggers use, and which outcomes or retrieval jobs matter.
4. Inspect the vault structure and identify its main documentation families, note families, and operating contexts.
5. Decide with the user whether the vault is:
   - one ontology
   - several ontology candidates inside one shared workspace
   - or a mixed case with one primary ontology plus operational side ontologies
6. Fill `templates/jtbd.yaml` — what the vault is for, who uses it, and which ontology candidates exist.
7. Only then propose a **provisional** model aligned with GhostCrab guidance.
8. Call `ghostcrab_workspace_create` — creates the isolated workspace.
9. Fill `templates/mvp_core_contract.yaml` — entity types, relation labels, enum values.
10. Call `ghostcrab_schema_register` for each entity type declared in the contract.
11. Use `ghostcrab_ddl_propose` → human approval → `ghostcrab_ddl_execute` for Layer 1 tables.
12. Call `ghostcrab_workspace_inspect` — verify Layer 1 tables exist with correct semantics.

### Phase B Decision Lens

- `One ontology` when the same actor, the same dominant retrieval jobs, and the same lifecycle explain most of the vault.
- `Several ontologies in one workspace` when different documentation families serve different jobs but still belong to the same project boundary.
- `Separate workspaces` only when the domains have different owners, different lifecycles, and little or no shared entities.

Guardrails:

- Folder structure alone is not enough to define ontology boundaries.
- A client-facing project vault is not automatically a CRM domain.
- Tasks, meeting notes, and launch checklists do not automatically require separate workspaces.
- Always state whether the current output is documentary, provisional, or MCP-validated.

Ultra-short examples:

- `Vault multi-ontologies dans un meme workspace` — a web client project vault containing `pages_web`, `gestion_projet`, `transcription_reunions`, and maybe `seo` or `design-system`: same project boundary, different retrieval jobs.
- `Vault mono-ontologie` — a personal documentation vault with notes, articles, research, and LinkedIn drafts: same dominant retrieval and synthesis job.

**Phase B is done when:** `ghostcrab_workspace_inspect` shows all declared entity types, and `ghostcrab_coverage` returns a baseline (even 0%).

---

## Phase C — Parse and Ingest Files

**Load:** `SOP2_obsidian_ontologie.md` §7 (injection sequence) + `SOP3_parsing_pipeline.md`

**Goal:** parse the vault (`.md` / `.pdf`) and bulk-load facts into PostgreSQL.

Sequence:

1. Choose the parsing environment (agentic IDE vs. autonomous script — SOP3 §2).
2. Configure the LLM prompt per file type (SOP3 §3).
3. Validate JSONB output per schema (SOP3 §3.7).
4. Generate COPY files (SOP3 §4).
5. Run COPY with the **same `DATABASE_URL`** as the GhostCrab MCP server — never use a different DSN.
6. Verify coverage: `ghostcrab_coverage` ≥ 80% on core schemas.

**Phase C is done when:** `ghostcrab_coverage` reports ≥ 80% coverage on core schemas declared in `mvp_core_contract.yaml`.

## Phase C2 — Compile External Sources

**Load:** `SOP5_source_import_compiler.md`

**Goal:** compile CSV/API/JSON/app exports into validated GhostCrab records without hard-coding a project-specific pipeline.

Sequence:

1. Fill `templates/source_profile.yaml` from the real source.
2. Export or load the target model contract.
3. Extend `templates/mapping_external_to_canonical.yaml` with record id, facets, enum maps, and edge rules.
4. Fill `templates/consumer_contract.yaml` before writing data, especially if a graph viewer is expected.
5. Dry-run into JSONB intermediate records and review `pending_review.json` / `pending_ddl.json`.
6. Import facets, materialize graph if required, test projections, then test consumers.
7. Record the run in `templates/import_manifest.yaml` or a project-local copy.

**Phase C2 is done when:** the manifest shows no blocking exceptions and every declared consumer passes its smoke tests.

---

## SOP Reference

| SOP | Phase | File |
|-----|-------|------|
| SOP4 | A — Environment | `SOP4_environment_bootstrap.md` |
| SOP1 | B — MCP architecture & DB contract | `SOP1_ghostcrab_mcp.md` |
| SOP2 | B+C — Ontology modeling + injection | `SOP2_obsidian_ontologie.md` |
| SOP3 | C — Parsing pipeline | `SOP3_parsing_pipeline.md` |
| SOP5 | C — Generic source import compiler | `SOP5_source_import_compiler.md` |

## Template Reference

| Template | Used in | File |
|----------|---------|------|
| JTBD | Phase B start | `templates/jtbd.yaml` |
| MVP Core Contract | Phase B | `templates/mvp_core_contract.yaml` |
| Ontology Core Provisioning | Phase B | `templates/ontology_core_provisioning.yaml` |
| Initial Referential | Phase B | `templates/initial_referential.yaml` |
| Mapping External → Canonical | Phase B | `templates/mapping_external_to_canonical.yaml` |
| Disambiguation | Phase B | `templates/disambiguation.yaml` |
| Source Profile | Phase C2 | `templates/source_profile.yaml` |
| Consumer Contract | Phase C2 | `templates/consumer_contract.yaml` |
| Import Manifest | Phase C2 | `templates/import_manifest.yaml` |

---

## IDE Entrypoints

| Agent | File |
|-------|------|
| Claude Code | `claude-code/CLAUDE.md` |
| Cursor | `cursor/starterkit.mdc` |
| Codex | `codex/SKILL.md` |
