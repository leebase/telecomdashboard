import json
from unittest.mock import Mock, patch

from telecomdashboard.main import _handle_health_command, _health_exit_code, main


def test_health_exit_code_mapping():
    assert _health_exit_code("healthy") == 0
    assert _health_exit_code("degraded") == 1
    assert _health_exit_code("unhealthy") == 2
    assert _health_exit_code("unknown") == 3


def test_handle_health_command_simple(capsys):
    checker = Mock()
    checker.get_simple_health.return_value = {"status": "healthy", "version": "test"}

    with patch("telecomdashboard.main._load_health_checker", return_value=checker):
        exit_code = _handle_health_command(simple=True, pretty=False)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {"status": "healthy", "version": "test"}
    checker.get_simple_health.assert_called_once_with()


def test_handle_health_command_pretty(capsys):
    checker = Mock()
    checker.run_all_checks.return_value = {"status": "degraded", "checks": {"db": {"status": "degraded"}}}

    with patch("telecomdashboard.main._load_health_checker", return_value=checker):
        exit_code = _handle_health_command(simple=False, pretty=True)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert json.loads(captured.out) == {"status": "degraded", "checks": {"db": {"status": "degraded"}}}
    assert "\n" in captured.out
    checker.run_all_checks.assert_called_once_with()


def test_main_health_subcommand():
    with patch("telecomdashboard.main._handle_health_command", return_value=2) as mock_health:
        exit_code = main(["health", "--simple"])

    assert exit_code == 2
    mock_health.assert_called_once_with(simple=True, pretty=False)
