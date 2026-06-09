---
version: 1.0
statut: Draft exploitable
périmètre: >
  Du vault Obsidian (fichiers .md / .pdf)
  jusqu'aux fichiers de migration prêts à être COPYés
  dans PostgreSQL via le pipeline LLM (stack GhostCrab MCP de référence — pas SQLite).
---

> **Edition: pro-mcp only.** Corpus documentaire plat → [SOP6_document_import.md](SOP6_document_import.md). Voir [EDITIONS.md](../EDITIONS.md) pour changer de piste.

# SOP 3 — Pipeline de parsing et génération des migrations ontologiques

---

## Section 1 — Objectif et périmètre

### 1.1 Ce que cette SOP couvre

- La sélection et la configuration de l'environnement de parsing (agentic IDE vs. script autonome).
- Le parcours des dossiers et fichiers du vault Obsidian (`.md`, `.pdf`).
- L'activation d'appels LLM pour générer le JSONB intermédiaire défini en SOP 2 (section 4.3).
- La validation des JSONB produits avant génération des fichiers de migration.
- La génération des fichiers de migration au format `COPY` pour **PostgreSQL** uniquement.

### 1.2 Ce que cette SOP ne couvre pas

- La modélisation des ontologies et la définition des schémas GhostCrab (→ SOP 2).
- Le déploiement de GhostCrab MCP ou de PostgreSQL.
- L'injection effective dans la base (→ séquence d'injection SOP 2, section 7).
- La gestion des droits d'accès au vault ou aux secrets d'API LLM.
- Le choix des modèles LLM, leur configuration de prompts ou leurs coûts (→ décision opérateur).

### 1.3 Position dans la séquence SOP

| SOP | Rôle | Artefact principal |
|-----|------|--------------------|
| SOP 1 | Architecture GhostCrab MCP, invariants DB | Workspace PostgreSQL + schémas opérationnels |
| SOP 2 | Préparation ontologique depuis le vault | `jtbd.yaml`, `mvp_core_contract.yaml`, JSONB intermédiaire validé |
| **SOP 3** | **Pipeline de parsing → génération des migrations** | **Fichiers `.csv` prêts pour `COPY` PostgreSQL** |

---

## Section 2 — Les deux environnements de parsing

Deux familles d'environnement couvrent les cas d'usage réels. Le choix conditionne l'architecture du pipeline, pas la logique de parsing elle-même.

### 2.1 Environnement A — Agentic IDE (Claude Code, Codex, Cursor)

Ces environnements exposent un agent LLM avec accès direct au système de fichiers, exécution de code et possibilité de charger des skills ou des outils custom.

**Avantages :**
- Itération rapide sur les prompts et les règles de parsing.
- Possibilité de lancer des sous-agents spécialisés (un par type de fichier ou par ontologie candidate).
- Accès aux outils MCP GhostCrab directement depuis l'agent (validation en boucle).
- Pas de gestion de rate-limit côté service : l'IDE gère la file.

**Contraintes :**
- Dépendance à l'environnement de développement : non portable en production autonome.
- La reproductibilité nécessite une skill ou un fichier de configuration versionné.
- Le contexte LLM est partagé avec l'IDE : attention à la pollution de contexte sur les vaults larges.

**Architecture recommandée dans cet environnement :**

```
vault/
├── .parsing/
│   ├── skills/
│   │   ├── parse-md.md          ← skill chargée par l'agent pour les .md
│   │   ├── parse-pdf.md         ← skill chargée par l'agent pour les .pdf
│   │   └── validate-jsonb.md    ← skill de validation JSONB
│   ├── config.yaml              ← workspace_id, granularité, schema_id autorisés
│   └── syncstate.json           ← source_ref → lastModified (incrémentalité)
```

L'agent reçoit les skills au démarrage de session, parcourt le vault via les outils filesystem, appelle le LLM embarqué de l'IDE pour chaque chunk, valide et produit les fichiers de migration.

### 2.2 Environnement B — Script autonome (Python / Golang) via OpenRouter

Un script standalone, lancé en CLI ou via cron, qui passe par OpenRouter (ou équivalent) pour déléguer les appels LLM à des modèles économiques adaptés au volume : `o4-mini`, `Qwen3`, `Gemini Flash`, `DeepSeek V3`.

