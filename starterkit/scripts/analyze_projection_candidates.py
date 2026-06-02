#!/usr/bin/env python3
"""Extract and score projection candidates from ontology notes.

This is an upstream modeling helper: before writing projections to GhostCrab,
it reads source ontology notes, extracts "Projections / rapports types" tables,
and prepares a reviewable candidate list for the user.

It can also apply deterministic analysis lenses from a prompt, for example:

  --prompt "utilise patterns Blind Spot pour un manager operations, avec JTBD"

The script remains read-only. It does not call an LLM and does not write
projections to GhostCrab.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB = "data/ghostcrab.sqlite"
DEFAULT_POSTGRES_DSN = "postgres://ghostcrab:ghostcrab@127.0.0.1:5434/ghostcrab"
DEFAULT_SOURCE_DIR = "."
WORKSPACE_ID = "default"


@dataclass(frozen=True)
class AnalysisPattern:
    lens: str
    name: str
    label: str
    business_question: str
    description: str
    suggested_proj_type: str
    retrieval_jobs: list[str]
    kpi_hints: list[str]
    required_schemas: list[str]
    required_facets: list[str]
    required_edges: list[str]
    human_jobs: list[str]
    ai_agent_jobs: list[str]
    impact_summary: str
    pattern_tags: list[str]
    confidence: float = 0.8


@dataclass
class ProjectionCandidate:
    name: str
    label: str
    ontology: str
    description: str
    source_file: str
    source_section: str
    expected_scope: str
    suggested_proj_type: str
    retrieval_jobs: list[str]
    kpi_hints: list[str]
    data_dependencies: list[str]
    materialization_status: str
    recommendation: str
    business_question: str = ""
    origin: str = "source_table"
    lens: str = ""
    role: str = ""
    required_schemas: list[str] | None = None
    required_facets: list[str] | None = None
    required_edges: list[str] | None = None
    human_jobs: list[str] | None = None
    ai_agent_jobs: list[str] | None = None
    impact_summary: str = ""
    pattern_tags: list[str] | None = None
    confidence: float = 1.0

    def __post_init__(self) -> None:
        self.required_schemas = self.required_schemas or []
        self.required_facets = self.required_facets or []
        self.required_edges = self.required_edges or []
        self.human_jobs = self.human_jobs or []
        self.ai_agent_jobs = self.ai_agent_jobs or []
        self.pattern_tags = self.pattern_tags or []


LLM_FINDINGS_SCHEMA = {
    "candidates": [
        {
            "name": "projection_slug",
            "label": "Human readable projection label",
            "business_question": "Question a manager or agent needs to answer",
            "description": "Why this projection matters",
            "suggested_proj_type": "FACT|STEP|CONSTRAINT|NOTE|GOAL",
            "retrieval_jobs": ["summary", "monitor", "graph_traversal"],
            "required_schemas": ["chantier:tache"],
            "required_facets": ["owner", "risk_status"],
            "required_edges": ["bloque", "menace_jalon"],
            "human_jobs": ["decide", "arbitrate"],
            "ai_agent_jobs": ["detect", "prioritize"],
            "impact_summary": "Model changes implied by this candidate",
            "pattern_tags": ["blind_spot", "jtbd"],
            "confidence": 0.8,
        }
    ],
    "notes": ["Optional model-level observations"],
}


BLIND_SPOT_MANAGER_PATTERNS: list[AnalysisPattern] = [
    AnalysisPattern(
        lens="blind_spot_manager",
        name="verification_reception_preuve",
        label="Termine mais non verifie, receptionne ou documente",
        business_question="Qu'est-ce qui est marque termine mais pas encore verifie, receptionne ou documente ?",
        description="Detecte les faux termines: statut operationnel positif sans preuve qualite, reception ou documentation.",
        suggested_proj_type="CONSTRAINT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["unverified_done_count", "missing_evidence_count"],
        required_schemas=["chantier:tache", "chantier:jalon"],
        required_facets=["status", "quality_status", "verification_status", "evidence_available", "handover_status"],
        required_edges=["valide_par", "confirme", "contredit"],
        human_jobs=["decider si le travail peut etre considere comme fini", "prioriser les controles manquants"],
        ai_agent_jobs=["detecter les statuts incoherents", "rapprocher preuve, tache et reception"],
        impact_summary="Ajoute une projection de fiabilite du statut et remonte des facettes de preuve/qualite.",
        pattern_tags=["status_reliability", "quality_gate", "evidence"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="finance_supply_reconciliation",
        label="Facture payee mais materiel non livre, pose ou accepte",
        business_question="Quelles factures sont payees alors que le materiel n'est pas livre, pose ou accepte ?",
        description="Repere les ecarts entre paiement ERP, livraison, installation terrain et acceptation.",
        suggested_proj_type="FACT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["paid_not_delivered_count", "paid_not_accepted_amount"],
        required_schemas=["erp:invoice", "erp:payment", "erp:delivery", "chantier:commande", "chantier:tache"],
        required_facets=["paid_status", "delivery_status", "received_quantity", "installed_quantity", "accepted_quantity", "reconciliation_status"],
        required_edges=["facture_commande", "paiement_facture", "erp_delivery_fulfills", "approvisionne_tache", "contredit"],
        human_jobs=["eviter de payer sans preuve de valeur terrain", "arbitrer fournisseur ou finance"],
        ai_agent_jobs=["reconcilier commande, facture, paiement, livraison et pose", "signaler contradictions inter-systemes"],
        impact_summary="Force la modelisation des quantites livre/pose/accepte et des liens finance-supply-tache.",
        pattern_tags=["reconciliation", "finance_supply", "data_trust"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="buffer_absorption",
        label="Retards absorbables versus buffer consomme",
        business_question="Quels retards sont absorbables, et lesquels consomment tout le buffer ?",
        description="Distingue un retard visible d'un retard vraiment critique pour le jalon.",
        suggested_proj_type="FACT",
        retrieval_jobs=["summary", "monitor", "graph_traversal"],
        kpi_hints=["buffer_days_remaining", "critical_delay_count"],
        required_schemas=["chantier:tache", "chantier:jalon", "chantier:commande", "erp:delivery"],
        required_facets=["delay_days", "buffer_days", "slack_days", "risk_status", "forecast_end", "impact_days"],
        required_edges=["depend_de", "menace_jalon", "protege_jalon", "bloque"],
        human_jobs=["savoir ou intervenir avant que le planning casse", "proteger les jalons critiques"],
        ai_agent_jobs=["calculer propagation retard-buffer-jalon", "separer alerte bruit et risque reel"],
        impact_summary="Ajoute slack/buffer/forecast comme dimensions de pilotage, pas seulement statut et retard.",
        pattern_tags=["critical_path", "buffer", "forecast_trust"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="patterns_recurrents",
        label="Incident isole ou pattern recurrent",
        business_question="Est-ce un incident isole ou un pattern recurrent par fournisseur, equipe, zone ou phase ?",
        description="Cherche les repetitions faibles qui signalent un probleme systemique.",
        suggested_proj_type="FACT",
        retrieval_jobs=["aggregate", "graph_traversal"],
        kpi_hints=["repeat_count", "root_cause_count"],
        required_schemas=["chantier:alerte", "chantier:fournisseur", "chantier:equipe", "chantier:zone"],
        required_facets=["root_cause", "pattern_type", "repeat_count", "risk_status"],
        required_edges=["combine_avec", "meme_cause_que", "impacte"],
        human_jobs=["distinguer incident ponctuel et defaut de systeme", "changer le plan d'action a la bonne echelle"],
        ai_agent_jobs=["clusteriser alertes par cause", "detecter recurrence fournisseur/equipe/zone"],
        impact_summary="Demande des facettes de cause racine et des aretes de regroupement entre signaux.",
        pattern_tags=["recurrence", "root_cause", "systems_thinking"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="ownership_alertes",
        label="Alertes et decisions sans responsable clair",
        business_question="Quelles alertes ou decisions n'ont pas de responsable clair ?",
        description="Identifie les risques qui restent ouverts parce que personne n'est vraiment accountable.",
        suggested_proj_type="STEP",
        retrieval_jobs=["monitor", "list"],
        kpi_hints=["unowned_risk_count", "overdue_action_count"],
        required_schemas=["chantier:alerte", "crm:decision", "crm:action"],
        required_facets=["owner", "accountable_role", "risk_status", "due_date", "action_status"],
        required_edges=["escalade_vers", "bloque"],
        human_jobs=["clarifier qui decide ou agit", "eviter que les sujets restent orphelins"],
        ai_agent_jobs=["detecter owner manquant ou echeance depassee", "proposer escalation"],
        impact_summary="Ajoute owner/accountable_role/due_date/action_status comme dimensions obligatoires du pilotage.",
        pattern_tags=["accountability", "escalation", "daily_attention"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="decisions_client_latentes",
        label="Decisions client qui bloquent indirectement",
        business_question="Quelles decisions attendent trop longtemps et bloquent indirectement le planning ?",
        description="Rend visibles les blocages CRM avant qu'ils apparaissent comme retard chantier.",
        suggested_proj_type="CONSTRAINT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["decision_age_days", "blocked_task_count"],
        required_schemas=["crm:decision", "crm:change_request", "chantier:tache", "chantier:jalon"],
        required_facets=["status", "due_date", "blocking", "contractual_impact", "owner"],
        required_edges=["crm_decision_for", "crm_change_request_affects", "bloque", "menace_jalon", "escalade_vers"],
        human_jobs=["relancer ou arbitrer une decision client", "mesurer l'impact planning d'un choix en attente"],
        ai_agent_jobs=["relier decision CRM aux taches menacees", "prioriser les relances par impact"],
        impact_summary="Connecte CRM et chantier par des aretes de blocage et d'impact contractuel.",
        pattern_tags=["crm_blocker", "latent_risk", "client_decision"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="remplacement_capacite_qualite",
        label="Equipe remplacante sans risque qualite",
        business_question="Si l'equipe prevue est absente, quelle equipe peut remplacer sans risque qualite ?",
        description="Ne teste pas seulement la disponibilite, mais aussi les competences et certifications.",
        suggested_proj_type="CONSTRAINT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["capacity_delta_pct", "qualified_replacement_count"],
        required_schemas=["hr:worker", "hr:absence", "chantier:equipe", "chantier:tache"],
        required_facets=["availability_pct", "capacity_delta_pct", "skills", "certifications", "replacement_team_id", "quality_status"],
        required_edges=["hr_absence_affects", "membre_de", "assigne_a", "peut_remplacer"],
        human_jobs=["choisir un remplacement viable", "eviter une solution qui degrade la qualite"],
        ai_agent_jobs=["matcher competences/certifications/taches", "simuler impact capacite"],
        impact_summary="Etend HR vers skills, certifications, capacite et aretes de remplacement.",
        pattern_tags=["capacity", "skills", "replacement"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="readiness_zone",
        label="Zone vraiment prete pour prochaine intervention",
        business_question="Une zone est-elle vraiment prete pour la prochaine intervention ?",
        description="Croise acces, preconditions, conflits BIM, materiaux et taches predecessrices.",
        suggested_proj_type="CONSTRAINT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["ready_zone_count", "blocked_zone_count"],
        required_schemas=["chantier:zone", "chantier:tache", "chantier:commande", "bim:clash", "bim:requirement"],
        required_facets=["readiness_status", "preconditions_met", "open_clashes_count", "access_status", "delivery_status"],
        required_edges=["affecte_zone", "necessite_materiau", "approvisionne_tache", "bim_clash_affects_room", "valide_par"],
        human_jobs=["autoriser la prochaine intervention", "eviter mobilisation inutile"],
        ai_agent_jobs=["verifier readiness multi-sources", "expliquer pourquoi une zone n'est pas prete"],
        impact_summary="Impose une projection readiness et des liens zone-tache-materiau-BIM.",
        pattern_tags=["readiness", "zone", "bim_quality"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="incoherences_inter_systemes",
        label="Incoherences ERP BIM HR CRM chantier",
        business_question="Quelles donnees se contredisent entre ERP, BIM, HR, CRM et chantier ?",
        description="Surveille la confiance dans les donnees qui alimentent les decisions.",
        suggested_proj_type="CONSTRAINT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["reconciliation_issue_count", "stale_source_count"],
        required_schemas=["erp:delivery", "hr:worker", "bim:clash", "crm:decision", "chantier:commande"],
        required_facets=["source_system", "last_sync_at", "source_status", "canonical_status", "reconciliation_status", "confidence"],
        required_edges=["maps_to", "sourced_from", "contredit", "confirme"],
        human_jobs=["savoir quelles donnees ne pas croire aveuglement", "declencher correction source"],
        ai_agent_jobs=["detecter contradictions et fraicheur source", "expliquer confiance par source"],
        impact_summary="Remonte les facettes de reconciliation et les aretes confirme/contredit.",
        pattern_tags=["data_quality", "multi_system", "trust"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="fiabilite_prevision",
        label="Confiance dans la date previsionnelle",
        business_question="Quelle confiance a-t-on dans la date previsionnelle actuelle ?",
        description="Transforme une date forecast en jugement de fiabilite base sur preuves, buffer et risques.",
        suggested_proj_type="FACT",
        retrieval_jobs=["summary", "aggregate", "graph_traversal"],
        kpi_hints=["forecast_confidence", "low_confidence_milestone_count"],
        required_schemas=["chantier:tache", "chantier:jalon", "chantier:alerte", "erp:delivery"],
        required_facets=["forecast_confidence", "slack_days", "buffer_days", "risk_status", "last_sync_at"],
        required_edges=["depend_de", "menace_jalon", "confirme", "mitige"],
        human_jobs=["savoir si la date annoncee est defendable", "preparer communication client/interne"],
        ai_agent_jobs=["combiner signaux de risque en confiance forecast", "justifier la confiance par evidence"],
        impact_summary="Ajoute la fiabilite comme projection, au lieu d'afficher seulement la date.",
        pattern_tags=["forecast", "confidence", "planning"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="risques_combines",
        label="Petits risques qui deviennent critiques ensemble",
        business_question="Quels petits risques deviennent critiques ensemble ?",
        description="Repere les combinaisons de signaux individuellement faibles mais collectivement critiques.",
        suggested_proj_type="CONSTRAINT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["combined_risk_score", "risk_cluster_count"],
        required_schemas=["chantier:alerte", "chantier:tache", "chantier:jalon"],
        required_facets=["risk_level", "risk_status", "root_cause", "impact_days", "mitigation_status"],
        required_edges=["combine_avec", "menace_jalon", "bloque", "impacte"],
        human_jobs=["voir les effets composes avant crise", "prioriser mitigation transverse"],
        ai_agent_jobs=["former clusters de risques", "calculer criticite composee"],
        impact_summary="Necessite aretes de combinaison et facettes d'impact pour eviter le pilotage silo.",
        pattern_tags=["combined_risk", "blind_spot", "manager_attention"],
    ),
    AnalysisPattern(
        lens="blind_spot_manager",
        name="manager_attention_today",
        label="Top actions manager du jour",
        business_question="Quelles 3 a 5 actions doivent remonter au manager aujourd'hui ?",
        description="Resume les arbitrages et actions qui changent vraiment le resultat de la journee.",
        suggested_proj_type="STEP",
        retrieval_jobs=["summary", "monitor"],
        kpi_hints=["top_action_count", "overdue_critical_count"],
        required_schemas=["chantier:alerte", "chantier:tache", "chantier:jalon", "crm:action"],
        required_facets=["owner", "due_date", "severity", "risk_status", "action_status"],
        required_edges=["bloque", "menace_jalon", "escalade_vers", "mitige"],
        human_jobs=["savoir quoi traiter aujourd'hui", "reduire charge cognitive du pilotage"],
        ai_agent_jobs=["prioriser par impact, urgence et responsabilite", "generer un brief manager actionnable"],
        impact_summary="Cree une projection d'attention quotidienne qui consomme les autres signaux manager.",
        pattern_tags=["attention", "daily_brief", "prioritization"],
    ),
]


JTBD_HUMAN_PATTERNS: list[AnalysisPattern] = [
    AnalysisPattern(
        lens="jtbd_human",
        name="manager_decide_arbitrate",
        label="JTBD manager: arbitrer avec preuves",
        business_question="Quand plusieurs signaux se contredisent, quelle decision puis-je prendre avec suffisamment de preuves ?",
        description="Vue d'arbitrage humain: preuves, confiance, responsabilite et impact business.",
        suggested_proj_type="STEP",
        retrieval_jobs=["summary", "monitor", "graph_traversal"],
        kpi_hints=["decision_confidence", "evidence_gap_count"],
        required_schemas=["chantier:alerte", "chantier:tache", "crm:decision"],
        required_facets=["confidence", "evidence_available", "owner", "impact_days", "impact_cost_eur"],
        required_edges=["confirme", "contredit", "escalade_vers", "bloque"],
        human_jobs=["decider", "arbitrer", "expliquer la decision"],
        ai_agent_jobs=["compiler preuves", "montrer contradictions", "proposer options"],
        impact_summary="Ajoute une projection d'aide a la decision, centree sur preuve et confiance.",
        pattern_tags=["jtbd", "human_manager", "decision"],
    ),
    AnalysisPattern(
        lens="jtbd_human",
        name="chef_chantier_coordinate",
        label="JTBD chef chantier: coordonner la prochaine intervention",
        business_question="Que faut-il coordonner maintenant pour que la prochaine intervention se passe sans reprise ni attente ?",
        description="Vue terrain: readiness, coactivite, ressources, materiaux et preconditions.",
        suggested_proj_type="STEP",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["ready_next_work_count", "blocked_next_work_count"],
        required_schemas=["chantier:zone", "chantier:tache", "chantier:equipe", "chantier:commande"],
        required_facets=["readiness_status", "access_status", "preconditions_met", "availability_pct", "delivery_status"],
        required_edges=["affecte_zone", "assigne_a", "necessite_materiau", "approvisionne_tache"],
        human_jobs=["coordonner", "securiser l'intervention", "eviter attente terrain"],
        ai_agent_jobs=["verifier preconditions", "detecter conflits ressources-zone-materiaux"],
        impact_summary="Complete les projections manager avec une vue execution terrain.",
        pattern_tags=["jtbd", "site_supervisor", "coordination"],
    ),
]


JTBD_AI_PATTERNS: list[AnalysisPattern] = [
    AnalysisPattern(
        lens="jtbd_ai",
        name="agent_watchtower_prioritize",
        label="JTBD agent IA: tour de controle priorisee",
        business_question="Quels signaux dois-je surveiller, expliquer et remonter sans saturer le manager ?",
        description="Role agent IA de veille: filtrage, explication, priorisation, escalation.",
        suggested_proj_type="STEP",
        retrieval_jobs=["monitor", "summary"],
        kpi_hints=["signal_to_noise_ratio", "escalated_signal_count"],
        required_schemas=["chantier:alerte", "chantier:tache", "chantier:jalon"],
        required_facets=["severity", "risk_status", "confidence", "due_date", "owner"],
        required_edges=["menace_jalon", "escalade_vers", "confirme", "contredit"],
        human_jobs=["recevoir uniquement les sujets qui meritent attention"],
        ai_agent_jobs=["surveiller", "prioriser", "expliquer", "escalader"],
        impact_summary="Formalise une projection consommee par agent IA avant synthese humaine.",
        pattern_tags=["jtbd", "ai_agent", "watchtower"],
    ),
    AnalysisPattern(
        lens="jtbd_ai",
        name="agent_reconciliation_detective",
        label="JTBD agent IA: detective de reconciliation",
        business_question="Quelles incoherences dois-je investiguer avant qu'elles deviennent une mauvaise decision ?",
        description="Role agent IA de qualite de donnees: rapprochement cross-systemes et detection de contradictions.",
        suggested_proj_type="CONSTRAINT",
        retrieval_jobs=["monitor", "graph_traversal"],
        kpi_hints=["reconciliation_issue_count", "stale_data_count"],
        required_schemas=["erp:delivery", "hr:worker", "bim:clash", "crm:decision", "chantier:commande"],
        required_facets=["last_sync_at", "source_status", "canonical_status", "reconciliation_status", "confidence"],
        required_edges=["maps_to", "sourced_from", "contredit", "confirme"],
        human_jobs=["etre alerte quand la donnee n'est pas fiable"],
        ai_agent_jobs=["rapprocher", "verifier", "investiguer", "documenter"],
        impact_summary="Ajoute une projection agent specialisee data quality, reutilisable par les vues manager.",
        pattern_tags=["jtbd", "ai_agent", "reconciliation"],
    ),
]


LENS_PATTERNS = {
    "blind_spot_manager": BLIND_SPOT_MANAGER_PATTERNS,
    "jtbd_human": JTBD_HUMAN_PATTERNS,
    "jtbd_ai": JTBD_AI_PATTERNS,
}


def slugify(value: str) -> str:
    value = value.lower()
    replacements = {
        "é": "e",
        "è": "e",
        "ê": "e",
        "à": "a",
        "ç": "c",
        "ù": "u",
        "ô": "o",
        "î": "i",
        "ï": "i",
        "’": "'",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    return re.sub(r"_+", "_", value)


def ontology_from_filename(path: Path) -> str:
    name = path.stem.lower()
    if "production" in name:
        return "production"
    if "comptabilite" in name:
        return "comptabilite"
    if "decisionnel" in name:
        return "decisionnel"
    if "administrative" in name:
        return "administrative"
    return slugify(path.stem)


def extract_projection_section(markdown: str) -> str:
    match = re.search(r"^## Projections / rapports types\s*$", markdown, re.M)
    if not match:
        return ""
    start = match.end()
    next_section = re.search(r"^##\s+", markdown[start:], re.M)
    end = start + next_section.start() if next_section else len(markdown)
    return markdown[start:end]


def parse_markdown_table(section: str) -> list[tuple[str, str]]:
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2 or cells[0].lower() in {"projection", "rapport"}:
            continue
        rows.append((cells[0], cells[1]))
    return rows


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read projection YAML files") from exc
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML file must contain an object: {path}")
    return payload


def infer_retrieval_jobs(label: str, description: str) -> list[str]:
    text = f"{label} {description}".lower()
    jobs = []
    if any(word in text for word in ["liste", "annuaire", "calendrier", "historique"]):
        jobs.append("list")
    if any(word in text for word in ["suivi", "en cours", "retard", "alerte", "echeance", "échéance"]):
        jobs.append("monitor")
    if any(word in text for word in ["fiche", "vue complète", "vue complete", "situation"]):
        jobs.append("summary")
    if any(word in text for word in ["répartition", "repartition", "comparaison", "par ", "avec nombre"]):
        jobs.append("aggregate")
    if any(word in text for word in ["chaine", "chaîne", "rôles", "roles", "multi", "impact"]):
        jobs.append("graph_traversal")
    return jobs or ["summary"]


def infer_kpis(label: str, description: str) -> list[str]:
    text = f"{label} {description}".lower()
    kpis = []
    if "retard" in text:
        kpis.append("late_count")
    if "échéance" in text or "echeance" in text:
        kpis.append("due_30_60_90")
    if "montant" in text or "€" in text or "budget" in text or "fonds" in text:
        kpis.append("amount_total")
    if "statut" in text or "en cours" in text:
        kpis.append("count_by_status")
    if "par copropriété" in text or "copropriété" in text:
        kpis.append("count_by_copropriete")
    return kpis


def infer_dependencies(label: str, description: str) -> list[str]:
    text = f"{label} {description}".lower()
    mapping = {
        "copropriete": "production:copropriete",
        "copropriété": "production:copropriete",
        "personne": "production:personne",
        "équipe": "production:equipe_gestion",
        "equipe": "production:equipe_gestion",
        "lot": "administrative:lot",
        "compte": "production:compte_coproprietaire",
        "mandat": "administrative:mandat_gestion",
        "mutation": "administrative:demande_information/transfert_propriete_entrant/cloture_sortant",
        "occupation": "administrative:occupation",
        "appel": "comptabilite:appel_fonds",
        "fonds": "comptabilite:appel_fonds",
        "facture": "comptabilite:facture_fournisseur",
        "budget": "comptabilite:budget",
        "vérification": "comptabilite:verification_comptes",
        "verification": "comptabilite:verification_comptes",
        "ag": "decisionnel:assemblee_generale",
        "ordre du jour": "decisionnel:point_ordre_jour",
        "décision": "decisionnel:decision",
        "decision": "decisionnel:decision",
        "pv": "decisionnel:proces_verbal",
        "chantier": "chantier:tache",
        "tache": "chantier:tache",
        "tâche": "chantier:tache",
        "jalon": "chantier:jalon",
        "livraison": "erp:delivery",
        "ouvrier": "hr:worker",
        "absence": "hr:absence",
        "bim": "bim:clash",
        "client": "crm:decision",
        "commande": "chantier:commande",
    }
    deps = [target for key, target in mapping.items() if key in text]
    return sorted(set(deps))


def suggested_type(jobs: list[str]) -> str:
    if "monitor" in jobs:
        return "STEP"
    if "aggregate" in jobs or "summary" in jobs:
        return "FACT"
    return "NOTE"


def materialized_scopes_sqlite(db_path: Path, workspace_id: str) -> set[str]:
    if not db_path.exists():
        return set()
    with sqlite3.connect(db_path) as conn:
        return {
            row[0]
            for row in conn.execute(
                "SELECT scope FROM projections WHERE scope = ? OR scope LIKE ?",
                (workspace_id, f"{workspace_id}:%"),
            )
            if row[0]
        }


def materialized_scopes_postgres(postgres_dsn: str, workspace_id: str) -> set[str]:
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2 is required for --db-kind postgres or --postgres-dsn") from exc

    with psycopg2.connect(postgres_dsn, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE (table_schema, table_name) IN (
                    ('mb_pragma', 'projections'),
                    ('public', 'projections')
                )
                """
            )
            tables = {(schema, table) for schema, table in cur.fetchall()}
            if ("mb_pragma", "projections") in tables:
                cur.execute(
                    """
                    SELECT scope
                    FROM mb_pragma.projections
                    WHERE scope = %s OR scope LIKE %s
                    """,
                    (workspace_id, f"{workspace_id}:%"),
                )
            elif ("public", "projections") in tables:
                cur.execute(
                    """
                    SELECT scope
                    FROM public.projections
                    WHERE scope = %s OR scope LIKE %s
                    """,
                    (workspace_id, f"{workspace_id}:%"),
                )
            else:
                return set()
            return {row[0] for row in cur.fetchall() if row[0]}


