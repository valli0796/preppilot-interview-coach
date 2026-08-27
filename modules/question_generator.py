import json
import streamlit as st
from google import genai
MODEL_NAME = "gemini-3.6-flash"
def _get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        return None
def _parse_response(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    data = json.loads(cleaned)
    required = ["question", "expected_keywords", "reference_answer", "difficulty"]
    for field in required:
        if field not in data or not data[field]:
            raise ValueError(f"LLM response missing required field: {field}")
    return data
def generate_question(job_role: str, category: str, avoid_questions: list = None) -> dict | None:
    api_key = _get_api_key()
    if not api_key:
        print("[question_generator] No GEMINI_API_KEY found in secrets.toml - skipping generation.")
        return None
    avoid_questions = avoid_questions or []
    avoid_block = ""
    if avoid_questions:
        avoid_list = "\n".join(f"- {q}" for q in avoid_questions[:15])
        avoid_block = f"\nDo NOT repeat or closely rephrase any of these already-asked questions:\n{avoid_list}\n"
    prompt = f"""Generate ONE interview question for a "{job_role}" candidate, category "{category}".
{avoid_block}
Respond with ONLY valid JSON, no markdown formatting, no code fences, no extra text.
Use exactly this shape:
{{
  "question": "the interview question text",
  "expected_keywords": "comma,separated,key,concepts,expected,in,a,good,answer",
  "reference_answer": "a 2-3 sentence model answer covering the key concepts",
  "difficulty": "Easy" or "Medium" or "Hard"
}}"""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return _parse_response(response.text)
    except Exception as e:
        print(f"[question_generator] Generation failed: {type(e).__name__}: {e}")
        return None