"""Audio transcription through Groq's Whisper-compatible API."""
import io
import os
from groq import Groq


def transcribe_audio(audio, language: str = "English") -> str:
    """Transcribe an uploaded file or browser recording with Groq Whisper."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Groq API key is missing. Add GROQ_API_KEY to your .env file.")

    if hasattr(audio, "getvalue"):
        audio_bytes = audio.getvalue()
        filename = getattr(audio, "name", "lecture_audio.wav")
    elif isinstance(audio, (bytes, bytearray)):
        audio_bytes = bytes(audio)
        filename = "lecture_recording.wav"
    else:
        raise ValueError("Audio input could not be read. Please upload or record it again.")

    if not audio_bytes:
        raise ValueError("The recording is empty. Record some audio before submitting.")

    file_obj = io.BytesIO(audio_bytes)
    file_obj.name = filename
    lang_map = {"English": "en", "Hindi": "hi", "Kannada": "kn", "Tamil": "ta"}
    try:
        result = Groq(api_key=api_key).audio.transcriptions.create(
            file=(filename, file_obj),
            model=os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3"),
            language=lang_map.get(language),
            response_format="text",
            temperature=0.0,
        )
    except Exception as exc:
        message = str(exc)
        if "401" in message or "authentication" in message.lower():
            raise RuntimeError("Groq rejected the API key. Check GROQ_API_KEY in .env.") from exc
        if "413" in message or "too large" in message.lower():
            raise RuntimeError("Audio is too large for transcription. Try a shorter recording.") from exc
        raise RuntimeError(f"Groq transcription failed: {message}") from exc

    text = result if isinstance(result, str) else getattr(result, "text", "")
    text = (text or "").strip()
    if not text:
        raise RuntimeError("No speech was detected. Try a clearer or longer recording.")
    return text
