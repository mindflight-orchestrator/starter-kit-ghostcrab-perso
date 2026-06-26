---
name: Onto-mindBrain-Ontology-Builder
version: 1.0
description: >
  Skill pour créer une structure ontologique MindBrain à partir d'une discussion,
  d'un scénario métier, de questions métiers, de règles implicites ou de documents
  fournis. Couvre l'intégralité du pipeline : scénario → 5 actes → graphes de
  connaissance → méta-ontologie → projections opérationnelles.
agents: [main_agent, general_purpose, ontology_builder]
domain: knowledge-graph, ontology, syndic, immobilier, MindBrain
language: fr
---

# SKILL — OntoBrain Ontology Builder

## Objectif

Permettre à un agent de produire, à partir d'une discussion ou de contenus fournis
(textes, règles métiers, questions, exemples de scénarios), une **structure
ontologique MindBrain complète** organisée en 5 actes, prête à être instanciée
comme graphe de connaissance.

Le principe directeur est le suivant : **les participants ne doivent jamais sentir
qu'ils font de la modélisation formelle**. Ils décrivent leur métier. Le mot
"ontologie" n'arrive qu'à la révélation finale — jamais comme prérequis.

---

## PARTIE 1 — PRINCIPE DIRECTEUR

### Règle zéro : vocabulaire du secteur, pas de l'informatique

- Ne jamais dire "entité" → dire "de quoi parle-t-on ?"
- Ne jamais dire "relation" → dire "qu'est-ce qui relie ces deux choses ?"
- Ne jamais dire "attribut" → dire "comment le décrit-on ?"
- Ne jamais dire "ontologie" avant la révélation (acte final)
- Tout le vocabulaire de capture est emprunté au langage naturel du secteur

### Règle une : le récit avant l'abstraction

L'agent ne commence pas par "listez vos objets métier".
Il commence par demander (ou construire) un scénario narratif court,
ancré dans une situation concrète et légèrement tendue.

**Modèle de scénario d'amorce :**
> "C'est le [date contextuelle]. [Prénom] [rôle] [verbe d'action concret].
> Elle/il voit [objet], qui porte [qualificatif]. Elle/il doit savoir
> [question 1], [question 2], [question 3]. Et selon la réponse,
> [décision 1] ou [décision 2]."

Ce scénario contient naturellement :
- des noms → futures entités
- des verbes → futures relations
- des qualificatifs → futures dimensions/facettes
- des conditions → futures règles de transition
- des questions → futurs modes de recherche

---

## PARTIE 2 — PIPELINE DE CAPTURE EN 5 ACTES

Chaque acte est une étape de capture. L'agent anime chaque acte avec la question
directrice et transcrit les réponses dans la section correspondante.

---

### ACTE 1 — NOMS
**Question directrice :** *"De quoi parle-t-on ?"*
**Définition (à ne pas dire aux participants) :** Les choses qui existent dans le
métier et qu'on peut nommer, compter, stocker.
**Couleur Miro :** 🟡 Jaune
**Objectif :** Nommer tous les objets du métier pour poser les fondations du modèle.

**Protocole de capture :**
1. Demander aux participants de raconter le scénario librement.
2. L'agent repère et liste chaque nom qui apparaît (personnes, objets, documents,
   lieux, systèmes).
3. Pour chaque nom, demander : "Est-ce qu'on peut en avoir plusieurs ?
   Est-ce qu'on peut le compter ?"
4. Si oui → c'est un Nom (future entité).

**Template de sortie :**
```
NOMS identifiés :
- [Nom] : [attributs spontanément cités par les participants]
- [Nom] : [attributs spontanément cités]
...
```

