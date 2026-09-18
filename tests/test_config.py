import pytest

from call_insights.config import Settings


def test_missing_settings_are_actionable_without_keys():
    settings = Settings(speech_api_key="never-print-me")
    assert "never-print-me" not in repr(settings)
    assert any("AZURE_SPEECH_ENDPOINT" in error for error in settings.azure_errors())
    assert all("never-print-me" not in error for error in settings.azure_errors())


@pytest.mark.parametrize("endpoint", ["http://azure.test", "https://key:secret@azure.test", "https://azure.test/path", "https://azure.test?key=secret"])
def test_endpoint_validation(endpoint):
    assert Settings(speech_endpoint=endpoint).azure_errors()


def test_bad_numeric_env_fails_safely(monkeypatch, tmp_path):
    monkeypatch.setenv("CALL_INSIGHTS_MAX_ATTEMPTS", "secret")
    with pytest.raises(ValueError, match="must be a number") as error:
        Settings.from_env(dotenv_path=tmp_path / "missing")
    assert "secret" not in str(error.value)
