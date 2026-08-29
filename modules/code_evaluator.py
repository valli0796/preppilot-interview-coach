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
    if "score" not in data or "feedback" not in data:
        raise ValueError("Response missing required fields")
    return data


def evaluate_code_answer(question: str, user_code: str, reference_solution: str,
                          expected_concepts: str) -> tuple[float, str]:
    if not user_code or not user_code.strip():
        return 0.0, "No code submitted."

    api_key = _get_api_key()
    if not api_key:
        return 50.0, "Code review unavailable (no API key configured). Score is a placeholder."

    prompt = f"""You are a technical interviewer reviewing a candidate's code submission.
Do NOT execute the code. Review it by reading it carefully.

Problem: {question}

Candidate's code:
Key concepts/algorithms expected: {expected_concepts}

Reference solution (for your comparison only, don't reveal it to the candidate):
Evaluate the candidate's code for correctness, edge cases, time/space
complexity, and code quality. Respond with ONLY valid JSON, no markdown,
no extra text, in exactly this shape:
{{
  "score": a number from 0 to 100,
  "feedback": "2-3 sentences of specific, constructive feedback on their code, mentioning what's right and what could improve"
}}"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        result = _parse_response(response.text)
        score = max(0.0, min(100.0, float(result["score"])))
        return round(score, 1), result["feedback"]
    except Exception as e:
        print(f"[code_evaluator] Evaluation failed: {type(e).__name__}: {e}")
        return 50.0, "Automated code review failed. Please try submitting again."