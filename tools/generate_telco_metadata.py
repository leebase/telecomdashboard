#!/usr/bin/env python3
"""Generate a deterministic Telecom KPI Dashboard metadata pack snapshot."""

import argparse
import ast
import copy
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GENERATOR_VERSION = "deterministic-normalize-v1"


def load_existing_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load existing metadata pack for reference."""
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def file_sha256(path: Path) -> str:
    """Return a stable digest for the source pack."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_pack(existing: Dict[str, Any], metadata_path: Path) -> Dict[str, Any]:
    """Normalize the current pack into a deterministic generated snapshot.

    This does not claim true legacy-code introspection yet. It makes generation
    reproducible by normalizing the existing canonical pack and recording stable
    provenance metadata derived from the source file content.
    """
    normalized = copy.deepcopy(existing)
    existing_sources = normalized.get("metadata_sources") or {}

    metadata_sources = {
        key: value
        for key, value in existing_sources.items()
        if key not in {"generated_on", "source_version"}
    }
    metadata_sources.update(
        {
            "generated_by": "tools/generate_telco_metadata.py",
            "generator_version": GENERATOR_VERSION,
            "generator_mode": "normalize_existing_pack",
            "source_pack_sha256": file_sha256(metadata_path),
        }
    )
    normalized["metadata_sources"] = metadata_sources

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


def build_generator_inventory(repo_root: Path) -> Dict[str, Any]:
    """Describe the first legacy/runtime surfaces the generator should derive from."""
    app_path = repo_root / "app.py"

    return {
        "generator_inputs": {
            "legacy_tabs": extract_tab_labels(app_path),
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


def generate_pack_from_legacy(metadata_path: Path, output_path: Path) -> None:
    """Generate a deterministic pack snapshot from the canonical telco pack."""
    logger.info("Loading existing metadata pack...")

    # Load existing pack
    existing = load_existing_metadata(metadata_path)

    if not existing:
        logger.error(f"No existing metadata found at {metadata_path}")
        return

    logger.info("Normalizing metadata pack into a deterministic generated snapshot...")
    generated = normalize_pack(existing, metadata_path)

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

    generate_pack_from_legacy(args.input, args.output)

    if args.inventory_output:
        write_generator_inventory(args.inventory_output, Path(__file__).resolve().parent.parent)

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
