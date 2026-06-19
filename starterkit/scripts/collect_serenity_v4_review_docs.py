#!/usr/bin/env python3
"""Collect Serenity-V4 review documents into a numbered finalisation folder."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("finalisation/serenity-v4/review_manifest.json")
DEFAULT_STATUS = Path("finalisation/serenity-v4/review_status.json")


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "document"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if "items" not in data or not isinstance(data["items"], list):
        raise ValueError(f"{path} must contain an items list")
    return data


def load_status(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and isinstance(data.get("items"), dict):
        return data["items"]
    return data if isinstance(data, dict) else {}


def resolve_output_dir(repo_root: Path, manifest: dict[str, Any], mode: str, review_round: str | None) -> Path:
    if mode == "current":
        return repo_root / manifest.get("output_dir", "finalisation/serenity-v4/current")
    round_name = review_round or datetime.now(timezone.utc).date().isoformat()
    return repo_root / "finalisation" / "serenity-v4" / "review_rounds" / round_name


def copy_review_docs(
    repo_root: Path,
    manifest_path: Path,
    dry_run: bool,
    mode: str,
    review_round: str | None,
    include_missing: bool,
    status_path: Path | None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    output_dir = resolve_output_dir(repo_root, manifest, mode, review_round)
    statuses = load_status(status_path)

    if not dry_run:
        if mode == "current" and output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "workspace_id": manifest.get("workspace_id"),
        "title": manifest.get("title"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(manifest_path),
        "output_dir": str(output_dir),
        "mode": mode,
        "review_round": review_round,
        "include_missing": include_missing,
        "status_file": str(status_path) if status_path else "",
        "dry_run": dry_run,
        "copied": [],
        "missing": [],
    }

    items = sorted(manifest["items"], key=lambda item: item["order"])
    for item in items:
        source = repo_root / item["source"]
        if not source.exists():
            missing = dict(item)
            missing["source_abs"] = str(source)
            missing["validation_status"] = status_for_item(item, statuses)
            report["missing"].append(missing)
            continue

        phase = item["phase"]
        extension = source.suffix or ".txt"
        target_name = f"{item['order']}_{slugify(item['title'])}{extension}"
        target = output_dir / phase / target_name

        copied = dict(item)
        copied["source_abs"] = str(source)
        copied["target"] = str(target)
        copied["size_bytes"] = source.stat().st_size
        copied["sha256"] = file_sha256(source)
        copied["validation_status"] = status_for_item(item, statuses)
        report["copied"].append(copied)

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or mode == "current":
                shutil.copy2(source, target)

    if not dry_run:
        write_index(output_dir, report)
        with (output_dir / "copy_report.json").open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)

    return report


def status_for_item(item: dict[str, Any], statuses: dict[str, Any]) -> str:
    key = str(item.get("order") or "")
    source = str(item.get("source") or "")
    default = "to_validate" if item.get("review") == "required" else str(item.get("review") or "context")
    value = statuses.get(key, statuses.get(source, default))
    if isinstance(value, dict):
        return str(value.get("status") or default)
    return str(value or default)


def write_index(output_dir: Path, report: dict[str, Any]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in report["copied"]:
        grouped.setdefault(item["phase"], []).append(item)

    lines = [
        "# Serenity-V4 — index de finalisation",
        "",
        f"- Workspace: `{report.get('workspace_id')}`",
        f"- Genere le: `{report.get('generated_at')}`",
        f"- Manifest: `{report.get('manifest')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- Review round: `{report.get('review_round') or 'n/a'}`",
        f"- Status file: `{report.get('status_file') or 'n/a'}`",
        f"- Fichiers copies: `{len(report['copied'])}`",
        f"- Sources manquantes: `{len(report['missing'])}`",
        "",
        "Les liens `source` pointent vers les fichiers de verite dans le repo. Les liens `copie` pointent vers les fichiers numerotes pour annotation/relecture.",
        "",
        "Statuts possibles: `required`, `context`, `machine`, `appendix`, `to_validate`, `validated`, `needs_fix`.",
        "",
    ]

    for phase in sorted(grouped):
        lines.extend([f"## {phase}", ""])
        for item in grouped[phase]:
            target = Path(item["target"])
            source = Path(item["source_abs"])
            rel_target = target.relative_to(output_dir)
            lines.append(
                f"- `{item['order']}` **{item['title']}** "
                f"(status: `{item.get('validation_status')}`, review: `{item['review']}`, role: `{item['role']}`) — "
                f"[copie]({rel_target.as_posix()}) — "
                f"[source]({source.as_posix()})"
            )
            if item.get("validation_question"):
                lines.append(f"  - Validation: {item['validation_question']}")
            if item.get("owner"):
                lines.append(f"  - Owner: `{item['owner']}`")
            if item.get("depends_on"):
                depends_on = item["depends_on"]
                if isinstance(depends_on, list):
                    depends_on = ", ".join(f"`{value}`" for value in depends_on)
                lines.append(f"  - Depends on: {depends_on}")
            if item.get("scenario_scope"):
                lines.append(f"  - Scenario scope: `{item['scenario_scope']}`")
        lines.append("")

    if report["missing"]:
        lines.extend(["## Sources manquantes", ""])
        for item in report["missing"]:
            lines.append(
                f"- `{item['order']}` **{item['title']}** "
                f"(status: `{item.get('validation_status')}`, review: `{item.get('review')}`, role: `{item.get('role')}`) — "
                f"`{item['source']}`"
            )
        lines.append("")

    (output_dir / "00_INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Review manifest JSON path")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--mode", choices=["current", "review-round"], default="current", help="current rewrites the mirror; review-round creates a stable annotation folder")
    parser.add_argument("--review-round", default=None, help="Review round name, default YYYY-MM-DD in review-round mode")
    parser.add_argument("--include-missing", action="store_true", help="Report missing future artifacts without returning a failing exit code")
    parser.add_argument("--status-file", default=str(DEFAULT_STATUS), help="Optional JSON file with per-document validation status")
    parser.add_argument("--dry-run", action="store_true", help="Do not copy files")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    status_path = (repo_root / args.status_file).resolve() if args.status_file else None
    report = copy_review_docs(
        repo_root=repo_root,
        manifest_path=manifest_path,
        dry_run=args.dry_run,
        mode=args.mode,
        review_round=args.review_round,
        include_missing=args.include_missing,
        status_path=status_path,
    )

    print(
        json.dumps(
            {
                "ok": not report["missing"] or args.include_missing,
                "copied": len(report["copied"]),
                "missing": len(report["missing"]),
                "output_dir": report["output_dir"],
                "mode": report["mode"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if (not report["missing"] or args.include_missing) else 1


if __name__ == "__main__":
    raise SystemExit(main())
