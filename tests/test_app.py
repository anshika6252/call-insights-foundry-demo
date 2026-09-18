from pathlib import Path

from streamlit.testing.v1 import AppTest

from call_insights.repository import Repository
from call_insights.sample_data import sample_call


def setup_app(monkeypatch, tmp_path):
    monkeypatch.setenv("CALL_INSIGHTS_DB_PATH", str(tmp_path / "app.sqlite3"))
    monkeypatch.setenv("CALL_INSIGHTS_TEMP_DIR", str(tmp_path / "audio"))
    for key in ["AZURE_SPEECH_ENDPOINT", "AZURE_SPEECH_API_KEY", "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"]:
        monkeypatch.setenv(key, "")
    return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15)


def test_missing_config_and_hindi_preview(monkeypatch, tmp_path):
    app = setup_app(monkeypatch, tmp_path).run()
    assert not app.exception
    assert any("Azure setup pending" in message.value for message in app.warning)
    assert app.get("file_uploader")[0].disabled
    app.radio[0].set_value("Hindi").run()
    assert not app.exception
    assert any("भुगतान" in message.value for message in app.markdown)
    assert len(Repository(tmp_path / "app.sqlite3").list_calls()) == 0


def test_saved_history_delete_requires_confirmation(monkeypatch, tmp_path):
    app = setup_app(monkeypatch, tmp_path)
    repo = Repository(tmp_path / "app.sqlite3")
    call_id = repo.create_call("example.wav", "hash", "english", "english", 500, 15000)
    transcript, summary = sample_call()
    run = repo.start_run(call_id, "transcription")
    repo.save_transcript(call_id, transcript)
    repo.finish_run(run)
    run = repo.start_run(call_id, "summarization")
    repo.save_summary(call_id, summary)
    repo.finish_run(run)
    app.run()
    assert not app.exception
    assert len(app.get("download_button")) == 6
    delete = next(button for button in app.button if button.label == "Delete call")
    assert delete.disabled
    app.checkbox[0].check().run()
    next(button for button in app.button if button.label == "Delete call").click().run()
    assert not app.exception
    assert repo.get_call(call_id) is None


def test_interrupted_between_stages_can_retry_without_automatic_processing(monkeypatch, tmp_path):
    import call_insights.pipeline
    def forbidden(*args, **kwargs):
        raise AssertionError("Reruns must never construct an Azure pipeline")
    monkeypatch.setattr(call_insights.pipeline, "build_pipeline", forbidden)
    app = setup_app(monkeypatch, tmp_path)
    repo = Repository(tmp_path / "app.sqlite3")
    call_id = repo.create_call("pending.wav", "hash", "english", "english", 500, 15000)
    run = repo.start_run(call_id, "transcription")
    repo.save_transcript(call_id, sample_call()[0])
    repo.finish_run(run)
    app.run()
    app.run()
    assert not app.exception
    retry = next(button for button in app.button if button.label == "Retry summary")
    assert retry.disabled  # Credentials remain absent.
    assert len(repo.list_calls()) == 1
    assert len(repo.list_runs(call_id)) == 1
