#!/usr/bin/env python3
"""Analyze an OpenAPI spec and propose GhostCrab ontology artifacts.

OpenAPI describes technical API surfaces, not a business ontology. This script
therefore generates reviewable intermediate artifacts:

- a machine ontology JSON for the raw API layer;
- a mappingProfile YAML candidate for source-to-canonical binding rules;
- a Markdown report for human review.

It does not write to GhostCrab or MindBrain.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    YAML_IMPORT_ERROR = exc
else:
    YAML_IMPORT_ERROR = None


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def require_yaml() -> None:
    if yaml is None:
        raise RuntimeError(f"PyYAML is required: {YAML_IMPORT_ERROR}")


def slug(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = re.sub(r"[\s\-/.:{}()]+", "_", text)
    text = re.sub(r"[^0-9A-Za-z_]+", "", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_").lower()


def pascal_case(value: Any) -> str:
    parts = [part for part in slug(value).split("_") if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Unnamed"


def load_spec(path: Path) -> dict[str, Any]:
    require_yaml()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not an OpenAPI object")
    return data


def ref_name(ref: str) -> str:
    return str(ref or "").split("/")[-1]


def schema_ref(schema: Any) -> str:
    if not isinstance(schema, dict):
        return ""
    if schema.get("$ref"):
        return ref_name(str(schema["$ref"]))
    if schema.get("items"):
        return schema_ref(schema.get("items"))
    if schema.get("allOf"):
        return next((schema_ref(item) for item in schema["allOf"] if schema_ref(item)), "")
    if schema.get("oneOf"):
        return next((schema_ref(item) for item in schema["oneOf"] if schema_ref(item)), "")
    if schema.get("anyOf"):
        return next((schema_ref(item) for item in schema["anyOf"] if schema_ref(item)), "")
    return str(schema.get("type") or "")


def schema_type(schema: Any) -> str:
    if not isinstance(schema, dict):
        return "string"
    if schema.get("$ref"):
        return "reference"
    if schema.get("enum"):
        return "enum"
    if schema.get("items"):
        return "array"
    if schema.get("allOf") or schema.get("oneOf") or schema.get("anyOf"):
        return "object"
    return str(schema.get("type") or "object")


def first_response_schema(operation: dict[str, Any]) -> str:
    responses = operation.get("responses") or {}
    for code in sorted(responses.keys(), key=lambda item: (str(item) == "default", str(item))):
        response = responses.get(code) or {}
        if response.get("$ref"):
            return ref_name(str(response["$ref"]))
        content = response.get("content") or {}
        for media in content.values():
            if isinstance(media, dict):
                found = schema_ref(media.get("schema"))
                if found:
                    return found
    return ""


def request_schema(operation: dict[str, Any]) -> str:
    body = operation.get("requestBody") or {}
    if body.get("$ref"):
        return ref_name(str(body["$ref"]))
    content = body.get("content") or {}
    for media in content.values():
        if isinstance(media, dict):
            found = schema_ref(media.get("schema"))
            if found:
                return found
    return ""


def operation_family(path: str, operation: dict[str, Any]) -> str:
    tags = operation.get("tags") or []
    if tags:
        return slug(tags[0])
    cleaned = path.strip("/").split("/", 1)[0]
    cleaned = re.sub(r"\{.*?\}", "", cleaned)
    return slug(cleaned or "root")


def operation_effect(method: str, operation: dict[str, Any]) -> str:
    op_kind = slug(operation.get("x-ms-docs-operation-type") or "")
    operation_id = slug(operation.get("operationId") or "")
    if op_kind in {"action", "function"}:
        return op_kind
    if method == "get":
        return "read"
    if method == "delete":
        return "delete"
    if method in {"put", "patch"}:
        return "update"
    if method == "post":
        if any(token in operation_id for token in ["create", "post", "add"]):
            return "create"
        if any(token in operation_id for token in ["delete", "remove", "purge"]):
            return "delete"
        return "action"
    return "other"


def sync_role(path: str, method: str, operation: dict[str, Any], effect: str) -> str:
    text = " ".join([path, str(operation.get("operationId") or ""), str(operation.get("summary") or "")]).lower()
    if method != "get":
        return "mutation_source"
    if any(token in text for token in ["active", "live", "status"]):
        return "live_snapshot"
    if any(token in text for token in ["log", "audit", "history", "cdr"]):
        return "audit_source"
    if "report" in text:
        return "report_source"
    if any(token in text for token in ["config", "setting", "policy", "shield"]):
        return "config_snapshot"
    if effect == "read":
        return "snapshot_source"
    return "enrichment_source"


def risk_level(path: str, method: str, operation: dict[str, Any], effect: str) -> str:
    text = " ".join([path, str(operation.get("operationId") or ""), str(operation.get("summary") or "")]).lower()
    if effect == "delete" or any(token in text for token in ["purge", "remove", "revoke"]):
        return "critical"
    if any(token in text for token in ["auth", "token", "shield", "policy", "permission", "collaboration", "external"]):
        return "high"
    if method in {"post", "put", "patch"}:
        return "medium"
    return "low"


def parameter_rows(operation: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for parameter in operation.get("parameters") or []:
        if not isinstance(parameter, dict):
            continue
        if parameter.get("$ref"):
            rows.append({"name": ref_name(str(parameter["$ref"])), "location": "ref", "required": False, "type": "reference"})
            continue
        schema = parameter.get("schema") or {}
        rows.append(
            {
                "name": str(parameter.get("name") or ""),
                "location": str(parameter.get("in") or ""),
                "required": bool(parameter.get("required")),
                "type": schema_type(schema),
                "schema_ref": schema_ref(schema),
                "description": str(parameter.get("description") or ""),
            }
        )
    return rows


def extract_schemas(spec: dict[str, Any]) -> list[dict[str, Any]]:
    schemas = spec.get("components", {}).get("schemas", {}) or {}
    rows = []
    for name, schema in sorted(schemas.items()):
        if not isinstance(schema, dict):
            schema = {}
        properties = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        fields = []
        for prop_name, prop_schema in sorted(properties.items()):
            if not isinstance(prop_schema, dict):
                prop_schema = {}
            fields.append(
                {
                    "name": prop_name,
                    "type": schema_type(prop_schema),
                    "range": schema_ref(prop_schema),
                    "required": prop_name in required,
                    "description": str(prop_schema.get("description") or ""),
                    "enum": prop_schema.get("enum") if isinstance(prop_schema.get("enum"), list) else [],
                }
            )
        rows.append(
            {
                "name": name,
                "type": schema_type(schema),
                "description": str(schema.get("description") or schema.get("title") or ""),
                "field_count": len(fields),
                "fields": fields,
            }
        )
    return rows


def extract_operations(spec: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for path, path_item in sorted((spec.get("paths") or {}).items()):
        if not isinstance(path_item, dict):
            continue
        for method, operation in sorted(path_item.items()):
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            method = method.lower()
            effect = operation_effect(method, operation)
            family = operation_family(path, operation)
            rows.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": str(operation.get("operationId") or f"{method}_{slug(path)}"),
                    "summary": str(operation.get("summary") or ""),
                    "description": str(operation.get("description") or ""),
                    "tags": operation.get("tags") or [],
                    "family": family,
                    "effect": effect,
                    "sync_role": sync_role(path, method, operation, effect),
                    "risk_level": risk_level(path, method, operation, effect),
                    "parameters": parameter_rows(operation),
                    "request_schema": request_schema(operation),
                    "response_schema": first_response_schema(operation),
                }
            )
    return rows


def property_value(name: str, value: Any, value_type: str = "text") -> dict[str, Any]:
    return {"name": name, "label": name.replace("_", " "), "value": value, "type": value_type, "targets": []}


def build_ontology_json(spec: dict[str, Any], service_id: str, service_label: str, source_path: Path, operations: list[dict[str, Any]], schemas: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [
        {
            "id": f"{service_id}_api_spec",
            "label": f"{service_label} API spec",
            "module": "mapping-profile",
            "kind": "api_spec",
            "description": spec.get("info", {}).get("description") or "",
            "properties": [
                property_value("service_id", service_id),
                property_value("title", spec.get("info", {}).get("title") or service_label),
                property_value("version", spec.get("info", {}).get("version") or ""),
                property_value("source_file", str(source_path)),
                property_value("openapi_version", spec.get("openapi") or spec.get("swagger") or ""),
            ],
            "source": str(source_path),
        }
    ]
    edges: list[dict[str, Any]] = []

    family_counts = Counter(op["family"] for op in operations)
    for family, count in sorted(family_counts.items()):
        node_id = f"{service_id}_family_{family}"
        nodes.append(
            {
                "id": node_id,
                "label": f"{service_label} {family}",
                "module": "mapping-profile",
                "kind": "api_family",
                "description": f"OpenAPI family inferred from tags/path: {family}",
                "properties": [property_value("family", family), property_value("operation_count", count, "integer")],
                "source": str(source_path),
            }
        )
        edges.append(
            {
                "id": f"{service_id}_api_spec__exposes_family__{family}",
                "module": "mapping-profile",
                "from": f"{service_id}_api_spec",
                "action": "exposes_family",
                "label": "exposes family",
                "to": node_id,
                "properties": [],
                "source": str(source_path),
            }
        )

    for op in operations:
        op_id = f"{service_id}_operation_{slug(op['operation_id'])}"
        nodes.append(
            {
                "id": op_id,
                "label": op["operation_id"],
                "module": "mapping-profile",
                "kind": "api_operation",
                "description": op["summary"] or op["description"],
                "properties": [
                    property_value("operation_id", op["operation_id"]),
                    property_value("path", op["path"]),
                    property_value("method", op["method"], "enum"),
                    property_value("family", op["family"], "enum"),
                    property_value("effect", op["effect"], "enum"),
                    property_value("sync_role", op["sync_role"], "enum"),
                    property_value("risk_level", op["risk_level"], "enum"),
                    property_value("request_schema", op["request_schema"]),
                    property_value("response_schema", op["response_schema"]),
                ],
                "source": str(source_path),
            }
        )
        edges.append(
            {
                "id": f"{service_id}_family_{op['family']}__has_operation__{slug(op['operation_id'])}",
                "module": "mapping-profile",
                "from": f"{service_id}_family_{op['family']}",
                "action": "has_operation",
                "label": "has operation",
                "to": op_id,
                "properties": [],
                "source": str(source_path),
            }
        )

    for schema in schemas:
        schema_id = f"{service_id}_schema_{slug(schema['name'])}"
        nodes.append(
            {
                "id": schema_id,
                "label": schema["name"],
                "module": "mapping-profile",
                "kind": "api_schema",
                "description": schema["description"],
                "properties": [
                    property_value("schema_name", schema["name"]),
                    property_value("schema_type", schema["type"], "enum"),
                    property_value("field_count", schema["field_count"], "integer"),
                ],
                "source": str(source_path),
            }
        )
    return {
        "metadata": {
            "workspace_id": "",
            "status": "provisional",
            "format": "json",
            "scope": "OpenAPI raw API ontology and mapping-profile candidates",
            "ontology_id": f"{service_id}::mapping-profile",
            "ontology_name": "mapping-profile",
            "description": f"Machine ontology candidates generated from {service_label} OpenAPI.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": str(source_path),
        },
        "nodes": nodes,
        "edges": edges,
    }


def mapping_confidence(op: dict[str, Any]) -> str:
    if op["risk_level"] in {"critical", "high"}:
        return "medium"
    if op["response_schema"] or op["request_schema"]:
        return "medium"
    return "low"


def build_mapping_profile(service_id: str, service_label: str, source_path: Path, operations: list[dict[str, Any]], schemas: list[dict[str, Any]]) -> dict[str, Any]:
    top_families = Counter(op["family"] for op in operations)
    families = []
    for family, count in top_families.most_common():
        effects = sorted({op["effect"] for op in operations if op["family"] == family})
        sync_roles = sorted({op["sync_role"] for op in operations if op["family"] == family})
        families.append({"id": family, "operation_count": count, "effects": effects, "sync_roles": sync_roles})

    resource_candidates = []
    for schema in schemas:
        if schema["field_count"] == 0:
            continue
        name = slug(schema["name"])
        key_fields = [
            field["name"]
            for field in schema["fields"]
            if slug(field["name"]) in {"id", "uuid", "guid", "file_id", "folder_id", "user_id", "template_id", "job_id", "batch_id", "call_id"}
            or slug(field["name"]).endswith("_id")
        ]
        resource_candidates.append(
            {
                "source_schema": schema["name"],
                "source_resource": name,
                "key_fields": key_fields[:8],
                "field_count": schema["field_count"],
                "mapping_status": "proposed",
                "target_domain_candidate": "mapping-profile",
                "target_entity_candidate": "",
                "confidence": "low",
            }
        )

    operation_bindings = []
    for op in operations:
        operation_bindings.append(
            {
                "operation_id": op["operation_id"],
                "method": op["method"],
                "path": op["path"],
                "family": op["family"],
                "effect": op["effect"],
                "sync_role": op["sync_role"],
                "risk_level": op["risk_level"],
                "request_schema": op["request_schema"],
                "response_schema": op["response_schema"],
                "target_process_candidate": "",
                "target_entity_candidate": "",
                "mapping_status": "proposed",
                "confidence": mapping_confidence(op),
            }
        )

    return {
        "mapping_profile_id": f"{service_id}:mapping-profile:openapi",
        "service_id": service_id,
        "service_label": service_label,
        "source_kind": "openapi",
        "source_file": str(source_path),
        "status": "proposed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "separation_principle": {
            "raw_api_layer": f"{service_label} technical resources stay close to OpenAPI.",
            "mapping_profile_layer": "Rules bind generic API resources to Serenity canonical ontologies.",
            "canonical_layer": "Serenity business ontologies remain the source of business meaning.",
        },
        "families": families,
        "resource_candidates": resource_candidates,
        "operation_bindings": operation_bindings,
        "review_gates": [
            "confirm_service_families",
            "select_sync_sources",
            "classify_mutation_risks",
            "map_source_schemas_to_serenity_entities",
            "define_key_resolution_rules",
            "define_confidence_and_human_review_policy",
        ],
    }


def write_markdown(path: Path, service_label: str, operations: list[dict[str, Any]], schemas: list[dict[str, Any]], profile: dict[str, Any]) -> None:
    family_counts = Counter(op["family"] for op in operations)
    effect_counts = Counter(op["effect"] for op in operations)
    risk_counts = Counter(op["risk_level"] for op in operations)
    lines = [
        f"# OpenAPI mappingProfile analysis - {service_label}",
        "",
        f"- generated_at: `{profile['generated_at']}`",
        f"- source_file: `{profile['source_file']}`",
        f"- operations: `{len(operations)}`",
        f"- schemas: `{len(schemas)}`",
        "",
        "## Families",
        "",
    ]
    for family, count in family_counts.most_common(30):
        lines.append(f"- `{family}`: {count} operation(s)")
    lines.extend(["", "## Effects", ""])
    for effect, count in sorted(effect_counts.items()):
        lines.append(f"- `{effect}`: {count}")
    lines.extend(["", "## Risk Levels", ""])
    for risk, count in sorted(risk_counts.items()):
        lines.append(f"- `{risk}`: {count}")
    lines.extend(["", "## Candidate Sync Sources", ""])
    for op in operations:
        if op["sync_role"] in {"live_snapshot", "audit_source", "report_source", "config_snapshot"}:
            lines.append(f"- `{op['operation_id']}` [{op['method']}] `{op['path']}` - {op['sync_role']} / {op['risk_level']}")
    lines.extend(["", "## Candidate Resources", ""])
    for schema in sorted(schemas, key=lambda item: item["field_count"], reverse=True)[:50]:
        lines.append(f"- `{schema['name']}`: {schema['field_count']} field(s)")
    lines.extend(["", "## Next Review Gates", ""])
    for gate in profile["review_gates"]:
        lines.append(f"- `{gate}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    source = Path(args.input)
    spec = load_spec(source)
    service_id = slug(args.service_id or spec.get("info", {}).get("title") or source.stem)
    service_label = args.service_label or spec.get("info", {}).get("title") or service_id
    output_dir = Path(args.output_dir)
    operations = extract_operations(spec)
    schemas = extract_schemas(spec)
    ontology = build_ontology_json(spec, service_id, service_label, source, operations, schemas)
    profile = build_mapping_profile(service_id, service_label, source, operations, schemas)

    output_dir.mkdir(parents=True, exist_ok=True)
    ontology_path = output_dir / f"{service_id}_openapi_ontology.json"
    profile_path = output_dir / f"{service_id}_mapping_profile.yaml"
    report_path = output_dir / f"{service_id}_openapi_analysis.md"
    summary_path = output_dir / f"{service_id}_openapi_summary.json"

    ontology_path.write_text(json.dumps(ontology, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require_yaml()
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), encoding="utf-8")
    write_markdown(report_path, service_label, operations, schemas, profile)

    summary = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "service_id": service_id,
        "service_label": service_label,
        "source": str(source),
        "operation_count": len(operations),
        "schema_count": len(schemas),
        "family_count": len({op["family"] for op in operations}),
        "outputs": {
            "ontology_json": str(ontology_path),
            "mapping_profile_yaml": str(profile_path),
            "markdown_report": str(report_path),
            "summary_json": str(summary_path),
        },
        "top_families": Counter(op["family"] for op in operations).most_common(20),
        "effect_counts": dict(sorted(Counter(op["effect"] for op in operations).items())),
        "risk_counts": dict(sorted(Counter(op["risk_level"] for op in operations).items())),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze OpenAPI and generate ontology/mappingProfile candidate artifacts.")
    parser.add_argument("--input", required=True, help="OpenAPI YAML or JSON file.")
    parser.add_argument("--service-id", help="Stable service id, e.g. box or threecx.")
    parser.add_argument("--service-label", help="Human label, e.g. Box or 3CX.")
    parser.add_argument("--output-dir", default="generated/openapi_mapping_profile", help="Output directory.")
    return parser.parse_args()


def main() -> int:
    try:
        summary = analyze(parse_args())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
