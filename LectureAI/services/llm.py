"""Study-pack generation and translation via Groq chat completions."""
import json
import os
from groq import Groq


def _client():
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Groq API key is missing. Add GROQ_API_KEY to your .env file.")
    return Groq(api_key=key)


def _chat(prompt: str, json_mode: bool = False) -> str:
    model = os.getenv("GROQ_CHAT_MODEL", "openai/gpt-oss-120b").strip()
    # The earlier LectureAI package used a Groq model that has since been retired.
    if model in {"llama-3.3-70b-versatile", "llama-3.1-8b-instant"}:
        model = "openai/gpt-oss-120b"
    try:
        request = dict(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        if json_mode:
            request["response_format"] = {"type": "json_object"}
        response = _client().chat.completions.create(**request)
        return response.choices[0].message.content or ""
    except Exception as exc:
        message = str(exc)
        if "model_decommissioned" in message.lower() or "model_deprecated" in message.lower():
            raise RuntimeError("The selected Groq chat model has been retired. Set GROQ_CHAT_MODEL=openai/gpt-oss-120b in .env.") from exc
        if "401" in message or "authentication" in message.lower():
            raise RuntimeError("Groq rejected the API key. Reopen EDIT_API_KEYS.bat and check GROQ_API_KEY in .env.") from exc
        raise RuntimeError(f"Groq request failed: {message}") from exc


def generate_study_pack(transcript: str, language: str = "English") -> dict:
    if not transcript.strip():
        raise ValueError("Transcript is empty. Add or transcribe lecture content first.")
    prompt = f"""Create a clear, accurate study pack based only on this lecture transcript. Write in {language}. Return ONLY valid JSON with this schema: {{"title": string, "summary": string, "notes": [{{"heading": string, "content": string}}], "key_points": [string], "definitions": [{{"term": string, "meaning": string}}], "mcqs": [{{"question": string, "options": {{"A": string, "B": string, "C": string, "D": string}}, "answer": "A|B|C|D", "explanation": string}}]}}. Include exactly five MCQs. Do not invent facts absent from the transcript.\n\nTRANSCRIPT:\n{transcript}"""
    raw = _chat(prompt, json_mode=True).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        pack = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The AI returned an invalid study pack. Please try again.") from exc
    if not isinstance(pack, dict):
        raise RuntimeError("The AI returned an unexpected study-pack format.")
    pack.setdefault("title", "Lecture Notes")
    pack.setdefault("summary", "")
    pack.setdefault("notes", [])
    pack.setdefault("key_points", [])
    pack.setdefault("definitions", [])
    pack.setdefault("mcqs", [])
    if not isinstance(pack["mcqs"], list) or len(pack["mcqs"]) != 5:
        raise RuntimeError("The AI did not return exactly five quiz questions. Please generate the study pack again.")
    if not isinstance(pack["notes"], list) or not all(isinstance(item, dict) for item in pack["notes"]):
        raise RuntimeError("The AI returned notes in an unexpected format. Please generate the study pack again.")
    if not isinstance(pack["key_points"], list) or not all(isinstance(item, str) for item in pack["key_points"]):
        raise RuntimeError("The AI returned key points in an unexpected format. Please try again.")
    if not isinstance(pack["definitions"], list) or not all(isinstance(item, dict) for item in pack["definitions"]):
        raise RuntimeError("The AI returned definitions in an unexpected format. Please try again.")
    if not isinstance(pack["title"], str) or not isinstance(pack["summary"], str):
        raise RuntimeError("The AI returned a title or summary in an unexpected format. Please try again.")
    for note in pack["notes"]:
        if not isinstance(note.get("heading", ""), str) or not isinstance(note.get("content", ""), str):
            raise RuntimeError("The AI returned a note in an unexpected format. Please try again.")
    for definition in pack["definitions"]:
        if not isinstance(definition.get("term", ""), str) or not isinstance(definition.get("meaning", ""), str):
            raise RuntimeError("The AI returned a definition in an unexpected format. Please try again.")
    for question in pack["mcqs"]:
        if not isinstance(question, dict):
            raise RuntimeError("The AI returned a quiz question in an unexpected format. Please try again.")
        options = question.get("options")
        answer = str(question.get("answer", "")).upper()
        if (not isinstance(question.get("question"), str) or not question["question"].strip()
                or not isinstance(options, dict) or any(letter not in options for letter in "ABCD")
                or any(not isinstance(options[letter], str) or not options[letter].strip() for letter in "ABCD")
                or answer not in "ABCD"):
            raise RuntimeError("The AI returned an incomplete quiz question. Please generate the study pack again.")
        question["answer"] = answer
        if not isinstance(question.get("explanation", ""), str):
            raise RuntimeError("The AI returned a quiz explanation in an unexpected format. Please try again.")
    return pack


def translate_text(text: str, target_language: str) -> str:
    if not text.strip():
        raise ValueError("There is no study material to translate.")
    return _chat(f"Translate the following study material into {target_language}. Preserve headings, lists, and meaning. Return only the translation.\n\n{text}").strip()