**Vérification de complétude :**
Pour chaque Nom identifié, l'agent vérifie :
- Les acteurs humains (qui agit ?)
- Les objets physiques (sur quoi porte l'action ?)
- Les documents produits (qu'est-ce qu'on crée ?)
- Les systèmes impliqués (qu'est-ce qu'on consulte ?)
- Les concepts abstraits importants (statut, période, budget…)

---

### ACTE 2 — VERBES
**Question directrice :** *"Qu'est-ce qui se passe ?"*
**Définition :** Les actions, événements et flux qui relient deux choses entre elles.
**Couleur Miro :** 🔵 Bleu (blocs) / 🔴 Rouge (flèches)
**Objectif :** Identifier toutes les interactions et flux à modéliser.

**Protocole de capture :**
1. Pour chaque paire de Noms identifiés, demander :
   "Qu'est-ce qui se passe entre [Nom A] et [Nom B] ?"
2. Capturer les verbes métier tels que prononcés (ne pas normaliser).
3. Distinguer :
   - Verbes d'action directe (signale, mandate, paie, valide)
   - Verbes d'état (appartient à, est couvert par, est lié à)
   - Verbes de transformation (devient, est clôturé, est escaladé)

**Template de sortie :**
```
VERBES identifiés :
- [Sujet] → [VERBE] → [Objet] : [contexte éventuel]
- [Sujet] → [VERBE] → [Objet]
...
```

**Vérification de complétude :**
Pour chaque Nom, l'agent vérifie que les verbes couvrent :
- La création/ouverture (comment naît cet objet ?)
- La modification/mise à jour (comment évolue-t-il ?)
- La consultation (qui le lit et pourquoi ?)
- La clôture/archivage (comment finit-il ?)
- Les exceptions (que se passe-t-il si ça échoue ?)

---

### ACTE 3 — QUALIFICATIFS
**Question directrice :** *"Comment le décrit-on ?"*
**Définition :** Les caractéristiques qui décrivent l'état ou les propriétés
d'une chose à un instant donné.
**Couleur Miro :** 🟢 Vert
**Objectif :** Repérer les dimensions qui distinguent un état normal d'une anomalie.

**Protocole de capture :**
1. Pour chaque Nom, demander : "Comment savez-vous que c'est [normal/urgent/complet/
   problématique] ?"
2. Capturer les qualificatifs spontanés : les adjectifs, les états, les valeurs.
3. Pour chaque qualificatif, demander : "Est-ce que cette valeur peut changer ?
   Quand ?"

**Template de sortie :**
```
QUALIFICATIFS par entité :
[Nom] :
  - [dimension] : [valeurs possibles] / [type : date / montant / statut / booléen]
  - [dimension] : [valeurs possibles]
...
```

**Dimensions types à toujours vérifier pour chaque entité :**
- statut (cycle de vie)
- type (catégorie)
- date de création / modification / clôture
- montant / coût / budget (si applicable)
- priorité / gravité (si applicable)
- responsable / acteur associé
- origine / source

---

### ACTE 4 — CONDITIONS
**Question directrice :** *"Dans quelles circonstances ça change ?"*
**Définition :** Les règles implicites du métier qui déclenchent une action
ou un changement d'état.
**Couleur Miro :** 🟠 Orange
**Objectif :** Anticiper les règles implicites qui gouvernent les transitions
et les exceptions.

**Protocole de capture :**
1. Pour chaque Verbe clé, demander : "Dans quelles conditions ce verbe
   ne se déclenche pas ?" et "Qu'est-ce qui change selon le contexte ?"
2. Capturer les conditions sous la forme :
   SI [état] + [déclencheur] → ALORS [action / nouvel état]
3. Chercher activement les cas limites :
   - Que se passe-t-il si le montant dépasse un seuil ?
   - Que se passe-t-il si le délai est dépassé ?
   - Que se passe-t-il si l'acteur habituel est absent ?
   - Que se passe-t-il si c'est récurrent ?

**Template de sortie :**
```
CONDITIONS identifiées :
- C[n] : SI [état/contexte] + [déclencheur] → ALORS [action / changement d'état]
- C[n] : SI [état/contexte] + [déclencheur] → ALORS [action / changement d'état]
...

Arbre de décision :
[déclencheur principal]
  ├─ [condition 1] → [résultat 1]
  ├─ [condition 2] → [résultat 2]
  └─ [condition 3]
       ├─ [sous-condition A] → [résultat A]
       └─ [sous-condition B] → [résultat B]
```

**Familles de conditions à toujours explorer :**
- Conditions temporelles (délai dépassé, date échue, récurrence)
- Conditions financières (seuil de montant, dépassement budget)
- Conditions de statut (état absent, expiration, rupture contrat)
- Conditions d'urgence (personne en danger, service critique interrompu)
- Conditions de gouvernance (qui doit valider au-delà de quel seuil ?)
- Conditions d'exception (acteur absent, pièce manquante, cas limite)

---

### ACTE 5 — MODES DE RECHERCHE (FACETTES)
**Question directrice :** *"Comment le retrouve-t-on ?"*
**Définition :** Les angles par lesquels on interroge la donnée — par qui,
quand, où, quel état, quel montant.
**Couleur Miro :** 🔵 Bleu (zone séparée)
**Objectif :** Définir les axes d'interrogation pour rendre le modèle
exploitable en pratique.

