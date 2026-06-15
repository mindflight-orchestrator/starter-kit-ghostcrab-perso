#!/usr/bin/env python3
"""Validate that JSON ontology structures are represented in LinkML.

This StarterKit gate compares business ontology JSON files against the LinkML
files that will be compiled/imported into MindBrain. It is intentionally
read-only and produces a JSON report plus an optional Markdown summary.

The validator is alias-aware so projects can rename source ontology concepts
while preserving historical source names, for example:

  production -> referentiel
  experience_client_missions -> missions
  point_a_l_ordre_du_jour -> point_odj

It checks:
- JSON nodes -> LinkML classes via ghostcrab.native_entity_type or class name
- JSON properties -> LinkML class slots
- JSON property types -> LinkML slot ranges/enums, when declared
- JSON edges -> LinkML relation classes or relation-like slots
- JSON imports / ontology ids -> manifest and LinkML metadata
- JSON source refs -> LinkML annotations, when configured as required
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - only hit when dependency is absent
    yaml = None  # type: ignore[assignment]
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None


DEFAULT_JSON_DIR = "ontology"
DEFAULT_LINKML_DIR = "ontology"
DEFAULT_MANIFEST = "ontology/manifest.json"


TYPE_COMPATIBILITY: dict[str, set[str]] = {
    "text": {"string", "str", "uri", "uriorcurie", "ncname"},
    "string": {"string", "str", "uri", "uriorcurie", "ncname"},
    "integer": {"integer", "int"},
    "int": {"integer", "int"},
    "decimal": {"decimal", "float", "double"},
    "float": {"decimal", "float", "double"},
    "number": {"decimal", "float", "double"},
    "boolean": {"boolean", "bool"},
    "bool": {"boolean", "bool"},
    "date": {"date", "datetime", "string"},
    "datetime": {"datetime", "date", "string"},
    "enum": {"enum"},
    "reference": {"reference", "string", "str", "uri", "uriorcurie", "ncname"},
    "reference_list": {"reference", "string", "str", "uri", "uriorcurie", "ncname"},
    "document": {"string", "str", "uri", "uriorcurie"},
}


@dataclass
class Issue:
    code: str
    severity: str
    message: str
    file: str = ""
    ontology: str = ""
    node: str = ""
    property: str = ""
    edge: str = ""
    expected: Any = None
    observed: Any = None


@dataclass
class JsonNode:
    node_id: str
    ontology: str
    file: str
    properties: list[dict[str, Any]] = field(default_factory=list)
    source: str = ""


@dataclass
class JsonEdge:
    edge_id: str
    ontology: str
    file: str
    source_node: str
    target_node: str
    label: str
    action: str = ""
    properties: list[dict[str, Any]] = field(default_factory=list)
    source: str = ""


@dataclass
class LinkMLClass:
    name: str
    file: str
    slots: set[str]
    annotations: dict[str, Any]
    source: str = ""


def slug(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("'", "")
    text = re.sub(r"[\s\-/]+", "_", text)
    text = re.sub(r"[^0-9A-Za-z_]+", "", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_").lower()


def camel_to_slug(value: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return slug(value)


def normalize_ontology(value: Any, aliases: dict[str, str]) -> str:
    key = slug(value)
    return slug(aliases.get(key, key))


def normalize_concept(value: Any, aliases: dict[str, str]) -> str:
    key = slug(value)
    return slug(aliases.get(key, key))


def normalize_edge_label(value: Any, aliases: dict[str, str]) -> str:
    key = slug(value)
    return slug(aliases.get(key, key))


def load_yaml_file(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError(f"PyYAML is required for LinkML validation: {YAML_IMPORT_ERROR}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def load_config(path: Path | None) -> dict[str, Any]:
    default = {
        "workspace_id": "",
        "aliases": {"ontology": {}, "concepts": {}, "properties": {}, "edges": {}},
        "checks": {
            "require_all_json_nodes_in_linkml": True,
            "require_all_json_properties_in_linkml": True,
            "require_all_json_edges_in_linkml": True,
            "require_imports_match_manifest": True,
            "require_source_refs_in_linkml": False,
            "allow_aliases": True,
        },
    }
    if not path:
        return default
    loaded = load_yaml_file(path)
    merged = dict(default)
    merged["aliases"] = {**default["aliases"], **(loaded.get("aliases") or {})}
    merged["checks"] = {**default["checks"], **(loaded.get("checks") or {})}
    for key, value in loaded.items():
        if key not in {"aliases", "checks"}:
            merged[key] = value
    return merged


def alias_map(config: dict[str, Any], family: str) -> dict[str, str]:
    raw = ((config.get("aliases") or {}).get(family) or {})
    return {slug(k): slug(v) for k, v in raw.items()}


def checks(config: dict[str, Any]) -> dict[str, bool]:
    return {str(k): bool(v) for k, v in (config.get("checks") or {}).items()}


def load_manifest(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def json_ontology_files(json_dir: Path, manifest: dict[str, Any]) -> list[Path]:
    if manifest.get("ontologies"):
        paths: list[Path] = []
        for item in manifest.get("ontologies", []):
            if not isinstance(item, dict):
                continue
            file_value = str(item.get("file") or "")
            candidate = Path(file_value)
            if not candidate.exists():
                candidate = json_dir / Path(file_value).name
            if candidate.exists() and candidate.suffix == ".json":
                paths.append(candidate)
        if paths:
            return sorted(dict.fromkeys(paths))
    return sorted(p for p in json_dir.glob("*.json") if p.name not in {"manifest.json", "serenity_p3_ontology.json"})


def load_json_structures(json_dir: Path, manifest: dict[str, Any], config: dict[str, Any]) -> tuple[list[JsonNode], list[JsonEdge], list[dict[str, Any]]]:
    ontology_aliases = alias_map(config, "ontology")
    files = json_ontology_files(json_dir, manifest)
    nodes: list[JsonNode] = []
    edges: list[JsonEdge] = []
    ontology_meta: list[dict[str, Any]] = []

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.get("metadata") or {}
        ontology_name = meta.get("ontology_name") or path.stem
        ontology = normalize_ontology(ontology_name, ontology_aliases)
        ontology_meta.append(
            {
                "file": str(path),
                "ontology": ontology,
                "ontology_id": meta.get("ontology_id"),
                "imports": [normalize_ontology(x.split("::")[-1], ontology_aliases) for x in meta.get("imports", [])],
            }
        )
        for item in data.get("nodes") or []:
            if not isinstance(item, dict):
                continue
            nodes.append(
                JsonNode(
                    node_id=str(item.get("id") or ""),
                    ontology=normalize_ontology(item.get("ontology") or item.get("module") or ontology, ontology_aliases),
                    file=str(path),
                    properties=[p for p in item.get("properties") or [] if isinstance(p, dict)],
                    source=str(item.get("source") or ""),
                )
            )
        for item in (data.get("edges") or data.get("relations") or []):
            if not isinstance(item, dict):
                continue
            edges.append(
                JsonEdge(
                    edge_id=str(item.get("id") or ""),
                    ontology=normalize_ontology(item.get("ontology") or item.get("module") or ontology, ontology_aliases),
                    file=str(path),
                    source_node=str(item.get("from") or ""),
                    target_node=str(item.get("to") or ""),
                    label=str(item.get("label") or ""),
                    action=str(item.get("action") or ""),
                    properties=[p for p in item.get("properties") or [] if isinstance(p, dict)],
                    source=str(item.get("source") or ""),
                )
            )
    return nodes, edges, ontology_meta


def annotation_value(annotations: Any, key: str) -> Any:
    if not isinstance(annotations, dict):
        return None
    value = annotations.get(key)
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def load_linkml_structures(linkml_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    ontology_aliases = alias_map(config, "ontology")
    concept_aliases = alias_map(config, "concepts")
    property_aliases = alias_map(config, "properties")
    edge_aliases = alias_map(config, "edges")

    classes_by_native: dict[str, LinkMLClass] = {}
    classes_by_name: dict[str, LinkMLClass] = {}
    class_defs_by_name: dict[str, dict[str, Any]] = {}
    class_files_by_name: dict[str, str] = {}
    slots: dict[str, dict[str, Any]] = {}
    enums: set[str] = set()
    relation_tokens: set[str] = set()
    ontology_meta: list[dict[str, Any]] = []

    for path in sorted(linkml_dir.glob("*.yaml")):
        data = load_yaml_file(path)
        imports = [normalize_ontology(x, ontology_aliases) for x in data.get("imports", []) if str(x) != "linkml:types"]
        ontology_meta.append(
            {
                "file": str(path),
                "name": normalize_ontology(data.get("name") or path.stem, ontology_aliases),
                "id": data.get("id"),
                "imports": imports,
            }
        )
        for enum_name in (data.get("enums") or {}).keys():
            enums.add(str(enum_name))
        for slot_name, slot_def in (data.get("slots") or {}).items():
            if not isinstance(slot_def, dict):
                slot_def = {}
            normalized = normalize_concept(slot_name, property_aliases)
            slots[normalized] = {"name": slot_name, "file": str(path), **slot_def}
            annotations = slot_def.get("annotations") or {}
            native_edge = annotation_value(annotations, "ghostcrab.native_edge_label")
            if native_edge:
                relation_tokens.add(normalize_edge_label(native_edge, edge_aliases))
        for class_name, class_def in (data.get("classes") or {}).items():
            if not isinstance(class_def, dict):
                class_def = {}
            class_defs_by_name[str(class_name)] = class_def
            class_files_by_name[str(class_name)] = str(path)

    resolved_slot_cache: dict[str, set[str]] = {}

    def resolve_class_slots(class_name: str, seen: set[str] | None = None) -> set[str]:
        if class_name in resolved_slot_cache:
            return resolved_slot_cache[class_name]
        seen = seen or set()
        if class_name in seen:
            return set()
        seen.add(class_name)
        class_def = class_defs_by_name.get(class_name) or {}
        resolved = {normalize_concept(slot_name, property_aliases) for slot_name in class_def.get("slots") or []}
        resolved.update({normalize_concept(slot_name, property_aliases) for slot_name in (class_def.get("slot_usage") or {}).keys()})
        parent = class_def.get("is_a")
        if parent:
            resolved.update(resolve_class_slots(str(parent), seen))
        resolved_slot_cache[class_name] = resolved
        return resolved

    for class_name, class_def in class_defs_by_name.items():
            annotations = class_def.get("annotations") or {}
            native = annotation_value(annotations, "ghostcrab.native_entity_type") or class_def.get("class_uri")
            class_slots = resolve_class_slots(class_name)
            item = LinkMLClass(
                name=str(class_name),
                file=class_files_by_name.get(class_name, ""),
                slots=class_slots,
                annotations=annotations if isinstance(annotations, dict) else {},
                source=str(annotation_value(annotations, "source") or annotation_value(annotations, "source_document") or ""),
            )
            by_name_key = normalize_concept(camel_to_slug(str(class_name)), concept_aliases)
            classes_by_name[by_name_key] = item
            if native:
                classes_by_native[normalize_concept(native, concept_aliases)] = item

            native_edge = annotation_value(annotations, "ghostcrab.native_edge_label")
            relation_kind = annotation_value(annotations, "ghostcrab.relation")
            if native_edge:
                relation_tokens.add(normalize_edge_label(native_edge, edge_aliases))
            if relation_kind:
                relation_tokens.add(normalize_edge_label(relation_kind, edge_aliases))
            if str(class_name).lower().endswith(("relation", "edge", "link")):
                relation_tokens.add(normalize_edge_label(class_name, edge_aliases))

    return {
        "classes_by_native": classes_by_native,
        "classes_by_name": classes_by_name,
        "class_range_tokens": set(classes_by_name.keys()) | set(classes_by_native.keys()),
        "slots": slots,
        "enums": enums,
        "relation_tokens": relation_tokens,
        "ontology_meta": ontology_meta,
    }


def find_linkml_class(node_id: str, linkml: dict[str, Any], concept_aliases: dict[str, str]) -> LinkMLClass | None:
    key = normalize_concept(node_id, concept_aliases)
    return linkml["classes_by_native"].get(key) or linkml["classes_by_name"].get(key)


def slot_range(slot_def: dict[str, Any]) -> str:
    value = slot_def.get("range")
    if value is None:
        return "string"
    return str(value)


def is_type_compatible(json_type: str, linkml_range: str, enums: set[str], class_range_tokens: set[str]) -> bool:
    json_key = slug(json_type)
    range_key = slug(linkml_range)
    if not json_key:
        return True
    if json_key in {"reference", "reference_list"} and range_key in class_range_tokens:
        return True
    if json_key == "enum":
        return linkml_range in enums or range_key.endswith("enum") or range_key == "string"
    compatible = TYPE_COMPATIBILITY.get(json_key)
    if compatible is None:
        return True
    return range_key in {slug(x) for x in compatible} or linkml_range in enums


def edge_tokens(edge: JsonEdge, edge_aliases: dict[str, str]) -> set[str]:
    tokens = {
        normalize_edge_label(edge.edge_id, edge_aliases),
        normalize_edge_label(edge.label, edge_aliases),
        normalize_edge_label(edge.action, edge_aliases),
    }
    if edge.source_node and edge.target_node and edge.action:
        tokens.add(normalize_edge_label(f"{edge.source_node}_{edge.action}_{edge.target_node}", edge_aliases))
    return {x for x in tokens if x}


def manifest_imports(manifest: dict[str, Any], ontology_aliases: dict[str, str]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for item in manifest.get("ontologies") or []:
        if not isinstance(item, dict):
            continue
        name = normalize_ontology(item.get("name") or str(item.get("ontology_id") or "").split("::")[-1], ontology_aliases)
        result[name] = {normalize_ontology(str(x).split("::")[-1], ontology_aliases) for x in item.get("imports") or []}
    return result


def validate(json_dir: Path, linkml_dir: Path, manifest_path: Path | None, config: dict[str, Any]) -> dict[str, Any]:
    ontology_aliases = alias_map(config, "ontology")
    concept_aliases = alias_map(config, "concepts")
    property_aliases = alias_map(config, "properties")
    edge_aliases = alias_map(config, "edges")
    active_checks = checks(config)

    manifest = load_manifest(manifest_path)
    json_nodes, json_edges, json_meta = load_json_structures(json_dir, manifest, config)
    linkml = load_linkml_structures(linkml_dir, config)
    issues: list[Issue] = []

    node_to_class: dict[str, LinkMLClass] = {}
    for node in json_nodes:
        linkml_class = find_linkml_class(node.node_id, linkml, concept_aliases)
        if not linkml_class:
            if active_checks.get("require_all_json_nodes_in_linkml", True):
                issues.append(
                    Issue(
                        code="node_in_json_missing_in_linkml",
                        severity="blocking",
                        message=f"JSON node '{node.node_id}' is not represented as a LinkML class.",
                        file=node.file,
                        ontology=node.ontology,
                        node=node.node_id,
                    )
                )
            continue
        node_to_class[node.node_id] = linkml_class

        if active_checks.get("require_source_refs_in_linkml", False) and node.source and not linkml_class.source:
            issues.append(
                Issue(
                    code="source_reference_not_preserved",
                    severity="warning",
                    message=f"JSON node '{node.node_id}' has a source reference but the LinkML class has no source annotation.",
                    file=linkml_class.file,
                    ontology=node.ontology,
                    node=node.node_id,
                    expected=node.source,
                    observed="",
                )
            )

        for prop in node.properties:
            prop_name = str(prop.get("name") or "")
            normalized_prop = normalize_concept(prop_name, property_aliases)
            slot_def = linkml["slots"].get(normalized_prop)
            in_class = normalized_prop in linkml_class.slots
            if active_checks.get("require_all_json_properties_in_linkml", True) and not in_class:
                issues.append(
                    Issue(
                        code="property_in_json_missing_in_linkml_class",
                        severity="blocking",
                        message=f"JSON property '{node.node_id}.{prop_name}' is not listed as a slot on the LinkML class.",
                        file=linkml_class.file,
                        ontology=node.ontology,
                        node=node.node_id,
                        property=prop_name,
                    )
                )
            if not slot_def:
                if active_checks.get("require_all_json_properties_in_linkml", True):
                    issues.append(
                        Issue(
                            code="property_slot_missing_in_linkml",
                            severity="blocking",
                            message=f"JSON property '{prop_name}' has no LinkML slot definition.",
                            file=linkml_class.file,
                            ontology=node.ontology,
                            node=node.node_id,
                            property=prop_name,
                        )
                    )
                continue
            json_type = str(prop.get("type") or "")
            rng = slot_range(slot_def)
            if not is_type_compatible(json_type, rng, linkml["enums"], linkml["class_range_tokens"]):
                issues.append(
                    Issue(
                        code="property_type_mismatch",
                        severity="blocking",
                        message=f"JSON property '{node.node_id}.{prop_name}' type '{json_type}' is not compatible with LinkML range '{rng}'.",
                        file=linkml_class.file,
                        ontology=node.ontology,
                        node=node.node_id,
                        property=prop_name,
                        expected=json_type,
                        observed=rng,
                    )
                )

    for edge in json_edges:
        tokens = edge_tokens(edge, edge_aliases)
        found = bool(tokens & linkml["relation_tokens"])
        if not found:
            # Accept relation-like slots on the source class as a weaker representation.
            source_class = find_linkml_class(edge.source_node, linkml, concept_aliases)
            if source_class:
                target_key = normalize_concept(edge.target_node, concept_aliases)
                action_key = normalize_edge_label(edge.action, edge_aliases)
                label_key = normalize_edge_label(edge.label, edge_aliases)
                found = any(token in source_class.slots for token in {target_key, action_key, label_key})
        if active_checks.get("require_all_json_edges_in_linkml", True) and not found:
            issues.append(
                Issue(
                    code="edge_in_json_missing_in_linkml",
                    severity="blocking",
                    message=f"JSON edge '{edge.edge_id}' is not represented as a LinkML relation class or relation-like slot.",
                    file=edge.file,
                    ontology=edge.ontology,
                    edge=edge.edge_id,
                    expected=sorted(tokens),
                    observed=[],
                )
            )

    if active_checks.get("require_imports_match_manifest", True) and manifest:
        expected_imports = manifest_imports(manifest, ontology_aliases)
        json_imports = {item["ontology"]: set(item["imports"]) for item in json_meta}
        linkml_imports_by_file = {Path(item["file"]).stem: set(item["imports"]) for item in linkml["ontology_meta"]}
        for ontology, expected in expected_imports.items():
            observed_json = json_imports.get(ontology, set())
            if observed_json and observed_json != expected:
                issues.append(
                    Issue(
                        code="json_imports_do_not_match_manifest",
                        severity="blocking",
                        message=f"JSON ontology '{ontology}' imports do not match manifest imports.",
                        ontology=ontology,
                        expected=sorted(expected),
                        observed=sorted(observed_json),
                    )
                )
            observed_linkml = linkml_imports_by_file.get(ontology, set())
            if observed_linkml and observed_linkml != expected:
                issues.append(
                    Issue(
                        code="linkml_imports_do_not_match_manifest",
                        severity="blocking",
                        message=f"LinkML ontology '{ontology}' imports do not match manifest imports.",
                        ontology=ontology,
                        expected=sorted(expected),
                        observed=sorted(observed_linkml),
                    )
                )

    counts = Counter(issue.code for issue in issues)
    severity_counts = Counter(issue.severity for issue in issues)
    blocking = [asdict(issue) for issue in issues if issue.severity == "blocking"]
    warnings = [asdict(issue) for issue in issues if issue.severity == "warning"]

    return {
        "ok": not blocking,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workspace_id": config.get("workspace_id") or (manifest.get("workspace_id") if manifest else ""),
        "summary": {
            "json_nodes": len(json_nodes),
            "json_edges": len(json_edges),
            "json_properties": sum(len(node.properties) for node in json_nodes),
            "linkml_classes": len(linkml["classes_by_name"]),
            "linkml_slots": len(linkml["slots"]),
            "linkml_relation_tokens": len(linkml["relation_tokens"]),
            "blocking_count": len(blocking),
            "warning_count": len(warnings),
            "issue_counts": dict(sorted(counts.items())),
            "severity_counts": dict(sorted(severity_counts.items())),
        },
        "blocking": blocking,
        "warnings": warnings,
        "observed": {
            "json_ontologies": json_meta,
            "linkml_ontologies": linkml["ontology_meta"],
        },
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    lines = [
        f"# Ontology JSON vs LinkML validation",
        "",
        f"- ok: `{str(report['ok']).lower()}`",
        f"- workspace_id: `{report.get('workspace_id') or ''}`",
        f"- generated_at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
    ]
    for key in [
        "json_nodes",
        "json_edges",
        "json_properties",
        "linkml_classes",
        "linkml_slots",
        "linkml_relation_tokens",
        "blocking_count",
        "warning_count",
    ]:
        lines.append(f"- {key}: `{summary.get(key, 0)}`")
    lines.extend(["", "## Blocking Issues", ""])
    if report["blocking"]:
        for issue in report["blocking"][:100]:
            location = issue.get("node") or issue.get("edge") or issue.get("ontology") or issue.get("file")
            lines.append(f"- `{issue['code']}` {location}: {issue['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        for issue in report["warnings"][:100]:
            location = issue.get("node") or issue.get("edge") or issue.get("ontology") or issue.get("file")
            lines.append(f"- `{issue['code']}` {location}: {issue['message']}")
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate JSON ontology structures against LinkML.")
    parser.add_argument("--json-dir", default=DEFAULT_JSON_DIR, help="Directory containing ontology JSON files.")
    parser.add_argument("--linkml-dir", default=DEFAULT_LINKML_DIR, help="Directory containing LinkML YAML files.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path to ontology manifest JSON.")
    parser.add_argument("--config", help="Optional YAML config with aliases and check toggles.")
    parser.add_argument("--output", help="Write JSON report to this path.")
    parser.add_argument("--markdown-output", help="Write Markdown summary to this path.")
    parser.add_argument("--no-exit-code", action="store_true", help="Always exit 0, even when blocking issues exist.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config) if args.config else None)
    manifest = Path(args.manifest) if args.manifest else None
    if manifest and not manifest.exists():
        manifest = None
    report = validate(Path(args.json_dir), Path(args.linkml_dir), manifest, config)

    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    if args.markdown_output:
        write_markdown(report, Path(args.markdown_output))
    if args.no_exit_code:
        return 0
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
