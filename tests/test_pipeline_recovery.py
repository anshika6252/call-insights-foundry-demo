from pathlib import Path
from unittest.mock import Mock
import pytest
from call_insights.azure_clients import AzureServiceError
from call_insights.config import Settings
from call_insights.models import CallSummary, Segment, Transcript, EvidenceItem
from call_insights.pipeline import Pipeline
from call_insights.repository import Repository


def setup_pipeline(tmp_path):
    repo = Repository(tmp_path / 'recovery.db')
    call = repo.create_call('call.wav', 'hash', 'english', 'english', 1, 1000)
    speech = Mock()
    transcript = Transcript(segments=[Segment(id='s1',start_ms=0,end_ms=1000,text='I will call tomorrow.')])
    speech.transcribe.return_value = transcript
    summary = CallSummary(overview='Follow-up',purpose='Call',outcome='Pending')
    model = Mock(last_usage={'total_tokens': 20})
    model.summarize.return_value = summary
    sleep = Mock()
    pipeline = Pipeline(repo,speech,model,Settings(db_path=tmp_path/'recovery.db'),sleep=sleep)
    return repo,call,speech,model,pipeline,sleep


def test_transient_eventual_success_records_one_run_per_stage(tmp_path):
    repo,call,speech,model,pipeline,sleep = setup_pipeline(tmp_path)
    transcript = speech.transcribe.return_value
    summary = model.summarize.return_value
    speech.transcribe.side_effect = [AzureServiceError('Throttled',True,1),transcript]
    model.summarize.side_effect = [AzureServiceError('Unavailable',True),summary]
    assert pipeline.process(call,Path('unused.wav')) == summary
    assert speech.transcribe.call_count == 2
    assert model.summarize.call_count == 2
    assert sleep.call_count == 2
    assert [run['outcome'] for run in repo.list_runs(call)] == ['completed','completed']
    assert repo.get_call(call)['status'] == 'completed'


def test_invalid_summary_evidence_is_not_retried_or_saved(tmp_path):
    repo,call,speech,model,pipeline,sleep = setup_pipeline(tmp_path)
    model.summarize.return_value = CallSummary(overview='x',purpose='y',outcome='z',decisions=[EvidenceItem(text='Unsupported',segment_ids=['missing'])])
    with pytest.raises(AzureServiceError):
        pipeline.process(call,Path('unused.wav'))
    model.summarize.assert_called_once()
    sleep.assert_not_called()
    assert repo.get_summary(call) is None
    assert repo.get_transcript(call) is not None
    assert repo.get_call(call)['failed_stage'] == 'summarization'
    assert [run['outcome'] for run in repo.list_runs(call)] == ['completed','failed']
