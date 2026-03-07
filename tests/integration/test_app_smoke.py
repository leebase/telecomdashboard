from streamlit.testing.v1 import AppTest


def test_main_dashboard_renders_without_exceptions():
    at = AppTest.from_file("app.py")
    at.run(timeout=60)

    assert not at.exception
    assert len(at.tabs) >= 5
