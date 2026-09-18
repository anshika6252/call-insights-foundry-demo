"""Streamlit entry point: run with `streamlit run app.py`."""
import json
from datetime import datetime

import streamlit as st

from call_insights.audio import AudioValidationError, cleanup_stale_audio, temporary_audio, validate_audio
from call_insights.config import Settings
from call_insights.exports import call_json, summary_markdown, timestamp, transcript_text
from call_insights.repository import Repository
from call_insights.pipeline import build_pipeline
from call_insights.sample_data import sample_call


@st.cache_resource
def bootstrap(db_path, temp_dir):
    repository = Repository(db_path)
    repository.recover_interrupted()
    cleanup_stale_audio(temp_dir)
    return repository


AZURE_FIELDS = (
    ("speech_endpoint", "Speech endpoint", False),
    ("speech_api_key", "Speech API key", True),
    ("summary_endpoint", "Azure OpenAI endpoint", False),
    ("summary_api_key", "Azure OpenAI API key", True),
    ("summary_deployment", "Model deployment name", False),
)


def clear_azure_settings():
    st.session_state.pop("azure_overrides", None)
    for name, _, _ in AZURE_FIELDS:
        st.session_state["azure_" + name] = ""


def azure_settings(fallback):
    with st.expander("Azure settings", expanded=bool(fallback.azure_errors())):
        st.caption("Enter settings for this session. Blank fields use environment/.env values. Keys are not saved to disk or shared with other sessions.")
        with st.form("azure_settings_form"):
            values = {}
            for name, label, secret in AZURE_FIELDS:
                values[name] = st.text_input(label, key="azure_" + name,
                    type="password" if secret else "default",
                    placeholder="Use fallback" if getattr(fallback, name) else "Required",
                    help="HTTPS resource root, without an API path." if name.endswith("endpoint") else None)
            submitted = st.form_submit_button("Apply Azure settings")
        if submitted:
            candidate = fallback.with_ui_overrides(values)
            errors = candidate.azure_errors()
            if errors:
                st.error("Settings were not applied. " + " ".join(errors))
            else:
                st.session_state["azure_overrides"] = {name: value.strip() for name, value in values.items() if value.strip()}
                st.success("Settings applied for this session. No connection test was performed.")
        st.button("Clear session settings", on_click=clear_azure_settings)
        if st.session_state.get("azure_overrides"):
            st.caption("Using session overrides; blank fields use fallback settings.")
        else:
            st.caption("Using environment/.env fallback settings where available.")
    return fallback.with_ui_overrides(st.session_state.get("azure_overrides", {}))


def show_results(transcript, summary, key, source_mode="live"):
    def evidence(references):
        with st.expander("View evidence: " + ", ".join(references)):
            for segment in transcript.segments if transcript else []:
                if segment.id in references:
                    st.caption(f"{segment.id} · {timestamp(segment.start_ms)}–{timestamp(segment.end_ms)} · {segment.speaker or 'Speaker unknown'}")
                    st.write(segment.text)
    if summary:
        st.subheader("Call summary")
        st.write(summary.overview)
        st.caption("Purpose")
        st.write(summary.purpose)
        for heading, items in [("Key points", summary.key_points), ("Unresolved questions", summary.unresolved_questions)]:
            with st.expander(heading, expanded=bool(items)):
                if not items:
                    st.caption("None stated.")
                for item in items:
                    st.write("• " + item)
        st.markdown("**Decisions**")
        if not summary.decisions:
            st.caption("None stated.")
        for item in summary.decisions:
            st.write(item.text)
            evidence(item.segment_ids)
        st.markdown("**Action items**")
        if not summary.action_items:
            st.caption("None stated.")
        for action in summary.action_items:
            st.write(action.description)
            st.caption(f"Owner: {action.owner or 'Not stated'} · Due: {action.due_date or 'Not stated'} · Evidence: {', '.join(action.segment_ids)}")
            evidence(action.segment_ids)
        st.markdown("**Outcome**")
        st.write(summary.outcome)
    if transcript:
        with st.expander("Transcript and evidence", expanded=not bool(summary)):
            for segment in transcript.segments:
                st.caption(f"{segment.id} · {timestamp(segment.start_ms)}–{timestamp(segment.end_ms)} · {segment.speaker or 'Speaker unknown'}")
                st.write(segment.text)
        st.caption("Export results")
        cols = st.columns(3)
        label = "SYNTHETIC PREVIEW — handwritten; no recording was processed.\n\n" if source_mode == "sample" else ""
        cols[0].download_button("Transcript (.txt)", label + transcript_text(transcript), "transcript.txt", "text/plain", key=key+"txt")
        if summary:
            cols[1].download_button("Summary (.md)", label + summary_markdown(summary), "summary.md", "text/markdown", key=key+"md")
        cols[2].download_button("Full results (.json)", call_json(transcript, summary, source_mode=source_mode), "call.json", "application/json", key=key+"json")