**Avantages :**
- Portable, reproductible, versionnable, intégrable en CI ou cron.
- Contrôle total du rate-limiting, retry, batching et coût par token.
- Choix du modèle par type de tâche (modèle léger pour extraction, modèle plus puissant pour normalisation).
- Pas de dépendance à un IDE tiers.

**Contraintes :**
- Développement initial plus long qu'une skill IDE.
- La gestion des erreurs LLM (timeouts, JSON invalide) doit être explicitement codée.
- Le debug de prompts est moins interactif.

**Stack minimale recommandée :**

| Composant | Python | Golang |
|-----------|--------|--------|
| Parsing Markdown | `python-frontmatter`, `mistune` | `goldmark`, `gomarkdown` |
| Parsing PDF | `pdfplumber`, `pymupdf` | `pdfcpu`, appel `pdfplumber` via subprocess |
| Appels LLM | `openai` SDK (compat OpenRouter), `httpx` | `go-openai`, `net/http` natif |
| Validation JSON | `jsonschema` | `go-jsonschema`, `encoding/json` |
| Génération CSV | `csv` stdlib, `pandas` | `encoding/csv` stdlib |
| CLI | `click`, `typer` | `cobra` (déjà dans la stack) |

---

## Section 3 — Architecture du pipeline de parsing

Le pipeline est identique dans les deux environnements. Seul l'exécuteur (agent IDE vs. script) diffère.

### 3.1 Vue d'ensemble des étapes

```
[1] Scan du vault
      ↓
[2] Filtrage et priorisation des fichiers
      ↓
[3] Extraction brute (Markdown → sections / PDF → chunks)
      ↓
[4] Construction du prompt LLM (contexte JTBD + chunk)
      ↓
[5] Appel LLM → JSONB brut
      ↓
[6] Validation JSONB (règles SOP 2 section 4.4)
      ↓
[7] Écriture dans le buffer de migration
      ↓
[8] Génération des fichiers de migration (COPY PostgreSQL)
```

### 3.2 Étape 1 — Scan du vault

Parcours récursif du dossier vault. Deux catégories :

```
fichiers .md  → pipeline Markdown
fichiers .pdf → pipeline PDF
```

Le fichier `syncstate.json` (maintenu entre les exécutions) permet l'incrémentialité :

```json
{
  "note/decisions/cms-choice.md": {
    "lastModified": "2025-11-15T10:23:00Z",
    "source_ref": "note:decisions-cms-choice",
    "status": "injected"
  }
}
```

**Règle :** un fichier dont le `lastModified` n'a pas changé depuis le dernier passage est ignoré sauf si `--force-reparse` est passé en argument.

### 3.3 Étape 2 — Filtrage

Appliquer les règles du fichier `mapping_external_to_canonical.yaml` (SOP 2, section 5.5) pour associer chaque fichier à sa `schema_family` et à sa stratégie de granularité :

| Pattern fichier | Granularité | Stratégie |
|-----------------|-------------|-----------|
| `decisions/*.md` | Section logique (headings) | Splitter par `##` |
| `clients/*.md` | Fichier entier | Chunk = note complète |
| `briefs/*.pdf` | Chunk fixe 512 tokens | Overlap 50 tokens |
| `tasks/*.md` | Fichier entier | Chunk = note complète |

Les fichiers ne correspondant à aucun pattern sont loggués dans `unmatched.log` et ignorés.

### 3.4 Étape 3 — Extraction brute

**Pour les fichiers `.md` :**

```python
import frontmatter

def extract_sections(filepath):
    post = frontmatter.load(filepath)
    meta = post.metadata        # → facets candidates
    body = post.content         # → à splitter par headings
    sections = split_by_heading(body, level=2)
    return meta, sections
```

Chaque section produit un chunk avec :
- `path` → base du `source_ref`
- `heading` → slug de section
- `meta` → frontmatter YAML (transmis au LLM dans le prompt)
- `text` → corps de la section

**Pour les fichiers `.pdf` :**

