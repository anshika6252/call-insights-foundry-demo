# Independent code review

Reviewed 2026-09-18 by the code-review agent. Scope: application, Azure adapters, SQLite lifecycle, upload handling, exports, tests and documentation. English and Hindi only; Hinglish is deferred. This review used no Azure credentials, resources, or live requests.

## Finding and regression evidence

**P1 — Streamlit cancellation could strand an active call.** `Pipeline._stage` caught `Exception`, while Streamlit's `StopException` and rerun control signals inherit `BaseException`. An interruption at the progress callback left the persisted stage running. Cached bootstrap recovery would not run again in the same process, preventing retry and deletion until restart.

The independent regression in `tests/test_review_regressions.py` reproduces cancellation during both transcription and summarization using the real Streamlit `StopException`. Both tests initially failed: persisted state remained `transcribing` or `summarizing`. **Resolved and independently rechecked:** the stage handler now releases its claimed stage with a sanitized cancellation error and re-raises the original control signal. Both regressions pass, including saved-transcript reuse on summary retry and deletion after cancelled transcription.

## Reviewed safeguards

- SQLite writes use per-operation connections, foreign keys, and atomic stage claims; a competing claim cannot fail the winning caller's stage.
- Completed calls are protected against accidental processing reruns. History deletion cascades to segments, summaries and run metadata and is prohibited during processing.
- Temporary audio uses generated filenames and a context manager; normal error and cancellation unwinding remove the file. Stale cleanup limits removal to generated, aged WAV/MP3 files.
- Azure requests do not follow redirects; displayable failures omit credentials, raw response bodies and transcript contents. Input limits are enforced before calls.
- Summaries require valid structure and existing segment references; this checks referential integrity, not factual support. Live bilingual factual review remains necessary.
- Preview transcripts and summaries are labeled handwritten and synthetic, do not make service requests, and are not saved to history. Export provenance is explicit.
- Transient retries are bounded. Failed summarization reuses the persisted transcript. Hindi survives storage and exports.
- Final observability changes were reviewed: request IDs come only from three allowlisted response headers, are limited to 128 safe characters, and reset before each provider call. Completed runs persist the final request ID; failed-run IDs are not currently persisted. The UI computes elapsed stage duration from repository-generated timestamps and labels that retries are included.

## Validation and acceptance boundary

Initial implementation suite: **53 passed**. The two independent cancellation regressions initially failed as described above. After correction and the other agents' additional tests, the independent full-suite run `.venv/Scripts/python.exe -m pytest -q` completed with **62 passed in 10.34 seconds**. The final request-ID persistence and stage-duration changes received focused independent code review; the coordinator then reported the final full suite at **69 passed in 10.61 seconds**, with `pip check` clean. That final run was not redundantly repeated by the reviewer. No unresolved implementation blocker was identified in this bounded review.

Offline implementation evidence supports scaffold/configuration (#3), SQLite (#4), upload handling (#5), history/exports/deletion (#9), and recovery (#10). UI (#8) and documentation (#12) remain open where their original acceptance criteria require actual end-to-end processing or a verified live walkthrough; do not weaken those criteria merely to close issues.

Azure resource verification (#1), language evaluation (#2), actual transcription integration (#6), generated-summary factual quality (#7), live end-to-end UI acceptance (#8), final multilingual acceptance (#11), and live demo walkthrough verification (#12) still require configured Azure resources and representative English/Hindi audio. Mock responses and synthetic text previews cannot establish those outcomes. No measured accuracy, live latency, or cost claims are made.

This is a bounded review for the documented local, single-process, single-user demo; it is not a production security certification or multi-process concurrency assessment.
