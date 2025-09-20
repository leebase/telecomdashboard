"""Tests for visual parity verification system."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.ui.visual_parity import VisualParityTester, DOMStructureAnalyzer


class TestVisualParityTester:
    """Test visual parity tester functionality."""

    def test_init(self):
        """Test initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir, tolerance=0.05)

            assert tester.baseline_dir == baseline_dir
            assert tester.tolerance == 0.05
            assert baseline_dir.exists()

    @patch('streamlit.session_state')
    def test_capture_screenshot(self, mock_session_state):
        """Test screenshot capture."""
        mock_session_state.get.return_value = "test content"

        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            screenshot = tester.capture_screenshot("test_area")

            assert screenshot is not None
            assert isinstance(screenshot, bytes)
            assert b"test_area" in screenshot

    def test_compare_screenshots_identical(self):
        """Test screenshot comparison with identical images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            test_data = b"test_screenshot_data"
            difference, details = tester.compare_screenshots(test_data, test_data)

            assert difference == 0.0
            assert "identical" in details.lower()

    def test_compare_screenshots_different(self):
        """Test screenshot comparison with different images."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            data1 = b"test_data_1"
            data2 = b"test_data_2"
            difference, details = tester.compare_screenshots(data1, data2)

            assert difference > 0.0
            assert isinstance(details, str)

    def test_test_subject_area_parity_create_baseline(self):
        """Test creating baseline for new subject area."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            with patch.object(tester, 'capture_screenshot', return_value=b"test_data"):
                result = tester.test_subject_area_parity("new_area")

                assert result["status"] == "baseline_created"
                assert result["subject_area"] == "new_area"
                assert "Created baseline" in result["message"]

                # Verify baseline file was created
                baseline_file = baseline_dir / "new_area_baseline.png"
                assert baseline_file.exists()

    def test_test_subject_area_parity_comparison_pass(self):
        """Test successful comparison with existing baseline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir, tolerance=0.1)

            # Create baseline
            baseline_file = baseline_dir / "test_area_baseline.png"
            baseline_file.write_bytes(b"test_baseline")

            with patch.object(tester, 'capture_screenshot', return_value=b"test_baseline"):
                with patch.object(tester, 'compare_screenshots', return_value=(0.05, "Minor differences")):
                    result = tester.test_subject_area_parity("test_area")

                    assert result["status"] == "compared"
                    assert result["passed"] is True
                    assert result["difference_ratio"] == 0.05

    def test_test_subject_area_parity_comparison_fail(self):
        """Test failed comparison with existing baseline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir, tolerance=0.01)

            # Create baseline
            baseline_file = baseline_dir / "test_area_baseline.png"
            baseline_file.write_bytes(b"test_baseline")

            with patch.object(tester, 'capture_screenshot', return_value=b"different_data"):
                with patch.object(tester, 'compare_screenshots', return_value=(0.05, "Major differences")):
                    result = tester.test_subject_area_parity("test_area")

                    assert result["status"] == "failed"
                    assert result["passed"] is False
                    assert result["difference_ratio"] == 0.05

    def test_get_baseline_info(self):
        """Test getting baseline information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            # Create baseline file
            baseline_file = baseline_dir / "test_area_baseline.png"
            baseline_file.write_bytes(b"test_data")

            info = tester.get_baseline_info("test_area")

            assert info is not None
            assert info["subject_area"] == "test_area"
            assert info["size"] == len(b"test_data")
            assert info["exists"] is True

    def test_get_baseline_info_nonexistent(self):
        """Test getting baseline info for nonexistent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            info = tester.get_baseline_info("nonexistent")

            assert info is None

    def test_list_baselines(self):
        """Test listing all baselines."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            # Create multiple baseline files
            (baseline_dir / "area1_baseline.png").write_bytes(b"data1")
            (baseline_dir / "area2_baseline.png").write_bytes(b"data2")

            baselines = tester.list_baselines()

            assert len(baselines) == 2
            assert "area1" in baselines
            assert "area2" in baselines

    def test_delete_baseline(self):
        """Test deleting baseline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            # Create baseline file
            baseline_file = baseline_dir / "test_area_baseline.png"
            baseline_file.write_bytes(b"test_data")

            # Delete it
            result = tester.delete_baseline("test_area")

            assert result is True
            assert not baseline_file.exists()

    def test_delete_baseline_nonexistent(self):
        """Test deleting nonexistent baseline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            result = tester.delete_baseline("nonexistent")

            assert result is False