def materialized_scopes(
    db_path: Path,
    workspace_id: str,
    db_kind: str = "auto",
    postgres_dsn: str | None = None,
) -> set[str]:
    if db_kind == "none":
        return set()
    if db_kind == "postgres":
        return materialized_scopes_postgres(postgres_dsn or DEFAULT_POSTGRES_DSN, workspace_id)
    if db_kind == "sqlite":
        return materialized_scopes_sqlite(db_path, workspace_id)
    if postgres_dsn:
        try:
            scopes = materialized_scopes_postgres(postgres_dsn, workspace_id)
            if scopes:
                return scopes
        except Exception:
            pass
    return materialized_scopes_sqlite(db_path, workspace_id)


def normalize_lens(value: str) -> str:
    value = slugify(value.replace("-", "_"))
    aliases = {
        "blind_spot": "blind_spot_manager",
        "blindspot": "blind_spot_manager",
        "manager_blind_spot": "blind_spot_manager",
        "jtbd": "jtbd_human",
        "human_jtbd": "jtbd_human",
        "ai_jtbd": "jtbd_ai",
        "agent_jtbd": "jtbd_ai",
    }
    return aliases.get(value, value)


def lenses_from_prompt(prompt: str) -> list[str]:
    text = prompt.lower()
    lenses: list[str] = []
    if "blind spot" in text or "blindspot" in text or "angle mort" in text:
        lenses.append("blind_spot_manager")
    if "jtbd" in text or "job to be done" in text or "jobs to be done" in text:
        lenses.append("jtbd_human")
        if any(word in text for word in ["agent", "agents", "ia", "ai"]):
            lenses.append("jtbd_ai")
    return lenses


