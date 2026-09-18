import json

import httpx
import pytest

from call_insights.azure_clients import AzureServiceError, SpeechClient, SummaryClient, summary_schema
from call_insights.models import InputMode, Segment, SummaryLanguage, Transcript


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize("mode,locale,text", [
    (InputMode.ENGLISH, "en-IN", "Payment was not received."),
    (InputMode.HINDI, "hi-IN", "भुगतान नहीं मिला।"),
])
def test_transcription_contract(tmp_path, mode, locale, text):
    audio = tmp_path / "private-name.wav"
    audio.write_bytes(b"mock audio")
    def respond(request):
        assert request.url.params["api-version"] == "2025-10-15"
        assert locale.encode() in request.content
        assert b'"diarization"' in request.content
        assert b"private-name" not in request.content
        return httpx.Response(200, json={"durationMilliseconds": 1000, "phrases": [
            {"text": text, "offsetMilliseconds": 100, "durationMilliseconds": 900,
             "speaker": 0, "locale": locale}]})
    with client(respond) as http:
        result = SpeechClient("https://speech.example", "test", http_client=http).transcribe(audio, mode)
    assert result.segments[0].text == text
    assert result.segments[0].speaker == "Speaker 1"
    assert result.segments[0].end_ms == 1000
    assert result.detected_locales == [locale]


@pytest.mark.parametrize("status,retryable", [(400, False), (401, False), (429, True), (503, True)])
def test_sanitized_service_errors(tmp_path, status, retryable):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"audio")
    with client(lambda _: httpx.Response(status, text="secret transcript", headers={"Retry-After": "2"})) as http:
        with pytest.raises(AzureServiceError) as caught:
            SpeechClient("https://speech.example", "key-secret", http_client=http).transcribe(audio, InputMode.ENGLISH)
    assert caught.value.retryable is retryable
    assert caught.value.retry_after == 2
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize("body", [{"phrases": []}, {"phrases": [{"text": "bad"}]}, {"phrases": None},
                                  {"phrases": [None]}, {"phrases": [{"text": None}]},
                                  {"phrases": [{"text": "bad", "offsetMilliseconds": "1", "durationMilliseconds": "2"}]}])
def test_malformed_or_empty_transcript(tmp_path, body):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"audio")
    with client(lambda _: httpx.Response(200, json=body)) as http:
        with pytest.raises(AzureServiceError):
            SpeechClient("https://speech.example", "key", http_client=http).transcribe(audio, InputMode.HINDI)


@pytest.fixture
def transcript():
    return Transcript(segments=[Segment(id="s1", text="रवि कल ईमेल भेजेंगे।", start_ms=0, end_ms=1000)])


def summary_body(reference="s1", finish="stop", refusal=None):
    return {"choices": [{"finish_reason": finish, "message": {"refusal": refusal, "content": json.dumps({
        "overview": "रवि ईमेल भेजेंगे।", "purpose": "Follow-up", "key_points": [], "decisions": [],
        "action_items": [{"description": "Send email", "owner": "रवि", "due_date": "कल", "segment_ids": [reference]}],
        "unresolved_questions": [], "outcome": "Follow-up pending"})}}], "usage": {"total_tokens": 100}}


@pytest.mark.parametrize("language", list(SummaryLanguage))
def test_summary_unicode_schema_and_usage(transcript, language):
    def respond(request):
        data = json.loads(request.content)
        assert request.url.path == "/openai/v1/chat/completions"
        assert language.value in data["messages"][0]["content"]
        assert "untrusted" in data["messages"][0]["content"]
        assert data["response_format"]["json_schema"]["strict"] is True
        return httpx.Response(200, json=summary_body())
    with client(respond) as http:
        adapter = SummaryClient("https://models.example/openai/v1/", "key", "deployment", http_client=http)
        result = adapter.summarize(transcript, language)
    assert result.action_items[0].owner == "रवि"
    assert adapter.last_usage == {"total_tokens": 100}


@pytest.mark.parametrize("body", [summary_body("missing"), summary_body(finish="length"), summary_body(refusal="refused"),
                                  {"choices": []}, {"choices": [None]}, {"choices": [{"message": None}]}, {"choices": None}])
def test_summary_rejects_unusable_response(transcript, body):
    with client(lambda _: httpx.Response(200, json=body)) as http:
        with pytest.raises(AzureServiceError):
            SummaryClient("https://models.example", "key", "model", http_client=http).summarize(transcript, SummaryLanguage.ENGLISH)


def test_budget_checked_before_network(transcript):
    with client(lambda _: pytest.fail("must not request over-budget input")) as http:
        with pytest.raises(AzureServiceError, match="No text was truncated"):
            SummaryClient("https://models.example", "key", "model", http_client=http, max_transcript_chars=5).summarize(transcript, SummaryLanguage.HINDI)


def test_null_optional_usage_does_not_discard_summary(transcript):
    body = summary_body()
    body["usage"] = None
    with client(lambda _: httpx.Response(200, json=body)) as http:
        adapter = SummaryClient("https://models.example", "key", "model", http_client=http)
        assert adapter.summarize(transcript, SummaryLanguage.HINDI).action_items
        assert adapter.last_usage == {}


def test_strict_schema_required_fields():
    schema = summary_schema()
    assert set(schema["required"]) == set(schema["properties"])
    action = schema["$defs"]["ActionItem"]
    assert set(action["required"]) == set(action["properties"])
    assert action["additionalProperties"] is False
    assert "default" not in json.dumps(schema)


def test_timeout_sanitized(tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"audio")
    def timeout(request):
        raise httpx.ReadTimeout("secret endpoint", request=request)
    with client(timeout) as http:
        with pytest.raises(AzureServiceError) as caught:
            SpeechClient("https://speech.example", "key", http_client=http).transcribe(audio, InputMode.ENGLISH)
    assert caught.value.retryable
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize("header", ["x-request-id", "apim-request-id", "x-ms-request-id"])
def test_summary_request_id_capture_and_reset(transcript, header):
    responses = iter([
        httpx.Response(200, json=summary_body(), headers={header: "abc-123:456"}),
        httpx.Response(503, text="private body"),
    ])
    with client(lambda _: next(responses)) as http:
        adapter = SummaryClient("https://models.example", "key", "model", http_client=http)
        adapter.summarize(transcript, SummaryLanguage.ENGLISH)
        assert adapter.last_request_id == "abc-123:456"
        with pytest.raises(AzureServiceError):
            adapter.summarize(transcript, SummaryLanguage.ENGLISH)
        assert adapter.last_request_id is None


@pytest.mark.parametrize("request_id", ["not an id", "x" * 129, "<secret>"])
def test_invalid_request_id_ignored(transcript, request_id):
    with client(lambda _: httpx.Response(200, json=summary_body(), headers={"x-request-id": request_id})) as http:
        adapter = SummaryClient("https://models.example", "key", "model", http_client=http)
        adapter.summarize(transcript, SummaryLanguage.HINDI)
        assert adapter.last_request_id is None


def test_speech_error_request_id_capture(tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(b"audio")
    with client(lambda _: httpx.Response(429, headers={"apim-request-id": "req-123"})) as http:
        adapter = SpeechClient("https://speech.example", "key", http_client=http)
        with pytest.raises(AzureServiceError):
            adapter.transcribe(audio, InputMode.ENGLISH)
        assert adapter.last_request_id == "req-123"
