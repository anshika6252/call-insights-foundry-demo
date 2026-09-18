from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pytest
from call_insights.repository import Repository, StateConflict
from call_insights.models import Transcript, Segment, CallSummary, EvidenceItem


@pytest.fixture
def repo(tmp_path):
    return Repository(tmp_path / 'calls.db')


def new_call(repo):
    return repo.create_call('test.wav', 'abc', 'hindi', 'english', 100, 1000)


def transcript():
    return Transcript(segments=[Segment(id='s1',start_ms=0,end_ms=1000,text='भुगतान हो गया',speaker='1')],detected_locales=['hi-IN'])


def test_restart_unicode_and_cascade(repo):
    call = new_call(repo)
    run = repo.start_run(call, 'transcription')
    repo.save_transcript(call, transcript())
    repo.finish_run(run)
    run = repo.start_run(call, 'summarization')
    summary = CallSummary(overview='भुगतान',purpose='Check payment',outcome='Confirmed', decisions=[EvidenceItem(text='Paid',segment_ids=['s1'])])
    repo.save_summary(call, summary, deployment='test')
    repo.finish_run(run, usage={'tokens': 100})
    restarted = Repository(repo.path)
    assert restarted.get_transcript(call) == transcript()
    assert restarted.get_summary(call) == summary
    assert restarted.get_call(call)['status'] == 'completed'
    assert len(restarted.find_by_hash('abc')) == 1
    restarted.delete_call(call)
    with sqlite3.connect(repo.path) as db:
        for table in ['calls','transcript_segments','summaries','processing_runs']:
            assert db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0


def test_claim_is_atomic(repo):
    call = new_call(repo)
    def claim(_):
        try:
            return repo.start_run(call, 'transcription')
        except StateConflict:
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(claim, range(4)))
    assert sum(value is not None for value in results) == 1
    with pytest.raises(StateConflict):
        repo.delete_call(call)


def test_interrupted_summary_reuses_transcript(repo):
    call = new_call(repo)
    run = repo.start_run(call, 'transcription')
    repo.save_transcript(call, transcript())
    repo.finish_run(run)
    repo.start_run(call, 'summarization')
    assert Repository(repo.path).recover_interrupted() == 1
    assert repo.get_call(call)['failed_stage'] == 'summarization'
    assert repo.list_runs(call)[-1]['outcome'] == 'interrupted'
    assert repo.get_transcript(call) == transcript()
    repo.start_run(call, 'summarization')
    repo.fail_call(call, 'summarization', 'The model response was invalid.')
    assert repo.get_call(call)['status'] == 'failed'


def test_missing_result_cannot_complete_and_evidence_checked(repo):
    call = new_call(repo)
    with pytest.raises(StateConflict):
        repo.start_run(call, 'summarization')
    run = repo.start_run(call, 'transcription')
    with pytest.raises(StateConflict):
        repo.finish_run(run)
    assert repo.list_runs(call)[0]['outcome'] == 'running'
    repo.save_transcript(call, transcript())
    bad = CallSummary(overview='a',purpose='b',outcome='c',decisions=[EvidenceItem(text='x',segment_ids=['missing'])])
    with pytest.raises(ValueError):
        repo.save_summary(call,bad)
    assert repo.get_summary(call) is None


def test_stale_failure_cannot_overwrite_new_stage(repo):
    call = new_call(repo)
    run = repo.start_run(call, 'transcription')
    repo.save_transcript(call, transcript())
    repo.finish_run(run)
    repo.start_run(call, 'summarization')
    with pytest.raises(StateConflict):
        repo.fail_call(call, 'transcription', 'Stale failure')
    assert repo.get_call(call)['status'] == 'summarizing'
    assert repo.list_runs(call)[-1]['outcome'] == 'running'


def test_metadata_and_transcription_recovery(repo):
    call = repo.create_call('हिंदी.wav', 'hash', 'hindi', 'hindi', 42, 2000, 'sample')
    assert repo.get_call(call)['source_mode'] == 'sample'
    assert repo.get_call(call)['summary_language'] == 'hindi'
    repo.start_run(call, 'transcription')
    assert repo.recover_interrupted() == 1
    assert repo.recover_interrupted() == 0
    assert repo.get_call(call)['failed_stage'] == 'transcription'
    repo.start_run(call, 'transcription')
    assert len(repo.list_runs(call)) == 2
    with pytest.raises(ValueError):
        repo.create_call('bad.wav', 'x', 'hinglish', 'english', 1, 1)


def test_schema_version_and_reject_newer_database(tmp_path):
    path = tmp_path / 'versioned.db'
    Repository(path)
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 1
        db.execute('PRAGMA user_version=2')
        before = db.execute('SELECT name,sql FROM sqlite_master ORDER BY name').fetchall()
    with pytest.raises(ValueError, match='newer'):
        Repository(path)
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 2
        assert db.execute('SELECT name,sql FROM sqlite_master ORDER BY name').fetchall() == before
