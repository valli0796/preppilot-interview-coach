import json
import streamlit as st
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.6-flash"
MAX_INLINE_BYTES = 20 * 1024 * 1024


def _get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        return None


def evaluate_media_answer(question: str, media_bytes: bytes, mime_type: str,
                           text_answer: str = "", expected_keywords: str = "") -> tuple[float, str]:
    if not media_bytes:
        return 0.0, "No file was attached."

    if len(media_bytes) > MAX_INLINE_BYTES:
        size_mb = len(media_bytes) / (1024 * 1024)
        return 0.0, f"That file is too large ({size_mb:.1f} MB). Please attach a file under 20 MB."

    api_key = _get_api_key()
    if not api_key:
        return 50.0, "Media review unavailable (no API key configured). Score is a placeholder."

    context_line = f"\nThe candidate also wrote this alongside their upload: {text_answer}\n" if text_answer else ""

    prompt = f"""You are an interview coach reviewing a candidate's submission,
which includes an attached image or video.

Question: {question}
Key concepts expected: {expected_keywords}
{context_line}
Look at the attached file (it may be a whiteboard diagram, code
screenshot, or a video explanation) and evaluate how well it answers
the question. Respond with ONLY valid JSON, no markdown, no extra text:
{{
  "score": a number from 0 to 100,
  "feedback": "2-3 sentences of specific, constructive feedback"
}}"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=media_bytes, mime_type=mime_type),
                prompt,
            ],
        )
        cleaned = response.text.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        score = max(0.0, min(100.0, float(result["score"])))
        return round(score, 1), result["feedback"]
    except Exception as e:
        print(f"[media_evaluator] Evaluation failed: {type(e).__name__}: {e}")
        return 50.0, "Automated media review failed. Please try again."