"""Command line interface for metadata runtime tooling."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from .loader import MetadataLoadError, load_metadata


def _format_errors(errors: Iterable[dict]) -> str:
    lines = []
    for entry in errors:
        location = ".".join(str(part) for part in entry.get("loc", [])) or "root"
        msg = entry.get("msg", "validation error")
        error_type = entry.get("type", "")
        suffix = f" ({error_type})" if error_type else ""
        lines.append(f"- {location}: {msg}{suffix}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metadata runtime tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a metadata pack")
    validate.add_argument("path", type=Path, help="Path to metadata YAML file")
    validate.add_argument(
        "--json", action="store_true", help="Emit validation errors as JSON"
    )
    validate.add_argument(
        "--quiet", action="store_true", help="Suppress success output"
    )

    return parser


def _handle_validate(args: argparse.Namespace) -> int:
    try:
        config = load_metadata(args.path, force_reload=True)
    except FileNotFoundError:
        print(f"Metadata file not found: {args.path}", file=sys.stderr)
        return 1
    except MetadataLoadError as exc:
        if args.json:
            print(json.dumps(exc.errors, indent=2), file=sys.stderr)
        else:
            print("Metadata validation failed:", file=sys.stderr)
            print(_format_errors(exc.errors), file=sys.stderr)
        return 1

    if not args.quiet:
        print(
            f"✅ Validated pack '{config.pack_id}' (schema {config.schema_version}, app {config.app_version})"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return _handle_validate(args)

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
