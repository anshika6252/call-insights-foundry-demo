# Azure setup

Adapters are implemented; resources, regional availability and live requests are unverified. Current scope: English and Hindi; Hinglish is deferred.

## Configure existing resources

1. Select a Speech resource supporting fast transcription in its region and verify en-IN and hi-IN availability.
2. Select an Azure OpenAI deployment supporting Chat Completions structured outputs. Check its context window, quota and regional pricing.
3. Copy .env.example to .env. Set AZURE_SPEECH_ENDPOINT (HTTPS resource root), AZURE_SPEECH_API_KEY, AZURE_OPENAI_ENDPOINT (HTTPS resource root), AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT (deployment name). The services can require different endpoints and keys. Keep credentials out of Git and issues.
4. Retain AZURE_SPEECH_API_VERSION=2025-10-15. Summaries use /openai/v1/chat/completions without a dated API query.
5. Follow the README to start the app. It reports missing setting names without exposing values. Authentication currently uses API keys; Entra ID is a future hardening option, not implemented behavior.

## Request behavior

Speech uploads audio as multipart data with explicit en-IN or hi-IN and diarization limited to two speakers. Timestamps come from phrases; anonymous speaker labels do not establish roles. Stereo uses the service default merged-channel behavior.

Summaries use strict JSON Schema with English or Hindi instructions. Actions and decisions cite segment IDs; local validation proves reference existence, not factual entailment. Refusals, truncated completions, empty speech and malformed responses fail clearly. Orchestration retries transient failures; provider bodies are never displayed.

CALL_INSIGHTS_MAX_TRANSCRIPT_CHARS=24000 bounds serialized transcript input; this is not a token count or context-window guarantee. Verify prompt/schema/output overhead against the deployment. Oversized input fails instead of being truncated. Timeout defaults to 120 seconds and maximum attempts to 3. Retries may incur additional charges. Available usage tokens are recorded without invented prices.

## Pending live acceptance

Record the six scripts in evaluation-fixtures.json with consent and bilingual reference transcripts. Evaluate three recordings per language and both summary output languages. Log region, versions, latency, word errors, speaker consistency and fact fidelity in language-feasibility.md. Mocked tests are not language or service validation.

Check regional pricing and spending controls before processing. No Azure resources were created by this project. If dedicated demo resources are later created, remove only those named resources after use; preserve shared resources.

## Official references (checked 2026-09-17)

- [Fast transcription](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
- [Languages](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Regions](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions)
- [Structured outputs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs)
- [Azure OpenAI v1](https://learn.microsoft.com/en-us/azure/foundry/openai/latest)
