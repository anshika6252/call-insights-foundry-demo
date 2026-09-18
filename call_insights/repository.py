"""Transactional SQLite persistence. Every operation uses its own connection."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4
from .models import CallSummary, Transcript, InputMode, SummaryLanguage


def _now():
    return datetime.now(timezone.utc).isoformat()


class StateConflict(ValueError):
    """An operation is incompatible with persisted processing state."""


class Repository:
    def __init__(self, path):
        self.path = str(path)
        if self.path == ':memory:':
            raise ValueError('Use a filesystem SQLite path so connections share persistence.')
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version > 1:
                raise ValueError('This database was created by a newer application version.')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS calls (
                    id TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT NOT NULL,
                    input_mode TEXT NOT NULL, summary_language TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL, duration_ms INTEGER NOT NULL,
                    source_mode TEXT NOT NULL, status TEXT NOT NULL,
                    failed_stage TEXT, error TEXT, created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL, detected_locales TEXT NOT NULL DEFAULT '[]',
                    transcript_duration_ms INTEGER);
                CREATE INDEX IF NOT EXISTS calls_hash ON calls(sha256);
                CREATE TABLE IF NOT EXISTS transcript_segments (
                    call_id TEXT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
                    sequence INTEGER NOT NULL, id TEXT NOT NULL, start_ms INTEGER NOT NULL,
                    end_ms INTEGER NOT NULL, text TEXT NOT NULL, speaker TEXT, locale TEXT,
                    PRIMARY KEY(call_id, id), UNIQUE(call_id, sequence));
                CREATE TABLE IF NOT EXISTS summaries (
                    call_id TEXT PRIMARY KEY REFERENCES calls(id) ON DELETE CASCADE,
                    structured_json TEXT NOT NULL, language TEXT NOT NULL,
                    deployment TEXT NOT NULL, prompt_version TEXT NOT NULL,
                    schema_version TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS processing_runs (
                    id TEXT PRIMARY KEY, call_id TEXT NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
                    stage TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT,
                    outcome TEXT NOT NULL, error TEXT, usage_json TEXT, provider_request_id TEXT);
                CREATE INDEX IF NOT EXISTS runs_call ON processing_runs(call_id);
                CREATE UNIQUE INDEX IF NOT EXISTS active_run ON processing_runs(call_id)
                    WHERE outcome = 'running';
                PRAGMA user_version=1;
            ''')

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def create_call(self, filename, sha256, input_mode, summary_language, size_bytes,
                    duration_ms, source_mode='live'):
        input_mode = InputMode(input_mode).value
        summary_language = SummaryLanguage(summary_language).value
        if source_mode not in {'live', 'sample'} or size_bytes < 0 or duration_ms < 0:
            raise ValueError('Invalid call metadata')
        call_id, now = str(uuid4()), _now()
        with self._connect() as db:
            db.execute('''INSERT INTO calls
                (id,filename,sha256,input_mode,summary_language,size_bytes,duration_ms,source_mode,
                 status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (call_id, filename, sha256, input_mode, summary_language, size_bytes,
                 duration_ms, source_mode, 'uploaded', now, now))
        return call_id

    def get_call(self, call_id):
        with self._connect() as db:
            row = db.execute('SELECT * FROM calls WHERE id=?', (call_id,)).fetchone()
            return dict(row) if row else None

    def list_calls(self):
        with self._connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM calls ORDER BY created_at DESC')]

    def find_by_hash(self, sha256):
        with self._connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM calls WHERE sha256=? ORDER BY created_at DESC', (sha256,))]

    def save_transcript(self, call_id, transcript: Transcript):
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT id FROM calls WHERE id=?', (call_id,)).fetchone():
                raise KeyError(call_id)
            db.execute('DELETE FROM transcript_segments WHERE call_id=?', (call_id,))
            db.executemany('INSERT INTO transcript_segments VALUES (?,?,?,?,?,?,?,?)',
                [(call_id, i, s.id, s.start_ms, s.end_ms, s.text, s.speaker, s.locale)
                 for i, s in enumerate(transcript.segments)])
            db.execute('UPDATE calls SET detected_locales=?, transcript_duration_ms=?,updated_at=? WHERE id=?',
                       (json.dumps(transcript.detected_locales), transcript.duration_ms, _now(), call_id))

    def get_transcript(self, call_id):
        with self._connect() as db:
            rows = db.execute('SELECT id,start_ms,end_ms,text,speaker,locale FROM transcript_segments WHERE call_id=? ORDER BY sequence', (call_id,)).fetchall()
            if not rows:
                return None
            call = db.execute('SELECT detected_locales,transcript_duration_ms FROM calls WHERE id=?', (call_id,)).fetchone()
            return Transcript(segments=[dict(row) for row in rows],
                              detected_locales=json.loads(call['detected_locales']),
                              duration_ms=call['transcript_duration_ms'])

    def save_summary(self, call_id, summary: CallSummary, language='english', deployment='', prompt_version='1'):
        transcript = self.get_transcript(call_id)
        if transcript is None:
            raise StateConflict('A transcript is required before saving a summary.')
        summary.validate_evidence(transcript)
        language = SummaryLanguage(language).value
        with self._connect() as db:
            db.execute('INSERT OR REPLACE INTO summaries VALUES (?,?,?,?,?,?,?)',
                       (call_id, summary.model_dump_json(), language, deployment, prompt_version, '1', _now()))

    def get_summary(self, call_id):
        with self._connect() as db:
            row = db.execute('SELECT structured_json FROM summaries WHERE call_id=?', (call_id,)).fetchone()
            return CallSummary.model_validate_json(row[0]) if row else None

    def start_run(self, call_id, stage):
        statuses = {'transcription': 'transcribing', 'summarization': 'summarizing'}
        if stage not in statuses:
            raise ValueError('Unknown processing stage')
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            call = db.execute('SELECT status FROM calls WHERE id=?', (call_id,)).fetchone()
            if call is None:
                raise KeyError(call_id)
            if call['status'] in {'transcribing', 'summarizing', 'completed'}:
                raise StateConflict('Call is already processing or completed.')
            has_transcript = db.execute('SELECT 1 FROM transcript_segments WHERE call_id=? LIMIT 1', (call_id,)).fetchone()
            if stage == 'summarization' and not has_transcript:
                raise StateConflict('Transcribe the recording first.')
            if stage == 'transcription' and has_transcript:
                raise StateConflict('Transcript already exists; retry summarization.')
            run_id = str(uuid4())
            db.execute('INSERT INTO processing_runs (id,call_id,stage,started_at,outcome) VALUES (?,?,?,?,?)',
                       (run_id, call_id, stage, _now(), 'running'))
            db.execute('UPDATE calls SET status=?,failed_stage=NULL,error=NULL,updated_at=? WHERE id=?',
                       (statuses[stage], _now(), call_id))
            return run_id

    def finish_run(self, run_id, usage=None, provider_request_id=None):
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            run = db.execute('SELECT * FROM processing_runs WHERE id=? AND outcome=?', (run_id, 'running')).fetchone()
            if run is None:
                raise StateConflict('Run is no longer active.')
            table = 'summaries' if run['stage'] == 'summarization' else 'transcript_segments'
            if not db.execute(f'SELECT 1 FROM {table} WHERE call_id=? LIMIT 1', (run['call_id'],)).fetchone():
                raise StateConflict('Persist the processing result before completing its run.')
            db.execute('UPDATE processing_runs SET outcome=?,ended_at=?,usage_json=?,provider_request_id=? WHERE id=?',
                       ('completed', _now(), json.dumps(usage) if usage is not None else None, provider_request_id, run_id))
            status = 'completed' if run['stage'] == 'summarization' else 'uploaded'
            db.execute('UPDATE calls SET status=?,failed_stage=NULL,error=NULL,updated_at=? WHERE id=?', (status, _now(), run['call_id']))

    def fail_call(self, call_id, stage, error):
        # Only caller-sanitized, user-facing messages belong here; never provider exception text.
        statuses = {'transcription': 'transcribing', 'summarization': 'summarizing'}
        if stage not in statuses:
            raise ValueError('Unknown processing stage')
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            call = db.execute('SELECT status FROM calls WHERE id=?', (call_id,)).fetchone()
            if call is None:
                raise KeyError(call_id)
            if call['status'] != statuses[stage]:
                raise StateConflict('Only the active processing stage can fail this call.')
            db.execute('UPDATE processing_runs SET outcome=?,ended_at=?,error=? WHERE call_id=? AND outcome=?',
                       ('failed', _now(), str(error), call_id, 'running'))
            db.execute('UPDATE calls SET status=?,failed_stage=?,error=?,updated_at=? WHERE id=?',
                       ('failed', stage, str(error), _now(), call_id))

    def recover_interrupted(self):
        """Call once at process startup, never on each UI rerun."""
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            active = db.execute("SELECT id,status FROM calls WHERE status IN ('transcribing','summarizing')").fetchall()
            for call in active:
                stage = 'transcription' if call['status'] == 'transcribing' else 'summarization'
                message = 'Processing was interrupted. Retry summary or re-upload audio as appropriate.'
                db.execute("UPDATE calls SET status='failed',failed_stage=?,error=?,updated_at=? WHERE id=?", (stage, message, _now(), call['id']))
                db.execute("UPDATE processing_runs SET outcome='interrupted',ended_at=?,error=? WHERE call_id=? AND outcome='running'", (_now(), message, call['id']))
            return len(active)

    def list_runs(self, call_id):
        with self._connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM processing_runs WHERE call_id=? ORDER BY started_at', (call_id,))]

    def delete_call(self, call_id):
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT status FROM calls WHERE id=?', (call_id,)).fetchone()
            if row and row['status'] in {'transcribing', 'summarizing'}:
                raise StateConflict('Wait for processing before deleting this call.')
            db.execute('DELETE FROM calls WHERE id=?', (call_id,))
