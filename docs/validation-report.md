# Validation report

Date: 2026-09-18. Scope: local, single-process English/Hindi demo. No live Azure requests were made.

## Completed checks

| Check | Result |
| --- | --- |
| Fresh Python 3.12 virtual environment and pinned direct dependencies | Installed successfully |
| Full offline pytest suite | 69 passed in 10.61 seconds |
| Dependency consistency (`python -m pip check`) | No broken requirements |
| Independent code review | Cancellation defect found, fixed and independently verified; no remaining implementation blocker identified |
| Local Streamlit startup | Server running on 127.0.0.1:8501 |
| Browser inspection | Setup warning and disabled upload visible; English/Hindi synthetic previews and expandable evidence render correctly |
| Git whitespace check | Passed |

Test evidence includes mocked English/Hindi Azure requests, malformed/refused/truncated responses, strict schema/evidence validation, safe errors, input budget checks, safe request-ID handling, retries, SQLite persistence/cascades/versioning, concurrent stage claims, interruption/cancellation recovery, WAV validation, MP3 rejection, temporary cleanup, Unicode exports, Streamlit history/delete guards and rerun behavior.

The independent reviewer ran the suite at 62 tests; seven request-ID cases were added afterward. The reviewer inspected that final change, and the coordinator ran all 69 tests. Completed-stage provider request IDs are persisted when available; IDs from failed requests are not currently saved to the database. Stage duration includes retries and is not advertised as provider-only latency.

![Hindi synthetic preview](screenshots/hindi-preview.png)

The preview is handwritten and cannot demonstrate recognition or generated-summary quality. WAV test audio is generated for parser checks. Mock responses are fabricated contract fixtures, not recorded Azure outputs.

## Pending checks

- Azure subscription/resource access, region, API compatibility, deployed model and quota verification (#1).
- Six representative English/Hindi recordings, reference transcripts, speech accuracy, speaker consistency and script behavior (#2/#6).
- Actual generated English/Hindi summaries reviewed for facts, evidence and unsupported commitments (#7/#11).
- Live upload-to-history/export workflow and fresh live demo rehearsal (#8/#12).
- Measured Azure cost and service latency; no estimates are presented as actuals.

GitHub Actions is configured for Python 3.12 on Ubuntu and Windows. Its remote run is tracked separately from these local checks.