```python
import pdfplumber

def extract_pdf_chunks(filepath, chunk_size=512, overlap=50):
    with pdfplumber.open(filepath) as pdf:
        full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    tokens = tokenize(full_text)
    return sliding_window(tokens, chunk_size, overlap)
```

Prévoir un fallback OCR (Tesseract) si `pdfplumber` retourne moins de 20 tokens par page.

### 3.5 Étape 4 — Construction du prompt LLM

Le prompt est assemblé à partir de trois éléments fixes :

1. **System prompt** — contexte du workspace, JTBD principal, liste des `schema_id` autorisés, liste des `node_type` fermés, liste des 8 edge labels fermés.
2. **Exemples few-shot** — 2 exemples de JSONB valides tirés du `initial_referential.yaml`.
3. **User prompt** — chunk brut + frontmatter + `source_ref` pré-calculé.

**Template system prompt (à paramétrer par workspace) :**

```
Tu es un extracteur ontologique strict.
Workspace : {workspace_id}
JTBD principal : {jtbd_main}
Schémas autorisés : {schema_id_list}
Types de nœuds autorisés : {node_type_list}
Labels d'arêtes autorisés : REFERENCES, DEPENDS_ON, ASSOCIATED_WITH, OBSERVED_ON, OWNED_BY, LOCATED_IN, PART_OF, CONNECTED_TO

Règles absolues :
- Ne produis que du JSON valide, aucun texte autour.
- N'invente pas d'entités absentes du texte.
- Si un type d'entité n'est pas dans la liste, utilise "concept" et génère un `projection_signal` avec `proj_type` aligné sur la convention PENDING_DDL du workspace (cf. SOP 2 §4.3).
- Le champ `source_ref` est fourni, ne le modifie pas.

Format de sortie obligatoire : cf. SOP 2 section 4.3.
```

**Règle de taille de contexte :** ne jamais dépasser 80% du context window du modèle sélectionné. Pour `o4-mini` (128k tokens), cela permet des chunks de 15 000 tokens environ avec un system prompt de 2 000 tokens.

### 3.6 Étape 5 — Appel LLM

**Via OpenRouter (environnement B) :**

```python
import openai

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

def call_llm(system_prompt, user_prompt, model="qwen/qwen3-235b-a22b"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    return response.choices[0].message.content
```

**Sélection du modèle par tâche :**

| Tâche | Modèle recommandé | Raison |
|-------|-------------------|--------|
| Extraction d'entités + facettes | `qwen/qwen3-235b-a22b` | Bon rapport qualité/coût, mode JSON fiable |
| Normalisation + désambiguïsation | `openai/o4-mini` | Raisonnement structuré, respect des listes fermées |
| Génération d'arêtes de graphe | `qwen/qwen3-235b-a22b` | Suffisant pour les 8 labels fermés |
| DDL assisté (types inconnus) | `anthropic/claude-opus-4` | Capacité de raisonnement schema-design |
| Fallback universel | `google/gemini-2.0-flash-001` | Économique, context window large |

**Gestion des erreurs :**
- JSON invalide → retry jusqu'à 3 fois avec le même prompt.
- Timeout → backoff exponentiel (1s, 2s, 4s).
- Rate limit → file d'attente avec délai configurable.
- Après 3 échecs → logguer dans `failed_chunks.log` avec le chunk source, continuer.

### 3.7 Étape 6 — Validation JSONB

Appliquer les règles de SOP 2 section 4.4 avant toute écriture :

```python
def validate_jsonb(record):
    errors = []
    if not record.get("source_ref"):
        errors.append("source_ref manquant")
    if not record.get("schema_id", "").startswith(workspace_id):
        errors.append(f"schema_id non-namespacé : {record.get('schema_id')}")
    if not record.get("content") or len(record["content"]) < 10:
        errors.append("content vide ou trop court")
    for edge in record.get("edges", []):
        if edge["label"] not in ALLOWED_EDGE_LABELS:
            errors.append(f"edge label non autorisé : {edge['label']}")
    for entity in record.get("entities", []):
        if entity["node_type"] not in ALLOWED_NODE_TYPES:
            errors.append(f"node_type non autorisé : {entity['node_type']}")
    return errors
```

