import streamlit as st
from google import genai
MODEL_NAME = "gemini-3.6-flash"
def _get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        return None
def generate_llm_feedback(question: str, answer: str, score: float,
                           matched: list, missing: list, fallback_feedback: str) -> str:
    """Generate warm, specific feedback via Gemini. Falls back safely on any failure."""
    api_key = _get_api_key()
    if not api_key:
        return fallback_feedback
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""You are a supportive interview coach reviewing a candidate's practice answer.
Question: {question}
Candidate's answer: {answer}
Score: {score}/100
Concepts covered well: {', '.join(matched) if matched else 'none'}
Concepts missing: {', '.join(missing) if missing else 'none'}
Write 2-3 sentences of warm, specific, actionable feedback. Do not repeat the
score number. Do not use bullet points or headers. Speak directly to the candidate."""
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = (response.text or "").strip()
        return text if text else fallback_feedback
    except Exception as e:
        print(f"[llm_feedback] Generation failed: {type(e).__name__}: {e}")
        return fallback_feedback