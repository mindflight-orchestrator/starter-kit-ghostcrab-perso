#!/usr/bin/env python3
"""Generate LinkML YAML modules from GhostCrab ontology JSON artifacts.

This script treats the JSON ontology files as the source of truth and writes a
LinkML module per JSON ontology. It is intentionally deterministic and does not
overwrite existing files unless --force is passed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
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


DEFAULT_JSON_DIR = "ontology"
DEFAULT_MANIFEST = "ontology/manifest.json"
DEFAULT_OUTPUT_DIR = "generated/linkml_from_json"


def require_yaml() -> None:
    if yaml is None:
        raise RuntimeError(f"PyYAML is required to generate LinkML YAML: {YAML_IMPORT_ERROR}")


def slug(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("'", "")
    text = re.sub(r"[\s\-/]+", "_", text)
    text = re.sub(r"[^0-9A-Za-z_]+", "", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_").lower()


def ascii_slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    return slug(text)


def pascal_case(value: Any) -> str:
    parts = [part for part in re.split(r"[_\W]+", ascii_slug(value)) if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Unnamed"


def load_yaml_file(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    require_yaml()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def load_config(path: Path | None) -> dict[str, Any]:
    loaded = load_yaml_file(path)
    aliases = loaded.get("aliases") or {}
    return {
        "workspace_id": loaded.get("workspace_id") or "",
        "aliases": {
            "ontology": aliases.get("ontology") or {},
            "concepts": aliases.get("concepts") or {},
            "properties": aliases.get("properties") or {},
            "edges": aliases.get("edges") or {},
        },
    }


def alias_map(config: dict[str, Any], family: str) -> dict[str, str]:
    raw = ((config.get("aliases") or {}).get(family) or {})
    return {slug(k): slug(v) for k, v in raw.items()}


def normalize_with_alias(value: Any, aliases: dict[str, str]) -> str:
    key = slug(value)
    return slug(aliases.get(key, key))


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
                candidate = json_dir / candidate.name
            if candidate.exists() and candidate.suffix == ".json":
                paths.append(candidate)
        if paths:
            return sorted(dict.fromkeys(paths))
    return sorted(
        p
        for p in json_dir.glob("*.json")
        if p.name not in {"manifest.json", "serenity_p3_ontology.json"}
    )


def enum_name_for_slot(slot_name: str) -> str:
    return f"{pascal_case(slot_name)}Enum"


def enum_values_from_property(prop: dict[str, Any]) -> list[str]:
    values = prop.get("values")
    if isinstance(values, list):
        raw_values = values
    else:
        raw = str(prop.get("value") or "")
        raw_values = re.split(r"\s*/\s*|\s*;\s*|\s*,\s*", raw) if raw else []
    normalized: list[str] = []
    for item in raw_values:
        value = ascii_slug(item)
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def reference_target_from_property(prop: dict[str, Any]) -> str:
    targets = prop.get("targets")
    if isinstance(targets, list) and targets:
        return pascal_case(targets[0])
    value = str(prop.get("value") or "")
    match = re.search(r"r[ée]f[ée]rence\s+([A-Za-zÀ-ÿ0-9_ -]+)", value, flags=re.IGNORECASE)
    if match:
        return pascal_case(match.group(1).strip())
    return "string"


def infer_slot(prop: dict[str, Any], known_class_names: set[str] | None = None) -> dict[str, Any]:
    known_class_names = known_class_names or set()
    json_type = slug(prop.get("type") or "")
    name = slug(prop.get("name") or "")
    slot: dict[str, Any] = {}
    label = str(prop.get("label") or "").strip()
    description = str(prop.get("value") or "").strip()
    source = str(prop.get("source") or "").strip()
    if label and label != name:
        slot["title"] = label
    if description:
        slot["description"] = description
    if json_type == "enum":
        slot["range"] = enum_name_for_slot(name)
    elif json_type == "reference":
        target = reference_target_from_property(prop)
        slot["range"] = target if target in known_class_names else "string"
    elif json_type == "reference_list":
        target = reference_target_from_property(prop)
        slot["range"] = target if target in known_class_names else "string"
        slot["multivalued"] = True
    elif json_type in {"integer", "int"}:
        slot["range"] = "integer"
    elif json_type in {"decimal", "float", "number"}:
        slot["range"] = "decimal"
    elif json_type in {"boolean", "bool"}:
        slot["range"] = "boolean"
    elif json_type == "date":
        slot["range"] = "date"
    elif json_type == "datetime":
        slot["range"] = "datetime"
    else:
        slot["range"] = "string"
    if source:
        slot["annotations"] = {"source": source}
    return slot


def merge_slot(existing: dict[str, Any], incoming: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    if not existing:
        return dict(incoming), None
    conflict = None
    if existing.get("range") != incoming.get("range"):
        conflict = f"range conflict: {existing.get('range')} vs {incoming.get('range')}"
    merged = dict(existing)
    if conflict:
        # A LinkML slot has one global range. When the same JSON property name is
        # used with different meanings, keep the generated schema permissive and
        # surface the conflict in the report for later human modeling.
        merged["range"] = "string"
    if incoming.get("description") and not merged.get("description"):
        merged["description"] = incoming["description"]
    if incoming.get("title") and not merged.get("title"):
        merged["title"] = incoming["title"]
    if incoming.get("multivalued"):
        merged["multivalued"] = True
    return merged, conflict


def build_module(
    data: dict[str, Any],
    manifest_item: dict[str, Any] | None,
    config: dict[str, Any],
    base_class: str,
    base_module: str,
    known_class_names: set[str],
) -> tuple[str, dict[str, Any], list[str]]:
    ontology_aliases = alias_map(config, "ontology")
    property_aliases = alias_map(config, "properties")
    edge_aliases = alias_map(config, "edges")
    meta = data.get("metadata") or {}
    source_ontology = meta.get("ontology_name") or (manifest_item or {}).get("name") or "ontology"
    ontology = normalize_with_alias(source_ontology, ontology_aliases)
    workspace_id = config.get("workspace_id") or meta.get("workspace_id") or (manifest_item or {}).get("ontology_id", "").split("::")[0]
    workspace_slug = slug(workspace_id or "ghostcrab")

    imports = ["linkml:types"]
    raw_imports = (manifest_item or {}).get("imports") or meta.get("imports") or []
    for item in raw_imports:
        imported = normalize_with_alias(str(item).split("::")[-1], ontology_aliases)
        if imported and imported not in imports:
            imports.append(imported)
    if ontology != base_module and base_module not in imports:
        imports.append(base_module)

    schema: dict[str, Any] = {
        "id": f"https://example.org/ontology/{workspace_slug}/{ontology}",
        "name": f"{workspace_slug.replace('-', '_')}_{ontology}",
        "title": f"{workspace_id or workspace_slug} {ontology} ontology",
        "description": meta.get("description") or (manifest_item or {}).get("description") or "",
        "license": "https://ghostcrab.be/Licence.md",
        "version": "0.1.0",
        "prefixes": {
            "linkml": "https://w3id.org/linkml/",
            "ghostcrab": "https://ghostcrab.be/ontology/",
            "serenity": f"https://example.org/ontology/{workspace_slug}/",
        },
        "imports": imports,
        "default_prefix": "serenity",
        "default_range": "string",
        "enums": {},
        "classes": {},
        "slots": {},
    }

    warnings: list[str] = []
    enum_values: dict[str, set[str]] = defaultdict(set)

    if ontology == base_module:
        schema["classes"][base_class] = {
            "abstract": True,
            "description": "Common identity and provenance contract for generated domain entities.",
            "slots": ["identifiant", "source_document", "notes_metier"],
        }
        schema["slots"]["source_document"] = {"range": "string"}
        schema["slots"]["notes_metier"] = {"range": "string"}

    for node in data.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id") or "")
        class_name = pascal_case(node_id)
        class_slots: list[str] = []
        for prop in node.get("properties") or []:
            if not isinstance(prop, dict):
                continue
            slot_name = normalize_with_alias(prop.get("name") or "", property_aliases)
            if not slot_name:
                continue
            class_slots.append(slot_name)
            slot_def = infer_slot({**prop, "name": slot_name}, known_class_names)
            merged, conflict = merge_slot(schema["slots"].get(slot_name) or {}, slot_def)
            if conflict:
                warnings.append(f"{ontology}.{slot_name}: {conflict}")
            schema["slots"][slot_name] = merged
            if slug(prop.get("type") or "") == "enum":
                enum_values[enum_name_for_slot(slot_name)].update(enum_values_from_property(prop))

        class_def: dict[str, Any] = {
            "is_a": base_class,
            "title": str(node.get("label") or node_id.replace("_", " ").title()),
            "slots": class_slots,
            "annotations": {
                "ghostcrab.native_entity_type": node_id,
                "ghostcrab.schema_family": f"{workspace_slug}:{ontology}",
            },
        }
        if node.get("source"):
            class_def["annotations"]["source"] = str(node.get("source"))
        schema["classes"][class_name] = class_def

    if data.get("edges") or data.get("relations"):
        schema["slots"].setdefault("source_entity", {"range": "string"})
        schema["slots"].setdefault("target_entity", {"range": "string"})

    for edge in (data.get("edges") or data.get("relations") or []):
        if not isinstance(edge, dict):
            continue
        edge_id = str(edge.get("id") or "")
        class_name = pascal_case(edge_id or f"{edge.get('from')}_{edge.get('action')}_{edge.get('to')}_relation")
        edge_slots = ["source_entity", "target_entity"]
        for prop in edge.get("properties") or []:
            if not isinstance(prop, dict):
                continue
            slot_name = normalize_with_alias(prop.get("name") or "", property_aliases)
            if not slot_name:
                continue
            edge_slots.append(slot_name)
            slot_def = infer_slot({**prop, "name": slot_name}, known_class_names)
            merged, conflict = merge_slot(schema["slots"].get(slot_name) or {}, slot_def)
            if conflict:
                warnings.append(f"{ontology}.{slot_name}: {conflict}")
            schema["slots"][slot_name] = merged
            if slug(prop.get("type") or "") == "enum":
                enum_values[enum_name_for_slot(slot_name)].update(enum_values_from_property(prop))

        native_edge_label = normalize_with_alias(edge.get("action") or edge.get("label") or edge_id, edge_aliases)
        relation_def: dict[str, Any] = {
            "is_a": base_class,
            "title": str(edge.get("label") or edge.get("action") or edge_id),
            "slots": edge_slots,
            "annotations": {
                "ghostcrab.native_edge_type": True,
                "ghostcrab.native_edge_label": native_edge_label,
                "ghostcrab.source_entity_type": str(edge.get("from") or ""),
                "ghostcrab.target_entity_type": str(edge.get("to") or ""),
                "ghostcrab.schema_family": f"{workspace_slug}:{ontology}",
            },
        }
        if edge.get("source"):
            relation_def["annotations"]["source"] = str(edge.get("source"))
        schema["classes"][class_name] = relation_def

    for enum_name, values in sorted(enum_values.items()):
        schema["enums"][enum_name] = {
            "permissible_values": {value: {} for value in sorted(values)}
        }
    if not schema["enums"]:
        schema.pop("enums")

    return ontology, schema, warnings


def manifest_items_by_ontology(manifest: dict[str, Any], config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ontology_aliases = alias_map(config, "ontology")
    result: dict[str, dict[str, Any]] = {}
    for item in manifest.get("ontologies") or []:
        if not isinstance(item, dict):
            continue
        name = normalize_with_alias(item.get("name") or str(item.get("ontology_id") or "").split("::")[-1], ontology_aliases)
        result[name] = item
    return result


def write_yaml(path: Path, data: dict[str, Any], force: bool) -> None:
    require_yaml()
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    path.write_text(rendered, encoding="utf-8")


def generate(args: argparse.Namespace) -> dict[str, Any]:
    require_yaml()
    json_dir = Path(args.json_dir)
    manifest_path = Path(args.manifest) if args.manifest else None
    manifest = load_manifest(manifest_path)
    config = load_config(Path(args.config) if args.config else None)
    output_dir = Path(args.output_dir)
    files = json_ontology_files(json_dir, manifest)
    manifest_by_ontology = manifest_items_by_ontology(manifest, config)
    ontology_aliases = alias_map(config, "ontology")

    loaded_files: list[tuple[Path, dict[str, Any]]] = []
    known_class_names: set[str] = set()
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        loaded_files.append((path, data))
        for node in data.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            if node.get("id"):
                known_class_names.add(pascal_case(node.get("id")))
            if node.get("label"):
                known_class_names.add(pascal_case(node.get("label")))

    generated: list[dict[str, Any]] = []
    warnings: list[str] = []
    module_names: list[str] = []

    for path, data in loaded_files:
        meta = data.get("metadata") or {}
        source_ontology = meta.get("ontology_name") or path.stem
        ontology = normalize_with_alias(source_ontology, ontology_aliases)
        module_names.append(ontology)
        manifest_item = manifest_by_ontology.get(ontology)
        ontology, schema, module_warnings = build_module(
            data,
            manifest_item,
            config,
            base_class=args.base_class,
            base_module=args.base_module,
            known_class_names=known_class_names,
        )
        target = output_dir / f"{ontology}.yaml"
        write_yaml(target, schema, args.force)
        generated.append(
            {
                "ontology": ontology,
                "source": str(path),
                "target": str(target),
                "classes": len(schema.get("classes") or {}),
                "slots": len(schema.get("slots") or {}),
                "enums": len(schema.get("enums") or {}),
            }
        )
        warnings.extend(module_warnings)

    if args.write_entrypoint:
        workspace_id = config.get("workspace_id") or manifest.get("workspace_id") or "ghostcrab"
        entrypoint = {
            "id": f"https://example.org/ontology/{slug(workspace_id)}/{args.entrypoint_name}",
            "name": f"{slug(workspace_id).replace('-', '_')}_{args.entrypoint_name}",
            "title": f"{workspace_id} LinkML import entrypoint",
            "description": "Technical LinkML bundle entrypoint generated from ontology JSON artifacts.",
            "imports": ["linkml:types", *module_names],
        }
        target = output_dir / f"{args.entrypoint_name}.yaml"
        write_yaml(target, entrypoint, args.force)
        generated.append(
            {
                "ontology": args.entrypoint_name,
                "source": "generated",
                "target": str(target),
                "classes": 0,
                "slots": 0,
                "enums": 0,
            }
        )

    report = {
        "ok": not warnings,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "json_dir": str(json_dir),
        "output_dir": str(output_dir),
        "generated": generated,
        "warnings": warnings,
    }
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate LinkML YAML files from ontology JSON artifacts.")
    parser.add_argument("--json-dir", default=DEFAULT_JSON_DIR, help="Directory containing ontology JSON files.")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="Path to ontology manifest JSON.")
    parser.add_argument("--config", help="Optional central contract YAML with aliases.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory where generated YAML files are written.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated YAML files.")
    parser.add_argument("--base-class", default="EntiteSerenity", help="Base class used for generated classes.")
    parser.add_argument("--base-module", default="production", help="Module that owns the base class.")
    parser.add_argument("--write-entrypoint", action="store_true", help="Also write a technical LinkML import entrypoint.")
    parser.add_argument("--entrypoint-name", default="linkml_import", help="Entrypoint YAML filename stem.")
    parser.add_argument("--report", help="Optional JSON generation report path.")
    return parser.parse_args()


def main() -> int:
    try:
        report = generate(parse_args())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
