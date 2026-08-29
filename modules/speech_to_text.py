import streamlit as st
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.6-flash"


def _get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        return None


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    if not audio_bytes:
        return ""

    api_key = _get_api_key()
    if not api_key:
        return ""

    prompt = "Transcribe the following audio recording verbatim. Respond with ONLY the transcribed text, nothing else — no preamble, no quotes."

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        return (response.text or "").strip()
    except Exception as e:
        print(f"[speech_to_text] Transcription failed: {type(e).__name__}: {e}")
        return ""