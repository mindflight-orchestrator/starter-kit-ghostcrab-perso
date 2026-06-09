#!/usr/bin/env python3
"""Audit GhostCrab projections and graph quality.

The audit answers five questions:
- what Type A projections are declared in mb_pragma.projections / projections;
- what Type B projection results are materialized in graph.entity;
- which planned projections from a model contract are missing;
- whether projection content is parseable and active;
- whether graph edge types required by projections are populated;
- whether schemas/facets required by projections are represented in data.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB = "data/ghostcrab.sqlite"
DEFAULT_POSTGRES_DSN = "postgres://ghostcrab:ghostcrab@127.0.0.1:5434/ghostcrab"
DEFAULT_MINDCLI = "../mindbot/cmd/mindcli"


def parse_json_maybe(value: Any) -> tuple[bool, Any]:
    if value is None:
        return False, None
    if isinstance(value, (dict, list)):
        return True, value
    try:
        return True, json.loads(str(value))
    except Exception:
        return False, None


def dt_from_unix(value: int | None) -> str | None:
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def load_model_contract(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_planned_projections(model: dict[str, Any], workspace_id: str | None) -> list[dict[str, Any]]:
    if not model:
        return []
    workspace = workspace_id or model.get("workspace_id", "")
    projections = model.get("projections") or {}
    planned: list[dict[str, Any]] = []

    # Current contract shape: {"projection_name": {scope, required_edges, ...}}
    if isinstance(projections, dict):
        for name, value in projections.items():
            if isinstance(value, dict):
                scope = value.get("scope") or f"{workspace}:projection:{name}"
                planned.append(
                    {
                        "workspace_id": workspace,
                        "ontology": scope.split(":")[1] if scope.startswith(f"{workspace}:") and len(scope.split(":")) > 2 else "projection",
                        "name": name,
                        "expected_scope": scope,
                        "label": value.get("label", name),
                        "business_question": value.get("business_question", ""),
                        "required_schemas": value.get("required_schemas", []),
                        "required_facets": value.get("required_facets", []),
                        "required_edges": value.get("required_edges", []),
                    }
                )
            elif isinstance(value, list):
                # Legacy starterkit shape: {"ontology": ["projection_name"]}
                for item in value:
                    planned.append(
                        {
                            "workspace_id": workspace,
                            "ontology": name,
                            "name": str(item),
                            "expected_scope": f"{workspace}:{name}:{item}",
                            "label": str(item),
                            "business_question": "",
                            "required_schemas": [],
                            "required_facets": [],
                            "required_edges": [],
                        }
                    )
    return planned


def sqlite_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return list(conn.execute(sql, params))


def sqlite_table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def sqlite_table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not sqlite_table_exists(conn, table):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def sqlite_where_workspace(columns: set[str], workspace_id: str | None) -> tuple[str, tuple[Any, ...]]:
    if workspace_id and "workspace_id" in columns:
        return "WHERE workspace_id = ?", (workspace_id,)
    return "", ()


def fetch_sqlite(db_path: Path, workspace_id: str | None) -> dict[str, Any]:
    if not db_path.exists():
        return {"backend": "sqlite", "available": False, "error": f"SQLite database not found: {db_path}"}

    with sqlite3.connect(db_path) as conn:
        projection_types = []
        if sqlite_table_exists(conn, "projection_types"):
            projection_types = [
                dict(row)
                for row in sqlite_rows(
                    conn,
                    """
                    SELECT type_name, compatibility_aliases, rank_bias, pack_priority,
                           next_hop_multiplier, structured
                    FROM projection_types
                    ORDER BY pack_priority, type_name
                    """,
                )
            ]

        projection_rows = []
        if sqlite_table_exists(conn, "projections"):
            params: tuple[Any, ...] = ()
            where = ""
            if workspace_id:
                where = "WHERE scope = ? OR scope LIKE ?"
                params = (workspace_id, f"{workspace_id}:%")
            projection_rows = [
                {
                    "id": str(row["id"]),
                    "agent_id": row["agent_id"],
                    "scope": row["scope"],
                    "proj_type": row["proj_type"],
                    "content": row["content"],
                    "weight": row["weight"],
                    "source_ref": row["source_ref"],
                    "source_type": row["source_type"],
                    "status": row["status"],
                    "created_at": dt_from_unix(row["created_at_unix"]),
                    "expires_at": dt_from_unix(row["expires_at_unix"]),
                }
                for row in sqlite_rows(
                    conn,
                    f"""
                    SELECT id, agent_id, scope, proj_type, content, weight, source_ref,
                           source_type, status, created_at_unix, expires_at_unix
                    FROM projections
                    {where}
                    ORDER BY created_at_unix DESC, scope, proj_type
                    """,
                    params,
                )
            ]

        schema_counts: Counter[str] = Counter()
        facet_keys: set[str] = set()
        if sqlite_table_exists(conn, "facets"):
            columns = sqlite_table_columns(conn, "facets")
            where, params = sqlite_where_workspace(columns, workspace_id)
            for row in sqlite_rows(conn, f"SELECT schema_id, facets FROM facets {where}", params):
                schema_counts[row["schema_id"]] += 1
                ok, facets = parse_json_maybe(row["facets"])
                if ok and isinstance(facets, dict):
                    facet_keys.update(facets)
        if sqlite_table_exists(conn, "agent_facts"):
            columns = sqlite_table_columns(conn, "agent_facts")
            schema_col = "schema_id" if "schema_id" in columns else None
            facets_col = "facets" if "facets" in columns else "facets_json" if "facets_json" in columns else None
            where, params = sqlite_where_workspace(columns, workspace_id)
            select_schema = schema_col or "NULL"
            select_facets = facets_col or "NULL"
            for row in sqlite_rows(conn, f"SELECT {select_schema} AS schema_id, {select_facets} AS facets FROM agent_facts {where}", params):
                if row["schema_id"]:
                    schema_counts[row["schema_id"]] += 1
                ok, facets = parse_json_maybe(row["facets"])
                if ok and isinstance(facets, dict):
                    facet_keys.update(facets)

        graph_relations = []
        graph_entities_count = 0
        type_b_projection_results = []
        if sqlite_table_exists(conn, "graph_entity"):
            columns = sqlite_table_columns(conn, "graph_entity")
            where, params = sqlite_where_workspace(columns, workspace_id)
            row = conn.execute(f"SELECT COUNT(*) FROM graph_entity {where}", params).fetchone()
            graph_entities_count = int(row[0] or 0)
            id_col = "id" if "id" in columns else "entity_id" if "entity_id" in columns else None
            type_col = "type" if "type" in columns else "entity_type" if "entity_type" in columns else None
            name_col = "name" if "name" in columns else id_col
            if id_col and type_col and name_col:
                metadata_col = "metadata" if "metadata" in columns else "metadata_json" if "metadata_json" in columns else None
                confidence_col = "confidence" if "confidence" in columns else None
                select_metadata = metadata_col or "NULL"
                select_confidence = confidence_col or "NULL"
                where_parts = [f"{type_col} = 'ProjectionResult'"]
                query_params: list[Any] = []
                if workspace_id and "workspace_id" in columns:
                    where_parts.append("workspace_id = ?")
                    query_params.append(workspace_id)
                for row in sqlite_rows(
                    conn,
                    f"""
                    SELECT {id_col} AS id, {type_col} AS type, {name_col} AS name,
                           {select_metadata} AS metadata, {select_confidence} AS confidence
                    FROM graph_entity
                    WHERE {' AND '.join(where_parts)}
                    ORDER BY name
                    """,
                    tuple(query_params),
                ):
                    ok, metadata = parse_json_maybe(row["metadata"])
                    metadata = metadata if ok and isinstance(metadata, dict) else {}
                    type_b_projection_results.append(
                        {
                            "id": str(row["id"]),
                            "type": row["type"],
                            "name": row["name"],
                            "projection_id": metadata.get("projection_id", ""),
                            "collection_id": metadata.get("collection_id", ""),
                            "confidence": row["confidence"],
                            "metadata": metadata,
                        }
                    )
        if sqlite_table_exists(conn, "graph_relation"):
            columns = sqlite_table_columns(conn, "graph_relation")
            where, params = sqlite_where_workspace(columns, workspace_id)
            relation_col = "relation_type" if "relation_type" in columns else "label" if "label" in columns else "type"
            graph_relations = [
                {"type": row["relation_type"], "source_name": "", "target_name": ""}
                for row in sqlite_rows(conn, f"SELECT {relation_col} AS relation_type FROM graph_relation {where}", params)
            ]

    return {
        "backend": "sqlite",
        "available": True,
        "projection_types": projection_types,
        "projections": projection_rows,
        "schema_counts": dict(schema_counts),
        "facet_keys": sorted(facet_keys),
        "graph": {
            "entity_count": graph_entities_count,
            "relation_count": len(graph_relations),
            "relations": graph_relations,
            "orphan_relation_count": 0,
            "projection_results": type_b_projection_results,
        },
    }


def pg_table_exists(cur: Any, schema: str, table: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """,
        (schema, table),
    )
    return bool(cur.fetchone())


