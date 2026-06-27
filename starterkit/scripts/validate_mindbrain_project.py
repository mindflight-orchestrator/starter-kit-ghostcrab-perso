#!/usr/bin/env python3
"""Validate a GhostCrab / MindBrain project run contract.

This validator is intentionally dependency-light. It behaves like a small
Pydantic-style gate runner: explicit schema checks, typed findings, JSON output,
and a non-zero exit code when hard gates fail.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - YAML is optional at runtime.
    yaml = None


STATUS_FAIL = "FAIL"
STATUS_PASS = "PASS"
STATUS_WARN = "WARN"


@dataclass
class Finding:
    code: str
    message: str
    severity: str = "error"
    phase: str = "general"
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "phase": self.phase,
        }
        if self.path:
            data["path"] = self.path
        return data


@dataclass
class ValidationContext:
    project: Path
    workspace: str
    edition: str
    scenario: Path | None
    projection_audit: Path | None
    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)
    phase_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    observed: dict[str, Any] = field(default_factory=dict)

    def error(self, code: str, message: str, phase: str, path: Path | None = None) -> None:
        self.errors.append(Finding(code, message, "error", phase, str(path) if path else None))

    def warn(self, code: str, message: str, phase: str, path: Path | None = None) -> None:
        self.warnings.append(Finding(code, message, "warning", phase, str(path) if path else None))

    def mark_phase(self, phase: str, status: str, **details: Any) -> None:
        self.phase_results[phase] = {"status": status, **details}


def load_structured(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".json"}:
        return json.loads(text)
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to parse YAML files")
        return yaml.safe_load(text)
    raise RuntimeError(f"Unsupported structured file extension: {path}")


def find_default_scenario(project: Path) -> Path | None:
    candidates = sorted(project.glob("simulations/**/scenario.json"))
    if candidates:
        return candidates[0]
    candidates = sorted(project.glob("seeds/*.jsonl"))
    return candidates[0] if candidates else None


def find_first_existing(project: Path, relative_paths: list[str]) -> Path | None:
    for relative_path in relative_paths:
        path = project / relative_path
        if path.exists():
            return path
    return None


def projection_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("projections", "items", "views"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                return [{"projection_id": name, **item} if isinstance(item, dict) else {"projection_id": name} for name, item in value.items()]
        return [{"projection_id": name, **item} if isinstance(item, dict) else {"projection_id": name} for name, item in data.items()]
    return []


def rule_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        value = data.get("rules")
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [{"rule_id": name, **item} if isinstance(item, dict) else {"rule_id": name} for name, item in value.items()]
    return []


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            item = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
        if isinstance(item, dict):
            rows.append(item)
    return rows


def normalize_nodes_edges(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if path.suffix.lower() == ".jsonl":
        rows = read_jsonl(path)
        nodes = [row for row in rows if row.get("kind") in {"node", "entity", None} and ("id" in row or "entity_id" in row)]
        edges = [row for row in rows if row.get("kind") in {"edge", "relation"} or ("source" in row and "target" in row)]
        return nodes, edges

    data = load_structured(path)
    if not isinstance(data, dict):
        raise RuntimeError("scenario file must contain an object")
    nodes = data.get("nodes") or data.get("entities") or []
    edges = data.get("edges") or data.get("relations") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise RuntimeError("scenario nodes/entities and edges/relations must be lists")
    return [item for item in nodes if isinstance(item, dict)], [item for item in edges if isinstance(item, dict)]


def node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("entity_id") or node.get("name") or "")


def node_type(node: dict[str, Any]) -> str:
    return str(node.get("entity_type") or node.get("type") or node.get("schema") or "")


def node_facets(node: dict[str, Any]) -> dict[str, Any]:
    facets = node.get("facets")
    metadata = node.get("metadata")
    if isinstance(facets, dict):
        return facets
    if isinstance(metadata, dict):
        return metadata
    return {key: value for key, value in node.items() if key not in {"id", "entity_id", "name", "entity_type", "type", "schema"}}


def edge_source(edge: dict[str, Any]) -> str:
    return str(edge.get("source") or edge.get("source_id") or edge.get("from") or "")


def edge_target(edge: dict[str, Any]) -> str:
    return str(edge.get("target") or edge.get("target_id") or edge.get("to") or "")


def edge_label(edge: dict[str, Any]) -> str:
    return str(edge.get("label") or edge.get("relation_type") or edge.get("type") or edge.get("predicate") or "")


def validate_environment(ctx: ValidationContext) -> None:
    if ctx.edition not in {"personal-mcp", "pro-mcp"}:
        ctx.error("invalid_edition", "edition must be personal-mcp or pro-mcp", "environment")
    if not ctx.workspace:
        ctx.error("missing_workspace", "workspace id is required", "environment")
    if not ctx.project.exists():
        ctx.error("missing_project", "project directory does not exist", "environment", ctx.project)
    ctx.mark_phase("environment", STATUS_FAIL if any(err.phase == "environment" for err in ctx.errors) else STATUS_PASS)


def validate_ontology_exploration(ctx: ValidationContext) -> None:
    path = find_first_existing(
        ctx.project,
        [
            "analysis/ontology-exploration.yaml",
            "analysis/ontology_exploration_brief.yaml",
            "ontology/exploration.yaml",
            "ontology/ontology-exploration.yaml",
        ],
    )
    if not path:
        ctx.error(
            "missing_ontology_exploration",
            "upstream ontology exploration brief is required before formal modeling",
            "ontology_exploration",
        )
        ctx.mark_phase("ontology_exploration", STATUS_FAIL)
        return

    try:
        data = load_structured(path)
    except Exception as exc:
        ctx.error("invalid_ontology_exploration", f"cannot parse ontology exploration brief: {exc}", "ontology_exploration", path)
        ctx.mark_phase("ontology_exploration", STATUS_FAIL)
        return

    if not isinstance(data, dict):
        ctx.error("invalid_ontology_exploration_shape", "ontology exploration brief must be a YAML/JSON object", "ontology_exploration", path)
        ctx.mark_phase("ontology_exploration", STATUS_FAIL)
        return

    missing = []
    for key in ("canonical_reformulation", "core_problem", "actors", "domains", "clarification_questions", "five_acts", "canvas"):
        value = data.get(key)
        if value in (None, "", [], {}):
            missing.append(key)

    five_acts = data.get("five_acts") or {}
    missing_acts = []
    if isinstance(five_acts, dict):
        for key in ("noms", "verbes", "qualificatifs", "conditions", "recherche"):
            if five_acts.get(key) in (None, "", [], {}):
                missing_acts.append(key)
    else:
        missing_acts = ["noms", "verbes", "qualificatifs", "conditions", "recherche"]

    domain_count = len(data.get("domains") or []) if isinstance(data.get("domains"), list) else 0
    actor_count = len(data.get("actors") or []) if isinstance(data.get("actors"), list) else 0

    if missing:
        ctx.error("incomplete_ontology_exploration", "ontology exploration brief misses required sections", "ontology_exploration", path)
    if missing_acts:
        ctx.error("incomplete_five_acts", "ontology exploration brief misses one or more 5-act sections", "ontology_exploration", path)
    if actor_count < 1:
        ctx.error("no_exploration_actors", "ontology exploration must identify actors and JTBD", "ontology_exploration", path)
    if domain_count < 1:
        ctx.error("no_exploration_domains", "ontology exploration must identify at least one MECE domain", "ontology_exploration", path)

    ctx.observed["ontology_exploration_path"] = str(path)
    ctx.mark_phase(
        "ontology_exploration",
        STATUS_FAIL if any(err.phase == "ontology_exploration" for err in ctx.errors) else STATUS_PASS,
        path=str(path),
        actors=actor_count,
        domains=domain_count,
        missing_sections=missing,
        missing_acts=missing_acts,
    )


def validate_model(ctx: ValidationContext) -> tuple[set[str], set[str]]:
    ontology_path = ctx.project / "ontology" / "core.yaml"
    if not ontology_path.exists():
        ctx.error("missing_ontology", "ontology/core.yaml is required", "model", ontology_path)
        ctx.mark_phase("model", STATUS_FAIL)
        return set(), set()

    try:
        ontology = load_structured(ontology_path)
    except Exception as exc:
        ctx.error("invalid_ontology", f"cannot parse ontology/core.yaml: {exc}", "model", ontology_path)
        ctx.mark_phase("model", STATUS_FAIL)
        return set(), set()

    classes: set[str] = set()
    facets: set[str] = set()
    if isinstance(ontology, dict):
        raw_classes = ontology.get("classes") or ontology.get("$defs") or {}
        if isinstance(raw_classes, dict):
            classes = {str(key) for key in raw_classes}
            for class_body in raw_classes.values():
                if isinstance(class_body, dict):
                    slots = class_body.get("slots") or class_body.get("attributes") or {}
                    if isinstance(slots, list):
                        facets.update(str(slot) for slot in slots)
                    elif isinstance(slots, dict):
                        facets.update(str(slot) for slot in slots)
        raw_slots = ontology.get("slots") or ontology.get("attributes") or {}
        if isinstance(raw_slots, dict):
            facets.update(str(key) for key in raw_slots)

    if not classes:
        ctx.error("no_model_classes", "ontology has no declared classes", "model", ontology_path)
    if not facets:
        ctx.warn("no_model_facets", "ontology has no declared slots/facets", "model", ontology_path)
    ctx.observed["model_classes"] = sorted(classes)
    ctx.observed["model_facets"] = sorted(facets)
    ctx.mark_phase("model", STATUS_FAIL if any(err.phase == "model" for err in ctx.errors) else STATUS_PASS, classes=len(classes), facets=len(facets))
    return classes, facets


def validate_projections(ctx: ValidationContext, model_classes: set[str], model_facets: set[str]) -> list[dict[str, Any]]:
    path = ctx.project / "projections" / "catalog.json"
    if not path.exists():
        ctx.error("missing_projection_catalog", "projections/catalog.json is required", "projections", path)
        ctx.mark_phase("projections", STATUS_FAIL)
        return []
    try:
        projections = projection_items(load_structured(path))
    except Exception as exc:
        ctx.error("invalid_projection_catalog", f"cannot parse projection catalog: {exc}", "projections", path)
        ctx.mark_phase("projections", STATUS_FAIL)
        return []

    if not projections:
        ctx.error("empty_projection_catalog", "projection catalog contains no projections", "projections", path)

    missing_questions: list[str] = []
    missing_facets: list[dict[str, Any]] = []
    for item in projections:
        projection_id = str(item.get("projection_id") or item.get("name") or item.get("id") or "(unnamed)")
        if not (item.get("business_question") or item.get("question") or item.get("manager_question")):
            missing_questions.append(projection_id)
        required_facets = item.get("required_facets") or []
        if isinstance(required_facets, list):
            absent = [str(facet) for facet in required_facets if str(facet) not in model_facets]
            if absent:
                missing_facets.append({"projection_id": projection_id, "missing_facets": absent})

    if missing_questions:
        ctx.error("projection_without_business_question", "some projections have no business question", "projections", path)
    if missing_facets:
        ctx.warn("projection_facets_not_in_model", "some projection required_facets are not declared as model slots", "projections", path)

    ctx.observed["projection_ids"] = [str(item.get("projection_id") or item.get("name") or item.get("id") or "") for item in projections]
    ctx.observed["projection_facet_gaps"] = missing_facets
    ctx.mark_phase(
        "projections",
        STATUS_FAIL if any(err.phase == "projections" for err in ctx.errors) else STATUS_WARN if missing_facets else STATUS_PASS,
        projections=len(projections),
        missing_business_questions=missing_questions,
        projection_facet_gaps=missing_facets,
    )
    return projections


def validate_rules(ctx: ValidationContext) -> list[dict[str, Any]]:
    path = ctx.project / "rules" / "gap-rules.json"
    if not path.exists():
        path = ctx.project / "rules" / "business_rules_catalog.yaml"
    if not path.exists():
        ctx.error("missing_rules_catalog", "rules/gap-rules.json or rules/business_rules_catalog.yaml is required", "business_rules")
        ctx.mark_phase("business_rules", STATUS_FAIL)
        return []

    try:
        rules = rule_items(load_structured(path))
    except Exception as exc:
        ctx.error("invalid_rules_catalog", f"cannot parse rules catalog: {exc}", "business_rules", path)
        ctx.mark_phase("business_rules", STATUS_FAIL)
        return []

    if not rules:
        ctx.error("empty_rules_catalog", "rules catalog contains no rules", "business_rules", path)

    missing_trigger = []
    missing_severity = []
    for item in rules:
        rule_id = str(item.get("rule_id") or item.get("id") or item.get("name") or "(unnamed)")
        has_trigger = bool(
            item.get("trigger")
            or item.get("when")
            or item.get("source_type")
            or item.get("edge_type")
            or (item.get("entity_type") and item.get("relation_type"))
            or (item.get("subject_type") and item.get("predicate"))
        )
        if not has_trigger:
            missing_trigger.append(rule_id)
        if not (item.get("severity") or item.get("level")):
            missing_severity.append(rule_id)

    if missing_trigger:
        ctx.error("rule_without_trigger", "some business rules have no trigger/source condition", "business_rules", path)
    if missing_severity:
        ctx.warn("rule_without_severity", "some business rules have no severity/level", "business_rules", path)

    ctx.observed["rule_ids"] = [str(item.get("rule_id") or item.get("id") or item.get("name") or "") for item in rules]
    ctx.mark_phase(
        "business_rules",
        STATUS_FAIL if any(err.phase == "business_rules" for err in ctx.errors) else STATUS_WARN if missing_severity else STATUS_PASS,
        rules=len(rules),
        missing_trigger=missing_trigger,
        missing_severity=missing_severity,
    )
    return rules


def validate_scenario(ctx: ValidationContext, model_classes: set[str], model_facets: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    path = ctx.scenario or find_default_scenario(ctx.project)
    if not path:
        ctx.error("missing_scenario", "no scenario found under simulations/**/scenario.json or seeds/*.jsonl", "fake_data")
        ctx.mark_phase("fake_data", STATUS_FAIL)
        return [], []
    ctx.scenario = path

    try:
        nodes, edges = normalize_nodes_edges(path)
    except Exception as exc:
        ctx.error("invalid_scenario", f"cannot parse scenario: {exc}", "fake_data", path)
        ctx.mark_phase("fake_data", STATUS_FAIL)
        return [], []

    ids = {node_id(node) for node in nodes if node_id(node)}
    types = Counter(node_type(node) or "(missing_type)" for node in nodes)
    facet_by_type: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        facet_by_type[node_type(node)].update(node_facets(node).keys())

    if not nodes:
        ctx.error("empty_scenario_nodes", "scenario has no nodes/entities", "fake_data", path)
    if not edges:
        ctx.error("empty_scenario_edges", "scenario has no edges/relations", "fake_data", path)

    orphan_edges = []
    missing_labels = []
    for edge in edges:
        source = edge_source(edge)
        target = edge_target(edge)
        if source not in ids or target not in ids:
            orphan_edges.append({"source": source, "target": target, "label": edge_label(edge)})
        if not edge_label(edge):
            missing_labels.append({"source": source, "target": target})
    if orphan_edges:
        ctx.error("scenario_orphan_edges", "some scenario edges reference missing nodes", "fake_data", path)
    if missing_labels:
        ctx.error("scenario_edges_without_label", "some scenario edges have no relation label/type", "fake_data", path)

    unknown_types = sorted(t for t in types if t and t != "(missing_type)" and model_classes and t not in model_classes)
    if unknown_types:
        ctx.warn("scenario_types_not_in_model", "some scenario entity types are not declared in ontology classes", "fake_data", path)

    weak_facet_types = sorted(t for t, facets in facet_by_type.items() if t and t != "(missing_type)" and len(facets) < 3)
    if weak_facet_types:
        ctx.warn("weak_entity_facets", "some entity types have fewer than three observed facets", "fake_data", path)

    tags = {str(node_facets(node).get("case_tag") or node.get("case_tag") or "") for node in nodes}
    all_text = json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False).lower()
    expected_cases = {
        "nominal": "nominal" in tags or "nominal" in all_text or "ready" in all_text,
        "blocked": "blocked" in tags or "blocked" in all_text,
        "incomplete": "incomplete" in tags or "incomplete" in all_text or "missing" in all_text or "not_found" in all_text,
        "routed_next_action": "routed_next_action" in tags or "next_action" in all_text or "routed_to" in all_text,
    }
    missing_cases = [case for case, present in expected_cases.items() if not present]
    if missing_cases:
        ctx.error("missing_fake_data_cases", "scenario must include nominal, blocked, incomplete and routed-next-action cases", "fake_data", path)

    ctx.observed["scenario_entity_types"] = dict(types)
    ctx.observed["scenario_relation_labels"] = dict(Counter(edge_label(edge) or "(missing_label)" for edge in edges))
    ctx.observed["scenario_facet_keys"] = sorted({key for facets in facet_by_type.values() for key in facets})
    ctx.mark_phase(
        "fake_data",
        STATUS_FAIL if any(err.phase == "fake_data" for err in ctx.errors) else STATUS_WARN if unknown_types or weak_facet_types else STATUS_PASS,
        scenario=str(path),
        nodes=len(nodes),
        edges=len(edges),
        entity_types=dict(types),
        orphan_edges=orphan_edges,
        missing_cases=missing_cases,
        unknown_types=unknown_types,
        weak_facet_types=weak_facet_types,
    )
    return nodes, edges


def validate_projection_audit(ctx: ValidationContext) -> None:
    if not ctx.projection_audit:
        ctx.warn("missing_projection_audit", "no projection audit JSON provided; DB import gates were not checked", "post_import_audit")
        ctx.mark_phase("post_import_audit", STATUS_WARN, checked=False)
        return
    if not ctx.projection_audit.exists():
        ctx.error("projection_audit_not_found", "projection audit JSON does not exist", "post_import_audit", ctx.projection_audit)
        ctx.mark_phase("post_import_audit", STATUS_FAIL)
        return

    try:
        audit = json.loads(ctx.projection_audit.read_text(encoding="utf-8"))
    except Exception as exc:
        ctx.error("invalid_projection_audit", f"cannot parse projection audit JSON: {exc}", "post_import_audit", ctx.projection_audit)
        ctx.mark_phase("post_import_audit", STATUS_FAIL)
        return

    counts = audit.get("counts") if isinstance(audit, dict) else {}
    summary = audit.get("summary") if isinstance(audit, dict) else {}
    quality = audit.get("quality_flags") if isinstance(audit, dict) else {}
    blocking: list[str] = []

    graph_entities = int((counts or {}).get("graph_entity_count") or (summary or {}).get("graph_entity_count") or 0)
    graph_relations = int((counts or {}).get("graph_relation_count") or (summary or {}).get("graph_relation_count") or 0)
    orphan_relations = int((counts or {}).get("orphan_relation_count") or (summary or {}).get("orphan_relation_count") or 0)

    planned_gap = audit.get("planned_projection_gap") or audit.get("analysis_plan_gap") or {}
    live_gap = audit.get("live_answer_view_gap") or {}
    answer_gap = audit.get("answer_snapshot_gap") or audit.get("type_b_projection_result_gap") or {}
    missing_projection_count = int(planned_gap.get("missing_count") or 0)
    missing_live_count = int(live_gap.get("missing_count") or 0)
    missing_answer_count = int(answer_gap.get("missing_count") or 0)

    if graph_entities == 0:
        blocking.append("graph has zero entities")
    if graph_relations == 0:
        blocking.append("graph has zero relations")
    if orphan_relations:
        blocking.append(f"graph has {orphan_relations} orphan relations")
    if missing_projection_count:
        blocking.append(f"{missing_projection_count} expected projections are missing")
    if missing_live_count:
        blocking.append(f"{missing_live_count} expected live answer artifacts are missing")
    if missing_answer_count:
        blocking.append(f"{missing_answer_count} expected answer snapshots are missing")
    if quality and quality.get("missing_required_facets"):
        ctx.warn("missing_required_facets", "projection audit reports missing required facets", "post_import_audit", ctx.projection_audit)

    for item in blocking:
        ctx.error("post_import_gate_failed", item, "post_import_audit", ctx.projection_audit)

    ctx.observed["post_import_blocking_findings"] = blocking
    ctx.mark_phase(
        "post_import_audit",
        STATUS_FAIL if blocking else STATUS_PASS,
        checked=True,
        graph_entity_count=graph_entities,
        graph_relation_count=graph_relations,
        orphan_relation_count=orphan_relations,
        missing_projection_count=missing_projection_count,
        missing_live_answer_artifact_count=missing_live_count,
        missing_answer_snapshot_count=missing_answer_count,
    )


def validate_audit_remediation(ctx: ValidationContext) -> None:
    post_import = ctx.phase_results.get("post_import_audit", {})
    if post_import.get("status") != STATUS_FAIL:
        ctx.mark_phase("audit_remediation", STATUS_PASS, required=False)
        return

    path = find_first_existing(
        ctx.project,
        [
            "remediation/audit-remediation-plan.yaml",
            "remediation/audit_remediation_plan.yaml",
            "reports/audit-remediation-plan.yaml",
            "reports/audit_remediation_plan.yaml",
        ],
    )
    if not path:
        ctx.error(
            "missing_audit_remediation_plan",
            "failed post-import audit requires remediation/audit-remediation-plan.yaml",
            "audit_remediation",
        )
        ctx.mark_phase("audit_remediation", STATUS_FAIL, required=True)
        return

    try:
        data = load_structured(path)
    except Exception as exc:
        ctx.error("invalid_audit_remediation_plan", f"cannot parse audit remediation plan: {exc}", "audit_remediation", path)
        ctx.mark_phase("audit_remediation", STATUS_FAIL, required=True)
        return

    if not isinstance(data, dict):
        ctx.error("invalid_audit_remediation_shape", "audit remediation plan must be a YAML/JSON object", "audit_remediation", path)
        ctx.mark_phase("audit_remediation", STATUS_FAIL, required=True)
        return

    findings = data.get("blocking_findings") or []
    if not isinstance(findings, list) or not findings:
        ctx.error("empty_audit_remediation_findings", "remediation plan must list blocking_findings", "audit_remediation", path)
        ctx.mark_phase("audit_remediation", STATUS_FAIL, required=True)
        return

    allowed_categories = {
        "analysis_gap",
        "model_gap",
        "rule_gap",
        "fake_data_gap",
        "import_gap",
        "projection_gap",
        "answer_artifact_gap",
        "graph_gap",
    }
    incomplete_findings = []
    invalid_categories = []
    for index, item in enumerate(findings, 1):
        if not isinstance(item, dict):
            incomplete_findings.append(f"F{index}")
            continue
        finding_id = str(item.get("finding_id") or f"F{index}")
        category = str(item.get("category") or item.get("root_cause") or "")
        if category not in allowed_categories:
            invalid_categories.append(finding_id)
        for key in ("target_artifacts", "fix_actions", "retest_commands", "acceptance_criteria"):
            if item.get(key) in (None, "", [], {}):
                incomplete_findings.append(finding_id)
                break

    if invalid_categories:
        ctx.error("invalid_remediation_category", "some remediation findings have an unknown category/root_cause", "audit_remediation", path)
    if incomplete_findings:
        ctx.error("incomplete_remediation_finding", "some remediation findings miss target, fix, retest, or acceptance criteria", "audit_remediation", path)

    ctx.observed["audit_remediation_path"] = str(path)
    ctx.mark_phase(
        "audit_remediation",
        STATUS_FAIL if any(err.phase == "audit_remediation" for err in ctx.errors) else STATUS_PASS,
        required=True,
        path=str(path),
        findings=len(findings),
        invalid_categories=invalid_categories,
        incomplete_findings=sorted(set(incomplete_findings)),
    )


def build_next_actions(ctx: ValidationContext) -> list[str]:
    actions = []
    phase_to_action = {
        "environment": "select edition/runtime/database/workspace and run status check",
        "ontology_exploration": "complete upstream ontology exploration brief before changing the formal model",
        "model": "complete ontology/model contract",
        "projections": "complete projection catalog and manager questions",
        "business_rules": "complete business rules catalog with triggers and severities",
        "fake_data": "complete scenario data with nominal, blocked, incomplete and routed cases",
        "post_import_audit": "import/reindex missing facts, graph, projections or answer artifacts, then rerun audit",
        "audit_remediation": "create a remediation plan that maps each failed audit finding to fixes and retest commands",
    }
    for phase in phase_to_action:
        result = ctx.phase_results.get(phase, {})
        if result.get("status") == STATUS_FAIL:
            actions.append(phase_to_action[phase])
    if not actions and any(result.get("status") == STATUS_WARN for result in ctx.phase_results.values()):
        actions.append("review warnings and decide whether to promote them to project-specific accepted gaps")
    return actions


def validate(ctx: ValidationContext) -> dict[str, Any]:
    validate_environment(ctx)
    validate_ontology_exploration(ctx)
    model_classes, model_facets = validate_model(ctx)
    validate_projections(ctx, model_classes, model_facets)
    validate_rules(ctx)
    validate_scenario(ctx, model_classes, model_facets)
    validate_projection_audit(ctx)
    validate_audit_remediation(ctx)

    status = STATUS_FAIL if ctx.errors else STATUS_WARN if ctx.warnings else STATUS_PASS
    return {
        "workspace": ctx.workspace,
        "edition": ctx.edition,
        "project": str(ctx.project),
        "status": status,
        "blocking_errors": [finding.as_dict() for finding in ctx.errors],
        "warnings": [finding.as_dict() for finding in ctx.warnings],
        "phase_results": ctx.phase_results,
        "observed": ctx.observed,
        "next_required_actions": build_next_actions(ctx),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="MindBrain project directory, for example mindbrain/campaign-ontology")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--edition", choices=["personal-mcp", "pro-mcp"], required=True)
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--projection-audit", default=None)
    parser.add_argument("--output", default=None, help="Optional JSON output path")
    parser.add_argument("--soft", action="store_true", help="Always exit 0 while still reporting FAIL")
    args = parser.parse_args()

    ctx = ValidationContext(
        project=Path(args.project),
        workspace=args.workspace,
        edition=args.edition,
        scenario=Path(args.scenario) if args.scenario else None,
        projection_audit=Path(args.projection_audit) if args.projection_audit else None,
    )
    report = validate(ctx)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    if args.soft:
        return 0
    return 1 if report["status"] == STATUS_FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
