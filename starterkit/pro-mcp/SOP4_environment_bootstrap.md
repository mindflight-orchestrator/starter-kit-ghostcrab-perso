# SOP 4 — Environment bootstrap (pro-mcp)

**Edition:** pro-mcp only. Voir [EDITIONS.md](../EDITIONS.md) pour changer de piste.

**Canon:** [SOP_SEQUENCE.md](SOP_SEQUENCE.md) Phase A.

### Pro (`ghostcrab-mcp`)

```bash
git clone https://gitlab.com/webigniter/ghostcrab.git ~/ghostcrab-mcp
cd ~/ghostcrab-mcp
git submodule update --init --recursive
```

> **Pro storage:** PostgreSQL only (Docker). Do not generate SQLite scripts on Pro.

This SOP (Phase A) focuses on **environment verification**. Conceptual model: SOP1/SOP2 + product glossary.

> **Tool limitation — ghostcrab_delete:** The V1 MCP server does not implement `ghostcrab_delete`. To handle note moves or deletions: use `ghostcrab_upsert` with a tombstone pattern (`facets.status: "deleted"`) for soft deletes, or execute manual SQL `DELETE` for hard deletes. See SOP2 §8.1 for the full workaround.

---

## Objectif de cette SOP

Cette SOP est le **point d'entrée Phase A** du workflow agentic. Elle garantit que GhostCrab MCP est opérationnel avant d'engager la modélisation ontologique (Phase B — SOP1/SOP2) ou l'ingestion (Phase C — SOP3).

**À exécuter :** à chaque nouvelle installation, après un redémarrage machine, ou lorsque `ghostcrab_status` retourne une erreur.

Follow [SOP_SEQUENCE.md](SOP_SEQUENCE.md) and [ROUTE_MAP.md](ROUTE_MAP.md) for Pro.

---

## pro-mcp — Phase A

**Sequence:** [pro-mcp/SOP_SEQUENCE.md](pro-mcp/SOP_SEQUENCE.md) Phase A.

**Operators:** Docker, `DATABASE_URL`, `make dev-bootstrap`, `npm run smoke:mcp`, MCP `ghostcrab_status`.

### Checklist pro-mcp

```
[ ] A1 — Docker, Node.js ≥ 20, git
[ ] A2 — ghostcrab-mcp cloned, .env configured, submodules init
[ ] A3 — PostgreSQL container healthy
[ ] A4 — Migrations applied (npm run migrate)
[ ] A5 — npm run smoke:mcp passes
[ ] A6 — MCP client connected (ghostcrab_* visible)
[ ] A7 — ghostcrab_status acceptable (native or fallback documented)
```

**Done when:** checklist complete → Phase B0 [SOP0](SOP0_import_path_choices.md).

---

## Legacy checklist (pro-mcp detail below)

The sections **A1–A7** that follow describe the **pro-mcp** path in full.

---

## A1 — Prérequis système

Vérifier la présence des outils suivants avant toute autre action :

```bash
# Docker Engine (Desktop ou daemon) — version 24+
docker --version

# Docker Compose plugin (intégré dans Docker Desktop ou installé séparément)
docker compose version

# Node.js — version 20 minimum
node --version   # doit afficher v20.x.x ou supérieur

# npm — inclus avec Node.js
npm --version

# git — pour cloner et gérer les submodules
git --version
```

**Résultat attendu :** toutes les commandes retournent une version. Si l'une échoue, installer le composant manquant avant de continuer.

> **Note macOS :** Docker Desktop est recommandé. Après installation, lancer Docker Desktop et attendre que le daemon soit actif (`docker info` sans erreur) avant de continuer.

---

## A2 — Clonage et configuration .env

### A2.1 — Cloner le repo

```bash
git clone https://gitlab.com/webigniter/ghostcrab.git ~/ghostcrab-mcp
cd ~/ghostcrab-mcp

# Initialiser les submodules (extensions natives)
git submodule update --init --recursive
```

### A2.2 — Copier et vérifier .env

```bash
cp .env.example .env
```

**Variables critiques à vérifier dans `.env` :**

| Variable | Valeur par défaut | Rôle | À changer ? |
|---|---|---|---|
| `DATABASE_URL` | `postgres://ghostcrab:ghostcrab@localhost:5432/ghostcrab` | DSN utilisé par le serveur MCP et les migrations | Seulement si port modifié |
| `PG_PORT` | `5432` | Port hôte mappé vers le container | Voir note port ci-dessous |
| `POSTGRES_USER` | `ghostcrab` | Utilisateur PostgreSQL | Non pour dev local |
| `POSTGRES_PASSWORD` | `ghostcrab` | Mot de passe PostgreSQL | Non pour dev local |
| `POSTGRES_DB` | `ghostcrab` | Nom de la base | Non pour dev local |
| `MFO_NATIVE_EXTENSIONS` | `native` | Mode d'extension : `native` ou `fallback` | Voir section A3 |
| `GHOSTCRAB_EMBEDDINGS_MODE` | `disabled` | Désactivé par défaut — ne pas changer pour le premier démarrage | Non |