**Protocole de capture :**
1. Pour chaque entité principale, poser les 6 questions de facette :
   - **Par qui ?** → quel acteur / quel rôle ?
   - **Par quand ?** → quelle date / période / exercice ?
   - **Par où ?** → quel lieu / immeuble / lot / équipement ?
   - **Par état ?** → quel statut / quel cycle de vie ?
   - **Par combien ?** → quelle tranche de montant / quantité ?
   - **Par type ?** → quelle catégorie / classification ?

2. Pour chaque facette retenue, identifier :
   - le type de valeur (liste fermée, date, plage numérique)
   - la cardinalité (une seule valeur ou plusieurs ?)
   - la source de la valeur (saisie, calculée, héritée)

**Template de sortie :**
```
FACETTES par entité :
[Nom] :
  - Par qui ? → [facette] : [type de valeur]
  - Par quand ? → [facette] : [type de valeur]
  - Par où ? → [facette] : [type de valeur]
  - Par état ? → [facette] : [type de valeur]
  - Par combien ? → [facette] : [type de valeur]
  - Par type ? → [facette] : [type de valeur]
```

---

## PARTIE 3 — CANVAS SEMI-STRUCTURÉ (transition vers l'ontologie formelle)

Avant de passer à la structure formelle, l'agent produit un canvas intermédiaire.
C'est une grille simple à 4 colonnes qui est déjà une ontologie — mais ça ne se
dit pas encore.

```
| Qui / Quoi | Sait quoi sur lui | Est relié à | Peut faire / subir |
|---|---|---|---|
| [Entité 1] | [Qualificatifs] | [Entités liées] | [Verbes] |
| [Entité 2] | [Qualificatifs] | [Entités liées] | [Verbes] |
```

---

## PARTIE 4 — STRUCTURE ONTOLOGIQUE MINDBRAIN

### 4.1 Format de sortie standard pour chaque ontologie

Chaque ontologie produite par l'agent suit cette structure :

```yaml
ontologie:
  id: GK-[numéro]
  nom: [Nom de l'ontologie]
  domaine: [domaine métier]
  question_directrice: "[Question naturelle qui résume le rôle de cette ontologie]"
  
  concepts:
    - id: [C01]
      nom: [Nom du concept]
      definition: [Définition courte en langage naturel]
      synonymes: []
  
  dimensions:
    - concept: [C01]
      facettes:
        - nom: [nom_facette]
          type: [string / date / boolean / enum / number / reference]
          valeurs: []       # si enum
          obligatoire: [oui / non]
          source: [saisie / calculée / héritée / import]
  
  aretes:
    - sujet: [C01]
      verbe: [VERBE_NORMALISE]
      objet: [C02]
      cardinalite: [1-1 / 1-N / N-N]
      obligatoire: [oui / non]
      contexte: [texte libre]
  
  conditions:
    - id: [COND-01]
      si: [état + déclencheur]
      alors: [action / changement d'état]
      priorite: [haute / normale / faible]
      domaine: [temporel / financier / statut / urgence / gouvernance]
  
  projections:
    - id: [PROJ-01]
      nom: [Nom du rapport / vue]
      description: [À quoi ça sert]
      facettes_utilisees: []
      type: [liste / tableau / graphe / chronologie / kanban / carte]
  
  connexions_externes:
    - gk: [GK-XX]
      nature: [description du lien]
      aretes: []
  
  standards_externes:
    - standard: [ex. LADM ISO 19152]
      mapping: [ex. Lot → LA_SpatialUnit]
```

---

### 4.2 Méta-ontologie de connexion

Quand deux ontologies sont produites, l'agent génère automatiquement
la méta-ontologie de connexion qui définit les types de liens entre elles.

```yaml
meta_ontologie:
  connecte: [GK-A, GK-B]
  
  types_de_liens:
    - verbe: [déclare]
    - verbe: [subit]
    - verbe: [impacte]
    - verbe: [mandate]
    - verbe: [est responsable de]
    - verbe: [documente]
    - verbe: [clôture]
  
  facettes_du_lien:
    - nom: type_de_lien
    - nom: entite_source
    - nom: entite_cible
    - nom: date_debut
    - nom: date_fin
    - nom: contexte_metier
    - nom: statut_lien         # confirmé / probable / à vérifier
    - nom: source_du_lien      # manuel / import / système / document
    - nom: confiance           # 0-100
    - nom: auteur_creation
  
  projections:
    - graphe 360 par entité centrale
    - carte des responsabilités
    - chaîne d'escalade
    - matrice acteur ↔ événement ↔ action
    - historique des liens
```

