"""Portable UTF-8 exports for saved calls and explicitly labeled previews."""
import json

from .models import CallSummary, Transcript


def timestamp(milliseconds: int) -> str:
    seconds = milliseconds // 1000
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def transcript_text(transcript: Transcript) -> str:
    return "\n".join(
        f"[{s.id} | {timestamp(s.start_ms)}–{timestamp(s.end_ms)}] "
        f"{s.speaker or 'Speaker unknown'}: {s.text}" for s in transcript.segments
    )


def summary_markdown(summary: CallSummary) -> str:
    lines = ["# Call summary", "", summary.overview, "", "## Purpose", summary.purpose,
             "", "## Key points", *[f"- {p}" for p in summary.key_points], "", "## Decisions"]
    lines += [f"- {d.text} (evidence: {', '.join(d.segment_ids)})" for d in summary.decisions]
    lines += ["", "## Action items"]
    lines += [f"- {a.description} — Owner: {a.owner or 'Not stated'}; due: {a.due_date or 'Not stated'} "
              f"(evidence: {', '.join(a.segment_ids)})" for a in summary.action_items]
    lines += ["", "## Unresolved questions", *[f"- {q}" for q in summary.unresolved_questions],
              "", "## Outcome", summary.outcome]
    return "\n".join(lines) + "\n"


def call_json(transcript: Transcript, summary: CallSummary | None, *, source_mode="live") -> str:
    return json.dumps({"schema_version": "1", "source_mode": source_mode,
                       "transcript": transcript.model_dump(mode="json"),
                       "summary": summary.model_dump(mode="json") if summary else None},
                      ensure_ascii=False, indent=2)