> **Port 5432 vs 55432 :** Le port par défaut dans `.env` est `5432`. Si une instance PostgreSQL tourne déjà sur la machine hôte (port 5432 occupé), changer `PG_PORT=55432` dans `.env` et mettre à jour `DATABASE_URL` en conséquence : `postgres://ghostcrab:ghostcrab@localhost:55432/ghostcrab`.  
> Le script `scripts/verify-e2e.mjs` utilise `55432` hors CI par défaut — ce comportement est normal et documenté.

### A2.3 — Installer les dépendances Node.js

```bash
npm install
```

---

## A3 — Démarrer la stack PostgreSQL

### Matrice de décision : quelle commande utiliser ?

| Situation | Commande | Container créé |
|---|---|---|
| **Cas normal** — Mac/Linux, image Docker pré-construite avec extensions natives | `make dev-bootstrap` | `ghostcrab_postgres_native` |
| **Cas normal (détaillé)** — démarrer uniquement le postgres | `docker compose --env-file .env up -d --build postgres` | `ghostcrab_postgres_native` |
| **Docker natif indisponible** — CI, environnement sans Zig/compilateur Zig local | `POSTGRES_STACK=fallback make dev-up` | `ghostcrab_postgres` |
| **Fallback manuel** | `docker compose --env-file .env -f docker/docker-compose.yml up -d postgres` | `ghostcrab_postgres` |

> **`make dev-bootstrap`** est l'alias recommandé : il démarre PostgreSQL, attend qu'il soit `healthy`, puis applique les migrations en une seule commande.

### Explication des deux stacks Docker

| Stack | Fichier compose | Container | Extensions |
|---|---|---|---|
| **native** (défaut) | `docker-compose.yml` (racine du repo) | `ghostcrab_postgres_native` | `pg_facets`, `pg_dgraph`, `pg_pragma` compilées et chargées |
| **fallback** | `docker/docker-compose.yml` | `ghostcrab_postgres` | Image pgvector standard — sans extensions natives |

En mode `fallback`, les outils MCP fonctionnent via SQL pur (mode dégradé) — pas de BM25 natif, pas de traversal `pg_dgraph`. Acceptable pour le développement ou les environnements CI sans accès aux binaires natifs.

### Vérifier que PostgreSQL est healthy

```bash
# Vérifier l'état du container (native stack)
docker inspect --format '{{.State.Health.Status}}' ghostcrab_postgres_native

# Résultat attendu : "healthy"
# Si "starting" : attendre 10-20s et relancer la commande
# Si "unhealthy" : consulter les logs
docker compose logs postgres
```

Avec `make dev-bootstrap`, l'attente est automatique (timeout 60 secondes, vérification toutes les 2 secondes).

---

## A4 — Appliquer les migrations

> **Si vous avez utilisé `make dev-bootstrap`**, les migrations ont déjà été appliquées — passer directement à A5.

Si vous avez démarré PostgreSQL manuellement :

```bash
# Mode native (port 5432)
npm run migrate

# Mode native avec port custom (ex: 55432)
PG_PORT=55432 npm run migrate

# Ou via make
make dev-migrate
```

**Résultat attendu :** migrations listées et marquées comme `applied`, aucune erreur. Le schéma `mindbrain` doit exister dans la base.

**Vérification optionnelle :**

```bash
# Connexion directe à la base pour vérifier le schéma
docker exec -it ghostcrab_postgres_native \
  psql -U ghostcrab -d ghostcrab -c "\dn"
# Doit lister : mindbrain, public, (et éventuellement runtime, graph, mfo)
```

---

## A5 — Smoke test MCP

Le smoke test démarre le serveur MCP en processus, exécute une séquence d'appels d'outils, et valide que les 24 outils répondent sans erreur critique.

```bash
npm run smoke:mcp
```

**Résultat attendu :** sortie sans `ERROR` ou `FATAL`. Le log doit indiquer que les outils ont été appelés et ont répondu.

**Si le smoke test échoue :**

| Symptôme | Cause probable | Action |
|---|---|---|
| `ECONNREFUSED localhost:5432` | PostgreSQL non démarré ou port incorrect | Vérifier A3, contrôler `PG_PORT` dans `.env` |
| `relation "mindbrain.workspaces" does not exist` | Migrations non appliquées | Relancer A4 |
| `Cannot find module './dist/index.js'` | Build absent | Lancer `npm run build` |
| Timeout sur outil natif | Extensions non chargées | Vérifier que `MFO_NATIVE_EXTENSIONS=native` et que le container est `ghostcrab_postgres_native` |