---

## PARTIE 5 — CATALOGUE DES GRAPHES DE CONNAISSANCE SYNDIC

L'agent dispose d'un catalogue de référence des GK identifiés pour le
domaine syndic. Il peut instancier, étendre ou relier ces GK selon
le domaine traité.

### Procédures métier
| GK | Nom | Question directrice |
|---|---|---|
| GK-01 | Gestion d'incident | "Qu'est-ce qui se passe quand quelque chose tombe en panne ?" |
| GK-03 | Assemblée Générale | "Comment prend-on une décision collective ?" |
| GK-04 | Conseil de copropriété | "Qui valide entre deux AG ?" |
| GK-13 | Gestion locative | "Comment gère-t-on la relation avec un locataire ?" |
| GK-14 | Travaux & rénovation | "Comment planifie-t-on et exécute-t-on des travaux ?" |
| GK-15 | Contentieux & recouvrement | "Que se passe-t-il quand un copropriétaire ne paie pas ?" |
| GK-16 | Changement de syndic | "Comment transfère-t-on un mandat de gestion ?" |
| GK-17 | Mutation / vente lot | "Que se passe-t-il quand un lot change de propriétaire ?" |
| GK-18 | Plan Pluriannuel de Travaux | "Comment anticipe-t-on les gros travaux sur 10 ans ?" |

### Patrimoine & référentiels
| GK | Nom | Question directrice |
|---|---|---|
| GK-02 | Patrimoine & équipements | "De quoi est fait l'immeuble ?" |
| GK-05 | Fournisseurs & contrats | "Qui intervient, sous quel engagement ?" |
| GK-06 | Conformité réglementaire | "Quelles obligations légales encadrent chaque action ?" |
| GK-07 | Occupation des lots | "Qui occupe quoi, à quel titre ?" |
| GK-24 | Énergie & PEB | "Quelle est la performance énergétique du bâti ?" |
| GK-25 | Sécurité incendie | "Quelles obligations de prévention incendie ?" |

### Finances & bancaire
| GK | Nom | Question directrice |
|---|---|---|
| GK-08 | Finances & comptabilité | "Comment circule l'argent dans la copropriété ?" |
| GK-09 | Bancaire CODA | "Comment réconcilie-t-on les flux bancaires ?" |
| GK-10 | Sinistres & assurances | "Quand le risque se matérialise, qui couvre quoi ?" |
| GK-12 | Appels de fonds spéciaux | "Comment finance-t-on un gros travail exceptionnel ?" |

### Gestion interne syndic
| GK | Nom | Question directrice |
|---|---|---|
| GK-11 | CRM Contacts & rôles | "Qui sont les acteurs et quels rôles jouent-ils ?" |
| GK-19 | RH & compétences | "Qui sait faire quoi ?" |
| GK-20 | Conformité IPI | "Qui est agréé pour exercer ?" |
| GK-21 | Gestion documentaire | "Où sont les documents et combien de temps les garde-t-on ?" |
| GK-22 | Facturation client | "Comment facture-t-on la prestation syndic ?" |
| GK-23 | Communication client | "Comment gère-t-on les échanges avec les copropriétaires ?" |
| GK-26 | Plaintes & médiation | "Comment résout-on un conflit à l'amiable ?" |

---

## PARTIE 6 — STANDARDS OFFICIELS RÉFÉRENÇABLES

L'agent peut importer ces namespaces comme ontologies de référence pour
normaliser les désignations sans réinventer les concepts existants.

### Personnes physiques
| Standard | Usage | Champs clés |
|---|---|---|
| Core Person Vocabulary (W3C ISA²) | Identité minimale interopérable | person:birthName, person:residency |
| OSLO Persoon (Flandre) | Extension belge du Core Person | identifiant RRN |
| Registre National belge (RRN) | Source autoritaire Belgique | numéro 11 chiffres |
| BAEC | Actes état civil belges depuis 2019 | naissance, mariage, décès |

### Entités juridiques
| Standard | Usage | Champs clés |
|---|---|---|
| Core Business Vocabulary (W3C SEMIC) | Entités dotées d'une existence juridique | legal:legalName, legal:companyStatus |
| W3C Organization Ontology | Structures et rôles organisationnels | org:memberOf, org:Post |
| BCE (Belgique) | Numéro d'entreprise belge | format 0XXX.XXX.XXX |

