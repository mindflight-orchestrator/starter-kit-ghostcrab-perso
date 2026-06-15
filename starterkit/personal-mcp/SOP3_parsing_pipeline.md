# SOP 3 — Pipeline de parsing vault Obsidian (personal-mcp)

**Edition:** personal-mcp only — SQLite, **`gcp`** + MCP **`ghostcrab_*`**.

**Version:** 0.1  
**Statut:** Draft exploitable  
**Périmètre:** Du vault Obsidian (`.md` / `.pdf`) jusqu'à JSONB validé et routage vers SOP6 ou injection MCP unitaire — **sans COPY PostgreSQL**.

**Canon:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase C (optionnel, avant SOP6).

---

## Objectif

Préparer et parser un vault Obsidian après Phase B ([SOP1](SOP1_ghostcrab_mcp.md) + [SOP2](SOP2_obsidian_ontologie.md)). Cette SOP couvre l'extraction et la validation ; l'écriture bulk passe par [SOP6](SOP6_gcp_document_import.md) ou [SOP5](SOP5_structured_import.md).

**Interdit:** mindCLI, `generate_copy_migrations.mjs`, COPY, `DATABASE_URL`.

---

## Position dans la séquence

| SOP | Rôle | Artefact |
|-----|------|----------|
| SOP2 | Ontologie + JSONB §4.3 | `jtbd.yaml`, specs, mapping |
| **SOP3** | **Parsing vault → JSONB validé** | chunks, JSONL dry-run, plan d'import |
| SOP6 | Bulk documents | `gcp brain document` |
| SOP5 | Bulk tabulaire | `gcp brain structured-import` |

---

## Deux voies après parsing

| Voie | Quand | Suite |
|------|-------|-------|
| **A — Documents (recommandé vault)** | Corpus `.md`/`.pdf`, qualification LinkML | [SOP6](SOP6_gcp_document_import.md) |
| **B — MCP unitaire** | Petit vault (<50 entités), seed ponctuel | SOP2 §7 (`remember`/`upsert`/`learn`) |

---

## Pipeline

```text
[1] Scan vault (find .md .pdf)
[2] Filtrage par source_patterns (jtbd.yaml)
[3] Extraction (section logique / chunk PDF — voir SOP2 §4.1)
[4] LLM → JSONB SOP2 §4.3
[5] Validation JSONB (scripts StarterKit dry-run)
[6] Routage → SOP6 normalize/ingest OU MCP unitaire
[7] ghostcrab_coverage ≥ 80 % (schémas core)
```

---

## Environnements d'exécution

**Agent IDE (Cursor, Claude Code, Codex):** skills `.parsing/` dans le vault ; boucle MCP (`ghostcrab_coverage`, `ghostcrab_search`).

**Script autonome:** Python/Go + OpenRouter ; produire JSONL dans `output/pending_review/` — **pas** de CSV COPY.

---

## Scripts StarterKit (dry-run)

| Gate | Script | Rôle |
|------|--------|------|
| 1 | `../scripts/export_model_contract.mjs` | modèle cible |
| 2 | `../scripts/profile_source.mjs` | `source_profile.yaml` |
| 3 | `../scripts/validate_mapping_contract.mjs` | mapping |
| 4 | `../scripts/transform_source_to_jsonb.mjs` | JSONB intermédiaire |
| — | validation manuelle | `pending_review.json` vide |

Écriture DB : **SOP6** ou MCP — jamais `import_facets.mjs` en mode COPY (Pro-only).

---

## Handoff vers SOP6

1. Phase B + LinkML importé si `document-qualify` taxonomique.
2. Arrêter MCP avant `gcp brain document`.
3. Normaliser le corpus issu du vault :

```bash
gcp brain document document-normalize --input ./vault-export --output-dir ./out
gcp brain document document-ingest --workspace-id <ws> --collection-id <ws>::vault ...
```

Détails : [SOP6_gcp_document_import.md](SOP6_gcp_document_import.md).

---

## Done when

- JSONB validator sans erreur bloquante sur l'échantillon représentatif
- `ontology_path.choice` (`linkml` ou `mcp_incremental`) enregistré dans `{starterkit}/templates/import_path_choices.yaml`
- Post-import : `ghostcrab_coverage` ≥ 80 % ou plan SOP6/SOP5 lancé

---

## Next

[SOP6](SOP6_gcp_document_import.md) · [SOP5](SOP5_structured_import.md) · [ROUTE_MAP.md](ROUTE_MAP.md)