def main():
    st.set_page_config(page_title="Call Insights", page_icon="🎧", layout="wide")
    st.title("🎧 Call Insights")
    st.caption("Turn English and Hindi recordings into transcripts, decisions, and clear next steps.")
    try:
        settings = Settings.from_env()
    except ValueError as error:
        st.error(str(error))
        return
    try:
        repository = bootstrap(str(settings.db_path), str(settings.temp_dir))
    except Exception:
        st.error("Application configuration or local storage could not be initialized. Check .env values and folder permissions.")
        return
    with st.sidebar:
        st.header("Workspace")
        st.caption("English · Hindi | Up to 10 minutes · 50 MB")
        settings = azure_settings(settings)
        errors = settings.azure_errors()
        if errors:
            st.warning("Azure setup pending")
            with st.expander("Required configuration"):
                for error in errors:
                    st.write(error)
        else:
            st.success("Azure configuration present")
            st.caption("Connectivity is checked when processing a recording.")
        st.caption("Audio is temporary. Transcripts and summaries remain in local SQLite until deleted.")
    upload_tab, preview_tab, history_tab = st.tabs(["New recording", "Sample preview", "Call history"])
    with upload_tab:
        st.subheader("Add a recording")
        if errors:
            st.info("Configure Azure to process recordings. Explore the handwritten sample preview while setup is pending.")
        input_mode = st.selectbox("Recording language", ["English", "Hindi"])
        summary_language = st.selectbox("Summary language", ["English", "Hindi"])
        uploaded = st.file_uploader("WAV or MP3 recording", type=["wav", "mp3"], disabled=bool(errors))
        if uploaded is not None:
            data = uploaded.getvalue()
            try:
                info = validate_audio(data, uploaded.name)
            except AudioValidationError as error:
                st.error(str(error))
            else:
                st.audio(data, format="audio/wav" if info.format == "wav" else "audio/mpeg")
                st.caption(f"{info.duration_seconds:.1f} seconds · {info.size_bytes / 1024:.0f} KB")
                duplicates = repository.find_by_hash(info.sha256)
                allow = True
                if duplicates:
                    st.warning("This recording already exists in call history.")
                    allow = st.checkbox("Process this recording again as a new call", key="reprocess_"+info.sha256)
                if st.button("Transcribe and summarize", type="primary", disabled=bool(errors) or not allow):
                    call_id = repository.create_call(uploaded.name, info.sha256, input_mode.lower(),
                        summary_language.lower(), info.size_bytes, round(info.duration_seconds * 1000))
                    st.session_state["latest_call"] = call_id
                    with st.status("Processing recording…", expanded=True) as status:
                        try:
                            with temporary_audio(data, info.format, settings.temp_dir) as path:
                                build_pipeline(repository, settings).process(call_id, path, on_progress=lambda stage: st.write(str(stage)))
                            status.update(label="Results saved", state="complete")
                        except Exception:
                            status.update(label="Processing did not complete. Open call history for recovery.", state="error")
                            st.error("Check Azure configuration, connectivity, and temporary folder permissions. Retry the saved summary or re-upload the audio from call history.")
        latest = st.session_state.get("latest_call")
        if latest and repository.get_call(latest):
            show_results(repository.get_transcript(latest), repository.get_summary(latest), "latest")
    with preview_tab:
        st.subheader("Explore a sample call")
        st.info("Synthetic preview — handwritten transcript and summary. No audio was transcribed and no Azure request is made. This preview is not saved to history.")
        language = st.radio("Preview language", ["English", "Hindi"], horizontal=True)
        transcript, summary = sample_call(language.lower())
        show_results(transcript, summary, "sample", "sample")
    with history_tab:
        st.subheader("Saved calls")
        calls = repository.list_calls()
        if not calls:
            st.info("No saved calls yet. Process a recording to start your history.")
        else:
            lookup = {call["id"]: call for call in calls}
            selected = st.selectbox("Choose a call", list(lookup), format_func=lambda value:
                f"{lookup[value]['filename']} · {lookup[value]['status']} · {lookup[value]['created_at'][:16]}")
            call = lookup[selected]
            st.caption(f"{call['input_mode'].title()} recording · {call['summary_language'].title()} summary · {call['status']} · {call['source_mode']}")
            transcript, summary = repository.get_transcript(selected), repository.get_summary(selected)
            if call["status"] in {"failed", "uploaded"}:
                if call["status"] == "failed":
                    st.error(call["error"] or "Processing failed.")
                if transcript:
                    if st.button("Retry summary", disabled=bool(errors)):
                        try:
                            with st.spinner("Retrying summary from saved transcript…"):
                                build_pipeline(repository, settings).retry_summary(selected)
                            st.rerun()
                        except Exception:
                            st.error("Summary retry did not complete. Check Azure configuration and try again.")
                else:
                    st.info("Upload the recording again to retry transcription.")
            show_results(transcript, summary, "history", call["source_mode"])
            with st.expander("Processing details"):
                for run in repository.list_runs(selected):
                    st.write(f"{run['stage'].title()} · {run['outcome']}")
                    st.caption(f"Started: {run['started_at']} · Finished: {run['ended_at'] or 'In progress'}")
                    if run["ended_at"]:
                        elapsed = (datetime.fromisoformat(run["ended_at"]) - datetime.fromisoformat(run["started_at"])).total_seconds()
                        st.caption(f"Stage duration (including retries): {elapsed:.2f} seconds")
                    if run["provider_request_id"]:
                        st.caption("Provider request ID: " + run["provider_request_id"])
                    if run["usage_json"]:
                        st.json(json.loads(run["usage_json"]))
            confirmed = st.checkbox("Delete this call and all its saved results", key="delete_"+selected)
            if st.button("Delete call", disabled=not confirmed or call["status"] in {"transcribing", "summarizing"}):
                repository.delete_call(selected)
                st.rerun()


if __name__ == "__main__":
    main()
