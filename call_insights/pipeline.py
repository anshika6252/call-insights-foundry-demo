"""Persisted stage orchestration with bounded retries and explicit recovery."""

import time
from pathlib import Path

from .azure_clients import AzureServiceError, PROMPT_VERSION, SpeechClient, SummaryClient
from .config import Settings
from .models import InputMode, SummaryLanguage


def retry_operation(operation, *, max_attempts=3, sleep=time.sleep):
    """Retry only sanitized transient provider failures; never retry validation errors."""
    if not 1 <= max_attempts <= 5:
        raise ValueError("max_attempts must be between 1 and 5")
    for attempt in range(max_attempts):
        try:
            return operation()
        except AzureServiceError as error:
            if not error.retryable or attempt + 1 == max_attempts:
                raise
            delay = error.retry_after if error.retry_after is not None else 2 ** attempt
            sleep(min(max(float(delay), 0), 30))


class Pipeline:
    def __init__(self, repository, speech_client, summary_client, settings: Settings,
                 *, sleep=time.sleep):
        self.repository = repository
        self.speech_client = speech_client
        self.summary_client = summary_client
        self.settings = settings
        self.sleep = sleep

    def _retry(self, operation):
        return retry_operation(operation, max_attempts=self.settings.max_attempts, sleep=self.sleep)

    def _stage(self, call_id, stage, work, on_progress):
        # Claim errors are deliberately outside the handler: a losing caller must
        # never mark another caller's active run failed.
        run_id = self.repository.start_run(call_id, stage)
        try:
            on_progress(stage)
            result, usage = work()
            client = self.speech_client if stage == "transcription" else self.summary_client
            request_id = getattr(client, "last_request_id", None)
            self.repository.finish_run(run_id, usage=usage,
                provider_request_id=request_id if isinstance(request_id, str) else None)
            return result
        except AzureServiceError as error:
            self.repository.fail_call(call_id, stage, str(error))
            raise
        except Exception:
            message = "Processing could not complete. Retry the summary or re-upload the recording."
            self.repository.fail_call(call_id, stage, message)
            raise AzureServiceError(message) from None
        except BaseException:
            # Streamlit's rerun/stop signals inherit BaseException. Release our
            # claimed stage while preserving the control signal for Streamlit.
            self.repository.fail_call(call_id, stage,
                "Processing was interrupted. Retry the saved summary or re-upload audio.")
            raise

    def process(self, call_id, audio_path: Path, on_progress=lambda stage: None):
        call = self.repository.get_call(call_id)
        if call is None:
            raise ValueError("Call was not found.")
        def transcribe():
            transcript = self._retry(lambda: self.speech_client.transcribe(
                Path(audio_path), InputMode(call["input_mode"])))
            self.repository.save_transcript(call_id, transcript)
            return transcript, None
        self._stage(call_id, "transcription", transcribe, on_progress)
        return self.retry_summary(call_id, on_progress)

    def retry_summary(self, call_id, on_progress=lambda stage: None):
        call = self.repository.get_call(call_id)
        if call is None:
            raise ValueError("Call was not found.")
        def summarize():
            transcript = self.repository.get_transcript(call_id)
            if transcript is None:
                raise ValueError("No saved transcript.")
            result = self._retry(lambda: self.summary_client.summarize(
                transcript, SummaryLanguage(call["summary_language"])))
            result.validate_evidence(transcript)
            self.repository.save_summary(call_id, result,
                language=call["summary_language"], deployment=self.settings.summary_deployment,
                prompt_version=PROMPT_VERSION)
            return result, getattr(self.summary_client, "last_usage", None)
        return self._stage(call_id, "summarization", summarize, on_progress)


def build_pipeline(repository, settings: Settings) -> Pipeline:
    errors = settings.azure_errors()
    if errors:
        raise ValueError(" ".join(errors))
    return Pipeline(repository,
        SpeechClient(settings.speech_endpoint, settings.speech_api_key,
                     timeout_seconds=settings.timeout_seconds, api_version=settings.speech_api_version),
        SummaryClient(settings.summary_endpoint, settings.summary_api_key, settings.summary_deployment,
                      timeout_seconds=settings.timeout_seconds,
                      max_transcript_chars=settings.max_transcript_chars), settings)