def selected_lenses(cli_lenses: list[str], prompts: list[str], include_blind_spots: bool, include_jtbd: bool) -> list[str]:
    lenses: list[str] = []
    for lens in cli_lenses:
        lenses.append(normalize_lens(lens))
    for prompt in prompts:
        lenses.extend(lenses_from_prompt(prompt))
    if include_blind_spots:
        lenses.append("blind_spot_manager")
    if include_jtbd:
        lenses.extend(["jtbd_human", "jtbd_ai"])
    known = []
    for lens in lenses:
        if lens in LENS_PATTERNS and lens not in known:
            known.append(lens)
    return known


def candidate_signature(candidate: ProjectionCandidate) -> set[str]:
    return {candidate.name, slugify(candidate.label), slugify(candidate.business_question or candidate.description)}


def source_text_index(candidates: list[ProjectionCandidate]) -> set[str]:
    values: set[str] = set()
    for candidate in candidates:
        values.update(candidate_signature(candidate))
    return values


def extract_markdown_candidates(
    source_dir: Path,
    db_path: Path,
    workspace_id: str,
    recursive: bool,
    db_kind: str,
    postgres_dsn: str | None,
) -> list[ProjectionCandidate]:
    scopes = materialized_scopes(db_path, workspace_id, db_kind, postgres_dsn)
    candidates = []
    paths = source_dir.rglob("*.md") if recursive else source_dir.glob("*.md")
    for path in sorted(paths):
        ontology = ontology_from_filename(path)
        markdown = path.read_text(encoding="utf-8")
        section = extract_projection_section(markdown)
        for label, description in parse_markdown_table(section):
            name = slugify(label)
            expected_scope = f"{workspace_id}:{ontology}:{name}"
            jobs = infer_retrieval_jobs(label, description)
            status = "materialized" if expected_scope in scopes else "candidate"
            dependencies = infer_dependencies(label, description)
            recommendation = "add" if status == "candidate" and dependencies else "review"
            if status == "materialized":
                recommendation = "keep"
            candidates.append(
                ProjectionCandidate(
                    name=name,
                    label=label,
                    ontology=ontology,
                    description=description,
                    source_file=str(path),
                    source_section="Projections / rapports types",
                    expected_scope=expected_scope,
                    suggested_proj_type=suggested_type(jobs),
                    retrieval_jobs=jobs,
                    kpi_hints=infer_kpis(label, description),
                    data_dependencies=dependencies,
                    materialization_status=status,
                    recommendation=recommendation,
                    business_question=description if description.endswith("?") else "",
                    required_schemas=dependencies,
                )
            )
    return candidates


