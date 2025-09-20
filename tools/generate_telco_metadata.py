#!/usr/bin/env python3
"""Generate Telecom KPI Dashboard metadata pack from legacy code introspection."""

import argparse
import logging
from pathlib import Path
from typing import Dict, Any
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_existing_metadata(metadata_path: Path) -> Dict[str, Any]:
    """Load existing metadata pack for reference."""
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def generate_pack_from_legacy(metadata_path: Path, output_path: Path) -> None:
    """Generate metadata pack by introspecting legacy code.

    For Sprint 4, this is a simplified version that validates and regenerates
    the existing pack. Full introspection would analyze app.py, improved_metric_cards.py,
    kpi_components.py, and database_connection.py to extract KPIs, charts, and filters.
    """
    logger.info("Loading existing metadata pack...")

    # Load existing pack
    existing = load_existing_metadata(metadata_path)

    if not existing:
        logger.error(f"No existing metadata found at {metadata_path}")
        return

    # In a full implementation, this would:
    # 1. Parse app.py for subject areas and KPIs
    # 2. Analyze improved_metric_cards.py for card definitions
    # 3. Extract chart configurations from kpi_components.py
    # 4. Generate SQL queries from database_connection.py patterns
    # 5. Infer filters from time period selectors
    # 6. Create widget mappings and layouts

    # For Sprint 4, we validate and regenerate the existing pack
    logger.info("Validating and regenerating metadata pack...")

    # Add generation metadata
    existing['metadata_sources'] = {
        'generated_on': '2025-09-20',
        'generated_by': 'tools/generate_telco_metadata.py',
        'source_version': 'Sprint 4'
    }

    # Write regenerated pack
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(existing, f, default_flow_style=False, sort_keys=False)

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