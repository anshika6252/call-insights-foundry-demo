# Azure setup plan

This is a setup checklist for future implementation. No resources or model deployments have been created or verified for this project.

## Required decisions

1. Identify the Azure subscription and project/resource group with access to Foundry and Speech.
2. Verify region, language, diarization, API, quota, and model availability before provisioning.
3. Validate Azure Speech fast transcription using English and Hindi samples, then mixed Hindi-English recordings. Evaluate the documented multilingual configuration; do not assume locale identifiers or behavior from UI labels.
4. Select a Foundry-hosted summarization deployment with structured output support and enough context for the permitted recordings.
5. Choose supported authentication for each endpoint. Prefer local developer identity where supported and practical; otherwise keep keys in environment variables outside Git. Record required roles or access settings.
6. Pin the selected SDK/API versions and document the exact resource/endpoint relationships. Speech and model inference may use different endpoints and authentication settings.
7. Record usage metrics available from the APIs and current regional pricing before estimating cost. Set appropriate spending controls for the demo.

## Planned configuration

The implementation should document required settings for Speech endpoint/region and authentication, Foundry model endpoint and deployment, applicable API version, SQLite path, temporary audio location, file-size/duration limits, request timeouts, and retry limits. Actual environment-variable names will be finalized with the SDK choices. A future `.env.example` must contain placeholders only.

## Service selection rationale

Fast transcription is the initial candidate for uploaded demo recordings and speaker separation. Microsoft documents multilingual configuration and language support. Continuous language identification has limitations around language changes within a sentence, so it must not be treated as proof of Hinglish accuracy. Multilingual feasibility testing is mandatory before promising support.

Structured model outputs support a predictable summary schema, but the app must also validate references and review factual fidelity. No model deployment name or availability is assumed.

## References

- [Fast transcription](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create)
- [Speech language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Language identification and limitations](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-identification)
- [Structured outputs in Foundry](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs)

These references informed the plan on 2026-09-17. Recheck availability during implementation.

## Cleanup

The final guide must identify project-created Azure resources and explain how to remove them after the demo without touching shared resources. No Azure resource creation is authorized by this documentation task.
