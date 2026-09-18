import json

from call_insights.exports import call_json, summary_markdown, transcript_text
from call_insights.sample_data import sample_call


def test_hindi_exports_preserve_unicode_and_evidence():
    transcript, summary = sample_call("hindi")
    assert "भुगतान" in transcript_text(transcript)
    assert "s2" in summary_markdown(summary)
    payload = json.loads(call_json(transcript, summary, source_mode="sample"))
    assert payload["source_mode"] == "sample"
    assert payload["transcript"]["segments"][0]["text"] == transcript.segments[0].text
    assert payload["summary"]["action_items"][0]["due_date"] == "आज"


def test_transcript_only_export():
    transcript, _ = sample_call()
    assert json.loads(call_json(transcript, None))["summary"] is None
    assert "[s1 | 00:00–00:05] Speaker 1:" in transcript_text(transcript)