| Résultat validation | Action |
|--------------------|--------|
| `errors = []` | Écriture dans le buffer de migration |
| `errors` non vide, corrigeable | Tentative de correction automatique (edge label → `ASSOCIATED_WITH`) |
| `errors` non corrigeable | Logguer dans `pending_review.json`, continuer |
| `node_type` inconnu détecté | Générer payload DDL dans `pending_ddl.json` (cf. SOP 2 §8.5) |

---

## Section 4 — Génération des fichiers de migration

### 4.1 Format cible PostgreSQL (`COPY`)

**Invariant (SOP 1) :** exécuter `COPY` / `psql` avec le **même `DATABASE_URL`** (même instance Postgres et même base) que le serveur GhostCrab MCP. Ne pas importer depuis un DSN « parallèle ».

Les données validées sont accumulées dans un buffer en mémoire, puis écrites en CSV adapté à la commande `COPY` PostgreSQL. Aucun chemin SQLite n'est prévu dans `src/` pour ce produit : ne pas générer de scripts `INSERT OR REPLACE` SQLite.

**Table cible principale : `mfo_facets`**

```sql
COPY mfo_facets (workspace_id, source_ref, schema_id, content, facets, created_at)
FROM '/data/migration_mfofacets_20260417.csv'
WITH (FORMAT csv, HEADER true, DELIMITER ',', QUOTE '"', ENCODING 'UTF8');
```

**Format du fichier CSV généré (exemple) :**

```csv
workspace_id,source_ref,schema_id,content,facets,created_at
"web-project-acme","note:decisions-cms-choice","web-project-acme:decision","Décision de choisir un CMS headless...","{""title"":""Décision choix CMS headless"",""date"":""2024-11-15"",""status"":""valide"",""tags"":[""cms"",""technique""],""client"":""acme-corp""}","2026-04-17T10:00:00Z"
```

**Règle d'échappement :** le champ `facets` est un JSONB sérialisé en chaîne avec les guillemets internes échappés selon la convention CSV RFC 4180.

**Tables cibles graphe : `graph.entity` et `graph.relation`**

Les colonnes réelles suivent le bootstrap GhostCrab (voir migrations). Pour les nœuds alignés sur `ghostcrab_learn`, `type` vaut en pratique la constante `entity` et `name` porte l'identifiant chaîne du nœud ; `metadata` JSONB peut contenir `node_type`, `label`, etc.

```csv
-- graph.entity (schéma simplifié pour export intermédiaire)
workspace_id,type,name,metadata,confidence,created_at

-- graph.relation — source_id / target_id sont des bigint référençant graph.entity.id
workspace_id,type,source_id,target_id,confidence,metadata,created_at
```

**Chargement graphe :** en pratique, privilégier `ghostcrab_learn` après résolution des ids ; un `COPY` direct dans `graph.relation` exige que `source_id` et `target_id` existent déjà (staging SQL ou jointure sur `graph.entity`).

**Table cible projections : `mfo_projections`**

Les colonnes exactes dépendent de la migration appliquée ; le pipeline documentaire peut produire un CSV aligné sur les champs utilisés par `ghostcrab_project` dans ton workspace (ex. `agent_id`, `scope`, `proj_type`, `content`, `status`, …). Vérifier le DDL courant avant le premier import en masse.

### 4.2 Structure des fichiers de sortie

```
output/
├── migration_mfofacets_{date}.csv         ← COPY PostgreSQL → mfo_facets
├── migration_graph_entity_{date}.csv      ← COPY PostgreSQL → graph.entity (si bulk)
├── migration_graph_relation_{date}.csv    ← COPY PostgreSQL → graph.relation (si bulk)
├── migration_projections_{date}.csv         ← COPY PostgreSQL → mfo_projections (si bulk)
├── syncstate.json                         ← Mis à jour après parsing complet
├── pending_review.json                    ← JSONB rejetés, à revoir manuellement
├── pending_ddl.json                       ← Types inconnus détectés, DDL à soumettre
└── failed_chunks.log                      ← Chunks en erreur LLM après 3 retries
```

### 4.3 Script d'import PostgreSQL (illustratif)

