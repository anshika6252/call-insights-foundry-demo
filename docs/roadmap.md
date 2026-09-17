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

## GitHub tracking

[View all phase milestones](https://github.com/anshika6252/call-insights-foundry-demo/milestones). The initial planning documentation is complete; the following implementation issues remain open.

| Issue | Work item | Phase | Dependencies |
| --- | --- | --- | --- |
| [#1](https://github.com/anshika6252/call-insights-foundry-demo/issues/1) | Verify Azure Foundry and Speech configuration | 1 | None |
| [#2](https://github.com/anshika6252/call-insights-foundry-demo/issues/2) | Evaluate English, Hindi and Hinglish transcription feasibility | 1 | [#1](https://github.com/anshika6252/call-insights-foundry-demo/issues/1) |
| [#3](https://github.com/anshika6252/call-insights-foundry-demo/issues/3) | Scaffold Streamlit application and configuration | 2 | [#1](https://github.com/anshika6252/call-insights-foundry-demo/issues/1) |
| [#4](https://github.com/anshika6252/call-insights-foundry-demo/issues/4) | Implement SQLite schema and processing lifecycle | 2 | [#3](https://github.com/anshika6252/call-insights-foundry-demo/issues/3) |
| [#5](https://github.com/anshika6252/call-insights-foundry-demo/issues/5) | Build audio upload, language selection and validation | 2 | [#3](https://github.com/anshika6252/call-insights-foundry-demo/issues/3), [#4](https://github.com/anshika6252/call-insights-foundry-demo/issues/4) |
| [#6](https://github.com/anshika6252/call-insights-foundry-demo/issues/6) | Integrate multilingual Azure transcription | 3 | [#2](https://github.com/anshika6252/call-insights-foundry-demo/issues/2), [#4](https://github.com/anshika6252/call-insights-foundry-demo/issues/4), [#5](https://github.com/anshika6252/call-insights-foundry-demo/issues/5) |
| [#7](https://github.com/anshika6252/call-insights-foundry-demo/issues/7) | Implement evidence-linked structured summaries | 3 | [#1](https://github.com/anshika6252/call-insights-foundry-demo/issues/1), [#4](https://github.com/anshika6252/call-insights-foundry-demo/issues/4), [#6](https://github.com/anshika6252/call-insights-foundry-demo/issues/6) |
| [#8](https://github.com/anshika6252/call-insights-foundry-demo/issues/8) | Build end-to-end Streamlit processing and result views | 3 | [#5](https://github.com/anshika6252/call-insights-foundry-demo/issues/5), [#6](https://github.com/anshika6252/call-insights-foundry-demo/issues/6), [#7](https://github.com/anshika6252/call-insights-foundry-demo/issues/7) |
| [#9](https://github.com/anshika6252/call-insights-foundry-demo/issues/9) | Add saved history, Unicode exports and call deletion | 4 | [#4](https://github.com/anshika6252/call-insights-foundry-demo/issues/4), [#8](https://github.com/anshika6252/call-insights-foundry-demo/issues/8) |
| [#10](https://github.com/anshika6252/call-insights-foundry-demo/issues/10) | Implement bounded retries and interrupted-run recovery | 4 | [#6](https://github.com/anshika6252/call-insights-foundry-demo/issues/6), [#7](https://github.com/anshika6252/call-insights-foundry-demo/issues/7), [#8](https://github.com/anshika6252/call-insights-foundry-demo/issues/8) |
| [#11](https://github.com/anshika6252/call-insights-foundry-demo/issues/11) | Validate multilingual quality and application acceptance | 4 | [#2](https://github.com/anshika6252/call-insights-foundry-demo/issues/2), [#8](https://github.com/anshika6252/call-insights-foundry-demo/issues/8), [#9](https://github.com/anshika6252/call-insights-foundry-demo/issues/9), [#10](https://github.com/anshika6252/call-insights-foundry-demo/issues/10) |
| [#12](https://github.com/anshika6252/call-insights-foundry-demo/issues/12) | Finalize setup guide and demo walkthrough | 4 | [#11](https://github.com/anshika6252/call-insights-foundry-demo/issues/11) |

## Deferred work

Streaming calls, telephony, identity/roles, sentiment, multilingual summary formats beyond English/Hindi, Romanized Hindi, cloud hosting, multiple users, and production retention/compliance controls are future scope.
