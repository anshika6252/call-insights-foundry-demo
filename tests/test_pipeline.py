from pathlib import Path
from unittest.mock import Mock

import pytest

from call_insights.azure_clients import AzureServiceError
from call_insights.config import Settings
from call_insights.models import CallSummary, Segment, Transcript
from call_insights.pipeline import Pipeline, retry_operation
from call_insights.repository import Repository, StateConflict


@pytest.fixture
def setup(tmp_path):
    repo = Repository(tmp_path / "calls.db")
    call_id = repo.create_call("call.wav", "abc", "hindi", "english", 100, 1000)
    transcript = Transcript(segments=[Segment(id="s1", start_ms=0, end_ms=1000,
                                               text="भुगतान पूरा हो गया है।")])
    summary = CallSummary(overview="Payment complete.", purpose="Payment check", outcome="Resolved")
    speech = Mock()
    speech.transcribe.return_value = transcript
    model = Mock(last_usage={"total_tokens": 42})
    speech.last_request_id = "speech-request-123"
    model.last_request_id = "summary-request-456"
    model.summarize.return_value = summary
    settings = Settings(db_path=tmp_path / "calls.db", summary_deployment="test")
    pipeline = Pipeline(repo, speech, model, settings, sleep=lambda _: None)
    return repo, call_id, speech, model, pipeline


def test_complete_persisted_pipeline_and_no_rerun(setup):
    repo, call_id, speech, model, pipeline = setup
    stages = []
    result = pipeline.process(call_id, Path("call.wav"), stages.append)
    assert repo.get_call(call_id)["status"] == "completed"
    assert repo.get_summary(call_id) == result
    assert stages == ["transcription", "summarization"]
    assert len(repo.list_runs(call_id)) == 2
    assert [run["provider_request_id"] for run in repo.list_runs(call_id)] == ["speech-request-123", "summary-request-456"]
    with pytest.raises(StateConflict):
        pipeline.process(call_id, Path("call.wav"))
    speech.transcribe.assert_called_once()
    model.summarize.assert_called_once()
    assert repo.get_call(call_id)["status"] == "completed"


def test_failed_summary_reuses_transcript(setup):
    repo, call_id, speech, model, pipeline = setup
    result = model.summarize.return_value
    model.summarize.side_effect = AzureServiceError("Quota unavailable.")
    with pytest.raises(AzureServiceError):
        pipeline.process(call_id, Path("call.wav"))
    assert repo.get_call(call_id)["failed_stage"] == "summarization"
    assert repo.get_transcript(call_id)
    model.summarize.side_effect = None
    assert pipeline.retry_summary(call_id) == result
    speech.transcribe.assert_called_once()
    assert repo.get_call(call_id)["status"] == "completed"


def test_retry_only_transient_and_bounded():
    operation = Mock(side_effect=AzureServiceError("Throttled", True, 999))
    sleep = Mock()
    with pytest.raises(AzureServiceError):
        retry_operation(operation, max_attempts=3, sleep=sleep)
    assert operation.call_count == 3
    assert sleep.call_count == 2
    assert all(call.args[0] <= 30 for call in sleep.call_args_list)
    operation = Mock(side_effect=AzureServiceError("Invalid credentials", False))
    with pytest.raises(AzureServiceError):
        retry_operation(operation, sleep=sleep)
    operation.assert_called_once()


def test_unexpected_error_is_sanitized(setup):
    repo, call_id, speech, model, pipeline = setup
    speech.transcribe.side_effect = RuntimeError("secret and transcript should not leak")
    with pytest.raises(AzureServiceError) as error:
        pipeline.process(call_id, Path("call.wav"))
    assert "secret" not in str(error.value)
    assert "secret" not in repo.get_call(call_id)["error"]
    assert repo.get_call(call_id)["failed_stage"] == "transcription"


def test_losing_claim_does_not_fail_active_run(setup):
    repo, call_id, speech, model, pipeline = setup
    repo.start_run(call_id, "transcription")
    with pytest.raises(StateConflict):
        pipeline.process(call_id, Path("call.wav"))
    speech.transcribe.assert_not_called()
    assert repo.get_call(call_id)["status"] == "transcribing"
    assert repo.list_runs(call_id)[0]["outcome"] == "running"


def test_restart_recovery_then_summary_retry(setup):
    repo, call_id, speech, model, pipeline = setup
    repo.save_transcript(call_id, speech.transcribe.return_value)
    repo.start_run(call_id, "summarization")
    assert repo.recover_interrupted() == 1
    pipeline.retry_summary(call_id)
    speech.transcribe.assert_not_called()
    assert repo.get_call(call_id)["status"] == "completed"