```bash
#!/bin/bash
# import_migration.sh — utiliser le même DATABASE_URL que GhostCrab MCP (SOP 1).

DATE=$1
PG_DSN=${DATABASE_URL}

psql "$PG_DSN" <<SQL
BEGIN;

\COPY mfo_facets (workspace_id, source_ref, schema_id, content, facets, created_at)
FROM 'output/migration_mfofacets_${DATE}.csv'
WITH (FORMAT csv, HEADER true);

\COPY graph.entity (workspace_id, type, name, metadata, confidence, created_at)
FROM 'output/migration_graph_entity_${DATE}.csv'
WITH (FORMAT csv, HEADER true);

\COPY graph.relation (workspace_id, type, source_id, target_id, confidence, metadata, created_at)
FROM 'output/migration_graph_relation_${DATE}.csv'
WITH (FORMAT csv, HEADER true);

-- mfo_projections : adapter la liste des colonnes au DDL réel avant d'activer cette ligne.
-- \COPY mfo_projections (...)
-- FROM 'output/migration_projections_${DATE}.csv'
-- WITH (FORMAT csv, HEADER true);

COMMIT;
SQL
```

**Règle d'idempotence :** `mfo_facets` est protégé par un index unique sur `(source_ref, workspace_id)` (cf. migrations). Pour les imports répétés, prévoir `ON CONFLICT` / table de staging / politique de merge conforme au workspace.

---

## Section 5 — Implémentation dans l'environnement A (Agentic IDE)

### 5.1 Structure de la skill de parsing

Dans Claude Code, Cursor ou Codex, une skill est un fichier Markdown chargé en contexte de l'agent. Elle décrit le comportement attendu de l'agent pour une tâche précise.

**Fichier : `.parsing/skills/parse-md.md`**

```markdown
# Skill : parse-md

## Objectif
Parser un fichier .md du vault Obsidian et produire le JSONB intermédiaire
conforme à SOP 2 section 4.3.

## Inputs attendus
- filepath : chemin absolu du fichier .md
- workspace_id : identifiant du workspace
- schema_family : famille de schéma mappée depuis le dossier parent
- granularity : "file" | "section" | "chunk-512"

## Processus
1. Lire le frontmatter YAML → candidats facets
2. Splitter le body selon granularity
3. Pour chaque chunk :
   a. Calculer le `source_ref` = "note:" + slug(filepath) [+ ":" + slug(heading)]
   b. Appeler le LLM avec le system prompt workspace
   c. Valider le JSONB retourné
   d. Si valide → append au buffer de migration
   e. Si invalide → append à pending_review.json

## Format JSONB obligatoire
[cf. SOP 2 section 4.3]

## Règles absolues
- Ne jamais modifier le `source_ref` calculé
- Ne jamais inventer d'entités
- Tout `node_type` inconnu → signaler DDL en attente (`pending_ddl.json`, cf. SOP 2 §8.5)
```

### 5.2 Sous-agents dans un agentic IDE

Pour les vaults larges (> 200 notes), activer des sous-agents parallèles par dossier :

```
Agent principal
├── Sous-agent A : dossier decisions/ (10 notes)
├── Sous-agent B : dossier clients/ (30 notes)
├── Sous-agent C : dossier tasks/ (80 notes)
└── Sous-agent D : dossier briefs/ (5 PDFs)
```

Chaque sous-agent charge les skills correspondantes et écrit dans un buffer partiel. L'agent principal fusionne les buffers et génère les fichiers de migration.

**Règle de fusion :** déduplication sur `source_ref` avant écriture finale. En cas de conflit sur un même `source_ref` (deux sous-agents ont parsé la même note), conserver le record avec le `content` le plus long.

---

## Section 6 — Implémentation dans l'environnement B (Script autonome)

### 6.1 Structure du projet

```
parser/
├── main.py (ou main.go)
├── config/
│   ├── workspace.yaml       ← workspace_id, backend, granularity par dossier
│   └── prompts/
│       ├── system.txt       ← system prompt template
│       └── examples.json    ← few-shot examples
├── parsers/
│   ├── markdown.py (ou .go)
│   └── pdf.py (ou .go)
├── llm/
│   └── client.py (ou .go)  ← wrapper OpenRouter avec retry
├── validators/
│   └── jsonb.py (ou .go)   ← règles SOP 2 section 4.4
├── writers/
│   └── csv_writer.py (ou .go)
└── syncstate.json
```

