# Backend implementation notes

`Repository(path)` initializes a local SQLite file and enables foreign keys on every connection. Source audio is never stored in SQLite. Calls preserve their selected English/Hindi input mode, summary language, source mode, size, duration, hash, and timestamps. Transcripts preserve Unicode, provider speaker labels, locales, segment order, and original timing. Summary records retain the deployment and prompt/schema versions.

## Processing ownership

`start_run(call_id, stage)` claims a call using a write transaction and a unique active-run index. Parallel claims, retranscribing a saved transcript, and processing completed calls are rejected. Persist a stage result before calling `finish_run`. Finishing transcription releases the active claim; the persisted transcript allows the pipeline to continue or retry summarization without audio. `fail_call` accepts only the currently active stage and a caller-sanitized message. Run records retain available usage and provider request identifiers.

Call `recover_interrupted()` once at application process startup, not on every Streamlit rerun. It marks previously active runs interrupted and calls failed. Interrupted summarization retains the transcript. Interrupted transcription requires re-upload because temporary audio is removed. This recovery policy assumes one application process; multiple independent app processes sharing a database are outside demo scope.

Deletion rejects active calls and otherwise removes dependent transcripts, summaries, and runs through foreign-key cascades.

## Audio lifetime and limits

`validate_audio` enforces extension, byte limit, and parsed duration. WAV files are read using the Python WAV parser with a complete-frame check; MP3 files are parsed using Mutagen. Limits default to 50 MiB and 600 seconds. Invalid, empty, truncated WAV, and unsupported recordings are rejected before Azure submission. This checks structural readability, not whether a recording contains speech or has sufficient quality.

`temporary_audio` writes to a generated filename and removes it on normal completion or exceptions. Configure a dedicated application temporary directory. `cleanup_stale_audio` removes only files matching the generated prefix and supported suffix, older than its retention window; it does not follow symlinks. Abrupt process termination can leave a temporary file until the next cleanup.

## Verification

Repository tests cover concurrent claims, restart persistence, Unicode, cascade deletion, active-deletion rejection, summary evidence references, result-before-completion safeguards, interrupted-stage recovery, and stale failure rejection. Audio tests cover parsing, limits, invalid content, truncated WAV, safe temporary paths, and cleanup after failure. Live Azure behavior and speech quality require separate evaluation.
