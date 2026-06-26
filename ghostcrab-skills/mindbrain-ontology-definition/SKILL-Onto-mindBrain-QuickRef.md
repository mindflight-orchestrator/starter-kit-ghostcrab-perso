---
name: Onto-mindBrain-QuickRef
version: 1.0
description: Fiche de référence rapide pour l'agent — 5 actes, templates et règles de qualité
---

# OntoBrain — Référence rapide

## Les 5 actes en un coup d'œil

| Acte | Question | Définition | Couleur | Objectif |
|---|---|---|---|---|
| **NOMS** | "De quoi parle-t-on ?" | Les choses qui existent, qu'on peut nommer, compter, stocker | 🟡 Jaune | Nommer tous les objets du métier |
| **VERBES** | "Qu'est-ce qui se passe ?" | Les actions et flux qui relient deux choses | 🔴 Rouge | Identifier toutes les interactions |
| **QUALIFICATIFS** | "Comment le décrit-on ?" | Les caractéristiques qui décrivent l'état d'une chose | 🟢 Vert | Repérer les dimensions d'état |
| **CONDITIONS** | "Dans quelles circonstances ça change ?" | Les règles implicites qui déclenchent une action | 🟠 Orange | Anticiper les règles de transition |
| **RECHERCHE** | "Comment le retrouve-t-on ?" | Les facettes d'interrogation de la donnée | 🔵 Bleu | Définir les axes d'indexation |

## Triplet condition
SI [état + contexte] + [déclencheur] → ALORS [action / nouvel état]

## 6 questions de facette (par entité)
1. Par qui ?
2. Par quand ?
3. Par où ?
4. Par état ?
5. Par combien ?
6. Par type ?

## Canvas intermédiaire (4 colonnes)
| Qui / Quoi | Sait quoi sur lui | Est relié à | Peut faire / subir |
|---|---|---|---|

## Vérifications minimales
- Chaque Nom → min. 3 facettes
- Chaque Nom → min. 1 Verbe entrant et 1 Verbe sortant
- Chaque Verbe → 2 extrémités identifiées comme Noms
- Chaque entité principale → min. 1 Condition
- Les Qualificatifs de statut → tout le cycle de vie couvert
- Les facettes enum → toutes les valeurs listées

## Phrase de révélation
"Ce que vous venez de décrire s'appelle une ontologie."
