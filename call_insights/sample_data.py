"""Handwritten synthetic previews; no audio or Azure processing is involved."""
from .models import CallSummary, Transcript


def sample_call(language="english") -> tuple[Transcript, CallSummary]:
    hindi = language == "hindi"
    texts = (["मेरा भुगतान हो गया है, लेकिन पुष्टि का ईमेल नहीं आया।",
              "मैं आज भुगतान की जाँच करके आपको ईमेल भेजूँगी। मेरा नाम प्रिया है।",
              "धन्यवाद। कृपया जाँच का परिणाम ईमेल से भेज दें।"] if hindi else
             ["My payment went through, but I have not received a confirmation email.",
              "My name is Priya. I will check the payment and email you today.",
              "Thank you. Please send the result of the check by email."])
    transcript = Transcript(segments=[dict(id=f"s{i+1}", start_ms=i*5000, end_ms=(i+1)*5000,
        text=text, speaker=f"Speaker {1 if i != 1 else 2}", locale="hi-IN" if hindi else "en-IN")
        for i, text in enumerate(texts)], detected_locales=["hi-IN" if hindi else "en-IN"], duration_ms=15000)
    summary = CallSummary(
        overview="भुगतान की पुष्टि का ईमेल नहीं मिला। प्रिया ने आज जाँच करके ईमेल भेजने का वादा किया।" if hindi else "A payment confirmation email is missing. Priya committed to checking the payment and emailing today.",
        purpose="भुगतान की पुष्टि प्राप्त करना।" if hindi else "Obtain payment confirmation.",
        key_points=[texts[0]], decisions=[], action_items=[dict(
            description="भुगतान की जाँच करके ईमेल भेजना।" if hindi else "Check the payment and email the result.",
            owner="प्रिया" if hindi else "Priya", due_date="आज" if hindi else "today", segment_ids=["s2"])],
        unresolved_questions=["क्या भुगतान सफल हुआ?" if hindi else "Was the payment successful?"],
        outcome="जाँच और ईमेल अभी बाकी हैं।" if hindi else "Payment verification and the follow-up email remain pending.")
    return transcript, summary.validate_evidence(transcript)
