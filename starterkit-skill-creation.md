<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Tu vas me créer un skill qui va pouvoir être copié en format Markdown. L'objectif, c'est de créer une séquence de travail où l'utilisateur va décrire l'application qu'il souhaite créer. La première étape du skill, c'est d'analyser la demande et de poser des questions d'éclaircissement. L'objectif premier est de lister les différentes ontologies qui vont pouvoir modéliser l'objectif de l'utilisateur. Ça peut être autant une application par exemple un CRM maison qu'un modèle mental qu'un texte de loi etc. Tout ce qui peut être modélisé par ontologie. Ton travail est de découper la demande en fonction d'une approche First Principle. MECE er JTBD pour les différents rôles qui vont être impliqués. Autant agent IA qui vont devoir comprendre l'intention d'un utilisateur et donc explorer le domaine que des interactions avec des utilisateurs humains. Dans le cadre d'une application, tu as toujours deux groupes d'humains : tu as ceux qui vont créer et gérer la plateforme et qui ont des contraintes de monitoring et de scaling. Et tu as les humains qui vont utiliser l'interface pour leurs besoins propres. Exemple : une gestion de projet web.. La deuxième étape, une fois que la liste des ontologies est définie, c'est-à-dire développer dans une nouvelle discussion 'est de développer le modèle d'ontologie MindBrain. Tu commences par lister les dimensions avec les facettes : tu listes les graphes avec les arêtes sémantiques. Sans oublier les logiques de règles ou de contraintes.. Si il y a plusieurs domaines qui sont modélisés, il faut évidemment prévoir une méta-ontologie qui va permettre de connecter ces domaines. Une fois que les dimensions et les graphes sont modélisés, il faut travailler sur les projections . Reprends la structure des projections DDL avec les facts,... : tous les éléments dont on a besoin pour créer ces projections. Propose-moi donc une première version de ce skill.

Voici la première version du skill. Voici ce qui structure sa logique :

## Architecture du skill

**Étape 1 — Analyse et clarification**

Le skill commence par une reformulation canonique de la demande, puis applique systématiquement trois grilles en parallèle :

- **First Principles** : décompose jusqu'aux entités et relations irréductibles
- **MECE** : chaque domaine ontologique est mutuellement exclusif et collectivement exhaustif
- **JTBD par acteur** : opérateurs, utilisateurs humains, et agents IA sont traités comme trois groupes distincts avec des besoins non superposables

Les questions d'éclaircissement sont volontairement limitées (3–5 max) et chacune indique son **impact structurel** sur le modèle — pas de questions cosmétiques.

**Étape 2 — Modélisation MindBrain**

La séquence suit un ordre de dépendance logique :

1. **Dimensions + Facettes** → le vocabulaire du domaine
2. **Graphes + Arêtes sémantiques** → les relations typées (composition, référence, inférence, temporelle)
3. **Règles et contraintes** → intégrité, dérivation, transitions d'état
4. **Méta-ontologie** → uniquement si plusieurs domaines, pour les connecter sans créer de couplage fort
5. **Projections DDL** → fact tables, dim tables, vues matérialisées, index, règles `pg_facets`

## Points à ajuster dans une prochaine itération

- **Format des arêtes d'inférence** : le skill distingue les arêtes stockées des inférées, mais tu voudras peut-être préciser la syntaxe `pg_pragma` pour les contraintes croisées
- **Granularité des JTBD agents IA** : si tu as des patterns MCP spécifiques (ex : agent de navigation vs agent de validation), on peut ajouter une grille dédiée
- **Projections pg_dgraph** : les vues de traversée de graphe ne sont pas encore formalisées — à ajouter en 2.6 si nécessaire

Dis-moi ce que tu veux amender avant de le finaliser.

---

# Tu dois imaginer que le skill va être uploadé dans n'importe quel chat LLM, que ce soit ChatGPT, Claude AI, Kimi ou même toi Perplexity. Il faut donc pouvoir expliquer l'approche mindBrain De façon générique, il ne faut aucune mention au moteurrs derrière. Exemple :pg_pragma, etc. « Le modèle LLM qui sera utilisé doit juste comprendre les concepts et la mécanique pour les différents étages qu'il faut utiliser. »éRéécris le skillen tenant compte de cette perspective. » idem dans la sortie du Skill pas besoin de générer code SQL ou autre. on reste en markdown sur une analyse méta.

Voici la v2, entièrement réécrite. Les changements substantiels par rapport à la v1 :

## Ce qui a changé

**Neutralité technologique totale** — Zéro mention à PostgreSQL, `pg_facets`, `pg_pragma`, `pg_dgraph` ou SQL. Le skill est utilisable tel quel dans ChatGPT, Claude, Kimi, Gemini ou n'importe quel autre LLM sans adaptation.

**Sorties en Markdown méta uniquement** — Plus de blocs de code SQL. Les projections sont maintenant décrites comme des structures analytiques en tableaux Markdown : faits mesurables, dimensions de navigation, facettes actives, indicateurs dérivés. Le LLM comprend la mécanique sans avoir besoin de connaître l'implémentation cible.

**Le cadre MindBrain expliqué en concepts** — Les trois couches (Modèle sémantique → Graphe → Projections) sont introduites en début de skill de façon générique. N'importe quel LLM saisit la logique de construction sans référence à un moteur spécifique.

**Les types d'arêtes restent** — La distinction composition / référence / inférence / temporelle est un concept sémantique universel, pas une spécificité moteur. Elle a été conservée car elle est centrale à la qualité du modèle.

**L'exemple reste concret** — Il illustre la mécanique sans aller jusqu'à la modélisation complète, ce qui garde le skill lisible sans être trop long.