def fetch_postgres(postgres_dsn: str, workspace_id: str | None) -> dict[str, Any]:
    try:
        import psycopg2
    except ImportError as exc:
        raise RuntimeError("psycopg2 is required for PostgreSQL audits") from exc

    with psycopg2.connect(postgres_dsn, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            projection_types = []
            if pg_table_exists(cur, "mb_pragma", "projection_types"):
                cur.execute(
                    """
                    SELECT type_name, compatibility_aliases, rank_bias, pack_priority,
                           next_hop_multiplier, structured
                    FROM mb_pragma.projection_types
                    ORDER BY pack_priority, type_name
                    """
                )
                columns = [desc[0] for desc in cur.description]
                projection_types = [dict(zip(columns, row)) for row in cur.fetchall()]
            elif pg_table_exists(cur, "public", "projection_types"):
                cur.execute(
                    """
                    SELECT type_name, compatibility_aliases, rank_bias, pack_priority,
                           next_hop_multiplier, structured
                    FROM public.projection_types
                    ORDER BY pack_priority, type_name
                    """
                )
                columns = [desc[0] for desc in cur.description]
                projection_types = [dict(zip(columns, row)) for row in cur.fetchall()]

            projections = []
            if pg_table_exists(cur, "mb_pragma", "projections"):
                if workspace_id:
                    cur.execute(
                        """
                        SELECT id::text, agent_id, scope, proj_type, content, weight,
                               source_ref::text, source_type, status, created_at, expires_at
                        FROM mb_pragma.projections
                        WHERE scope = %s OR scope LIKE %s
                        ORDER BY created_at DESC, scope, proj_type
                        """,
                        (workspace_id, f"{workspace_id}:%"),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id::text, agent_id, scope, proj_type, content, weight,
                               source_ref::text, source_type, status, created_at, expires_at
                        FROM mb_pragma.projections
                        ORDER BY created_at DESC, scope, proj_type
                        """
                    )
                columns = [desc[0] for desc in cur.description]
                projections = [dict(zip(columns, row)) for row in cur.fetchall()]
            elif pg_table_exists(cur, "public", "projections"):
                if workspace_id:
                    cur.execute("SELECT * FROM public.projections WHERE scope = %s OR scope LIKE %s", (workspace_id, f"{workspace_id}:%"))
                else:
                    cur.execute("SELECT * FROM public.projections")
                columns = [desc[0] for desc in cur.description]
                projections = [dict(zip(columns, row)) for row in cur.fetchall()]

            schema_counts: Counter[str] = Counter()
            facet_keys: set[str] = set()
            if pg_table_exists(cur, "mb_pragma", "facets"):
                if workspace_id:
                    cur.execute("SELECT schema_id, facets FROM mb_pragma.facets WHERE workspace_id = %s", (workspace_id,))
                else:
                    cur.execute("SELECT schema_id, facets FROM mb_pragma.facets")
                for schema_id, facets in cur.fetchall():
                    schema_counts[schema_id] += 1
                    if isinstance(facets, dict):
                        facet_keys.update(facets)

            graph_entities_count = 0
            graph_relations = []
            type_b_projection_results = []
            orphan_relation_count = 0
            if pg_table_exists(cur, "graph", "entity"):
                if workspace_id:
                    cur.execute("SELECT COUNT(*) FROM graph.entity WHERE workspace_id = %s", (workspace_id,))
                else:
                    cur.execute("SELECT COUNT(*) FROM graph.entity")
                graph_entities_count = int(cur.fetchone()[0] or 0)

                if workspace_id:
                    cur.execute(
                        """
                        SELECT id::text, type, name, confidence, COALESCE(metadata, '{}'::jsonb) AS metadata
                        FROM graph.entity
                        WHERE workspace_id = %s
                          AND type = 'ProjectionResult'
                          AND deprecated_at IS NULL
                        ORDER BY name, id
                        """,
                        (workspace_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id::text, type, name, confidence, COALESCE(metadata, '{}'::jsonb) AS metadata
                        FROM graph.entity
                        WHERE type = 'ProjectionResult'
                          AND deprecated_at IS NULL
                        ORDER BY name, id
                        """
                    )
                for row in cur.fetchall():
                    metadata = row[4] if isinstance(row[4], dict) else {}
                    type_b_projection_results.append(
                        {
                            "id": row[0],
                            "type": row[1],
                            "name": row[2],
                            "confidence": float(row[3] or 0),
                            "projection_id": metadata.get("projection_id", ""),
                            "collection_id": metadata.get("collection_id", ""),
                            "metadata": metadata,
                        }
                    )
            if pg_table_exists(cur, "graph", "relation"):
                if workspace_id:
                    cur.execute(
                        """
                        SELECT r.type, s.name AS source_name, t.name AS target_name
                        FROM graph.relation r
                        LEFT JOIN graph.entity s ON s.id = r.source_id
                        LEFT JOIN graph.entity t ON t.id = r.target_id
                        WHERE r.workspace_id = %s
                        """,
                        (workspace_id,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT r.type, s.name AS source_name, t.name AS target_name
                        FROM graph.relation r
                        LEFT JOIN graph.entity s ON s.id = r.source_id
                        LEFT JOIN graph.entity t ON t.id = r.target_id
                        """
                    )
                graph_relations = [
                    {"type": row[0], "source_name": row[1], "target_name": row[2]}
                    for row in cur.fetchall()
                ]
                orphan_relation_count = sum(1 for row in graph_relations if not row["source_name"] or not row["target_name"])

    normalized = []
    for row in projections:
        normalized.append(
            {
                "id": str(row.get("id")),
                "agent_id": row.get("agent_id"),
                "scope": row.get("scope"),
                "proj_type": row.get("proj_type"),
                "content": row.get("content"),
                "weight": float(row.get("weight") or 0),
                "source_ref": row.get("source_ref"),
                "source_type": row.get("source_type"),
                "status": row.get("status"),
                "created_at": row.get("created_at").isoformat() if hasattr(row.get("created_at"), "isoformat") else str(row.get("created_at") or ""),
                "expires_at": row.get("expires_at").isoformat() if hasattr(row.get("expires_at"), "isoformat") else str(row.get("expires_at") or ""),
            }
        )

    return {
        "backend": "postgres",
        "available": True,
        "projection_types": projection_types,
        "projections": normalized,
        "schema_counts": dict(schema_counts),
        "facet_keys": sorted(facet_keys),
        "graph": {
            "entity_count": graph_entities_count,
            "relation_count": len(graph_relations),
            "relations": graph_relations,
            "orphan_relation_count": orphan_relation_count,
            "projection_results": type_b_projection_results,
        },
    }


def fetch_backend(db_kind: str, db_path: Path, postgres_dsn: str, workspace_id: str | None) -> dict[str, Any]:
    if db_kind == "none":
        return {"backend": "none", "available": False, "projection_types": [], "projections": [], "schema_counts": {}, "facet_keys": [], "graph": {"entity_count": 0, "relation_count": 0, "relations": [], "orphan_relation_count": 0}}
    if db_kind == "postgres":
        return fetch_postgres(postgres_dsn, workspace_id)
    if db_kind == "sqlite":
        return fetch_sqlite(db_path, workspace_id)
    if postgres_dsn:
        try:
            return fetch_postgres(postgres_dsn, workspace_id)
        except Exception:
            pass
    return fetch_sqlite(db_path, workspace_id)


def projection_name_from_scope(scope: str | None) -> str:
    if not scope:
        return ""
    return str(scope).split(":")[-1]


def audit(db_path: Path, workspace_id: str | None, model_path: Path | None, db_kind: str, postgres_dsn: str, mindcli_path: str = DEFAULT_MINDCLI) -> dict[str, Any]:
    model = load_model_contract(model_path)
    planned = load_planned_projections(model, workspace_id)
    backend = fetch_backend(db_kind, db_path, postgres_dsn, workspace_id)

    now = datetime.now(tz=timezone.utc)
    projections = []
    invalid_json = []
    expired = []
    custom_types = set()
    scopes = Counter()
    statuses = Counter()
    types = Counter()
    allowed_types = {row.get("type_name") for row in backend.get("projection_types", []) if row.get("type_name")}

    for row in backend.get("projections", []):
        ok_json, parsed = parse_json_maybe(row.get("content"))
        if not ok_json:
            invalid_json.append(row.get("id"))
        expires_raw = row.get("expires_at")
        if expires_raw:
            try:
                expires_at = datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))
                if expires_at < now:
                    expired.append(row.get("id"))
            except Exception:
                pass
        if allowed_types and row.get("proj_type") not in allowed_types:
            custom_types.add(row.get("proj_type"))
        scopes[row.get("scope") or ""] += 1
        statuses[row.get("status")] += 1
        types[row.get("proj_type")] += 1
        content = row.get("content")
        content_preview = json.dumps(content, ensure_ascii=False)[:260] if isinstance(content, (dict, list)) else str(content or "")[:260]
        projections.append(
            {
                "id": row.get("id"),
                "agent_id": row.get("agent_id"),
                "scope": row.get("scope"),
                "proj_type": row.get("proj_type"),
                "status": row.get("status"),
                "weight": row.get("weight"),
                "created_at": row.get("created_at"),
                "expires_at": row.get("expires_at"),
                "content_is_json": ok_json,
                "content_preview": content_preview,
                "json_keys": sorted(parsed.keys()) if isinstance(parsed, dict) else [],
            }
        )

    # Type A = declared/working-memory projection rows.
    materialized_scopes = {row.get("scope") for row in backend.get("projections", []) if row.get("scope")}
    planned_missing = [item for item in planned if item["expected_scope"] not in materialized_scopes]
    planned_materialized = [item for item in planned if item["expected_scope"] in materialized_scopes]

    # Type B = graph-level calculated projection snapshots / report results.
    type_b_results = backend.get("graph", {}).get("projection_results", [])
    type_b_projection_ids = {row.get("projection_id") for row in type_b_results if row.get("projection_id")}
    planned_type_b_materialized = [item for item in planned if item["name"] in type_b_projection_ids or projection_name_from_scope(item["expected_scope"]) in type_b_projection_ids]
    planned_type_b_missing = [item for item in planned if item not in planned_type_b_materialized]

    relation_counts = Counter(row["type"] for row in backend.get("graph", {}).get("relations", []))
    schema_counts = Counter(backend.get("schema_counts", {}))
    facet_keys = set(backend.get("facet_keys", []))
    required_edges = sorted({edge for item in planned for edge in item.get("required_edges", [])})
    required_schemas = sorted({schema for item in planned for schema in item.get("required_schemas", [])})
    required_facets = sorted({facet for item in planned for facet in item.get("required_facets", [])})

    missing_required_edge_types = [edge for edge in required_edges if relation_counts.get(edge, 0) == 0]
    required_schemas_without_records = [schema for schema in required_schemas if schema_counts.get(schema, 0) == 0]
    required_facets_not_observed = [facet for facet in required_facets if facet not in facet_keys]

    missing_by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in planned_missing:
        missing_by_family[item["ontology"]].append(item)

    graph = backend.get("graph", {})
    quality_score = 100
    quality_score -= min(30, len(planned_missing) * 3)
    quality_score -= min(20, len(missing_required_edge_types) * 2)
    quality_score -= min(20, len(required_schemas_without_records) * 3)
    quality_score -= min(15, len(required_facets_not_observed))
    quality_score -= min(15, len(invalid_json) * 2 + len(expired) + graph.get("orphan_relation_count", 0))
    quality_score = max(0, quality_score)

    return {
        "backend": backend.get("backend"),
        "db_path": str(db_path),
        "postgres_dsn": postgres_dsn.replace("ghostcrab:ghostcrab@", "ghostcrab:***@") if postgres_dsn else "",
        "mindcli_path": mindcli_path,
        "workspace_filter": workspace_id,
        "model_path": str(model_path) if model_path else "",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "summary": {
            "quality_score": quality_score,
            "projection_count": len(projections),
            "type_a_declared_projection_count": len(projections),
            "type_b_projection_result_count": len(type_b_results),
            "planned_projection_count": len(planned),
            "planned_materialized_count": len(planned_materialized),
            "planned_missing_count": len(planned_missing),
            "planned_type_a_materialized_count": len(planned_materialized),
            "planned_type_a_missing_count": len(planned_missing),
            "planned_type_b_materialized_count": len(planned_type_b_materialized),
            "planned_type_b_missing_count": len(planned_type_b_missing),
            "graph_entity_count": graph.get("entity_count", 0),
            "graph_relation_count": graph.get("relation_count", 0),
            "orphan_relation_count": graph.get("orphan_relation_count", 0),
            "required_edge_type_gap_count": len(missing_required_edge_types),
            "required_schema_record_gap_count": len(required_schemas_without_records),
            "required_facet_observation_gap_count": len(required_facets_not_observed),
            "allowed_projection_type_count": len(backend.get("projection_types", [])),
            "custom_projection_types": sorted(custom_types),
            "invalid_json_content_count": len(invalid_json),
            "expired_projection_count": len(expired),
        },
        "counts": {
            "by_type": dict(sorted(types.items())),
            "by_status": dict(sorted(statuses.items())),
            "by_scope": dict(sorted(scopes.items())),
            "graph_relations_by_type": dict(sorted(relation_counts.items())),
            "facets_by_schema": dict(sorted(schema_counts.items())),
        },
        "allowed_projection_types": backend.get("projection_types", []),
        "projections": projections,
        "type_b_projection_results": type_b_results,
        "quality_flags": {
            "invalid_json_projection_ids": invalid_json,
            "expired_projection_ids": expired,
            "custom_projection_types_not_registered": sorted(custom_types),
            "missing_required_edge_types": missing_required_edge_types,
            "required_schemas_without_records": required_schemas_without_records,
            "required_facets_not_observed": required_facets_not_observed,
            "orphan_relation_count": graph.get("orphan_relation_count", 0),
        },
        "planned_projection_gap": {
            "mode": "type_a_declared_projections",
            "planned_count": len(planned),
            "materialized_count": len(planned_materialized),
            "missing_count": len(planned_missing),
            "missing_by_ontology": {key: value for key, value in sorted(missing_by_family.items())},
        },
        "type_b_projection_result_gap": {
            "mode": "type_b_graph_projection_results",
            "planned_count": len(planned),
            "materialized_count": len(planned_type_b_materialized),
            "missing_count": len(planned_type_b_missing),
            "available_projection_ids": sorted(type_b_projection_ids),
            "missing_projection_ids": [item["name"] for item in planned_type_b_missing],
        },
    }


def mindcli_command_examples(report: dict[str, Any]) -> list[str]:
    if report["backend"] != "postgres":
        return []
    workspace = report.get("workspace_filter") or "<workspace_id>"
    dsn = '"$GHOSTCRAB_DSN"'
    mindcli_path = report.get("mindcli_path") or DEFAULT_MINDCLI
    first_scope = ""
    if report.get("projections"):
        first_scope = report["projections"][0].get("scope") or ""
    if not first_scope:
        first_scope = f"{workspace}:<domain>:<projection_name>"
    return [
        f"DATABASE_URL={dsn} go run {mindcli_path} --json mb_pragma projections list --workspace {workspace}",
        f"DATABASE_URL={dsn} go run {mindcli_path} --json mb_pragma projection get --scope {first_scope}",
        f"DATABASE_URL={dsn} go run {mindcli_path} --json mb_pragma inspect --user <agent_id> --query '<natural-language question>' --limit 8",
    ]


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# GhostCrab Projection and Graph Audit",
        "",
        f"- Backend: `{report['backend']}`",
        f"- DB: `{report['db_path']}`",
        f"- PostgreSQL: `{report['postgres_dsn'] or 'n/a'}`",
        f"- mindCLI path: `{report.get('mindcli_path') or 'n/a'}`",
        f"- Workspace filter: `{report['workspace_filter'] or 'all'}`",
        f"- Model: `{report['model_path'] or 'n/a'}`",
        f"- Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(
        [
            "",
            "## Projection Modes",
            "",
            "GhostCrab uses two practical projection modes:",
            "",
            "- **Type A / declared projection**: rows in `mb_pragma.projections` (or SQLite `projections`). This is the JSONB contract used by `ghostcrab_pack`, `mb_pragma.pragma_pack_context`, and mindCLI. It describes the business question, required schemas, facets, edges, and retrieval jobs.",
            "- **Type B / graph ProjectionResult**: rows in `graph.entity` where `type = 'ProjectionResult'`. This is a calculated snapshot/report with evidence links, read by `ghostcrab_projection_get` / `mb_ontology.ghostcrab_projection_get`.",
            "",
            "A healthy Type A count means the projection catalogue is available to agents. A zero Type B count does not mean Type A is missing; it means no calculated graph snapshot has been written for those projections.",
        ]
    )

    if report["backend"] == "postgres":
        commands = mindcli_command_examples(report)
        lines.extend(["", "## mindCLI PostgreSQL Commands", ""])
        lines.append("Use these commands for PostgreSQL / GhostCrab Pro audits:")
        lines.append("")
        lines.append("```bash")
        lines.extend(commands)
        lines.append("```")

    flags = report["quality_flags"]
    lines.extend(["", "## Quality Flags", ""])
    for key, value in flags.items():
        rendered = ", ".join(f"`{item}`" for item in value) if isinstance(value, list) and value else value
        lines.append(f"- `{key}`: {rendered if rendered else 'n/a'}")

    lines.extend(["", "## Counts By Projection Type", ""])
    for key, value in report["counts"]["by_type"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Graph Relation Coverage", ""])
    for key, value in report["counts"]["graph_relations_by_type"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Type A Declared Projections", ""])
    for item in report["projections"]:
        lines.append(
            f"- `{item['scope'] or '(no scope)'}` | `{item['proj_type']}` | "
            f"`{item['status']}` | `{item['agent_id']}`"
        )

    lines.extend(["", "## Type B Projection Results", ""])
    if report.get("type_b_projection_results"):
        for item in report["type_b_projection_results"]:
            lines.append(
                f"- `{item.get('projection_id') or '(no projection_id)'}` | "
                f"`{item.get('name')}` | confidence `{item.get('confidence')}`"
            )
    else:
        lines.append("- n/a")

    gap = report["planned_projection_gap"]
    lines.extend(["", "## Planned Type A Projection Gap", ""])
    lines.append(f"- Planned: {gap['planned_count']}")
    lines.append(f"- Materialized: {gap['materialized_count']}")
    lines.append(f"- Missing: {gap['missing_count']}")
    for ontology, items in gap["missing_by_ontology"].items():
        lines.append(f"- `{ontology}`: " + ", ".join(f"`{item['name']}`" for item in items))

    type_b_gap = report["type_b_projection_result_gap"]
    lines.extend(["", "## Planned Type B ProjectionResult Gap", ""])
    lines.append(f"- Planned: {type_b_gap['planned_count']}")
    lines.append(f"- Materialized: {type_b_gap['materialized_count']}")
    lines.append(f"- Missing: {type_b_gap['missing_count']}")
    if type_b_gap["missing_projection_ids"]:
        lines.append("- Missing projection ids: " + ", ".join(f"`{item}`" for item in type_b_gap["missing_projection_ids"]))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--db-kind", choices=["auto", "sqlite", "postgres", "none"], default="auto")
    parser.add_argument("--postgres-dsn", default="")
    parser.add_argument("--mindcli-path", default=DEFAULT_MINDCLI)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--output-dir", default="generated/projection_audits")
    args = parser.parse_args()

    db_path = Path(args.db)
    model_path = Path(args.model) if args.model else None
    report = audit(
        db_path,
        args.workspace,
        model_path,
        args.db_kind,
        args.postgres_dsn or DEFAULT_POSTGRES_DSN if args.db_kind == "postgres" else args.postgres_dsn,
        args.mindcli_path,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = args.workspace or "all"
    json_path = output_dir / f"projection_audit_{suffix}.json"
    md_path = output_dir / f"projection_audit_{suffix}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(report, md_path)
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "summary": report["summary"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
