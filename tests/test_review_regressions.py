"""Independent review regressions for cancellation and provider response boundaries."""
from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.runtime.scriptrunner_utils.exceptions import StopException

from call_insights.config import Settings
from call_insights.pipeline import Pipeline
from call_insights.repository import Repository
from call_insights.sample_data import sample_call


@pytest.mark.parametrize("stage", ["transcription", "summarization"])
def test_streamlit_cancellation_releases_owned_stage(tmp_path, stage):
    repo = Repository(tmp_path / "review.db")
    call_id = repo.create_call("test.wav", "hash", "english", "english", 1, 1000)
    transcript, summary = sample_call()
    speech = Mock()
    speech.transcribe.return_value = transcript
    model = Mock(last_usage={})
    model.summarize.return_value = summary
    pipeline = Pipeline(repo, speech, model, Settings())

    def progress(current):
        if current == stage:
            raise StopException()

    with pytest.raises(StopException):
        pipeline.process(call_id, Path("unused.wav"), on_progress=progress)

    assert repo.get_call(call_id)["status"] == "failed"
    assert repo.get_call(call_id)["failed_stage"] == stage
    assert all(run["outcome"] != "running" for run in repo.list_runs(call_id))
    if stage == "summarization":
        assert repo.get_transcript(call_id) == transcript
        assert pipeline.retry_summary(call_id) == summary
        speech.transcribe.assert_called_once()
    else:
        speech.transcribe.assert_not_called()
        repo.delete_call(call_id)
        assert repo.get_call(call_id) is None
