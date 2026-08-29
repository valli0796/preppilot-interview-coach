import json
import streamlit as st
from google import genai

MODEL_NAME = "gemini-3.6-flash"
RESUME_MAX_CHARS = 3000


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


def _build_resume_block(resume_text: str) -> str:
    if not resume_text or not resume_text.strip():
        return ""
    truncated = resume_text[:RESUME_MAX_CHARS]
    return (
        f"\nThe candidate's resume includes this background — tailor the "
        f"question to reference their actual skills, projects, or experience "
        f"where relevant, but do not quote the resume verbatim:\n{truncated}\n"
    )


def generate_question(job_role: str, category: str, avoid_questions: list = None,
                       resume_text: str = "") -> dict | None:
    api_key = _get_api_key()
    if not api_key:
        print("[question_generator] No GEMINI_API_KEY found in secrets.toml - skipping generation.")
        return None

    avoid_questions = avoid_questions or []
    avoid_block = ""
    if avoid_questions:
        avoid_list = "\n".join(f"- {q}" for q in avoid_questions[:15])
        avoid_block = f"\nDo NOT repeat or closely rephrase any of these already-asked questions:\n{avoid_list}\n"

    resume_block = _build_resume_block(resume_text)

    if category == "Coding":
        prompt = f"""Generate ONE coding interview problem for a "{job_role}" candidate.
{avoid_block}{resume_block}
The problem should be solvable in Python in about 10-20 lines. Include a
clear problem statement with at least one example input/output.

Respond with ONLY valid JSON, no markdown formatting, no code fences, no extra text.
Use exactly this shape:
{{
  "question": "the full problem statement including an example input/output",
  "expected_keywords": "comma,separated,key,algorithms,or,concepts,e.g.,two pointers,hash map,recursion",
  "reference_answer": "a correct, working Python solution as a code string",
  "difficulty": "Easy" or "Medium" or "Hard"
}}"""
    else:
        prompt = f"""Generate ONE interview question for a "{job_role}" candidate, category "{category}".
{avoid_block}{resume_block}
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