### 6.2 Commande CLI (Golang / Cobra)

```go
// cmd/parse.go
var parseCmd = &cobra.Command{
    Use:   "parse [vault-path]",
    Short: "Parser un vault Obsidian et générer les fichiers de migration",
    RunE: func(cmd *cobra.Command, args []string) error {
        vaultPath := args[0]
        workspaceID, _ := cmd.Flags().GetString("workspace")
        model, _ := cmd.Flags().GetString("model")
        output, _ := cmd.Flags().GetString("output")
        forceReparse, _ := cmd.Flags().GetBool("force")

        pipeline := NewParsingPipeline(PipelineConfig{
            VaultPath:    vaultPath,
            WorkspaceID:  workspaceID,
            Model:        model,
            OutputDir:    output,
            ForceReparse: forceReparse,
        })
        return pipeline.Run()
    },
}

func init() {
    parseCmd.Flags().String("workspace", "", "Workspace ID (requis)")
    parseCmd.Flags().String("model", "qwen/qwen3-235b-a22b", "Modèle LLM via OpenRouter")
    parseCmd.Flags().String("output", "./output", "Dossier de sortie")
    parseCmd.Flags().Bool("force", false, "Forcer le re-parsing complet")
    parseCmd.MarkFlagRequired("workspace")
}
```

### 6.3 Commande CLI (Python / Typer)

```python
import typer
from pathlib import Path

app = typer.Typer()

@app.command()
def parse(
    vault_path: Path = typer.Argument(..., help="Chemin du vault Obsidian"),
    workspace: str = typer.Option(..., help="Workspace ID"),
    model: str = typer.Option("qwen/qwen3-235b-a22b", help="Modèle LLM"),
    output: Path = typer.Option(Path("./output"), help="Dossier de sortie"),
    force: bool = typer.Option(False, help="Forcer le re-parsing complet"),
):
    pipeline = ParsingPipeline(
        vault_path=vault_path,
        workspace_id=workspace,
        model=model,
        output_dir=output,
        force_reparse=force,
    )
    pipeline.run()

if __name__ == "__main__":
    app()
```

---

## Section 7 — Gestion de l'incrémentialité

### 7.1 Fichier syncstate.json

```json
{
  "workspace_id": "web-project-acme",
  "last_run": "2026-04-17T10:00:00Z",
  "files": {
    "decisions/cms-choice.md": {
      "last_modified": "2025-11-15T10:23:00Z",
      "source_ref": "note:decisions-cms-choice",
      "status": "injected",
      "chunks_produced": 3,
      "chunks_validated": 3
    },
    "briefs/brief-client-acme.pdf": {
      "last_modified": "2025-10-01T08:00:00Z",
      "source_ref": "pdf:brief-client-acme",
      "status": "pending_review",
      "chunks_produced": 12,
      "chunks_validated": 10,
      "chunks_rejected": 2
    }
  }
}
```

### 7.2 Politique de mise à jour

| Événement | Action dans syncstate | Action sur la migration |
|-----------|----------------------|------------------------|
| Fichier inchangé | Pas de mise à jour | Ignoré |
| Fichier modifié | `status → re_parsed` | Re-parser, écraser les lignes dans le CSV (même `source_ref`) |
| Fichier supprimé | `status → deleted` | Générer un fichier `migration_deletes_{date}.sql` avec `DELETE` ciblant le `source_ref` (même DSN que MCP) |
| Nouveau fichier | Nouvelle entrée | Parser et ajouter au CSV |

---

## Section 8 — Hypothèses critiques à valider avant exécution

