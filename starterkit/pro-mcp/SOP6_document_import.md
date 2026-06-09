# SOP 6 — Import documents non structurés (pro-mcp)

**Edition:** pro-mcp only — PostgreSQL, COPY bulk, MCP audit, **mindCLI**.

**Version:** 0.1  
**Statut:** Draft exploitable  
**Périmètre:** Corpus PDF/HTML/Markdown (hors ou post-vault Obsidian) → PostgreSQL via parsing + COPY — complète [SOP3](SOP3_parsing_pipeline.md) pour corpus plats.

**Canon:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase C (optionnel, parallèle ou après SOP3).

Pour changer de piste édition, voir [../EDITIONS.md](../EDITIONS.md).

---

## Objectif

Ingérer des documents non structurés après Phase B. Contrairement au vault structuré ([SOP3](SOP3_parsing_pipeline.md)), cette SOP cible :

- dossiers plats de PDF/HTML/MD ;
- exports one-shot sans arborescence Obsidian ;
- compléments post-vault (nouveaux briefs, annexes).

**Règle:** bulk = SQL COPY — MCP pour modélisation avant et audit après ; **pas** MCP hot-path en volume.

---

## Position dans la séquence

| SOP | Rôle |
|-----|------|
| SOP3 | Vault Obsidian → JSONB → COPY |
| **SOP6** | Corpus documentaire générique → COPY + reindex |
| SOP5 | Sources tabulaires/API → COPY |

---

## Pipeline

```text
[1] Inventaire corpus (find, mime)
[2] Normalisation texte (pdfplumber, markdown parse — cf. SOP3 §2)
[3] LLM → JSONB SOP2 §4.3
[4] Validation JSONB
[5] generate_copy_migrations.mjs / import_facets plan → COPY PostgreSQL
[6] Graph + projections si requis (scripts StarterKit)
[7] MCP ghostcrab_coverage + ghostcrab_pack
[8] mindCLI mb_pragma audit (recommandé — plus performant que MCP seul)
```

---

## Gates

| Gate | Opérateur | Sortie |
|------|-----------|--------|
| 0 | `ghostcrab_status`, `DATABASE_URL` | workspace Pro actif |
| 1 | `../scripts/profile_source.mjs` | `source_profile.yaml` |
| 2 | `../scripts/transform_source_to_jsonb.mjs` | JSONL validé |
| 3 | COPY exécuté (psql / pgx) | `mfo_facets` peuplé |
| 4 | `ghostcrab_graph_reindex` ou pipeline produit | graphe à jour |
| 5 | MCP `ghostcrab_coverage` | ≥ 80 % schémas core |
| 6 | mindCLI projections | catalogue pragma cohérent |
| 7 | `../templates/consumer_contract.yaml` | smoke consommateurs |

---

## mindCLI — audit projections (recommandé)

```bash
export DATABASE_URL="$GHOSTCRAB_DSN"
go run ../mindbot/cmd/mindcli --json mb_pragma projections list --workspace <workspace_id>
go run ../mindbot/cmd/mindcli --json mb_pragma projection get --scope <scope>
```

Compléter avec MCP `ghostcrab_pack` pour le contexte agent.

---

## Relation SOP3

- **SOP3** : vault Obsidian avec wikilinks, frontmatter, JTBD dossiers.
- **SOP6** : corpus documentaire sans structure vault — réutilise JSONB SOP2 et scripts COPY de SOP3/SOP5.

Ne pas utiliser `gcp brain document` sur Pro (opérateur Personal).

---

## Done when

- COPY appliqué sans erreur transactionnelle
- `ghostcrab_coverage` ≥ 80 %
- mindCLI + `consumer_contract` OK
- `../templates/import_manifest.yaml` documente le run (`edition: pro-mcp`)

---

## Next

[SOP5](SOP5_source_import_compiler.md) · [ROUTE_MAP.md](ROUTE_MAP.md)
