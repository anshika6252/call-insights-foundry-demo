# Language feasibility

**Blocked on Azure configuration and representative audio. No measured transcription or summary-quality results exist.** English and Hindi are in scope; Hinglish is deferred by user instruction.

Candidate: Speech REST `2025-10-15`, explicit `en-IN`/`hi-IN`, two-speaker diarization, and Azure OpenAI v1 structured summaries. Official request documentation does not establish measured accuracy. Region, deployment and quota require verification on user resources. No subscription was provisioned.

`evaluation-fixtures.json` provides six synthetic **text scenarios**, three per language. These are scripts for recording and human review, not audio or transcription results. Adapter tests use fabricated responses and establish request/response contracts only.

## Pending evaluation worksheet

For each EN-01 through EN-03 and HI-01 through HI-03 record:

| Field | Current value |
|---|---|
| Audio consent/source, duration, noise, speakers | Pending |
| Speech region and API version | Pending |
| Summary deployment/model version | Pending |
| Reference and recognized transcript | Pending |
| Word error rate and normalization rules | Pending |
| Name, amount, date, negation errors | Pending |
| Speaker consistency and script behavior | Pending |
| Latency and available usage | Pending |
| English and Hindi summary fact/evidence review | Pending |
| Pass/fail and remediation | Pending |

Every annotated critical fact, negation, commitment and unresolved outcome must remain correct; owners and dates must not be invented. References must support decisions/actions. A critical fact error fails the sample even with low word error rate. Establish a transparent baseline before agreeing a numeric word-error threshold. Transliteration differences require bilingual review, not normalization that hides errors.

Do not close live language-feasibility or Azure smoke-test acceptance based on unit tests. Future Hinglish work requires a fresh service/configuration decision and audio evaluation; current modes do not expose it.

Sources: [Speech request guide](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create), [language support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support), [structured outputs](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs).
