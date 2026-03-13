"""Visual parity verification for metadata runtime."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import streamlit as st
from PIL import Image, ImageChops, ImageStat

logger = logging.getLogger(__name__)

_DEFAULT_CHROME_BINARY = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
_REFERENCE_SCREENSHOTS = {
    "network_performance": "00-shell-network.png",
    "customer_experience": "01-customer-experience.png",
    "revenue_monetization": "02-revenue-monetization.png",
    "usage_adoption": "03-usage-adoption.png",
    "operational_efficiency": "04-operational-efficiency.png",
    "benchmark_management": "05-benchmark-management.png",
}
_TAB_LABELS = {
    "network_performance": "📡 Network Performance",
    "customer_experience": "😊 Customer Experience",
    "revenue_monetization": "💰 Revenue & Monetization",
    "usage_adoption": "📶 Usage & Adoption",
    "operational_efficiency": "🛠️ Operational Efficiency",
    "benchmark_management": "🎯 Benchmark Management",
}


def _playwright_installed() -> bool:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception:
        return False
    return True


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http_json(url: str, method: str = "GET") -> Dict[str, Any]:
    request = Request(url, method=method)
    with urlopen(request, timeout=10) as response:
        return json.load(response)


class _ChromePageClient:
    def __init__(self, ws_url: str) -> None:
        parsed = urlparse(ws_url)
        self._socket = socket.create_connection((parsed.hostname, parsed.port))
        websocket_key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {parsed.path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {websocket_key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self._socket.sendall(request.encode())
        response = self._socket.recv(4096)
        if b"101" not in response:
            raise RuntimeError(f"WebSocket handshake failed: {response!r}")
        self._message_id = 0

    def close(self) -> None:
        try:
            self._socket.close()
        except Exception:
            pass

    def call(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
        self._message_id += 1
        message_id = self._message_id
        self._send({"id": message_id, "method": method, "params": params or {}})
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = self._recv()
            if message is None:
                raise RuntimeError("Chrome DevTools socket closed unexpectedly")
            if message.get("id") == message_id:
                return message
        raise TimeoutError(f"Timed out waiting for DevTools response to {method}")

    def _send(self, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        mask = os.urandom(4)
        header = bytearray([0x81])
        length = len(body)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(body))
        self._socket.sendall(header + masked)

    def _recv(self) -> Optional[Dict[str, Any]]:
        header = self._socket.recv(2)
        if not header:
            return None
        first_byte, second_byte = header
        length = second_byte & 0x7F
        masked = second_byte >> 7
        if length == 126:
            length = struct.unpack("!H", self._socket.recv(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._socket.recv(8))[0]
        mask = self._socket.recv(4) if masked else b""
        payload = b""
        while len(payload) < length:
            payload += self._socket.recv(length - len(payload))
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        if first_byte & 0x0F == 0x8:
            return None
        return json.loads(payload)


class VisualParityTester:
    """Test harness for visual parity between legacy and metadata dashboards."""

    def __init__(
        self,
        baseline_dir: Path,
        tolerance: float = 0.25,
        app_url: Optional[str] = None,
        reference_dir: Optional[Path] = None,
        chrome_binary: Optional[str] = None,
    ):
        self.baseline_dir = baseline_dir
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.tolerance = tolerance
        self.app_url = app_url or os.getenv("VISUAL_PARITY_APP_URL")
        reference_dir_value = reference_dir or os.getenv("VISUAL_PARITY_REFERENCE_DIR")
        self.reference_dir = Path(reference_dir_value).resolve() if reference_dir_value else None
        self.chrome_binary = chrome_binary or os.getenv("VISUAL_PARITY_CHROME", _DEFAULT_CHROME_BINARY)

    def browser_capture_available(self) -> bool:
        return _playwright_installed() or Path(self.chrome_binary).exists()

    def capture_screenshot(self, subject_area: str) -> Optional[bytes]:
        """Capture screenshot of current dashboard state.

        Uses a browser session when an app URL is configured.
        Falls back to a deterministic session-state hash for unit tests.
        """
        if self.app_url and self.browser_capture_available():
            return self._capture_browser_screenshot(subject_area)

        try:
            page_content = st.session_state.get('page_content', '')
            content_hash = hashlib.md5(page_content.encode()).hexdigest()
            return f"screenshot_{subject_area}_{content_hash}".encode()
        except Exception as e:
            logger.error(f"Failed to capture screenshot for {subject_area}: {e}")
            return None

    def _detect_capture_quality_issue(self, screenshot: bytes) -> Optional[str]:
        """Return a message when a decoded screenshot looks blank or background-only."""
        try:
            image = Image.open(io.BytesIO(screenshot)).convert("RGB")
        except Exception:
            return None

        stat = ImageStat.Stat(image)
        max_stddev = max(float(channel) for channel in stat.stddev)
        max_mean = max(float(channel) for channel in stat.mean)

        if max_stddev < 10.0 and max_mean < 80.0:
            return (
                "Captured screenshot appears background-only "
                f"(mean={max_mean:.1f}, stddev={max_stddev:.1f})"
            )

        return None

    def compare_screenshots(self, baseline: bytes, current: bytes) -> Tuple[float, str]:
        """Compare two screenshots and return difference ratio and details."""
        if baseline == current:
            return 0.0, "Screenshots identical"

        try:
            baseline_image = Image.open(io.BytesIO(baseline)).convert("RGB")
            current_image = Image.open(io.BytesIO(current)).convert("RGB")
        except Exception:
            baseline_hash = hashlib.md5(baseline).hexdigest()
            current_hash = hashlib.md5(current).hexdigest()
            if baseline_hash == current_hash:
                return 0.0, "Content identical"
            return 1.0, "Binary content differs and could not be decoded as images"

        original_size = current_image.size
        if baseline_image.size != current_image.size:
            current_image = current_image.resize(baseline_image.size)

        diff = ImageChops.difference(baseline_image, current_image)
        mean_channels = ImageStat.Stat(diff).mean
        difference_ratio = sum(mean_channels) / (len(mean_channels) * 255)
        details = f"Pixel difference ratio {difference_ratio:.3f}; current size {original_size}, baseline size {baseline_image.size}"
        return difference_ratio, details

    def test_subject_area_parity(self, subject_area: str) -> Dict[str, Any]:
        """Test visual parity for a subject area."""
        baseline_path = self._baseline_path(subject_area)

        # Capture current screenshot
        current_screenshot = self.capture_screenshot(subject_area)

        if current_screenshot is None:
            return {
                "subject_area": subject_area,
                "status": "error",
                "message": "Failed to capture screenshot"
            }

        result = {
            "subject_area": subject_area,
            "timestamp": time.time(),
            "baseline_exists": baseline_path.exists()
        }

        quality_issue = self._detect_capture_quality_issue(current_screenshot)
        if quality_issue:
            result.update({
                "status": "failed",
                "passed": False,
                "message": quality_issue,
            })
            return result

        if baseline_path.exists():
            # Compare with baseline
            try:
                with open(baseline_path, 'rb') as f:
                    baseline_screenshot = f.read()

                difference, details = self.compare_screenshots(baseline_screenshot, current_screenshot)

                result.update({
                    "status": "compared",
                    "difference_ratio": difference,
                    "details": details,
                    "passed": difference <= self.tolerance
                })

                if difference > self.tolerance:
                    result["status"] = "failed"
                    result["message"] = f"Visual parity failed: difference {difference:.3f} > {self.tolerance}"

            except Exception as e:
                result.update({
                    "status": "error",
                    "message": f"Comparison failed: {e}"
                })

        else:
            # Create baseline
            try:
                with open(baseline_path, 'wb') as f:
                    f.write(current_screenshot)

                result.update({
                    "status": "baseline_created",
                    "message": f"Created baseline for {subject_area}"
                })

            except Exception as e:
                result.update({
                    "status": "error",
                    "message": f"Failed to create baseline: {e}"
                })

        return result

    def get_baseline_info(self, subject_area: str) -> Optional[Dict[str, Any]]:
        """Get information about existing baseline."""
        baseline_path = self._baseline_path(subject_area)

        if not baseline_path.exists():
            return None

        try:
            stat = baseline_path.stat()
            return {
                "subject_area": subject_area,
                "path": str(baseline_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "exists": True
            }
        except Exception:
            return None

    def list_baselines(self) -> Dict[str, Dict[str, Any]]:
        """List all available baselines."""
        baselines = {}

        for baseline_file in self.baseline_dir.glob("*_baseline.png"):
            subject_area = baseline_file.stem.replace("_baseline", "")
            info = self.get_baseline_info(subject_area)
            if info:
                baselines[subject_area] = info

        return baselines

    def delete_baseline(self, subject_area: str) -> bool:
        """Delete baseline for subject area."""
        baseline_path = self.baseline_dir / f"{subject_area}_baseline.png"

        try:
            if baseline_path.exists():
                baseline_path.unlink()
                return True
            return False
        except Exception:
            return False

    def _baseline_path(self, subject_area: str) -> Path:
        if self.reference_dir:
            reference_name = _REFERENCE_SCREENSHOTS.get(subject_area)
            if reference_name:
                reference_path = self.reference_dir / reference_name
                if reference_path.exists():
                    return reference_path
        return self.baseline_dir / f"{subject_area}_baseline.png"

    def _capture_browser_screenshot(self, subject_area: str) -> Optional[bytes]:
        if _playwright_installed():
            screenshot = self._capture_playwright_screenshot(subject_area)
            if screenshot is not None:
                return screenshot

        if Path(self.chrome_binary).exists():
            return self._capture_chrome_cdp_screenshot(subject_area)

        logger.error("No browser capture backend is available for visual parity")
        return None

    def _capture_playwright_screenshot(self, subject_area: str) -> Optional[bytes]:
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            logger.error("Playwright import failed for %s: %s", subject_area, exc)
            return None

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1600, "height": 1800}, device_scale_factor=1)
                page.goto(self.app_url, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_function(
                    "() => document.querySelectorAll('button').length >= 10",
                    timeout=30_000,
                )
                page.wait_for_timeout(2_000)

                tab_label = _TAB_LABELS.get(subject_area)
                if tab_label:
                    tab = page.get_by_role("tab", name=tab_label, exact=True)
                    if tab.count():
                        tab.click()
                    else:
                        page.locator("button", has_text=tab_label).first.click()
                    page.wait_for_timeout(1_000)

                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(500)
                screenshot = page.screenshot(full_page=True, type="png")
                browser.close()
                return screenshot
        except PlaywrightTimeoutError as exc:
            logger.error("Playwright screenshot capture timed out for %s: %s", subject_area, exc)
            return None
        except Exception as exc:
            logger.error("Playwright screenshot capture failed for %s: %s", subject_area, exc)
            return None

    def _capture_chrome_cdp_screenshot(self, subject_area: str) -> Optional[bytes]:
        port = _find_free_port()
        user_data_dir = Path(tempfile.mkdtemp(prefix="visual-parity-chrome-"))
        chrome_process = subprocess.Popen(
            [
                self.chrome_binary,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-first-run",
                "--no-default-browser-check",
                f"--remote-debugging-port={port}",
                f"--user-data-dir={user_data_dir}",
                "--window-size=1600,1800",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        client: Optional[_ChromePageClient] = None
        try:
            for _ in range(40):
                try:
                    _http_json(f"http://127.0.0.1:{port}/json/version")
                    break
                except Exception:
                    time.sleep(0.25)
            else:
                raise RuntimeError("Chrome DevTools endpoint did not become ready")

            target = _http_json(f"http://127.0.0.1:{port}/json/new?{self.app_url}", method="PUT")
            client = _ChromePageClient(target["webSocketDebuggerUrl"])
            client.call("Page.enable")
            time.sleep(2.0)

            tab_label = _TAB_LABELS.get(subject_area)
            if tab_label:
                expression = (
                    "(() => {"
                    "const btn = Array.from(document.querySelectorAll('button')).find("
                    f"button => button.innerText.trim() === {tab_label!r}"
                    ");"
                    "if (btn) { btn.click(); return true; }"
                    "return false;"
                    "})()"
                )
                client.call("Runtime.evaluate", {"expression": expression})
                time.sleep(1.0)

            client.call("Runtime.evaluate", {"expression": "window.scrollTo(0, 0)"})
            metrics = client.call("Page.getLayoutMetrics")["result"]["contentSize"]
            screenshot = client.call(
                "Page.captureScreenshot",
                {
                    "format": "png",
                    "captureBeyondViewport": True,
                    "clip": {
                        "x": 0,
                        "y": 0,
                        "width": metrics["width"],
                        "height": metrics["height"],
                        "scale": 1,
                    },
                },
                timeout=20.0,
            )
            return base64.b64decode(screenshot["result"]["data"])
        except Exception as exc:
            logger.error("Browser screenshot capture failed for %s: %s", subject_area, exc)
            return None
        finally:
            if client:
                client.close()
            chrome_process.kill()
            chrome_process.wait()
            shutil.rmtree(user_data_dir, ignore_errors=True)


class DOMStructureAnalyzer:
    """Analyze DOM structure for layout validation."""

    def __init__(self):
        self.structure_cache: Dict[str, Dict[str, Any]] = {}

    def analyze_current_page(self) -> Dict[str, Any]:
        """Analyze current page DOM structure."""
        # In production, this would parse the actual DOM
        # For Sprint 5, we'll analyze Streamlit session state

        structure = {
            "timestamp": time.time(),
            "elements": {},
            "layout": {}
        }

        # Analyze session state for component information
        if hasattr(st, 'session_state'):
            session_keys = list(st.session_state.keys())
            structure["session_state_keys"] = len(session_keys)

            # Look for component-related keys
            component_keys = [k for k in session_keys if any(term in k.lower()
                            for term in ['chart', 'metric', 'kpi', 'tab'])]
            structure["component_keys"] = component_keys

        return structure

    def compare_structures(self, baseline: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two DOM structures."""
        differences = {
            "structure_match": True,
            "differences": [],
            "baseline_timestamp": baseline.get("timestamp"),
            "current_timestamp": current.get("timestamp")
        }

        # Compare session state keys
        baseline_count = int(baseline.get("session_state_keys", 0) or 0)
        current_count = int(current.get("session_state_keys", 0) or 0)

        if baseline_count != current_count:
            differences["structure_match"] = False
            differences["differences"].append({
                "type": "session_state_keys",
                "baseline_count": baseline_count,
                "current_count": current_count,
            })

        # Compare component keys
        baseline_components = set(baseline.get("component_keys", []))
        current_components = set(current.get("component_keys", []))

        if baseline_components != current_components:
            differences["structure_match"] = False
            differences["differences"].append({
                "type": "component_keys",
                "added": list(current_components - baseline_components),
                "removed": list(baseline_components - current_components)
            })

        return differences

    def save_baseline_structure(self, subject_area: str, structure: Dict[str, Any]) -> bool:
        """Save DOM structure as baseline."""
        try:
            baseline_file = Path(f"tests/visual/baselines/{subject_area}_structure.json")
            baseline_file.parent.mkdir(parents=True, exist_ok=True)

            handle = open(baseline_file, 'w')
            try:
                json.dump(structure, handle, indent=2)
            finally:
                handle.close()

            return True
        except Exception as e:
            logger.error(f"Failed to save baseline structure for {subject_area}: {e}")
            return False

    def load_baseline_structure(self, subject_area: str) -> Optional[Dict[str, Any]]:
        """Load baseline DOM structure."""
        try:
            baseline_file = Path(f"tests/visual/baselines/{subject_area}_structure.json")

            if not baseline_file.exists():
                return None

            handle = open(baseline_file, 'r')
            try:
                return json.load(handle)
            finally:
                handle.close()

        except Exception as e:
            logger.error(f"Failed to load baseline structure for {subject_area}: {e}")
            return None


