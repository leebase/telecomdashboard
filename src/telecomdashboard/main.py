"""
Main entry point for telecomdashboard.
"""

import argparse
import logging
import json
from pathlib import Path
import subprocess
import sys
from contextlib import contextmanager, redirect_stdout


def _repo_root() -> Path:
    """Resolve the repository root when running from the editable source tree."""
    return Path(__file__).resolve().parents[2]


def _streamlit_app_path(name: str) -> Path:
    """Return the absolute path to a top-level Streamlit app file."""
    return _repo_root() / name


def _load_health_checker():
    """Load the shared health checker lazily to keep CLI startup light."""
    repo_root = str(_repo_root())
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    from health_check import health_checker

    return health_checker


@contextmanager
def _route_log_stdout_to_stderr():
    """Keep stdout reserved for command output while the app logs to stderr."""
    swapped_handlers = []
    loggers = [logging.getLogger()]
    loggers.extend(
        logger
        for logger in logging.Logger.manager.loggerDict.values()
        if isinstance(logger, logging.Logger)
    )

    for logger in loggers:
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
                swapped_handlers.append((handler, handler.stream))
                handler.setStream(sys.stderr)

    try:
        yield
    finally:
        for handler, original_stream in reversed(swapped_handlers):
            handler.setStream(original_stream)


def _health_exit_code(status: str) -> int:
    """Map health status to CLI exit code."""
    if status == "healthy":
        return 0
    if status == "degraded":
        return 1
    if status == "unhealthy":
        return 2
    return 3


def _handle_health_command(simple: bool, pretty: bool) -> int:
    """Run health checks and print JSON output."""
    with redirect_stdout(sys.stderr), _route_log_stdout_to_stderr():
        checker = _load_health_checker()
        payload = checker.get_simple_health() if simple else checker.run_all_checks()
    print(json.dumps(payload, indent=2 if pretty else None, sort_keys=pretty, default=str))
    return _health_exit_code(payload.get("status", "unknown"))


def main(argv=None):
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="telecomdashboard",
        description="Helper CLI for the telecomdashboard Streamlit apps.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    parser.add_argument(
        "--run-dashboard",
        action="store_true",
        help="Launch the main Streamlit dashboard (app.py).",
    )
    parser.add_argument(
        "--run-agent-prototype",
        action="store_true",
        help="Launch the separate agent prototype (runAgentsApp.py).",
    )
    subparsers = parser.add_subparsers(dest="command")
    health_parser = subparsers.add_parser(
        "health",
        help="Run health checks and print JSON output.",
    )
    health_parser.add_argument(
        "--simple",
        action="store_true",
        help="Run the lightweight health check instead of the comprehensive report.",
    )
    health_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON output.",
    )

    args = parser.parse_args(argv)

    if args.command == "health":
        return _handle_health_command(simple=args.simple, pretty=args.pretty)

    if args.run_dashboard or args.run_agent_prototype:
        app_name = "runAgentsApp.py" if args.run_agent_prototype else "app.py"
        app_path = _streamlit_app_path(app_name)
        if not app_path.exists():
            parser.error(f"Could not find {app_name} at expected path: {app_path}")

        try:
            return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app_path)])
        except KeyboardInterrupt:
            return 130

    parser.print_help()
    print("\nPrimary app: streamlit run app.py")
    print("Agent prototype: streamlit run runAgentsApp.py")
    print("Health report: telecomdashboard health --pretty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
