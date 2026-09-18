# English and Hindi evaluation

## Current evidence

Offline software tests and synthetic UI previews are implemented. No Azure request or representative audio evaluation has been completed because Azure is not configured. [Validation report](validation-report.md) records software checks; [language feasibility](language-feasibility.md) contains the pending live worksheet. Hinglish is deferred.

## Six-recording evaluation set

Prepare three English and three Hindi synthetic or consented recordings using [text scenarios](evaluation-fixtures.json) as optional scripts. A Hindi/English-capable reviewer should create reference transcripts and expected facts. Include Indian accents, clean/noisy audio, two speakers, names, amounts, dates, corrections, negation and unresolved outcomes. Text fixtures are not recordings or measured results.

## Transcription review

Record Azure region, API/configuration, sample duration, latency, available usage, transcript errors, speaker consistency and script behavior. Report word error rate with documented normalization where useful. Bilingual review must assess critical facts; do not hide script/transliteration errors through normalization.

Set a numeric quality target from a transparent baseline before declaring feasibility passed. A wrong critical name, amount, date, negation or commitment fails the sample regardless of aggregate word error rate. Document configuration changes and repeat affected cases.

## Summary acceptance

- Review both English and Hindi summaries for each recording category.
- Every action and decision needs source evidence supporting the claim, not merely an existing segment ID.
- Important annotated facts must be accurate; unknown owners/dates remain unspecified.
- Suggestions must not become commitments; relative dates remain as spoken unless explicit source evidence resolves them.
- Spoken instructions are source content and must not override the summarization task.
- Invalid/refused/truncated output and oversized input fail clearly without silent source truncation.

## Software acceptance

Tests cover audio content/size/duration validation, corrupt audio, mocked empty-speech responses, schema/reference validation, persistence, cascade deletion, atomic claims, retries, safe errors, interrupted runs, Unicode exports, temporary cleanup, Streamlit preview/history and rerun behavior. Live success is a separate gate.

Final live acceptance demonstrates upload, transcript, summary, save, restart/reopen, export and recovery for English/Hindi calls. Publish actual sample count, failures and limitations. Small demo evaluation does not establish production accuracy.