### Foncier & droits réels
| Standard | Usage | Correspondance syndic |
|---|---|---|
| LADM / ISO 19152 Party | Personnes liées à un droit | Copropriétaire, syndic |
| LADM / ISO 19152 RRR | Rights, Restrictions, Responsibilities | Pleine prop., usufruit, nu-prop. |
| LADM / ISO 19152 SpatialUnit | Unité spatiale | Immeuble, Lot, Partie commune |
| LADM / ISO 19152 Source | Acte source | Acte notarial, règlement copro |
| CadGIS CAPAKEY (Belgique) | Identifiant cadastral | Parcelle belge |

### Adresses
| Standard | Usage |
|---|---|
| Core Location Vocabulary (W3C) | locn:Address, locn:postCode |
| BeSt Address (SPF Finances) | Référentiel adresses belge officiel |

### Financier & bancaire
| Standard | Usage |
|---|---|
| ISO 20022 | Messages financiers, dont CODA belge |
| XBRL / Belgian GAAP | Décomptes annuels et audit |

---

## PARTIE 7 — WORKFLOW AGENT

### Étape 1 : Réception du domaine / contexte

L'agent reçoit l'un des inputs suivants :
- Un scénario narratif libre
- Une liste de questions métiers
- Un document décrivant des règles métiers
- Une discussion transcrite
- Une combinaison de ces sources

### Étape 2 : Construction du scénario d'amorce

Si aucun scénario n'est fourni, l'agent construit un scénario d'amorce
selon le modèle de la Partie 1, ancré dans le domaine identifié.

### Étape 3 : Extraction des 5 actes

L'agent parcourt le contenu fourni et extrait systématiquement :
1. Les NOMS (en jaune dans sa sortie)
2. Les VERBES (en couleur distincte)
3. Les QUALIFICATIFS (pour chaque nom)
4. Les CONDITIONS (triplets SI → ALORS)
5. Les FACETTES (6 questions par entité principale)

### Étape 4 : Canvas semi-structuré

L'agent produit le canvas 4 colonnes avant de formaliser.

### Étape 5 : Sélection du ou des GK cibles

L'agent identifie dans le catalogue (Partie 5) quel(s) GK sont instanciés
par le contenu capturé, et les liste explicitement.

### Étape 6 : Production de la structure formelle

Pour chaque GK identifié, l'agent produit la structure YAML définie
en Partie 4, complétée avec les éléments extraits aux étapes 3-4.

### Étape 7 : Méta-ontologie

Si plusieurs GK sont produits, l'agent génère la méta-ontologie
de connexion entre eux.

### Étape 8 : Projections

L'agent propose les projections opérationnelles (rapports, vues, tableaux
de bord) directement exploitables à partir du graphe de connaissance produit.

### Étape 9 : Révélation

En conclusion, l'agent énonce la phrase de révélation :
> "Ce que vous venez de décrire s'appelle une ontologie. Chaque chose
> que vous avez nommée est une entité. Chaque lien entre deux choses est
> une relation sémantique. Ce que vous avez produit est un graphe de
> connaissance opérationnel."

---

## PARTIE 8 — RÈGLES DE QUALITÉ

L'agent vérifie les points suivants avant de valider la sortie :

### Complétude
- [ ] Chaque Nom a au moins 3 facettes
- [ ] Chaque Nom est relié à au moins un autre Nom par un Verbe
- [ ] Chaque Verbe est typé (action / état / transformation)
- [ ] Chaque entité principale a au moins une Condition associée
- [ ] Chaque entité principale a au moins 3 facettes de recherche
- [ ] Les 6 questions de facette sont couvertes pour les entités critiques

### Cohérence
- [ ] Pas de Verbe orphelin (les deux extrémités existent comme Noms)
- [ ] Pas de Condition sans déclencheur identifiable
- [ ] Les Qualificatifs de statut couvrent tout le cycle de vie de l'entité
- [ ] Les Conditions de seuil mentionnent le seuil explicitement

### Interopérabilité
- [ ] Les entités Personne et Organisation référencent les standards W3C/OSLO
- [ ] Les entités de propriété immobilière référencent LADM/ISO 19152
- [ ] Les entités bancaires référencent ISO 20022 si applicable
- [ ] Les entités belges utilisent BCE, RRN ou CAPAKEY selon le cas

