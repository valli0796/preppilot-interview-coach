import re
from functools import lru_cache
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
KEYWORD_WEIGHT = 0.35
SEMANTIC_WEIGHT = 0.45
COMPLETENESS_WEIGHT = 0.20
MIN_EXPECTED_WORDS = 25
@lru_cache(maxsize=1)
def _get_nlp():
    return spacy.load("en_core_web_sm")
@lru_cache(maxsize=1)
def _get_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")
def _lemmatize(text: str) -> set:
    nlp = _get_nlp()
    doc = nlp(text.lower())
    return {tok.lemma_ for tok in doc if not tok.is_stop and not tok.is_punct and tok.text.strip()}
def _keyword_score(answer: str, expected_keywords: str):
    keywords = [k.strip().lower() for k in (expected_keywords or "").split(",") if k.strip()]
    if not keywords:
        return 50.0, [], []
    answer_lemmas = _lemmatize(answer)
    matched, missing = [], []
    for kw in keywords:
        kw_lemmas = _lemmatize(kw)
        if kw_lemmas & answer_lemmas or kw in answer.lower():
            matched.append(kw)
        else:
            missing.append(kw)
    score = (len(matched) / len(keywords)) * 100
    return score, matched, missing
def _semantic_score(answer: str, reference_answer: str) -> float:
    if not reference_answer or not reference_answer.strip():
        return 50.0
    embedder = _get_embedder()
    embeddings = embedder.encode([answer, reference_answer])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(max(0.0, min(1.0, similarity))) * 100
def _completeness_score(answer: str):
    words = re.findall(r"\b\w+\b", answer)
    word_count = len(words)
    nlp = _get_nlp()
    doc = nlp(answer)
    sentence_count = len(list(doc.sents))
    if word_count == 0:
        return 0.0, "no_answer"
    length_ratio = min(word_count / MIN_EXPECTED_WORDS, 1.0)
    score = length_ratio * 100
    note = None
    if word_count < 10:
        note = "too_short"
    elif sentence_count <= 1 and word_count > 15:
        note = "run_on"
    return score, note
def score_answer(answer: str, expected_keywords: str, reference_answer: str = ""):
    if not answer or not answer.strip():
        return 0.0, "No answer submitted. Try to write at least a few sentences."
    kw_score, matched, missing = _keyword_score(answer, expected_keywords)
    sem_score = _semantic_score(answer, reference_answer)
    comp_score, comp_note = _completeness_score(answer)
    final_score = round(
        kw_score * KEYWORD_WEIGHT
        + sem_score * SEMANTIC_WEIGHT
        + comp_score * COMPLETENESS_WEIGHT,
        1,
    )
    feedback = _build_feedback(final_score, matched, missing, comp_note)
    return final_score, feedback
def score_answer_with_details(answer: str, expected_keywords: str, reference_answer: str = ""):
    if not answer or not answer.strip():
        return 0.0, "No answer submitted. Try to write at least a few sentences.", [], []
    kw_score, matched, missing = _keyword_score(answer, expected_keywords)
    sem_score = _semantic_score(answer, reference_answer)
    comp_score, comp_note = _completeness_score(answer)
    final_score = round(
        kw_score * KEYWORD_WEIGHT
        + sem_score * SEMANTIC_WEIGHT
        + comp_score * COMPLETENESS_WEIGHT,
        1,
    )
    rule_based_feedback = _build_feedback(final_score, matched, missing, comp_note)
    return final_score, rule_based_feedback, matched, missing
def _build_feedback(score, matched, missing, comp_note):
    parts = []
    if score >= 80:
        parts.append("Strong answer overall.")
    elif score >= 55:
        parts.append("Solid attempt, with room to improve.")
    else:
        parts.append("This answer needs more depth.")

    if matched:
        parts.append(f"Covered well: {', '.join(matched)}.")
    if missing:
        parts.append(f"Consider mentioning: {', '.join(missing)}.")

    if comp_note == "too_short":
        parts.append("Try expanding your answer with more detail or an example.")
    elif comp_note == "run_on":
        parts.append("Consider breaking your answer into shorter, clearer sentences.")

    return " ".join(parts)