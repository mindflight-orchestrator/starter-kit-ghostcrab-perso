# StarterKit path resolution (Personal)

Agents and operators resolve file paths **portably** — the Git clone folder name is not fixed.

## Notation

| Token | Meaning |
| --- | --- |
| `{starterkit}` | The `starterkit/` folder inside this Git clone (templates, scripts, `personal-mcp/`) |
| `{project}` | Delivery project root (`ontology/`, `generated/`, `import_path_choices.yaml`) |

Examples:

```text
{starterkit}/personal-mcp/SOP_SEQUENCE.md
{starterkit}/templates/linkml_ontology.stub.yaml
{project}/ontology/production.yaml
```

LinkML domain files live in **`{project}/ontology/`**, not inside the starter-kit clone.

## Resolve `{starterkit}`

Run once per session before reading SOP or template files:

1. **`GHOSTCRAB_STARTERKIT_ROOT`** — if set, `{starterkit}` = `$GHOSTCRAB_STARTERKIT_ROOT/starterkit`
2. **`.ghostcrab/starterkit-root`** in `{project}` — one line: path to clone root (parent of `starterkit/`)
3. **Probes from `{project}` CWD** (first match):
   - `./starterkit/personal-mcp/SOP_SEQUENCE.md` → clone root = `.`
   - `../<clone-name>/starterkit/personal-mcp/SOP_SEQUENCE.md`
   - `./vendor/<clone-name>/starterkit/personal-mcp/SOP_SEQUENCE.md`
4. **Ask once** — record path in `.ghostcrab/starterkit-root`

Canonical clone (any destination folder):

```bash
git clone git@github.com:mindflight-orchestrator/starter-kit-ghostcrab-perso.git
```

## Canonical Personal paths

| Usage | Path |
| --- | --- |
| SOP sequence | `{starterkit}/personal-mcp/SOP_SEQUENCE.md` |
| Route map | `{starterkit}/personal-mcp/ROUTE_MAP.md` |
| Skill route map | `{starterkit}/personal-mcp/SKILL_ROUTE_MAP.md` |
| Path resolution (this file) | `{starterkit}/personal-mcp/STARTERKIT_PATHS.md` |
| SOP0 import choices | `{starterkit}/personal-mcp/SOP0_import_path_choices.md` |
| SOP2 ontology | `{starterkit}/personal-mcp/SOP2_obsidian_ontologie.md` |
| SOP5 tabular import | `{starterkit}/personal-mcp/SOP5_structured_import.md` |
| Templates | `{starterkit}/templates/*` |
| Gate scripts | `{starterkit}/scripts/*` |

**Do not use on Personal SQLite:** `pro-mcp/`, `SOP5_source_import_compiler.md` (Pro track).

## GhostCrab skills bundle (product)

Install from `@mindflight/ghostcrab-personal-mcp` — not from this starter-kit:

```bash
gcp brain setup cursor    # or claude | codex | generic
```

Shared contracts land in `ghostcrab-shared/` next to each skill (always replaced on install). Key files for delivery:

| Topic | Installed path (after setup) |
| --- | --- |
| Path resolution (full) | `ghostcrab-shared/STARTERKIT_PATHS.md` |
| Schema design | `ghostcrab-shared/SCHEMA_DESIGN.md` |
| Enum facet naming | `ghostcrab-shared/ENUM_BUSINESS_FACETS.md` |
| Path/content ingest facets | `ghostcrab-shared/PATH_CONTENT_FACETS.md` |
| Artifact kinds | `ghostcrab-shared/ARTIFACT_KINDS.md` |
| Projection discovery | `ghostcrab-shared/PROJECTIONS_DISCOVERY.md` |
| Phase × skill matrix | `ghostcrab-shared/SKILL_ROUTE_MAP_ESSENTIALS.md` |
| Onboarding gates | `ghostcrab-shared/ONBOARDING_CONTRACT.md` |
| Import closure gates | `ghostcrab-shared/IMPORT_CLOSURE_GATES.md` |

Human deep reference (optional): [ghostcrab-personal-mcp on GitHub](https://github.com/mindflight-orchestrator/ghostcrab-personal-mcp).