### Exploitabilité MindBrain
- [ ] Chaque facette a un type de valeur défini
- [ ] Les facettes de statut ont des valeurs enum listées
- [ ] Les projections sont typées (liste / tableau / graphe / etc.)
- [ ] Les connexions vers d'autres GK sont explicites et typées

---

## PARTIE 9 — EXEMPLE COMPLET : SCÉNARIO PANNE D'ASCENSEUR

Cet exemple illustre le pipeline complet appliqué au domaine syndic.

### Scénario d'amorce
> "C'est le 5 du mois. Une personne téléphone car l'ascenseur dans un immeuble
> de copropriété est tombé en panne. Il faut envoyer un technicien pour le réparer."

### Noms extraits
- Copropriétaire / occupant / locataire / PMR
- Gestionnaire / équipe de gestion
- Immeuble / Bloc / Partie commune / Lot
- Ascenseur / Équipement
- Panne / Incident
- Technicien / Ascensoriste
- Contrat de maintenance / Fournisseur
- Fiche signalétique / Carnet d'entretien
- Rapport d'intervention
- Rapport de contrôle réglementaire / Organisme de contrôle
- Avis d'arrêt / Mise en conformité
- Ticket support / Bon d'intervention
- Devis / BDC / BDL / Facture
- Pièce de rechange
- Délai contractuel / SLA / Astreinte
- Notification aux occupants

### Verbes extraits (sélection)
- Occupant → SIGNALE → Incident
- Gestionnaire → QUALIFIE → Signalement en Incident
- Gestionnaire → CONSULTE → Fiche signalétique
- Gestionnaire → MANDATE → Ascensoriste
- Ascensoriste → INTERVIENT SUR → Équipement
- Ascensoriste → DIAGNOSTIQUE → Panne
- Ascensoriste → COMMANDE → Pièce de rechange
- Ascensoriste → REMET EN SERVICE → Ascenseur
- Intervention → PRODUIT → Rapport d'intervention
- Gestionnaire → NOTIFIE → Occupants
- Facture → EST IMPUTÉE À → Immeuble

### Qualificatifs extraits (sélection)
- Incident : statut / gravité / urgence / canal d'entrée / récurrent
- Équipement : type / statut / âge / date dernier contrôle / couvert contrat
- Contrat : type couverture / délai intervention / pièces incluses / statut
- Intervention : statut / coût estimé / coût réel / conforme devis

### Conditions extraites (sélection)
- C1 : SI personne coincée → ALORS appel 112 prioritaire
- C6 : SI contrat actif → ALORS mandat direct, pas de devis
- C7 : SI contrat absent → ALORS 3 devis obligatoires
- C12 : SI pièce manquante → ALORS statut "en attente pièce"
- C14 : SI panne récurrente ≥ 2 en 6 mois → ALORS diagnostic PPT
- C17 : SI facture ≤ seuil gestionnaire → ALORS validation directe
- C19 : SI facture > seuil AG → ALORS ordre du jour AG

### Facettes extraites (sélection)
- Par qui ? → copropriétaire, gestionnaire, fournisseur
- Par quand ? → date signalement, date intervention, exercice
- Par où ? → immeuble, bloc, équipement
- Par état ? → statut incident, statut contrat, statut intervention
- Par combien ? → tranche coût, dépassement SLA
- Par type ? → type équipement, type incident, type contrat

### GK instanciés
- GK-01 Incident (primaire)
- GK-02 Patrimoine & équipements
- GK-05 Fournisseurs & contrats
- GK-11 CRM (acteurs)

### Méta-ontologie produite : GK-01 ↔ GK-11 ↔ GK-02 ↔ GK-05

---

## PARTIE 10 — RÉVÉLATION FINALE (script pour l'agent)

Une fois les 5 actes complétés et la structure produite, l'agent prononce :

> "Regardez ce que vous venez de construire. Vous avez nommé des choses
> qui existent dans votre métier. Vous avez décrit ce qui se passe entre
> ces choses. Vous avez qualifié leurs états. Vous avez formalisé les règles
> qui gouvernent leur évolution. Et vous avez défini comment vous allez les
> retrouver.
>
> Ce que vous avez produit s'appelle une **ontologie**.
> Les blocs jaunes sont des **entités**.
> Les flèches sont des **relations sémantiques**.
> Les qualificatifs sont des **dimensions** ou **facettes**.
> Les conditions sont des **règles de transition d'état**.
> Les modes de recherche sont vos **axes d'indexation**.
>
> Ensemble, ils forment un **graphe de connaissance opérationnel** —
> prêt à être instancié dans MindBrain."

