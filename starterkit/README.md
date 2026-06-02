# mindBrain StarterKit

Companion kit for [GhostCrab MCP](https://gitlab.com/webigniter/ghostcrab). Load this alongside a running GhostCrab MCP instance to model and ingest a project into GhostCrab / mindBrain.

---

## What this is

This starterkit provides:

- **SOP0** — Import path choices (LinkML vs MCP ontology; structured-import CLI vs SOP5 scripts)
- **SOP4** — Phase A environment verification (is GhostCrab MCP running correctly?)
- **SOP1** — MCP architecture and database contract (Phase B)
- **SOP2** — Ontology modeling from an Obsidian vault (Phase B + Phase C)
- **SOP3** — Parsing pipeline from vault files to PostgreSQL COPY files (Phase C)
- **SOP5** — Generic source import compiler for CSV/API/JSON/app exports
- **Templates** — Starter YAML files for JTBD, contracts, and schema provisioning
- **IDE entrypoints** — Thin loaders for Claude Code, Cursor, and Codex

This kit does **not** replace or modify GhostCrab MCP. It is the reference you use once GhostCrab is running.

---

## What this is not

- Not a fork of GhostCrab MCP
- Not a deployment tool (GhostCrab MCP handles its own Docker setup)
- Not a black-box data migration tool (imports are compiled through explicit contracts, dry runs, and validation)

---

## Prerequisites

1. **GhostCrab MCP cloned and running** — see [ghostcrab README](https://gitlab.com/webigniter/ghostcrab) and `SOP4_environment_bootstrap.md` in this kit.
2. **A frontier-class agent** — Sonnet 4.5+, Opus 4.5+, Kimi 2.5, or Composer 2 Fast. Smaller models skip intake contracts and produce inconsistent schemas.
3. **An Obsidian vault** (or equivalent file collection) you want to model.

---

## Start here

1. Clone this repo alongside `ghostcrab-mcp`:
   ```bash
   git clone https://gitlab.com/webigniter/starter-kit-ghostcrab-perso.git ~/mindbrain-starterkit
   ```
2. Open `QUICKSTART.md` in your agent. It tells the agent which SOP to load at each phase.
3. The agent starts with Phase A (SOP4), then Phase B0 (SOP0), then Phase B (SOP1 + SOP2), then Phase C / C2.

---

## Repo structure

```
mindbrain-starterkit/
├── README.md                          ← This file
├── QUICKSTART.md                      ← Agent entrypoint: phased checklist + SOP pointers
├── SOP0_import_path_choices.md        ← B0/C2.0: LinkML vs MCP; CLI vs scripts
├── SOP4_environment_bootstrap.md      ← Phase A: verify Docker, migrations, smoke test, MCP client
├── SOP1_ghostcrab_mcp.md              ← Phase B: MCP tools, DB contract, DDL lifecycle
├── SOP2_obsidian_ontologie.md         ← Phase B+C: ontology modeling + injection sequence
├── SOP3_parsing_pipeline.md           ← Phase C: LLM parsing pipeline, COPY file generation
├── SOP5_source_import_compiler.md      ← Phase C: generic CSV/API/JSON/app export compiler
├── templates/
│   ├── jtbd.yaml                      ← Job-to-be-done for the vault
│   ├── mvp_core_contract.yaml         ← Entity types, relations, enum values
│   ├── ontology_core_provisioning.yaml
│   ├── initial_referential.yaml
│   ├── mapping_external_to_canonical.yaml
│   ├── disambiguation.yaml
│   ├── source_profile.yaml
│   ├── consumer_contract.yaml
│   ├── import_manifest.yaml
│   ├── import_path_choices.yaml
│   └── linkml_ontology.stub.yaml
├── scripts/
│   ├── profile_source.mjs
│   ├── validate_source_profile.mjs
│   ├── export_model_contract.mjs
│   ├── validate_mapping_contract.mjs
│   ├── transform_source_to_jsonb.mjs
│   ├── write_pending_files.mjs
│   ├── import_facets.mjs
│   ├── materialize_graph_from_edges.mjs
│   ├── generate_copy_migrations.mjs
│   ├── validate_graph_contract.mjs
│   ├── validate_consumer_contract.mjs
│   ├── update_syncstate.mjs
│   └── audit_import_pipeline.mjs
├── claude-code/
│   └── CLAUDE.md                      ← Claude Code entrypoint rule
├── cursor/
│   └── starterkit.mdc                 ← Cursor always-apply rule
└── codex/
    └── SKILL.md                       ← Codex skill descriptor
```

---

## The 3-phase workflow

```
Phase A — Verify GhostCrab MCP    →  SOP4
Phase B0 — Choose ontology path   →  SOP0
Phase B — Model the project        →  SOP1 + SOP2 (§6 bis LinkML or §7 MCP)
Phase C — Parse and ingest         →  SOP2 + SOP3 or SOP5
Phase C2.0 — Choose tabular path  →  SOP0
Phase C2 — Tabular import          →  SOP5 §1 bis or §3
```

See `QUICKSTART.md` for the detailed checklist and success signals per phase.