def extract_projection_catalog_candidates(
    path: Path,
    db_path: Path,
    workspace_id: str,
    db_kind: str,
    postgres_dsn: str | None,
) -> list[ProjectionCandidate]:
    payload = load_yaml_file(path)
    scopes = materialized_scopes(db_path, workspace_id, db_kind, postgres_dsn)
    candidates: list[ProjectionCandidate] = []
    for item in payload.get("projections", []) or []:
        if not isinstance(item, dict):
            continue
        name = slugify(str(item.get("name") or item.get("label") or item.get("business_question") or "projection"))
        scope = str(item.get("scope") or f"{workspace_id}:catalog:{name}")
        parts = scope.split(":")
        ontology = parts[1] if len(parts) > 2 and parts[0] == workspace_id else "catalog"
        jobs = as_list(item.get("retrieval_jobs")) or ["summary"]
        status = "materialized" if scope in scopes else "candidate"
        candidates.append(
            ProjectionCandidate(
                name=name,
                label=str(item.get("label") or name),
                ontology=ontology,
                description=str(item.get("description") or item.get("business_question") or ""),
                source_file=str(path),
                source_section="projection_catalog.yaml",
                expected_scope=scope,
                suggested_proj_type=str(item.get("proj_type") or suggested_type(jobs)),
                retrieval_jobs=jobs,
                kpi_hints=as_list(item.get("kpi_hints")),
                data_dependencies=as_list(item.get("required_schemas")),
                materialization_status=status,
                recommendation="keep" if status == "materialized" else "add",
                business_question=str(item.get("business_question") or ""),
                origin="projection_catalog",
                required_schemas=as_list(item.get("required_schemas")),
                required_facets=as_list(item.get("required_facets")),
                required_edges=as_list(item.get("required_edges")),
                impact_summary="Projection deja declaree dans le catalogue decisionnel.",
                confidence=1.0,
            )
        )
    return candidates


