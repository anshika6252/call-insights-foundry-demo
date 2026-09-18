# Phased roadmap and execution status

Current scope: **English and Hindi only**. Hinglish and automatic language detection are deferred. Software implementation is available and tested offline. Azure configuration and live speech/summary validation remain pending.

| Phase | Delivered | Exit gate still pending |
| --- | --- | --- |
| 1 — Azure and language feasibility | API adapters, setup instructions, six synthetic text scripts, evaluation worksheet | Real configured Azure endpoints and representative recording evaluation |
| 2 — Application foundation | Python/Streamlit startup, configuration, SQLite, audio validation | Complete under offline test scope |
| 3 — End-to-end call insights | Transcription/summary adapters, evidence validation, processing UI, synthetic previews | Real English/Hindi calls through Azure and human summary review |
| 4 — Reliability and demo readiness | History, exports, deletion, retries, cancellation/restart recovery, tests, guides, independent review | Live demo rehearsal and final language-quality signoff |

Original planning estimate was 5–7 focused development days, excluding Azure access delays. This estimate is historical, not a claim of elapsed work or a revised delivery date.

## Agent roles

All five requested roles contributed. Because the session permits three concurrent subagents, they worked in stages.

- **Architect:** provider-independent models, validation contracts and architectural boundaries; issue #1 configuration design.
- **AI expert:** issues #2/#6/#7, Azure adapter request/response contracts, safe errors, structured summaries, setup/evaluation documentation.
- **Developer 1:** issues #4/#5/#10 backend, SQLite transactions, audio validation, temporary-file cleanup and recovery tests.
- **Developer 2:** issues #3/#5/#8/#9/#12 UI work, Streamlit preview/results/history, exports and AppTest.
- **Code reviewer:** issue #11 software review, independent cancellation regressions, acceptance boundary checks.
- **Coordinator:** dependency/configuration scaffolding, pipeline integration, final documentation, GitHub tracking and verification.

Owner labels and assignment comments represent agent responsibilities; subagents are not GitHub user accounts. Reviewer findings are in [code-review.md](code-review.md).

## Issues

| Issue | Owner | Implementation / acceptance status |
| --- | --- | --- |
| [#1 Verify Azure configuration](https://github.com/anshika6252/call-insights-foundry-demo/issues/1) | Architect | Instructions ready; blocked on user Azure setup |
| [#2 English/Hindi feasibility](https://github.com/anshika6252/call-insights-foundry-demo/issues/2) | AI expert | Text scenarios ready; actual audio evaluation pending |
| [#3 Scaffold/configuration](https://github.com/anshika6252/call-insights-foundry-demo/issues/3) | Developer 2 + coordinator | Implemented; local startup and configuration tested |
| [#4 SQLite](https://github.com/anshika6252/call-insights-foundry-demo/issues/4) | Developer 1 | Implemented; persistence, claims, schema and cascade tests pass |
| [#5 Upload validation](https://github.com/anshika6252/call-insights-foundry-demo/issues/5) | Developer 1 + Developer 2 | Implemented; audio validation and upload/UI guards tested |
| [#6 Transcription](https://github.com/anshika6252/call-insights-foundry-demo/issues/6) | AI expert | Adapter tests pass; live service acceptance pending |
| [#7 Summaries](https://github.com/anshika6252/call-insights-foundry-demo/issues/7) | AI expert | Schema/prompt/reference tests pass; factual live evaluation pending |
| [#8 End-to-end UI](https://github.com/anshika6252/call-insights-foundry-demo/issues/8) | Developer 2 | UI/offline workflow implemented; real Azure end-to-end run pending |
| [#9 History/export/delete](https://github.com/anshika6252/call-insights-foundry-demo/issues/9) | Developer 2 | Implemented; restart/history/Unicode export/deletion checks pass |
| [#10 Recovery](https://github.com/anshika6252/call-insights-foundry-demo/issues/10) | Developer 1 + coordinator | Implemented; retry, cancellation and interrupted-run checks pass |
| [#11 Quality acceptance](https://github.com/anshika6252/call-insights-foundry-demo/issues/11) | Code reviewer | Offline suite and review complete; live bilingual evaluation pending |
| [#12 Final guides](https://github.com/anshika6252/call-insights-foundry-demo/issues/12) | Developer 2 + coordinator | Offline quickstart/screenshots/troubleshooting ready; live rehearsal pending |

[Milestones](https://github.com/anshika6252/call-insights-foundry-demo/milestones) track these phases. Complete software issues are closed with validation comments; any issue whose original acceptance requires Azure or human audio review stays open. No live acceptance criterion is silently dropped.

## Next execution steps

1. Configure existing Speech and Foundry Azure OpenAI resources using [Azure setup](azure-setup.md).
2. Validate deployed access/region/quota and complete #1.
3. Record the six scripts or supply consented representative audio; measure English/Hindi transcription and summary quality for #2/#6/#7/#11.
4. Rehearse the real upload-to-history/export workflow and finalize #8/#12.
5. Consider Hinglish only as separately scoped future work.

## Deferred work

Hinglish, auto language detection, live streaming, telephony, authentication, multiuser/cloud hosting, persistent audio playback, sentiment analysis, vector search, agent orchestration and production retention controls.
