#!/usr/bin/env python3
"""Generate a deterministic Telecom KPI Dashboard metadata pack snapshot."""

import argparse
import copy
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

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

    args = parser.parse_args()

    generate_pack_from_legacy(args.input, args.output)

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
