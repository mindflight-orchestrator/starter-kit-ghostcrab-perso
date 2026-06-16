#!/usr/bin/env python3
"""Generate GhostCrab MCP schema/facet activation payloads from LinkML.

The script is read-only against GhostCrab. It produces JSONL payloads that can
be reviewed, then applied with MCP tools:

- ghostcrab_schema_register for facet, graph_node, and graph_edge schemas
- ghostcrab_facet_register for enum business facets

It is meant to run after LinkML validation and before declaring an ontology
workspace ready for imports or agent queries.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
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


DEFAULT_LINKML_DIR = "generated/linkml_from_json"
DEFAULT_OUTPUT_DIR = "generated/ghostcrab_schema_activation"
DEFAULT_SKIP_MODULES = {"linkml_import"}


def require_yaml() -> None:
    if yaml is None:
        raise RuntimeError(f"PyYAML is required to read LinkML YAML: {YAML_IMPORT_ERROR}")


def slug(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("'", "")
    text = re.sub(r"[\s\-/]+", "_", text)
    text = re.sub(r"[^0-9A-Za-z_]+", "", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_").lower()


def workspace_slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^0-9a-z-]+", "", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def split_modules(values: list[str] | None) -> list[str]:
    if not values:
        return []
    modules: list[str] = []
    for value in values:
        for part in str(value).split(","):
            normalized = slug(part)
            if normalized and normalized not in modules:
                modules.append(normalized)
    return modules


def load_yaml_file(path: Path) -> dict[str, Any]:
    require_yaml()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def annotation_value(annotations: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in annotations:
        return annotations[key]
    # LinkML can serialize annotation values either directly or as objects.
    nested = annotations.get(key.replace(".", "_"))
    if isinstance(nested, dict) and "value" in nested:
        return nested["value"]
    return nested if nested is not None else default


def permissible_values(enum_def: dict[str, Any]) -> list[str]:
    raw = enum_def.get("permissible_values") or {}
    if isinstance(raw, dict):
        return [str(key) for key in raw.keys()]
    if isinstance(raw, list):
        values: list[str] = []
        for item in raw:
            if isinstance(item, dict):
                value = item.get("text") or item.get("name") or item.get("value")
            else:
                value = item
            if value is not None:
                values.append(str(value))
        return values
    return []


def module_files(linkml_dir: Path, modules: list[str], include_entrypoints: bool) -> list[Path]:
    if modules:
        files = []
        for module in modules:
            path = linkml_dir / f"{module}.yaml"
            if not path.exists():
                raise FileNotFoundError(f"LinkML module not found: {path}")
            files.append(path)
        return files

    files = sorted(linkml_dir.glob("*.yaml"))
    if include_entrypoints:
        return files
    return [path for path in files if slug(path.stem) not in DEFAULT_SKIP_MODULES]


@dataclass
class ModuleActivation:
    module: str
    source: Path
    facet_keys: list[str]
    enum_facets: dict[str, list[str]]
    slot_ranges: dict[str, str]
    entity_payloads: list[dict[str, Any]]
    edge_payloads: list[dict[str, Any]]


def build_module_activation(
    path: Path,
    workspace_id: str,
    schema_prefix: str,
    enum_only: bool,
) -> ModuleActivation:
    module = slug(path.stem)
    data = load_yaml_file(path)
    slots = data.get("slots") or {}
    enums = data.get("enums") or {}
    classes = data.get("classes") or {}

    if not isinstance(slots, dict):
        slots = {}
    if not isinstance(enums, dict):
        enums = {}
    if not isinstance(classes, dict):
        classes = {}

    enum_names = set(enums.keys())
    slot_ranges: dict[str, str] = {}
    enum_facets: dict[str, list[str]] = {}
    all_facet_keys: list[str] = []

    for slot_name in sorted(slots.keys()):
        slot_def = slots.get(slot_name) or {}
        if not isinstance(slot_def, dict):
            continue
        slot_key = slug(slot_name)
        slot_range = str(slot_def.get("range") or data.get("default_range") or "string")
        facet_name = f"{module}.{slot_key}"
        slot_ranges[facet_name] = slot_range
        if slot_range in enum_names:
            enum_def = enums.get(slot_range) or {}
            values = permissible_values(enum_def if isinstance(enum_def, dict) else {})
            enum_facets[facet_name] = values
        if not enum_only or slot_range in enum_names:
            all_facet_keys.append(facet_name)

    entity_payloads: list[dict[str, Any]] = []
    edge_payloads: list[dict[str, Any]] = []
    for class_name in sorted(classes.keys()):
        class_def = classes.get(class_name) or {}
        if not isinstance(class_def, dict):
            continue
        annotations = class_def.get("annotations") or {}
        if not isinstance(annotations, dict):
            annotations = {}

        native_entity_type = annotation_value(annotations, "ghostcrab.native_entity_type")
        native_edge_type = annotation_value(annotations, "ghostcrab.native_edge_type")
        class_slots = class_def.get("slots") or []
        if not isinstance(class_slots, list):
            class_slots = []

        if native_entity_type:
            node_type = slug(native_entity_type)
            entity_payloads.append(
                {
                    "tool": "ghostcrab_schema_register",
                    "arguments": {
                        "workspace_id": workspace_id,
                        "target": "graph_node",
                        "definition": {
                            "schema_id": f"{schema_prefix}:{module}:{node_type}",
                            "description": f"GhostCrab graph node schema generated from LinkML class {class_name}.",
                            "version": 1,
                            "label": class_def.get("title") or class_name,
                            "node_type": node_type,
                            "module": module,
                            "source_linkml": str(path),
                            "source_ontology": f"{workspace_id}::{module}",
                            "linkml_class": class_name,
                            "slots": [slug(item) for item in class_slots],
                            "annotations": annotations,
                        },
                    },
                }
            )

        if truthy(native_edge_type):
            edge_label = slug(annotation_value(annotations, "ghostcrab.native_edge_label", class_name))
            edge_payloads.append(
                {
                    "tool": "ghostcrab_schema_register",
                    "arguments": {
                        "workspace_id": workspace_id,
                        "target": "graph_edge",
                        "definition": {
                            "schema_id": f"{schema_prefix}:{module}:edge:{slug(class_name)}",
                            "description": f"GhostCrab graph edge schema generated from LinkML class {class_name}.",
                            "version": 1,
                            "label": class_def.get("title") or edge_label,
                            "edge_label": edge_label,
                            "module": module,
                            "source_linkml": str(path),
                            "source_ontology": f"{workspace_id}::{module}",
                            "linkml_class": class_name,
                            "source_entity_type": annotation_value(annotations, "ghostcrab.source_entity_type"),
                            "target_entity_type": annotation_value(annotations, "ghostcrab.target_entity_type"),
                            "slots": [slug(item) for item in class_slots],
                            "annotations": annotations,
                        },
                    },
                }
            )

    return ModuleActivation(
        module=module,
        source=path,
        facet_keys=sorted(dict.fromkeys(all_facet_keys)),
        enum_facets={key: enum_facets[key] for key in sorted(enum_facets.keys())},
        slot_ranges={key: slot_ranges[key] for key in sorted(slot_ranges.keys())},
        entity_payloads=entity_payloads,
        edge_payloads=edge_payloads,
    )


def facet_schema_payload(activation: ModuleActivation, workspace_id: str, schema_prefix: str) -> dict[str, Any]:
    return {
        "tool": "ghostcrab_schema_register",
        "arguments": {
            "workspace_id": workspace_id,
            "target": "facets",
            "definition": {
                "schema_id": f"{schema_prefix}:{activation.module}",
                "description": f"GhostCrab facet schema generated from LinkML module {activation.module}.",
                "version": 1,
                "module": activation.module,
                "source_linkml": str(activation.source),
                "source_ontology": f"{workspace_id}::{activation.module}",
                "facet_keys": activation.facet_keys,
                "enum_facets": activation.enum_facets,
                "slot_ranges": activation.slot_ranges,
                "class_count": len(activation.entity_payloads) + len(activation.edge_payloads),
                "enum_facet_count": len(activation.enum_facets),
            },
        },
    }


def facet_register_payloads(activation: ModuleActivation, workspace_id: str) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for facet_name, values in activation.enum_facets.items():
        slot_range = activation.slot_ranges.get(facet_name)
        payloads.append(
            {
                "tool": "ghostcrab_facet_register",
                "arguments": {
                    "workspace_id": workspace_id,
                    "definition": {
                        "facet_name": facet_name,
                        "label": facet_name,
                        "description": (
                            f"Enum business facet generated from LinkML range {slot_range}. "
                            f"Allowed values: {', '.join(values[:12])}"
                            + ("..." if len(values) > 12 else "")
                        ),
                        "native": False,
                        "native_column": None,
                        "native_kind": "plain",
                    },
                },
            }
        )
    return payloads


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_plan(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# GhostCrab schema activation plan",
        "",
        f"Workspace: `{summary['workspace_id']}`",
        f"Generated at: `{summary['generated_at']}`",
        "",
        "This plan does not call MCP. Review the JSONL payloads, then apply them with the GhostCrab MCP tools.",
        "",
        "## Definition of done",
        "",
        "1. Native LinkML ontologies are imported.",
        "2. Facet schemas are registered with `ghostcrab_schema_register`.",
        "3. Enum facets are registered with `ghostcrab_facet_register`.",
        "4. Read tests pass with `ghostcrab_schema_list`, `ghostcrab_facet_inspect`, and a small `ghostcrab_search` / `ghostcrab_pack` smoke test once data exists.",
        "",
        "## Generated files",
        "",
        f"- `{summary['files']['schema_register_payloads']}`",
        f"- `{summary['files']['facet_register_payloads']}`",
        f"- `{summary['files']['summary']}`",
        "",
        "## Modules",
        "",
        "| Module | Facet keys | Enum facets | Graph nodes | Graph edges |",
        "|--------|------------|-------------|-------------|-------------|",
    ]
    for module in summary["modules"]:
        lines.append(
            f"| `{module['module']}` | {module['facet_key_count']} | {module['enum_facet_count']} | "
            f"{module['graph_node_schema_count']} | {module['graph_edge_schema_count']} |"
        )
    lines.extend(
        [
            "",
            "## Apply order",
            "",
            "Apply `schema_register_payloads.jsonl` first, then `facet_register_payloads.jsonl`.",
            "Do not mark the workspace ready after ontology import alone.",
            "",
            "## Verification",
            "",
            "Use MCP reads after applying the payloads:",
            "",
            "```text",
            'ghostcrab_schema_list(domain="<workspace_id>", target="facets")',
            'ghostcrab_facet_inspect(facet_name="<module>.<slot>")',
            "ghostcrab_coverage(domain=\"<workspace_id>\")",
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--linkml-dir", default=DEFAULT_LINKML_DIR, help="Directory containing LinkML .yaml modules")
    parser.add_argument("--workspace-id", required=True, help="GhostCrab workspace id")
    parser.add_argument("--schema-prefix", default=None, help="Schema id prefix; defaults to --workspace-id")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory for generated activation payloads")
    parser.add_argument("--modules", nargs="*", help="Optional module list, comma-separated or space-separated")
    parser.add_argument("--include-entrypoints", action="store_true", help="Include technical entrypoints such as linkml_import.yaml")
    parser.add_argument("--enum-only", action="store_true", help="Facet schema includes only enum slots instead of all slots")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    linkml_dir = Path(args.linkml_dir)
    output_dir = Path(args.output_dir)
    workspace_id = workspace_slug(args.workspace_id)
    schema_prefix = workspace_slug(args.schema_prefix or workspace_id)
    modules = split_modules(args.modules)

    if not workspace_id:
        raise SystemExit("--workspace-id must normalize to a non-empty slug")
    if not linkml_dir.exists():
        raise SystemExit(f"LinkML directory not found: {linkml_dir}")

    files = module_files(linkml_dir, modules, args.include_entrypoints)
    if not files:
        raise SystemExit(f"No LinkML .yaml modules found in {linkml_dir}")

    activations = [
        build_module_activation(path, workspace_id=workspace_id, schema_prefix=schema_prefix, enum_only=args.enum_only)
        for path in files
    ]

    schema_payloads: list[dict[str, Any]] = []
    facet_payloads: list[dict[str, Any]] = []
    for activation in activations:
        schema_payloads.append(facet_schema_payload(activation, workspace_id, schema_prefix))
        schema_payloads.extend(activation.entity_payloads)
        schema_payloads.extend(activation.edge_payloads)
        facet_payloads.extend(facet_register_payloads(activation, workspace_id))

    schema_path = output_dir / "schema_register_payloads.jsonl"
    facet_path = output_dir / "facet_register_payloads.jsonl"
    summary_path = output_dir / "summary.json"
    plan_path = output_dir / "activation_plan.md"

    write_jsonl(schema_path, schema_payloads)
    write_jsonl(facet_path, facet_payloads)

    generated_at = datetime.now(timezone.utc).isoformat()
    module_summary = []
    for activation in activations:
        module_summary.append(
            {
                "module": activation.module,
                "source_linkml": str(activation.source),
                "facet_key_count": len(activation.facet_keys),
                "enum_facet_count": len(activation.enum_facets),
                "graph_node_schema_count": len(activation.entity_payloads),
                "graph_edge_schema_count": len(activation.edge_payloads),
            }
        )

    summary = {
        "ok": True,
        "workspace_id": workspace_id,
        "schema_prefix": schema_prefix,
        "generated_at": generated_at,
        "linkml_dir": str(linkml_dir),
        "output_dir": str(output_dir),
        "schema_register_payload_count": len(schema_payloads),
        "facet_register_payload_count": len(facet_payloads),
        "modules": module_summary,
        "files": {
            "schema_register_payloads": str(schema_path),
            "facet_register_payloads": str(facet_path),
            "summary": str(summary_path),
            "activation_plan": str(plan_path),
        },
    }
    write_json(summary_path, summary)
    write_plan(plan_path, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