| Hypothèse | Question à lever | Comment valider |
|-----------|-----------------|-----------------|
| H1 | La clé API OpenRouter est valide et le modèle cible est disponible | Appel test : `POST /api/v1/models` + appel minimal sur un chunk de 10 tokens |
| H2 | Les fichiers `.md` sont en UTF-8 sans BOM | `file --mime-encoding vault/**/*.md \| grep -v utf-8` |
| H3 | Les PDFs sont extractibles (non scannés, non protégés) | `pdfplumber` sur 3 PDFs représentatifs, vérifier > 20 tokens/page |
| H4 | Le `mapping_external_to_canonical.yaml` est complet (tous les dossiers couverts) | Compter les fichiers non matchés dans `unmatched.log` après un premier run |
| H5 | Les `schema_id` et `node_type` définis en SOP 2 sont disponibles dans `config/workspace.yaml` | Vérifier la cohérence avec `ghostcrab schema-list` |
| H6 | La base PostgreSQL cible a les tables et index attendus | Exécuter le DDL de bootstrap GhostCrab avant le premier `COPY` |
| H7 | Le context window du modèle sélectionné est suffisant pour les chunks les plus longs | Calculer `max(len(chunks))` en tokens avant de choisir le modèle |

---

## Section 9 — Acceptance criteria

```gherkin
Given un vault de 10 notes .md avec frontmatter et sections
When le pipeline est exécuté avec --workspace web-project-acme
Then migration_mfofacets_{date}.csv est produit
And il contient au moins 10 lignes (une par note minimum)
And chaque ligne a workspace_id, source_ref, schema_id, content, facets non vides
And source_ref commence par "note:"
And schema_id commence par "web-project-acme:"
And facets est un JSON valide
And syncstate.json est mis à jour avec le statut de chaque fichier
```

```gherkin
Given un JSONB produit par le LLM avec un edge label non autorisé "INSPIREDBY"
When le validateur s'exécute
Then l'injection dans le buffer est bloquée
And le JSONB est loggué dans pending_review.json
And le pipeline continue sans interruption
```

```gherkin
Given un fichier .md déjà parsé (présent dans syncstate.json avec status = "injected")
And le fichier n'a pas été modifié depuis le dernier run
When le pipeline est exécuté sans --force
Then le fichier est ignoré
And aucune ligne supplémentaire n'est ajoutée au CSV pour ce `source_ref`
```

```gherkin
Given le fichier de migration migration_mfofacets_{date}.csv
When la commande COPY est exécutée sur PostgreSQL
Then toutes les lignes sont insérées sans erreur de contrainte
And ghostcrab-search retourne les entités insérées
And ghostcrab-coverage retourne un taux > 80% sur les schémas core
```

---

## Annexe A — Sélection du modèle par profil de vault

| Profil vault | Volume estimé | Modèle recommandé | Coût estimé |
|--------------|---------------|-------------------|-------------|
| Vault projet (50-200 notes) | < 500k tokens | `qwen/qwen3-235b-a22b` | ~$0.50-2.00 |
| Vault KB technique (200-1000 notes) | 500k-2M tokens | `qwen/qwen3-235b-a22b` + batch | ~$2-8 |
| Vault PDF-lourd (> 50 PDFs) | > 2M tokens | `google/gemini-2.0-flash-001` | ~$1-4 |
| Normalisation / DDL assisté | Ponctuel | `openai/o4-mini` | ~$0.10-0.50 |

Les estimations sont indicatives et dépendent de la densité du texte et de la granularité choisie.

---

## Annexe B — Checklist de démarrage

Avant le premier run du pipeline :

- [ ] `jtbd.yaml` produit et validé (SOP 2 section 2.2)
- [ ] `mvp_core_contract.yaml` finalisé (SOP 2 annexe A)
- [ ] `mapping_external_to_canonical.yaml` configuré pour tous les dossiers du vault
- [ ] `initial_referential.yaml` renseigné avec les entités stables (pivots)
- [ ] `disambiguation.yaml` créé pour les synonymes connus
- [ ] Clé API OpenRouter disponible dans `OPENROUTER_API_KEY`
- [ ] Base de données bootstrappée (DDL GhostCrab exécuté)
- [ ] Modèle LLM cible validé sur un appel test
- [ ] `output/` et `syncstate.json` initialisés
- [ ] `config/workspace.yaml` paramétré avec `workspace_id`, `schema_id`, `node_type` autorisés

---

*Fin de SOP 3 — Version 1.0*
