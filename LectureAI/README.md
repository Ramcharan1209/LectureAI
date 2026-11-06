# LectureAI

LectureAI turns a lecture into an editable transcript, structured notes, and a five-question quiz. It also has a separate voice-translation page. Use a browser microphone or upload audio, or paste a transcript directly for study-pack creation.

## Windows quick start

1. Extract this ZIP.
2. Double-click `EDIT_API_KEYS.bat`, add your Groq API key to `.env`, and save.
3. Double-click `RUN_LECTUREAI.bat` and wait for Streamlit to open.

Python 3.10 or newer is required. Get a key from [Groq Console](https://console.groq.com/keys). Keep `.env` private. The launcher creates a local environment, installs dependencies, and starts LectureAI.

## Create notes and take a quiz

1. Open **Lecture-to-Notes & Quiz**.
2. Choose the lecture language and whether to use audio or paste a transcript.
3. For audio, record with the microphone or upload a file, then click **Transcribe lecture**.
4. Review or edit the transcript, then click **Generate Notes & Quiz**.
5. Read or download the notes. Answer the five quiz questions and select **Submit quiz** to see your score and explanations.

## Translate speech

Open **Voice Translation**, choose the spoken language (or auto-detect) and target language, then record or upload audio. Select **Transcribe & translate** to view and download the translated text.

## Audio and microphone

Audio uploads support WAV, MP3, M4A, FLAC, OGG, and WebM. Browser recording requires microphone permission and works on `localhost` or secure HTTPS sites. The audio is sent to Groq for transcription.

## Configuration

The `.env` file supports `GROQ_API_KEY`, `GROQ_WHISPER_MODEL` (default `whisper-large-v3`), and `GROQ_CHAT_MODEL` (default `openai/gpt-oss-120b`). Older retired Llama model settings are automatically replaced with the current default.

## Project contents

- `app.py`: notes/quiz and voice-translation interface
- `services/speech.py`: Groq Whisper transcription
- `services/llm.py`: notes, quiz, and translation generation
- `EDIT_API_KEYS.bat`: opens API key settings
- `RUN_LECTUREAI.bat`: installs dependencies and launches the app
