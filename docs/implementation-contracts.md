# Implementation contracts

The application is a single-process Streamlit demo. Python modules share the
Pydantic v2 contracts in `call_insights/models.py`; Azure response dictionaries
must be converted at the adapter boundary. UI code must not depend on provider
response formats. JSON and exports preserve Unicode.

## Models and service boundary

- `InputMode`: `english`, `hindi`. Users select the recording language explicitly.
  Hinglish and automatic language detection are outside this implementation.
- `SummaryLanguage`: `english`, `hindi`.
- `Segment`: stable string `id`, nonnegative `start_ms`/`end_ms`, original `text`,
  optional neutral `speaker` label and `locale`.
- `Transcript`: nonempty `segments` with unique IDs, `detected_locales`, optional
  `duration_ms`. Preserve segment ordering from the provider. Overlapping speaker
  segments are allowed.
- `CallSummary`: `overview`, `purpose`, `key_points`, `decisions`, `action_items`,
  `unresolved_questions`, `outcome`. Decisions use `text` and `segment_ids`;
  actions use `description`, optional `owner`/`due_date`, and `segment_ids`.
- `CallSummary.validate_evidence(transcript)` rejects unknown references.
  Decisions and actions require at least one reference. This validates links,
  not truth: human language evaluation is a separate release gate.

Adapter methods:

```python
SpeechClient.transcribe(path: Path, input_mode: InputMode) -> Transcript
SummaryClient.summarize(transcript: Transcript, language: SummaryLanguage) -> CallSummary
```

Construct adapters from explicit configuration. Never read credentials from
model objects, UI widgets, or saved calls. Provider errors exposed to the UI
contain a safe message and retryability classification; raw response bodies
must not appear in logs or history.

## Persistence and orchestration responsibilities

The repository owns SQLite transactions and foreign-key cascade deletion. It
stores transcript and summary models as lossless JSON or normalized records.
Persist original filename, SHA-256, input mode, summary language, status,
timestamps, and failure stage alongside results. Summary metadata contains
deployment, schema version, and prompt version outside model-generated text.

The pipeline owns explicit processing commands, in-flight exclusion, bounded
transient retries, status transitions, and run metrics. Save a successful
transcript before calling summarization. A summary retry reloads the transcript
and makes no Speech call. UI reruns only render state until a user explicitly
submits a processing command. Interrupted active jobs become failed with a
recoverable stage at application startup, never on ordinary UI reruns.

Temporary audio cleanup runs in `finally`, including validation and service
failures. A failed transcription requires re-upload after cleanup. Avoid
filename-derived paths. Reject oversized audio and transcript inputs before
sending a provider request. Never truncate a transcript silently.

## Feasibility and release gates

Implementation and mock tests can proceed without Azure credentials. They do
not prove deployed model availability, live Speech compatibility, or language
quality. Issue #1 requires live Azure configuration verification; issue #2
requires representative recordings with checked reference transcripts. These
issues remain open until evidence exists. The same limit applies to live
acceptance portions of issues #6, #7, and #11.

Use at least three recordings each for English and Hindi. Explicitly
test negation, amounts, dates, named entities, speaker separation, and script
behavior. Record provider configuration,
latency, failures, and factual summary review without storing private samples
or credentials in Git. A mock or synthetic demo must be visibly identified as
such and cannot be used as evidence of Azure or multilingual quality.
