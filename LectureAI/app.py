import json
import streamlit as st
from dotenv import load_dotenv
from streamlit_mic_recorder import mic_recorder

from services.llm import generate_study_pack, translate_text
from services.speech import transcribe_audio

load_dotenv()
st.set_page_config(page_title="LectureAI", page_icon="🎓", layout="wide")

LANGUAGES = ["English", "Hindi", "Kannada", "Tamil"]
SOURCE_LANGUAGES = ["Auto-detect"] + LANGUAGES
AUDIO_TYPES = ["wav", "mp3", "m4a", "flac", "ogg", "webm"]

DEFAULTS = {
    "transcript_editor": "",
    "study_transcript_editor": "",
    "study_pack": None,
    "quiz_result": None,
    "quiz_answers": {},
    "voice_recording": None,
    "voice_translation": None,
}
for name, default in DEFAULTS.items():
    if name not in st.session_state:
        st.session_state[name] = default


def capture_audio(label, key_prefix, source_language):
    """Render either browser recording or uploaded audio; return its bytes."""
    method = st.radio(
        f"{label} input",
        ["Record with microphone", "Upload audio"],
        horizontal=True,
        key=f"{key_prefix}_method",
    )
    if method == "Record with microphone":
        st.caption("Allow microphone access in your browser. Recording requires localhost or a secure HTTPS site.")
        try:
            recording = mic_recorder(
                start_prompt="🔴 Start recording",
                stop_prompt="⏹️ Stop recording",
                just_once=True,
                use_container_width=True,
                key=f"{key_prefix}_mic",
            )
            if recording is not None:
                data = recording.get("bytes")
                if data:
                    st.session_state[f"{key_prefix}_recording"] = data
                    st.audio(data, format="audio/wav")
                else:
                    st.error("The recording is empty. Start again and speak before stopping.")
        except Exception as exc:
            st.error("Microphone access failed. Allow microphone access in your browser settings and reload.")
            st.caption(str(exc))
        return st.session_state.get(f"{key_prefix}_recording")

    audio_file = st.file_uploader(
        "Choose an audio file",
        type=AUDIO_TYPES,
        key=f"{key_prefix}_upload",
    )
    if audio_file:
        st.audio(audio_file)
        return audio_file
    return None


def show_pack(pack):
    st.markdown(f"# {pack.get('title') or 'Lecture Notes'}")
    st.subheader("Summary")
    st.write(pack.get("summary", ""))
    st.subheader("Detailed notes")
    for note in pack.get("notes", []):
        with st.expander(note.get("heading") or "Topic", expanded=True):
            st.write(note.get("content", ""))
    if pack.get("key_points"):
        st.subheader("Key points")
        for point in pack["key_points"]:
            st.markdown(f"- {point}")
    if pack.get("definitions"):
        st.subheader("Important definitions")
        for definition in pack["definitions"]:
            st.markdown(f"**{definition.get('term', '')}:** {definition.get('meaning', '')}")


def pack_markdown(pack):
    lines = [f"# {pack.get('title', 'Lecture Notes')}", "", "## Summary", "", pack.get("summary", ""), "", "## Notes", ""]
    for note in pack.get("notes", []):
        lines.extend([f"### {note.get('heading', 'Topic')}", "", note.get("content", ""), ""])
    if pack.get("key_points"):
        lines.extend(["## Key points", ""])
        lines.extend(f"- {point}" for point in pack["key_points"])
    if pack.get("definitions"):
        lines.extend(["", "## Definitions", ""])
        lines.extend(f"- **{item.get('term', '')}:** {item.get('meaning', '')}" for item in pack["definitions"])
    return "\n".join(lines)


