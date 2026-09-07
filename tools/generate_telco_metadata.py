#!/usr/bin/env python3
"""Generate a deterministic Telecom KPI Dashboard metadata pack snapshot."""

import argparse
import ast
import copy
import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATOR_VERSION = "deterministic-normalize-v3"

RENDER_FUNCTION_TO_SUBJECT_AREA = {
    "render_network_performance": "network_performance",
    "render_customer_experience": "customer_experience",
    "render_revenue_monetization": "revenue_monetization",
    "render_usage_adoption": "usage_adoption",
    "render_operational_efficiency": "operational_efficiency",
}


def load_existing_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load existing metadata pack for reference."""
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def file_sha256(path: Path) -> str:
    """Return a stable digest for the source pack."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonicalize_label(value: str) -> str:
    """Convert a title or id into a stable comparison key."""
    normalized = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").lower()
    return normalized


class HeadingCollector(ast.NodeVisitor):
    """Collect Streamlit headers from a render function in source order."""

    def __init__(self) -> None:
        self.headers: List[str] = []
        self.subheaders: List[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "st"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            if func.attr == "header":
                self.headers.append(node.args[0].value)
            elif func.attr == "subheader":
                self.subheaders.append(node.args[0].value)

        self.generic_visit(node)


def apply_section_contract(
    subject_area: Dict[str, Any],
    section_contracts: Dict[str, Dict[str, Any]],
) -> None:
    """Apply overlapping legacy section headings to an existing subject area."""
    contract = section_contracts.get(str(subject_area.get("id", "")))
    if not contract:
        return

    layout = subject_area.get("layout")
    if not isinstance(layout, dict):
        return

    sections = layout.get("sections")
    if not isinstance(sections, list):
        return

    legacy_sections = contract.get("sections") or []
    for index, legacy_title in enumerate(legacy_sections, start=1):
        if index >= len(sections):
            break
        if isinstance(sections[index], dict):
            sections[index]["title"] = legacy_title


def normalize_subject_areas(
    subject_areas: List[Dict[str, Any]],
    legacy_tabs: List[str],
    section_contracts: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Apply the legacy tab contract to subject area titles and order."""
    indexed_subject_areas: List[Tuple[int, Dict[str, Any]]] = [
        (index, copy.deepcopy(subject_area))
        for index, subject_area in enumerate(subject_areas)
    ]
    if not legacy_tabs:
        return [subject_area for _, subject_area in indexed_subject_areas]

    matched_indexes = set()
    ordered_subject_areas: List[Dict[str, Any]] = []

    for tab_order, tab_label in enumerate(legacy_tabs, start=1):
        tab_key = canonicalize_label(tab_label)
        matched_index = None

        for index, subject_area in indexed_subject_areas:
            if index in matched_indexes:
                continue

            candidate_keys = {
                canonicalize_label(str(subject_area.get("id", ""))),
                canonicalize_label(str(subject_area.get("title", ""))),
            }
            if tab_key in candidate_keys:
                matched_index = index
                break

        if matched_index is None:
            continue

        matched_indexes.add(matched_index)
        subject_area = copy.deepcopy(indexed_subject_areas[matched_index][1])
        subject_area["title"] = tab_label
        subject_area["order"] = tab_order
        apply_section_contract(subject_area, section_contracts or {})
        ordered_subject_areas.append(subject_area)

    remaining_subject_areas = [
        copy.deepcopy(subject_area)
        for index, subject_area in indexed_subject_areas
        if index not in matched_indexes
    ]
    remaining_subject_areas.sort(
        key=lambda subject_area: (
            subject_area.get("order", float("inf")),
            canonicalize_label(str(subject_area.get("id", ""))),
        )
    )

    next_order = len(ordered_subject_areas) + 1
    for subject_area in remaining_subject_areas:
        subject_area["order"] = next_order
        apply_section_contract(subject_area, section_contracts or {})
        next_order += 1
        ordered_subject_areas.append(subject_area)

    return ordered_subject_areas


def normalize_pack(
    existing: Dict[str, Any],
    metadata_path: Path,
    app_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Normalize the current pack into a deterministic generated snapshot.

    This does not claim true legacy-code introspection yet. It makes generation
    reproducible by normalizing the existing canonical pack and recording stable
    provenance metadata derived from the source file content.
    """
    normalized = copy.deepcopy(existing)
    existing_sources = normalized.get("metadata_sources") or {}
    legacy_tabs = extract_tab_labels(app_path) if app_path and app_path.exists() else []
    section_contracts = (
        extract_section_contracts(app_path) if app_path and app_path.exists() else {}
    )

    metadata_sources = {
        key: value
        for key, value in existing_sources.items()
        if key not in {"generated_on", "source_version"}
    }
    metadata_sources.update(
        {
            "generated_by": "tools/generate_telco_metadata.py",
            "generator_version": GENERATOR_VERSION,
            "generator_mode": (
                "normalize_existing_pack_with_legacy_tab_contract"
                if legacy_tabs
                else "normalize_existing_pack"
            ),
            "source_pack_sha256": file_sha256(metadata_path),
        }
    )
    if app_path and app_path.exists():
        metadata_sources["legacy_tab_contract_sha256"] = file_sha256(app_path)
    normalized["metadata_sources"] = metadata_sources
    normalized["subject_areas"] = normalize_subject_areas(
        normalized.get("subject_areas") or [],
        legacy_tabs,
        section_contracts=section_contracts,
    )

    return normalized


def extract_tab_labels(app_path: Path) -> List[str]:
    """Extract the legacy dashboard tab labels from app.py."""
    tree = ast.parse(app_path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "tabs":
            continue

        if not node.args or not isinstance(node.args[0], ast.List):
            continue

        labels = []
        for element in node.args[0].elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                labels.append(element.value)

        if labels:
            return labels

    return []


def extract_section_contracts(app_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract legacy subject-area headers and section headings from app.py."""
    tree = ast.parse(app_path.read_text(encoding="utf-8"))
    contracts: Dict[str, Dict[str, Any]] = {}

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        subject_area_id = RENDER_FUNCTION_TO_SUBJECT_AREA.get(node.name)
        if not subject_area_id:
            continue

        collector = HeadingCollector()
        collector.visit(node)
        contracts[subject_area_id] = {
            "function": node.name,
            "header": collector.headers[0] if collector.headers else None,
            "sections": collector.subheaders,
        }

    return contracts


def build_generator_inventory(repo_root: Path) -> Dict[str, Any]:
    """Describe the first legacy/runtime surfaces the generator should derive from."""
    app_path = repo_root / "app.py"

    return {
        "generator_inputs": {
            "legacy_tabs": extract_tab_labels(app_path),
            "legacy_section_contracts": extract_section_contracts(app_path),
            "source_files": [
                {
                    "path": "app.py",
                    "role": "Legacy Streamlit tab contract and section headings",
                },
                {
                    "path": "benchmark_manager.py",
                    "role": "Benchmark management tab structure and export/import affordances",
                },
                {
                    "path": "database_connection.py",
                    "role": "Legacy KPI/query patterns that still inform proof-pack semantics",
                },
                {
                    "path": "scripts/create_views.py",
                    "role": "SQLite view surface used by the maintained metadata proof path",
                },
            ],
        }
    }


def write_generator_inventory(output_path: Path, repo_root: Path) -> None:
    """Write a concrete inventory of the next generator input surfaces."""
    inventory = build_generator_inventory(repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(inventory, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Wrote generator inventory at {output_path}")


def generate_pack_from_legacy(
    metadata_path: Path,
    output_path: Path,
    app_path: Optional[Path] = None,
) -> None:
    """Generate a deterministic pack snapshot from the canonical telco pack."""
    logger.info("Loading existing metadata pack...")

    # Load existing pack
    existing = load_existing_metadata(metadata_path)

    if not existing:
        logger.error(f"No existing metadata found at {metadata_path}")
        return

    logger.info("Normalizing metadata pack into a deterministic generated snapshot...")
    generated = normalize_pack(existing, metadata_path, app_path=app_path)

    # Write regenerated pack
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(generated, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Generated metadata pack at {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate Telecom metadata pack")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("metadata/dashboard_telco.yaml"),
        help="Input metadata file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("metadata/dashboard_telco_generated.yaml"),
        help="Output metadata file"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated pack"
    )
    parser.add_argument(
        "--inventory-output",
        type=Path,
        help="Optional YAML output describing the next legacy/runtime generator inputs"
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    generate_pack_from_legacy(args.input, args.output, app_path=repo_root / "app.py")

    if args.inventory_output:
        write_generator_inventory(args.inventory_output, repo_root)

    if args.validate:
        # Import here to avoid circular dependency
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from metadata_runtime.loader import load_metadata

        try:
            config = load_metadata(args.output, force_reload=True)
            logger.info(f"✅ Validation successful: {config.pack_id} v{config.schema_version}")
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
