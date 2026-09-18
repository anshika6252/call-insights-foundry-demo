# Validation report

Date: 2026-09-18. Scope: local, single-process English/Hindi demo. No live Azure requests were made.

## UI configuration follow-up (#13)

Added session-only Azure endpoint/key/deployment configuration, with environment/.env fallback. Full local suite: **72 passed in 8.25 seconds**. New checks cover field precedence, blank fallback, masked inputs, invalid-submission rollback, clearing, rerun persistence and separate-session isolation. Browser inspection confirmed the sidebar form renders. Applying settings makes no Azure request; live acceptance remains pending. The earlier implementation validation below is retained as historical evidence.

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

GitHub Actions also passed on both **Ubuntu and Windows with Python 3.12**, including fresh dependency installation and the full offline suite. [Successful run for implementation commit 33a9165](https://github.com/anshika6252/call-insights-foundry-demo/actions/runs/35317563741). This remote run independently confirms the software checks; it uses no Azure credentials.
