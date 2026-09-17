# Planned demo walkthrough

This walkthrough describes the intended experience. Setup commands and screenshots will be added once the application exists.

## Preparation

Complete Azure/language feasibility, configure the documented endpoints and credentials, initialize local storage, and prepare synthetic or consented English, Hindi, and Hinglish samples. Check quota and connectivity before presenting. Never present cached or mock outputs as live Azure results.

## Presentation sequence

1. Explain the flow: recording → Azure transcript → structured summary → SQLite history.
2. Upload an English call, select input mode and summary language, and preview it.
3. Run processing and show stage progress, transcript timestamps, and available speaker labels.
4. Show decisions/actions and follow their supporting transcript references.
5. Repeat with Hindi and Hinglish, including a language switch within a sentence; show a Hindi summary option.
6. Open an earlier saved call and export TXT transcript, Markdown summary, and JSON results.
7. Demonstrate a safe failure/retry scenario and call deletion.

## Points to explain

Speaker labels do not identify people. Hinglish quality was evaluated on a small documented set. Raw transcript wording is preserved; summary language is a separate choice. Audio is temporary, while transcripts and summaries persist locally until deleted. Model output can be wrong and important facts should be checked against the recording/transcript.

## Final documentation deliverables

Add tested installation/run instructions, selected Azure settings and versions, actual screenshots, measured sample results, troubleshooting, known limitations, and resource cleanup. The final setup guide must work from a fresh checkout without committed credentials or runtime data.
