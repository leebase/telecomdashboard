"""Entry point shim for `python -m metadata_cli`."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from metadata_runtime.cli import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