def extract_manager_question_candidates(
    path: Path,
    db_path: Path,
    workspace_id: str,
    db_kind: str,
    postgres_dsn: str | None,
) -> list[ProjectionCandidate]:
    payload = load_yaml_file(path)
    scopes = materialized_scopes(db_path, workspace_id, db_kind, postgres_dsn)
    candidates: list[ProjectionCandidate] = []
    for family, questions in (payload.get("families") or {}).items():
        if not isinstance(questions, list):
            continue
        for question in questions:
            if not isinstance(question, dict):
                continue
            projection = str(question.get("projection") or "")
            q_text = str(question.get("question") or "")
            if not q_text:
                continue
            name = slugify(projection or question.get("id") or q_text)
            scope = f"{workspace_id}:{slugify(str(family))}:{name}"
            matching_projection_scope = next((item for item in sorted(scopes) if projection and item.endswith(f":{projection}")), "")
            if matching_projection_scope:
                scope = matching_projection_scope
            status = "materialized" if scope in scopes else "candidate"
            candidates.append(
                ProjectionCandidate(
                    name=name,
                    label=q_text,
                    ontology=slugify(str(family)),
                    description=q_text,
                    source_file=str(path),
                    source_section="manager_questions.yaml",
                    expected_scope=scope,
                    suggested_proj_type="NOTE",
                    retrieval_jobs=["question"],
                    kpi_hints=[],
                    data_dependencies=[],
                    materialization_status=status,
                    recommendation="keep" if status == "materialized" else "review",
                    business_question=q_text,
                    origin="manager_questions",
                    impact_summary=f"Question manager associee a la projection `{projection}`.",
                    confidence=1.0,
                )
            )
    return candidates


def extract_source_candidates(
    source_dir: Path,
    db_path: Path,
    workspace_id: str,
    recursive_markdown: bool,
    projection_catalog: Path | None,
    manager_questions: Path | None,
    db_kind: str,
    postgres_dsn: str | None,
) -> list[ProjectionCandidate]:
    candidates = extract_markdown_candidates(source_dir, db_path, workspace_id, recursive_markdown, db_kind, postgres_dsn)
    if projection_catalog and projection_catalog.exists():
        candidates.extend(extract_projection_catalog_candidates(projection_catalog, db_path, workspace_id, db_kind, postgres_dsn))
    if manager_questions and manager_questions.exists():
        candidates.extend(extract_manager_question_candidates(manager_questions, db_path, workspace_id, db_kind, postgres_dsn))
    return append_unique_candidates([], candidates)


def extract_lens_candidates(
    workspace_id: str,
    db_path: Path,
    lenses: list[str],
    role: str,
    source_candidates: list[ProjectionCandidate],
    db_kind: str,
    postgres_dsn: str | None,
) -> list[ProjectionCandidate]:
    scopes = materialized_scopes(db_path, workspace_id, db_kind, postgres_dsn)
    existing = source_text_index(source_candidates)
    candidates: list[ProjectionCandidate] = []

    for lens in lenses:
        for pattern in LENS_PATTERNS[lens]:
            name = slugify(pattern.name)
            if name in existing or slugify(pattern.business_question) in existing:
                continue
            expected_scope = f"{workspace_id}:{slugify(role)}:{name}"
            status = "materialized" if expected_scope in scopes else "candidate"
            recommendation = "keep" if status == "materialized" else "add"
            candidates.append(
                ProjectionCandidate(
                    name=name,
                    label=pattern.label,
                    ontology=slugify(role),
                    description=pattern.description,
                    source_file="analysis_lens",
                    source_section=pattern.lens,
                    expected_scope=expected_scope,
                    suggested_proj_type=pattern.suggested_proj_type,
                    retrieval_jobs=pattern.retrieval_jobs,
                    kpi_hints=pattern.kpi_hints,
                    data_dependencies=sorted(set(pattern.required_schemas)),
                    materialization_status=status,
                    recommendation=recommendation,
                    business_question=pattern.business_question,
                    origin="analysis_lens",
                    lens=pattern.lens,
                    role=role,
                    required_schemas=pattern.required_schemas,
                    required_facets=pattern.required_facets,
                    required_edges=pattern.required_edges,
                    human_jobs=pattern.human_jobs,
                    ai_agent_jobs=pattern.ai_agent_jobs,
                    impact_summary=pattern.impact_summary,
                    pattern_tags=pattern.pattern_tags,
                    confidence=pattern.confidence,
                )
            )
    return candidates


