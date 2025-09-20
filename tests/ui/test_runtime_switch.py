from ui.runtime_switch import is_metadata_enabled


def test_metadata_flag_defaults_false(monkeypatch):
    monkeypatch.delenv("USE_METADATA", raising=False)
    assert is_metadata_enabled() is False


def test_metadata_flag_true(monkeypatch):
    monkeypatch.setenv("USE_METADATA", "true")
    # clear cache
    is_metadata_enabled.cache_clear()  # type: ignore[attr-defined]
    assert is_metadata_enabled() is True


def test_metadata_flag_handles_numeric(monkeypatch):
    monkeypatch.setenv("USE_METADATA", "1")
    is_metadata_enabled.cache_clear()  # type: ignore[attr-defined]
    assert is_metadata_enabled() is True
