"""
scoring.py
----------
WEEK 1 PLACEHOLDER. Simple keyword-overlap score just so the
end-to-end flow works. Week 2 replaces this with real NLP scoring.
"""


def score_answer(answer: str, expected_keywords: str) -> tuple[float, str]:
    if not answer or not answer.strip():
        return 0.0, "No answer submitted. Try to write at least a few sentences."

    keywords = [k.strip().lower() for k in (expected_keywords or "").split(",") if k.strip()]
    if not keywords:
        return 50.0, "No keyword benchmark set for this question yet."

    answer_lower = answer.lower()
    matched = [k for k in keywords if k in answer_lower]

    score = round((len(matched) / len(keywords)) * 100, 1)

    if score >= 80:
        feedback = f"Strong answer. Covered: {', '.join(matched)}."
    elif score >= 40:
        missing = [k for k in keywords if k not in matched]
        feedback = f"Decent start, but missing some key concepts: {', '.join(missing)}."
    else:
        feedback = (
            "This answer needs more depth. Try to mention concepts like: "
            f"{', '.join(keywords)}."
        )

    return score, feedback