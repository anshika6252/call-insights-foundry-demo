# Phased roadmap

All implementation is pending. Phase milestones and issues in GitHub track execution; this document defines the gates. Estimates are planning ranges, not commitments, and exclude Azure access delays.

| Phase | Scope | Exit gate | Estimate |
| --- | --- | --- | --- |
| 1 — Azure and language feasibility | Verify Azure access, region and deployment; evaluate English/Hindi/Hinglish | Selected transcription configuration and model, documented language findings and agreed limitations | 1–2 days |
| 2 — Application foundation | Python/Streamlit scaffold, configuration, SQLite, upload validation | App starts, validates inputs, and persists call metadata across restart | 1 day |
| 3 — End-to-end call insights | Transcription adapter, structured summarization, processing UI | Representative calls in all three language categories produce saved transcript and summary | 2 days |
| 4 — Reliability and demo readiness | History/exports/deletion, recovery, quality checks, final guides | End-to-end acceptance checks pass and demo is reproducible | 1–2 days |

Expected total: approximately 5–7 focused development days, subject to the Hinglish feasibility gate.

## Sequencing

Phase 1 Azure verification precedes language evaluation. Phase 2 can start once configuration requirements are clear, but final transcription integration depends on Phase 1 findings. Persistence and upload validation precede integration. Summarization depends on the transcript contract. UI orchestration follows both integrations. Recovery and history lead into final validation and documentation.

## Decision gates

1. **Language feasibility:** Do not claim Hinglish support based only on separate Hindi and English support. Evaluate within-sentence switches and script behavior. If the initial Azure Speech configuration is inadequate, compare an available Azure-hosted transcription alternative and document feature tradeoffs before implementation proceeds.
2. **Summary fidelity:** Important decisions and actions need valid evidence references. Unknown owners/dates must remain unspecified. Structural validation and human factual review are both required.
3. **Demo readiness:** Show all three language categories, persistence, export, and a recoverable failure. Record known limitations and measured performance.

## Backlog conventions

Each issue includes objective, scope/checklist, acceptance criteria, dependencies, and validation. Milestones map to the four phases. Labels identify functional areas and priorities; P0 marks prerequisites and core flow, and P1 marks readiness work. Dependencies are recorded as linked issue references. No dates are assigned until implementation scheduling is agreed.

## Deferred work

Streaming calls, telephony, identity/roles, sentiment, multilingual summary formats beyond English/Hindi, Romanized Hindi, cloud hosting, multiple users, and production retention/compliance controls are future scope.