# Streamlit component for visual testing
def create_visual_test_interface():
    """Create Streamlit interface for visual testing."""
    st.header("🎯 Visual Parity Testing")

    # Initialize tester
    baseline_dir = Path("tests/visual/baselines")
    tester = VisualParityTester(baseline_dir)
    dom_analyzer = DOMStructureAnalyzer()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Current Baselines")
        baselines = tester.list_baselines()

        if baselines:
            for subject_area, info in baselines.items():
                with st.expander(f"📁 {subject_area}"):
                    st.write(f"Size: {info['size']} bytes")
                    st.write(f"Modified: {time.ctime(info['modified'])}")
                    if st.button(f"Delete {subject_area} baseline", key=f"delete_{subject_area}"):
                        if tester.delete_baseline(subject_area):
                            st.success(f"Deleted baseline for {subject_area}")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete baseline for {subject_area}")
        else:
            st.info("No baselines found. Run tests to create them.")

    with col2:
        st.subheader("🧪 Run Visual Tests")

        subject_areas = [
            "network_performance",
            "customer_experience",
            "revenue_monetization",
            "usage_adoption",
            "operational_efficiency",
            "benchmark_management"
        ]

        selected_area = st.selectbox("Select subject area to test:", subject_areas)

        if st.button("Run Visual Test", type="primary"):
            with st.spinner(f"Testing visual parity for {selected_area}..."):
                result = tester.test_subject_area_parity(selected_area)

                if result["status"] == "compared":
                    if result["passed"]:
                        st.success(f"✅ Visual parity passed for {selected_area}")
                        st.write(f"Difference ratio: {result['difference_ratio']:.3f}")
                        st.write(f"Details: {result['details']}")
                    else:
                        st.error(f"❌ Visual parity failed for {selected_area}")
                        st.write(f"Difference ratio: {result['difference_ratio']:.3f}")
                        st.write(f"Details: {result['details']}")

                elif result["status"] == "baseline_created":
                    st.info(f"📸 Created baseline for {selected_area}")
                    st.write(result["message"])

                else:
                    st.error(f"❌ Test failed: {result.get('message', 'Unknown error')}")

        if st.button("Analyze Current Page Structure"):
            structure = dom_analyzer.analyze_current_page()

            st.subheader("📄 Current Page Structure")
            st.json(structure)

            # Load and compare with baseline if exists
            baseline_structure = dom_analyzer.load_baseline_structure(selected_area)
            if baseline_structure:
                comparison = dom_analyzer.compare_structures(baseline_structure, structure)

                st.subheader("🔍 Structure Comparison")
                if comparison["structure_match"]:
                    st.success("✅ DOM structures match")
                else:
                    st.warning("⚠️ DOM structure differences detected")
                    for diff in comparison["differences"]:
                        st.write(f"**{diff['type']}:**")
                        if 'added' in diff:
                            st.write(f"- Added: {diff['added']}")
                        if 'removed' in diff:
                            st.write(f"- Removed: {diff['removed']}")

            if st.button("Save as Baseline Structure"):
                if dom_analyzer.save_baseline_structure(selected_area, structure):
                    st.success(f"Saved baseline structure for {selected_area}")
                else:
                    st.error("Failed to save baseline structure")


__all__ = [
    "VisualParityTester",
    "DOMStructureAnalyzer",
    "create_visual_test_interface"
]
