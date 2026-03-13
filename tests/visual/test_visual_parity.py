from __future__ import annotations

import os
import socket
import subprocess
import time
from pathlib import Path

import pytest

from src.ui.visual_parity import VisualParityTester


REFERENCE_DIR = Path("/Users/leeharrington/projects/telecomdashboard/docs/screen-grabs/current-look")
SUBJECT_AREAS = [
    "network_performance",
    "customer_experience",
    "revenue_monetization",
    "usage_adoption",
    "operational_efficiency",
    "benchmark_management",
]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_port(port: int, timeout_seconds: float = 20.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.25)
    raise TimeoutError(f"Timed out waiting for Streamlit on port {port}")


@pytest.fixture(scope="session")
def metadata_server():
    if not VisualParityTester(Path("tests/visual/baselines")).browser_capture_available():
        pytest.skip("No browser capture backend available for visual parity")
    if not REFERENCE_DIR.exists():
        pytest.skip("Source screenshot references are not available locally")

    port = _free_port()
    process = subprocess.Popen(
        [
            ".venv/bin/streamlit",
            "run",
            "app.py",
            "--server.headless",
            "true",
            "--server.port",
            str(port),
        ],
        cwd=Path.cwd(),
        env={**os.environ, "USE_METADATA": "true"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port(port)
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture
def visual_tester(metadata_server):
    baseline_dir = Path("tests/visual/baselines")
    return VisualParityTester(
        baseline_dir=baseline_dir,
        tolerance=0.27,
        app_url=metadata_server,
        reference_dir=REFERENCE_DIR,
    )


@pytest.mark.visual
@pytest.mark.parametrize("subject_area", SUBJECT_AREAS)
def test_metadata_visual_parity_against_source(visual_tester, subject_area):
    result = visual_tester.test_subject_area_parity(subject_area)

    assert result["status"] in {"compared", "failed"}
    assert result["baseline_exists"] is True
    assert result.get("passed") is True, result