class TestDOMStructureAnalyzer:
    """Test DOM structure analyzer functionality."""

    def test_analyze_current_page(self):
        """Test analyzing current page structure."""
        analyzer = DOMStructureAnalyzer()

        with patch('streamlit.session_state', {'key1': 'value1', 'chart_data': 'test', 'kpi_metric': 42}):
            structure = analyzer.analyze_current_page()

            assert 'timestamp' in structure
            assert 'elements' in structure
            assert 'layout' in structure
            assert structure['session_state_keys'] == 3
            assert 'chart_data' in structure['component_keys']
            assert 'kpi_metric' in structure['component_keys']

    def test_compare_structures_identical(self):
        """Test comparing identical structures."""
        analyzer = DOMStructureAnalyzer()

        structure = {
            'timestamp': 1234567890,
            'session_state_keys': 5,
            'component_keys': ['chart1', 'kpi1']
        }

        comparison = analyzer.compare_structures(structure, structure)

        assert comparison['structure_match'] is True
        assert len(comparison['differences']) == 0

    def test_compare_structures_different(self):
        """Test comparing different structures."""
        analyzer = DOMStructureAnalyzer()

        baseline = {
            'timestamp': 1234567890,
            'session_state_keys': 3,
            'component_keys': ['chart1', 'kpi1']
        }

        current = {
            'timestamp': 1234567891,
            'session_state_keys': 4,
            'component_keys': ['chart1', 'kpi2']
        }

        comparison = analyzer.compare_structures(baseline, current)

        assert comparison['structure_match'] is False
        assert len(comparison['differences']) == 2

        # Check session state difference
        session_diff = next(d for d in comparison['differences'] if d['type'] == 'session_state_keys')
        assert session_diff['baseline_count'] == 3
        assert session_diff['current_count'] == 4

        # Check component difference
        component_diff = next(d for d in comparison['differences'] if d['type'] == 'component_keys')
        assert 'kpi2' in component_diff['added']
        assert 'kpi1' in component_diff['removed']

    @patch('builtins.open')
    @patch('json.dump')
    def test_save_baseline_structure(self, mock_json_dump, mock_open):
        """Test saving baseline structure."""
        analyzer = DOMStructureAnalyzer()

        structure = {'test': 'data'}
        result = analyzer.save_baseline_structure('test_area', structure)

        assert result is True
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once_with(structure, mock_open(), indent=2)

    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    @patch('json.load')
    def test_load_baseline_structure(self, mock_json_load, mock_open, mock_exists):
        """Test loading baseline structure."""
        mock_exists.return_value = True
        mock_json_load.return_value = {'test': 'data'}

        analyzer = DOMStructureAnalyzer()
        result = analyzer.load_baseline_structure('test_area')

        assert result == {'test': 'data'}
        mock_open.assert_called_once()

    @patch('pathlib.Path.exists')
    def test_load_baseline_structure_nonexistent(self, mock_exists):
        """Test loading nonexistent baseline structure."""
        mock_exists.return_value = False

        analyzer = DOMStructureAnalyzer()
        result = analyzer.load_baseline_structure('test_area')

        assert result is None


@pytest.mark.integration
class TestVisualParityIntegration:
    """Integration tests for visual parity system."""

    def test_full_workflow(self):
        """Test complete visual parity workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            # First run - create baseline
            with patch.object(tester, 'capture_screenshot', return_value=b"initial_data"):
                result1 = tester.test_subject_area_parity("integration_test")
                assert result1["status"] == "baseline_created"

            # Second run - compare with baseline
            with patch.object(tester, 'capture_screenshot', return_value=b"initial_data"):
                with patch.object(tester, 'compare_screenshots', return_value=(0.0, "Identical")):
                    result2 = tester.test_subject_area_parity("integration_test")
                    assert result2["status"] == "compared"
                    assert result2["passed"] is True

    def test_baseline_management(self):
        """Test baseline creation, listing, and deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            baseline_dir = Path(temp_dir) / "baselines"
            tester = VisualParityTester(baseline_dir)

            # Create baseline
            with patch.object(tester, 'capture_screenshot', return_value=b"test_data"):
                result = tester.test_subject_area_parity("management_test")
                assert result["status"] == "baseline_created"

            # List baselines
            baselines = tester.list_baselines()
            assert "management_test" in baselines

            # Get baseline info
            info = tester.get_baseline_info("management_test")
            assert info is not None
            assert info["size"] == len(b"test_data")

            # Delete baseline
            deleted = tester.delete_baseline("management_test")
            assert deleted is True

            # Verify deletion
            baselines_after = tester.list_baselines()
            assert "management_test" not in baselines_after