---

## A6 — Connecter le client MCP

### A6.1 — Construire le serveur

```bash
npm run build
# Le serveur est maintenant dans dist/index.js
```

### A6.2 — Configuration MCP client

**Claude Code** (`~/.claude/server.json` ou via la commande `/mcp`) :

```json
{
  "mcpServers": {
    "ghostcrab": {
      "command": "node",
      "args": ["/chemin/absolu/vers/ghostcrab-mcp/dist/index.js"],
      "env": {
        "DATABASE_URL": "postgres://ghostcrab:ghostcrab@localhost:5432/ghostcrab"
      }
    }
  }
}
```

**Cursor** (Settings → MCP Servers → Add) :

```json
{
  "ghostcrab": {
    "command": "node",
    "args": ["/chemin/absolu/vers/ghostcrab-mcp/dist/index.js"],
    "env": {
      "DATABASE_URL": "postgres://ghostcrab:ghostcrab@localhost:5432/ghostcrab"
    }
  }
}
```

> **Règle DSN (SOP1, invariant #5) :** Le `DATABASE_URL` dans la config MCP client doit être **identique** à celui dans `.env` et à celui utilisé pour les migrations. Ne jamais utiliser des DSN différents entre l'agent d'ingestion et le serveur MCP — cela crée des états incohérents.

### A6.3 — Vérifier la connexion client

Après avoir redémarré le client MCP :
1. Ouvrir une nouvelle conversation
2. Demander à l'agent : "liste les outils ghostcrab disponibles"
3. Résultat attendu : liste de 24 outils `ghostcrab_*`

Si les outils ne sont pas visibles : vérifier le chemin absolu dans la config, relancer le client, vérifier que `dist/index.js` existe.

---

## A7 — Validation finale : ghostcrab_status

Depuis l'agent MCP connecté, appeler `ghostcrab_status` (sans arguments).

### Réponse "OK" — mode natif (extensions compilées)

```json
{
  "native_readiness": true,
  "backends": {
    "pg_facets": "ready",
    "pg_dgraph": "ready",
    "pg_pragma": "ready"
  },
  "capabilities": {
    "bm25_search": true,
    "graph_traversal": true,
    "projections": true
  }
}
```

### Réponse "OK" — mode fallback (SQL pur, sans extensions)

```json
{
  "native_readiness": false,
  "backends": {
    "pg_facets": "fallback",
    "pg_dgraph": "fallback",
    "pg_pragma": "fallback"
  },
  "capabilities": {
    "bm25_search": false,
    "graph_traversal": false,
    "projections": true
  }
}
```

Le mode fallback est acceptable pour démarrer. Les fonctionnalités avancées (BM25, traversal natif) ne seront pas disponibles, mais le reste du workflow Phase B et Phase C fonctionne.

### Réponse "FAIL" — action requise

| Champ en erreur | Cause | Correction |
|---|---|---|
| `database: "unreachable"` | PostgreSQL non accessible | Retourner à A3 |
| `migrations: "pending"` | Migrations non appliquées | Retourner à A4 |
| `server: "not_started"` | Serveur MCP non lancé | Vérifier config client A6 |
| Outil absent du client | Build ou config incorrect | Relancer `npm run build` et vérifier A6.2 |

---

## Commandes de récupération rapide

```bash
# Reset complet — reconstruire la base depuis zéro
make dev-db-reset

# Redémarrer uniquement le container postgres
make dev-restart

# Voir les logs postgres en temps réel
make dev-logs

# Vérifier l'état des services compose
make dev-ps

# Relancer le build TypeScript
npm run build

# Séquence bootstrap complète (DB + migrations)
make dev-bootstrap
```

---

## Passage Phase A → Phase B

Phase A est validée lorsque :

1. `docker inspect --format '{{.State.Health.Status}}' ghostcrab_postgres_native` → `healthy`
2. `npm run smoke:mcp` → aucune erreur critique
3. `ghostcrab_status` → pas d'erreur `database: unreachable` ou `migrations: pending`
4. Les outils `ghostcrab_*` sont visibles dans le client MCP (24 outils listés)

**Étape suivante :** charger **SOP1_ghostcrab_mcp.md** (architecture MCP et contrat DB) puis **SOP2_obsidian_ontologie.md** (modélisation ontologique depuis le vault).

---

*FIN SOP 4 — GhostCrab MCP Environment Bootstrap v1.0*