def extract_candidates(
    source_dir: Path,
    db_path: Path,
    workspace_id: str,
    lenses: list[str] | None = None,
    role: str = "manager_operations",
    recursive_markdown: bool = False,
    projection_catalog: Path | None = None,
    manager_questions: Path | None = None,
    db_kind: str = "auto",
    postgres_dsn: str | None = None,
) -> list[ProjectionCandidate]:
    source_candidates = extract_source_candidates(
        source_dir,
        db_path,
        workspace_id,
        recursive_markdown,
        projection_catalog,
        manager_questions,
        db_kind,
        postgres_dsn,
    )
    lens_candidates = extract_lens_candidates(workspace_id, db_path, lenses or [], role, source_candidates, db_kind, postgres_dsn)
    return source_candidates + lens_candidates


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if isinstance(value, str):
        return [value] if value else []
    return [str(value)]


def load_llm_findings(
    path: Path,
    workspace_id: str,
    role: str,
    db_path: Path,
    db_kind: str,
    postgres_dsn: str | None,
) -> tuple[list[ProjectionCandidate], dict[str, Any]]:
    """Load optional agent/LLM findings produced outside this script.

    Expected shape:
      {"candidates": [{... ProjectionCandidate-like fields ...}], "notes": [...]}
    """
    if not path.exists():
        raise FileNotFoundError(f"LLM findings file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("LLM findings file must contain a JSON object")

    scopes = materialized_scopes(db_path, workspace_id, db_kind, postgres_dsn)
    candidates: list[ProjectionCandidate] = []
    for index, item in enumerate(payload.get("candidates", []), 1):
        if not isinstance(item, dict):
            raise ValueError(f"LLM candidate #{index} must be a JSON object")
        label = str(item.get("label") or item.get("business_question") or f"LLM candidate {index}")
        name = slugify(str(item.get("name") or label))
        ontology = slugify(str(item.get("ontology") or role))
        expected_scope = str(item.get("expected_scope") or f"{workspace_id}:{ontology}:{name}")
        status = "materialized" if expected_scope in scopes else "candidate"
        required_schemas = as_list(item.get("required_schemas") or item.get("data_dependencies"))
        retrieval_jobs = as_list(item.get("retrieval_jobs")) or ["summary"]
        candidates.append(
            ProjectionCandidate(
                name=name,
                label=label,
                ontology=ontology,
                description=str(item.get("description") or item.get("business_question") or ""),
                source_file=str(path),
                source_section="llm_findings",
                expected_scope=expected_scope,
                suggested_proj_type=str(item.get("suggested_proj_type") or suggested_type(retrieval_jobs)),
                retrieval_jobs=retrieval_jobs,
                kpi_hints=as_list(item.get("kpi_hints")),
                data_dependencies=required_schemas,
                materialization_status=status,
                recommendation="keep" if status == "materialized" else str(item.get("recommendation") or "review"),
                business_question=str(item.get("business_question") or ""),
                origin="llm_review",
                lens=str(item.get("lens") or "agent_llm_review"),
                role=role,
                required_schemas=required_schemas,
                required_facets=as_list(item.get("required_facets")),
                required_edges=as_list(item.get("required_edges")),
                human_jobs=as_list(item.get("human_jobs")),
                ai_agent_jobs=as_list(item.get("ai_agent_jobs")),
                impact_summary=str(item.get("impact_summary") or ""),
                pattern_tags=as_list(item.get("pattern_tags")),
                confidence=float(item.get("confidence", 0.7)),
            )
        )
    return candidates, payload


def append_unique_candidates(base: list[ProjectionCandidate], additions: list[ProjectionCandidate]) -> list[ProjectionCandidate]:
    seen: set[str] = set()
    merged: list[ProjectionCandidate] = []
    for candidate in base + additions:
        signature = f"{candidate.origin}|{candidate.expected_scope}|{slugify(candidate.business_question or candidate.label)}"
        if signature in seen:
            continue
        seen.add(signature)
        merged.append(candidate)
    return merged


def collect_model_impacts(candidates: list[ProjectionCandidate]) -> dict[str, Any]:
    impact_candidates = [item for item in candidates if item.origin in {"analysis_lens", "llm_review"}]
    facets = sorted({facet for item in impact_candidates for facet in (item.required_facets or [])})
    edges = sorted({edge for item in impact_candidates for edge in (item.required_edges or [])})
    schemas = sorted({schema for item in impact_candidates for schema in (item.required_schemas or [])})
    by_lens: dict[str, int] = {}
    for item in impact_candidates:
        by_lens[item.lens] = by_lens.get(item.lens, 0) + 1
    return {
        "lens_candidate_count": len(impact_candidates),
        "by_lens": dict(sorted(by_lens.items())),
        "required_schemas": schemas,
        "required_facets": facets,
        "required_edges": edges,
    }


def load_model_contract(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def known_terms_from_contract(contract: dict[str, Any]) -> dict[str, set[str]]:
    schemas = set((contract.get("schemas") or {}).keys())
    facets: set[str] = {"record_id", "workspace_id", "label"}
    for schema in (contract.get("schemas") or {}).values():
        facets.update((schema.get("facets") or {}).keys())
    edges = {edge.get("type") for edge in contract.get("edge_types", []) if edge.get("type")}
    return {"schemas": schemas, "facets": facets, "edges": edges}


def collect_validation_gaps(candidates: list[ProjectionCandidate], contract: dict[str, Any]) -> dict[str, Any]:
    source_origins = {"source_table", "projection_catalog", "manager_questions"}
    proposal_origins = {"analysis_lens", "llm_review"}
    source_candidates = [item for item in candidates if item.origin in source_origins]
    proposal_candidates = [item for item in candidates if item.origin in proposal_origins]

    source_schemas = {schema for item in source_candidates for schema in (item.required_schemas or [])}
    source_facets = {facet for item in source_candidates for facet in (item.required_facets or [])}
    source_edges = {edge for item in source_candidates for edge in (item.required_edges or [])}
    proposal_schemas = {schema for item in proposal_candidates for schema in (item.required_schemas or [])}
    proposal_facets = {facet for item in proposal_candidates for facet in (item.required_facets or [])}
    proposal_edges = {edge for item in proposal_candidates for edge in (item.required_edges or [])}

    terms = known_terms_from_contract(contract)
    return {
        "extension_schemas": sorted(proposal_schemas - source_schemas),
        "extension_facets": sorted(proposal_facets - source_facets),
        "extension_edges": sorted(proposal_edges - source_edges),
        "unknown_schemas": sorted(proposal_schemas - terms["schemas"]) if contract else [],
        "unknown_facets": sorted(proposal_facets - terms["facets"]) if contract else [],
        "unknown_edges": sorted(proposal_edges - terms["edges"]) if contract else [],
        "contract_checked": bool(contract),
    }


def fmt_values(values: list[str]) -> str:
    return ", ".join(f"`{item}`" for item in values) if values else "n/a"


def write_validation_markdown(payload: dict[str, Any], path: Path) -> None:
    by_origin = {}
    for item in payload["candidates"]:
        by_origin.setdefault(item.get("origin", "source_table"), []).append(item)

    gaps = payload.get("validation_gaps", {})
    lines = [
        "# Projection Model Validation",
        "",
        "Ce document sert de base de validation humaine pour décider quelles projections, dimensions et arêtes doivent entrer dans le modèle.",
        "",
        "## Synthese",
        "",
        f"- Workspace: `{payload['workspace_id']}`",
        f"- Backend materialisation: `{payload.get('db_kind', 'sqlite')}`",
        f"- Projections/entrées sources: {payload['summary'].get('source_input_count', 0)}",
        f"- Projections catalogue: {payload['summary'].get('projection_catalog_count', 0)}",
        f"- Questions manager: {payload['summary'].get('manager_questions_count', 0)}",
        f"- Questions/projections ajoutees par patterns: {payload['summary'].get('analysis_lens_count', 0)}",
        f"- Questions/projections ajoutees par revue LLM: {payload['summary'].get('llm_review_count', 0)}",
        f"- Scopes materialises uniques: {payload['summary'].get('unique_materialized_scope_count', 0)}",
        "",
        "## Questions business deja identifiees",
        "",
    ]

    for item in by_origin.get("projection_catalog", []):
        question = item.get("business_question") or item.get("description") or item.get("label")
        lines.extend(
            [
                f"### {item['label']}",
                f"- Question: {question}",
                f"- Projection: `{item['name']}`",
                f"- Scope: `{item['expected_scope']}`",
                f"- Statut: `{item['materialization_status']}`",
                f"- Facettes requises: {fmt_values(item.get('required_facets', []))}",
                f"- Arêtes requises: {fmt_values(item.get('required_edges', []))}",
                "",
            ]
        )

    if by_origin.get("manager_questions"):
        lines.extend(["## Questions manager associees", ""])
        for item in by_origin["manager_questions"]:
            lines.extend(
                [
                    f"- {item.get('business_question') or item['label']} -> `{item['name']}` ({item['materialization_status']})",
                ]
            )
        lines.append("")

    proposed = by_origin.get("analysis_lens", []) + by_origin.get("llm_review", [])
    if proposed:
        lines.extend(["## Questions manquantes proposees", ""])
        for item in proposed:
            question = item.get("business_question") or item.get("description") or item.get("label")
            lines.extend(
                [
                    f"### {item['label']}",
                    f"- Categorie: `{item.get('lens') or item.get('origin')}`",
                    f"- Question: {question}",
                    f"- Projection proposee: `{item['name']}`",
                    f"- Type: `{item['suggested_proj_type']}`",
                    f"- Jobs humain: {', '.join(item.get('human_jobs', [])) or 'n/a'}",
                    f"- Jobs agent IA: {', '.join(item.get('ai_agent_jobs', [])) or 'n/a'}",
                    f"- Impact modele: {item.get('impact_summary') or 'n/a'}",
                    f"- Facettes requises: {fmt_values(item.get('required_facets', []))}",
                    f"- Arêtes requises: {fmt_values(item.get('required_edges', []))}",
                    "",
                ]
            )

    lines.extend(
        [
            "## Dimensions et graphes a valider",
            "",
            "### Facettes nouvelles par rapport aux sources",
            "",
            fmt_values(gaps.get("extension_facets", [])),
            "",
            "### Arêtes nouvelles par rapport aux sources",
            "",
            fmt_values(gaps.get("extension_edges", [])),
            "",
            "### Schemas nouveaux par rapport aux sources",
            "",
            fmt_values(gaps.get("extension_schemas", [])),
            "",
        ]
    )

    if gaps.get("contract_checked"):
        lines.extend(
            [
                "## Gaps versus model_contract",
                "",
                "Ces éléments sont requis par les propositions mais ne sont pas connus dans le contrat fourni.",
                "",
                f"- Schemas inconnus: {fmt_values(gaps.get('unknown_schemas', []))}",
                f"- Facettes inconnues: {fmt_values(gaps.get('unknown_facets', []))}",
                f"- Arêtes inconnues: {fmt_values(gaps.get('unknown_edges', []))}",
                "",
            ]
        )

    if payload.get("llm_notes"):
        lines.extend(["## Notes de revue LLM", ""])
        for note in payload["llm_notes"]:
            lines.append(f"- {note}")
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Projection Candidate Review",
        "",
        f"- Workspace: `{payload['workspace_id']}`",
        f"- DB kind: `{payload.get('db_kind', 'sqlite')}`",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Candidate count: {payload['summary']['candidate_count']}",
        f"- Materialized count: {payload['summary']['materialized_count']}",
        f"- Analysis lens count: {payload['summary']['analysis_lens_count']}",
        f"- Active lenses: {', '.join(payload['active_lenses']) or 'n/a'}",
        "",
    ]

    impacts = payload["model_impacts"]
    if impacts["lens_candidate_count"]:
        lines.extend(
            [
                "## Model Impact Summary",
                "",
                "### Facets to confirm or add",
                "",
                ", ".join(f"`{item}`" for item in impacts["required_facets"]) or "n/a",
                "",
                "### Edges to confirm or add",
                "",
                ", ".join(f"`{item}`" for item in impacts["required_edges"]) or "n/a",
                "",
                "### Schemas touched",
                "",
                ", ".join(f"`{item}`" for item in impacts["required_schemas"]) or "n/a",
                "",
            ]
        )

    for ontology, items in payload["by_ontology"].items():
        lines.extend([f"## {ontology}", ""])
        for item in items:
            jobs = ", ".join(item["retrieval_jobs"])
            deps = ", ".join(f"`{dep}`" for dep in item["data_dependencies"]) or "n/a"
            facets = ", ".join(f"`{dep}`" for dep in item.get("required_facets", [])) or "n/a"
            edges = ", ".join(f"`{dep}`" for dep in item.get("required_edges", [])) or "n/a"
            lines.append(f"### {item['label']}")
            lines.append(f"- Scope: `{item['expected_scope']}`")
            lines.append(f"- Status: `{item['materialization_status']}`")
            lines.append(f"- Origin: `{item.get('origin', 'source_table')}`")
            if item.get("lens"):
                lines.append(f"- Lens: `{item['lens']}`")
            lines.append(f"- Suggested type: `{item['suggested_proj_type']}`")
            lines.append(f"- Jobs: {jobs}")
            lines.append(f"- Dependencies: {deps}")
            if item.get("business_question"):
                lines.append(f"- Business question: {item['business_question']}")
            lines.append(f"- Required facets: {facets}")
            lines.append(f"- Required edges: {edges}")
            if item.get("impact_summary"):
                lines.append(f"- Model impact: {item['impact_summary']}")
            lines.append(f"- Description: {item['description']}")
            lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compact_candidate_for_agent(candidate: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "name",
        "label",
        "ontology",
        "business_question",
        "description",
        "expected_scope",
        "suggested_proj_type",
        "retrieval_jobs",
        "data_dependencies",
        "required_facets",
        "required_edges",
        "origin",
        "lens",
        "impact_summary",
    ]
    return {key: candidate.get(key) for key in keys if candidate.get(key) not in (None, "", [])}


def build_agent_review_prompt(payload: dict[str, Any]) -> str:
    context = {
        "workspace_id": payload["workspace_id"],
        "role": payload["role"],
        "active_lenses": payload["active_lenses"],
        "summary": payload["summary"],
        "model_impacts": payload["model_impacts"],
        "candidates": [compact_candidate_for_agent(item) for item in payload["candidates"]],
    }
    return "\n".join(
        [
            "# Agent Review Prompt: Projection Candidates",
            "",
            "Tu es un agent de modelisation GhostCrab. Analyse les candidats de projections ci-dessous.",
            "",
            "Objectif:",
            "- identifier les questions business manquantes pour le role indique;",
            "- appliquer les patterns Blind Spot et JTBD lorsque pertinents;",
            "- deduire les impacts sur projections, facettes et aretes semantiques;",
            "- eviter les doublons avec les candidats existants;",
            "- garder uniquement les propositions utiles pour une decision manager ou un agent IA.",
            "",
            "Retourne uniquement du JSON conforme a cette forme:",
            "",
            "```json",
            json.dumps(LLM_FINDINGS_SCHEMA, indent=2, ensure_ascii=False),
            "```",
            "",
            "Contexte candidat:",
            "",
            "```json",
            json.dumps(context, indent=2, ensure_ascii=False),
            "```",
            "",
        ]
    )


def write_agent_context(payload: dict[str, Any], output_dir: Path) -> dict[str, str]:
    context_path = output_dir / "projection_candidates_agent_context.json"
    prompt_path = output_dir / "projection_candidates_agent_prompt.md"
    context = {
        "workspace_id": payload["workspace_id"],
        "role": payload["role"],
        "active_lenses": payload["active_lenses"],
        "summary": payload["summary"],
        "model_impacts": payload["model_impacts"],
        "candidates": [compact_candidate_for_agent(item) for item in payload["candidates"]],
        "expected_llm_findings_schema": LLM_FINDINGS_SCHEMA,
    }
    context_path.write_text(json.dumps(context, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    prompt_path.write_text(build_agent_review_prompt(payload), encoding="utf-8")
    return {"agent_context": str(context_path), "agent_prompt": str(prompt_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--db-kind", choices=["auto", "sqlite", "postgres", "none"], default="auto", help="Backend used to detect materialized projections")
    parser.add_argument("--postgres-dsn", default="", help="PostgreSQL DSN for GhostCrab Pro projection lookup")
    parser.add_argument("--workspace", default=WORKSPACE_ID)
    parser.add_argument("--output-dir", default="generated/projection_candidates")
    parser.add_argument("--recursive-markdown", action="store_true", help="Scan Markdown files recursively instead of only source-dir/*.md")
    parser.add_argument("--projection-catalog", help="Optional specs/projection_catalog.yaml to import declared projections")
    parser.add_argument("--manager-questions", help="Optional specs/manager_questions.yaml to import natural-language manager questions")
    parser.add_argument("--model-contract", help="Optional artifacts/model_contract.json used to flag unknown schemas, facets, and edges")
    parser.add_argument("--role", default="manager_operations", help="Role slug used for lens-generated scopes")
    parser.add_argument("--prompt", action="append", default=[], help="Prompt text used to activate deterministic lenses")
    parser.add_argument("--lens", action="append", default=[], help=f"Analysis lens to apply. Known: {', '.join(sorted(LENS_PATTERNS))}")
    parser.add_argument("--include-blind-spots", action="store_true", help="Shortcut for --lens blind_spot_manager")
    parser.add_argument("--include-jtbd", action="store_true", help="Shortcut for --lens jtbd_human --lens jtbd_ai")
    parser.add_argument("--write-agent-context", action="store_true", help="Write a compact prompt/context pack for the calling LLM agent")
    parser.add_argument("--llm-findings", help="Optional JSON file produced by an agent/LLM review to merge into candidates")
    parser.add_argument("--list-lenses", action="store_true", help="List known deterministic lenses and exit")
    args = parser.parse_args()

    if args.list_lenses:
        print(json.dumps({name: len(patterns) for name, patterns in sorted(LENS_PATTERNS.items())}, indent=2, ensure_ascii=False))
        return

    lenses = selected_lenses(args.lens, args.prompt, args.include_blind_spots, args.include_jtbd)
    candidates = extract_candidates(
        Path(args.source_dir),
        Path(args.db),
        args.workspace,
        lenses=lenses,
        role=args.role,
        recursive_markdown=args.recursive_markdown,
        projection_catalog=Path(args.projection_catalog) if args.projection_catalog else None,
        manager_questions=Path(args.manager_questions) if args.manager_questions else None,
        db_kind=args.db_kind,
        postgres_dsn=args.postgres_dsn or None,
    )
    llm_payload: dict[str, Any] = {}
    if args.llm_findings:
        llm_candidates, llm_payload = load_llm_findings(
            Path(args.llm_findings),
            args.workspace,
            args.role,
            Path(args.db),
            args.db_kind,
            args.postgres_dsn or None,
        )
        candidates = append_unique_candidates(candidates, llm_candidates)
    model_contract = load_model_contract(Path(args.model_contract) if args.model_contract else None)

    by_ontology: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        by_ontology.setdefault(candidate.ontology, []).append(asdict(candidate))

    payload = {
        "workspace_id": args.workspace,
        "source_dir": args.source_dir,
        "db_path": args.db,
        "db_kind": args.db_kind,
        "postgres_dsn": args.postgres_dsn.replace("ghostcrab:ghostcrab@", "ghostcrab:***@") if args.postgres_dsn else "",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "active_lenses": lenses,
        "role": args.role,
        "prompts": args.prompt,
        "llm_findings_file": args.llm_findings or "",
        "llm_notes": llm_payload.get("notes", []),
        "model_contract_path": args.model_contract or "",
        "summary": {
            "candidate_count": sum(1 for item in candidates if item.materialization_status == "candidate"),
            "materialized_count": sum(1 for item in candidates if item.materialization_status == "materialized"),
            "unique_materialized_scope_count": len({item.expected_scope for item in candidates if item.materialization_status == "materialized"}),
            "analysis_lens_count": sum(1 for item in candidates if item.origin == "analysis_lens"),
            "llm_review_count": sum(1 for item in candidates if item.origin == "llm_review"),
            "projection_catalog_count": sum(1 for item in candidates if item.origin == "projection_catalog"),
            "manager_questions_count": sum(1 for item in candidates if item.origin == "manager_questions"),
            "source_table_count": sum(1 for item in candidates if item.origin == "source_table"),
            "source_input_count": sum(1 for item in candidates if item.origin in {"source_table", "projection_catalog", "manager_questions"}),
            "total_count": len(candidates),
        },
        "model_impacts": collect_model_impacts(candidates),
        "validation_gaps": collect_validation_gaps(candidates, model_contract),
        "by_ontology": dict(sorted(by_ontology.items())),
        "candidates": [asdict(item) for item in candidates],
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "projection_candidates.json"
    md_path = output_dir / "projection_candidates.md"
    validation_md_path = output_dir / "projection_model_validation.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(payload, md_path)
    write_validation_markdown(payload, validation_md_path)
    agent_outputs = write_agent_context(payload, output_dir) if args.write_agent_context else {}
    print(
        json.dumps(
            {
                "json": str(json_path),
                "markdown": str(md_path),
                "validation_markdown": str(validation_md_path),
                **agent_outputs,
                "summary": payload["summary"],
                "active_lenses": lenses,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