def notes_and_quiz_page():
    st.title("📚 Lecture-to-Notes & Quiz Generator")
    st.write("Record or upload a lecture, or paste a transcript. LectureAI creates study notes and five quiz questions.")
    language = st.selectbox("Lecture language", LANGUAGES, key="study_language")
    source_mode = st.radio("Transcript source", ["Audio", "Paste transcript"], horizontal=True, key="study_source_mode")

    if source_mode == "Audio":
        audio = capture_audio("Lecture", "study_audio", language)
        if audio and st.button("🎧 Transcribe lecture", type="secondary", key="transcribe_study"):
            with st.spinner("Transcribing lecture with Groq Whisper..."):
                try:
                    transcript = transcribe_audio(audio, language)
                    st.session_state.transcript_editor = transcript
                    st.session_state.study_transcript_editor = transcript
                    st.success("Transcription completed. Review it below, then generate the study pack.")
                except Exception as exc:
                    st.error(f"Transcription failed: {exc}")
    else:
        st.text_area(
            "Paste lecture transcript",
            key="transcript_editor",
            height=220,
            placeholder="Paste lecture content here...",
        )

    if source_mode == "Audio":
        transcript = st.text_area(
            "Review or edit transcript",
            key="study_transcript_editor",
            value=st.session_state.transcript_editor,
            height=220,
            placeholder="Your transcript will appear here after transcription.",
        )
    else:
        transcript = st.text_area(
            "Paste lecture transcript",
            key="transcript_editor",
            height=220,
            placeholder="Paste lecture content here...",
        )
    if source_mode == "Audio":
        st.session_state.transcript_editor = transcript
    if st.button("✨ Generate Notes & Quiz", type="primary", key="generate_pack"):
        if not transcript.strip():
            st.error("Transcript is empty. Transcribe audio or paste the lecture first.")
        else:
            with st.spinner("Creating study notes and five quiz questions..."):
                try:
                    st.session_state.study_pack = generate_study_pack(transcript, language)
                    st.session_state.quiz_result = None
                    st.session_state.quiz_answers = {}
                    st.success("Study pack created.")
                except Exception as exc:
                    st.error(f"Could not generate the study pack: {exc}")

    pack = st.session_state.study_pack
    if not pack:
        return
    st.divider()
    show_pack(pack)
    st.download_button(
        "Download notes (Markdown)",
        pack_markdown(pack),
        file_name="lecture_notes.md",
        mime="text/markdown",
    )
    st.download_button(
        "Download complete study pack (JSON)",
        json.dumps(pack, ensure_ascii=False, indent=2),
        file_name="lecture_study_pack.json",
        mime="application/json",
    )
    st.divider()
    st.header("❓ Quiz")
    questions = pack.get("mcqs", [])
    with st.form("study_quiz"):
        answers = {}
        for i, question in enumerate(questions):
            st.markdown(f"**Question {i + 1}.** {question['question']}")
            choices = question["options"]
            answers[i] = st.radio(
                f"Select an answer for question {i + 1}",
                ["A", "B", "C", "D"],
                format_func=lambda letter, options=choices: f"{letter}. {options[letter]}",
                key=f"quiz_answer_{i}",
            )
        submitted = st.form_submit_button("Submit quiz")
    if submitted:
        correct_count = sum(
            str(answers.get(i, "")).upper() == str(question.get("answer", "")).upper()
            for i, question in enumerate(questions)
        )
        st.session_state.quiz_answers = answers
        st.session_state.quiz_result = correct_count
    if st.session_state.quiz_result is not None:
        correct_count = st.session_state.quiz_result
        st.metric("Your score", f"{correct_count} / {len(questions)}")
        st.progress(correct_count / len(questions))
        for i, question in enumerate(questions):
            answer = str(question.get("answer", "")).upper()
            chosen = st.session_state.quiz_answers.get(i, "")
            if chosen == answer:
                st.success(f"Question {i + 1}: Correct")
            else:
                st.error(f"Question {i + 1}: Incorrect. Correct answer: {answer}")
            if question.get("explanation"):
                st.caption(question["explanation"])


def voice_translation_page():
    st.title("🎙️ Voice Translator")
    st.write("Record or upload spoken audio and translate it into another language.")
    source_language = st.selectbox("Spoken language", SOURCE_LANGUAGES, key="voice_source_language")
    target_language = st.selectbox("Translate into", LANGUAGES, key="voice_target_language")
    audio = capture_audio("Voice", "voice_audio", source_language)
    if audio and st.button("🌐 Transcribe & translate", type="primary", key="translate_voice"):
        with st.spinner("Transcribing and translating your audio..."):
            try:
                transcript = transcribe_audio(audio, source_language)
                translation = transcript if source_language == target_language else translate_text(transcript, target_language)
                st.session_state.voice_translation = {
                    "transcript": transcript,
                    "translation": translation,
                    "target_language": target_language,
                }
            except Exception as exc:
                st.error(f"Could not translate the audio: {exc}")

    result = st.session_state.voice_translation
    if result:
        st.subheader("Original speech")
        st.write(result["transcript"])
        st.subheader(f"Translation · {result['target_language']}")
        st.write(result["translation"])
        st.download_button(
            "Download translation",
            result["translation"],
            file_name="voice_translation.txt",
            mime="text/plain",
            key="download_voice_translation",
        )


st.title("🎓 LectureAI")
study_tab, translate_tab = st.tabs(["Lecture-to-Notes & Quiz", "Voice Translation"])
with study_tab:
    notes_and_quiz_page()
with translate_tab:
    voice_translation_page()
