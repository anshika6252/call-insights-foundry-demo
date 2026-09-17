# Call Insights — Foundry Demo

A planned Streamlit demo that transcribes recorded calls in **English, Hindi, and Hinglish**, produces evidence-linked summaries using Azure AI Foundry services, and saves results in SQLite.

**Status: planning only.** This repository contains project documentation and an implementation backlog. No application, Azure resources, or working demo have been built.

## Demo experience

1. Upload and preview a WAV or MP3 recording.
2. Choose Auto, English, Hindi, or Hinglish input mode.
3. Start transcription and summarization and see processing progress.
4. Read timestamped transcript segments and speaker labels where available.
5. Review an overview, discussion points, decisions, action items, unresolved questions, and outcome.
6. Reopen saved calls, export results, or delete a call.

Summaries default to English, with Hindi as an output option. Hinglish means Hindi-English code-switching, including changes within a sentence; it is an application mode, not a separate Azure locale. Speaker labels do not establish personal identity or customer/agent roles.

## Scope

- Local, single-user Streamlit application with Python service modules and SQLite persistence.
- Proposed application limits: one recording at a time, up to 10 minutes and 50 MB, WAV/MP3.
- Azure Speech fast transcription is the initial candidate; the final configuration depends on an early multilingual evaluation.
- A model deployed through Foundry generates structured summaries; exact deployment, region, API version, and authentication are selected during feasibility work.
- Keep original transcript output; target Hindi in Devanagari and English in Latin script, subject to measured provider behavior.
- Temporary audio is removed after processing; saved history contains transcripts and summaries, not persistent audio playback.

Out of scope: live transcription, telephony integrations, login, multiple users, sentiment analysis, vector search, agent frameworks, and production hosting. Romanized Hindi conversion is not part of the initial scope.

## Project documents

- [Phases and delivery roadmap](docs/roadmap.md)
- [Architecture and data model](docs/architecture.md)
- [Azure setup plan](docs/azure-setup.md)
- [Language and quality evaluation](docs/evaluation.md)
- [Demo walkthrough](docs/demo-guide.md)
- [GitHub implementation issues](https://github.com/anshika6252/call-insights-foundry-demo/issues)

## Completion criteria

Representative English, Hindi, and Hinglish recordings can be uploaded, processed, saved, reopened after restart, and exported. A bilingual reviewer verifies important facts and language-switching behavior. Decisions and action items have valid transcript references, unsupported owners or dates are absent, and failures have understandable recovery paths.

Use only synthetic or consented recordings. Credentials, recordings, generated outputs, and the SQLite database must not be committed. No accuracy, latency, or cost claims are established yet.
