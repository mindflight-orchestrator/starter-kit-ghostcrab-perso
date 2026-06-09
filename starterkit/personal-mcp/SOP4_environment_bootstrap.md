# SOP 4 — Environment bootstrap (personal-mcp)

**Edition:** personal-mcp only. Pro path → [../pro-mcp/SOP4_environment_bootstrap.md](../pro-mcp/SOP4_environment_bootstrap.md).

**Phase:** A — verify GhostCrab Personal before modeling.

**Canon:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase A.

---

## Prerequisites

Install the user package first. The v0.5.0 install flow can detect older v0.4.4+ SQLite data, stop active MCP processes, migrate compatible databases, and report clearly when migration is not possible.

```bash
npm install -g @mindflight/ghostcrab-personal-mcp@0.5.0
gcp authorize
gcp brain upgrade --help
```

For a project-local database, set an explicit path. Otherwise GhostCrab Personal uses `~/.ghostcrab/databases/ghostcrab.sqlite`.

```bash
export GHOSTCRAB_SQLITE_PATH="$PWD/data/ghostcrab.sqlite"
```

Source clones are for development only. Disable the install-upgrade hook when installing dependencies in the source checkout:

```bash
git clone git@github.com:mindflight-orchestrator/ghostcrab-personal-mcp.git ~/ghostcrab-personal-mcp
cd ~/ghostcrab-personal-mcp
GHOSTCRAB_SKIP_INSTALL_UPGRADE=1 npm install
npm run build
node bin/gcp.mjs authorize
```

Catalogue: `ghostcrab-personal-mcp/docs/reference/operator-catalog.md`

---

## Operators

`gcp smoke`, `gcp brain up`, MCP `ghostcrab_status`. Backend `:8091` when using `gcp brain document` / `structured-import`.

**Not required:** Docker PostgreSQL, `make dev-bootstrap`, mindCLI.

---

## Checklist

```
[ ] A1 — Node.js ≥ 20, git
[ ] A2 — @mindflight/ghostcrab-personal-mcp@0.5.0 installed, gcp authorize
[ ] A3 — GHOSTCRAB_SQLITE_PATH set when project-local DB is required, otherwise default ~/.ghostcrab/databases/ghostcrab.sqlite accepted
[ ] A4 — gcp smoke passes
[ ] A5 — gcp brain up + MCP client shows ghostcrab_* tools
[ ] A6 — ghostcrab_status OK (no database unreachable)
```

**Done when:** checklist complete → Phase B0 [SOP0](SOP0_import_path_choices.md).

---

## Tool note — ghostcrab_delete

Not exposed in V1. Use tombstone `ghostcrab_upsert` with `facets.status: "deleted"`, or manual SQLite DELETE only when you own the file.
