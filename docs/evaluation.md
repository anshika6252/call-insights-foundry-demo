# Language and quality evaluation

## Evaluation set

Prepare at least nine short synthetic or consented recordings: three English, three Hindi, and three Hinglish. Have a Hindi/English-capable reviewer produce reference transcripts and expected facts. Include Indian accents, clean and noisy audio, two speakers, names, amounts, dates, corrections, negation, and unresolved outcomes. Hinglish samples must include within-sentence switching, not only alternating monolingual turns.

Example content: “Payment ho gaya hai, but confirmation email nahi aaya.” Include both clear actions and suggestions that must not be reported as commitments.

## Transcription review

Record selected Azure service/configuration, region, API/model version, sample language category, duration, processing latency, available usage, transcript errors, speaker consistency, and script behavior. Report word error rate where useful with documented normalization; cross-script/transliteration differences require bilingual review and must not be concealed by normalization.

The language feasibility issue sets measured thresholds after the baseline. Before proceeding, document whether critical names, amounts, dates, and negation are preserved on the demo set and whether errors require a configuration change or an explicit limitation. No measured results exist yet.

## Summary acceptance

- English and Hindi summaries reflect the source meaning and do not invent decisions, owners, dates, or outcomes.
- Every action item and decision has valid segment references supporting the claim.
- All important manually annotated facts appear correctly in the curated acceptance set, or the case fails review.
- Unknown owners/dates remain unspecified, and suggestions remain distinguishable from commitments.
- Instructions spoken in the recording cannot override the summary schema or application instructions.
- Invalid/empty model responses and out-of-budget transcripts produce clear errors; no silent truncation.

## Application validation

Test input type/size/duration validation, corrupt or silent audio, SQLite restart persistence, foreign-key deletion, schema/reference validation, UI rerun duplicate prevention, transient errors, throttling, timeouts, failed-summary retry, interrupted-run recovery, Unicode exports, and temporary-file cleanup. Use mocked Azure responses for repeatable automated tests, plus a small consented/synthetic live smoke test for integration.

Final acceptance demonstrates processing and reopening a representative call from each language category, exporting results, deleting a call, and recovering from a failure. Report live findings honestly, including sample count and limitations; small demo evaluation is not a production accuracy guarantee.
