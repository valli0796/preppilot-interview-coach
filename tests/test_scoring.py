import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.scoring import score_answer
REFERENCE = (
    "Lists are mutable and can be changed after creation, while tuples "
    "are immutable and cannot be modified once created. Both are ordered collections."
)
KEYWORDS = "mutable,immutable,list,tuple,ordered"
def test_empty_answer_scores_zero():
    score, feedback = score_answer("", KEYWORDS, REFERENCE)
    assert score == 0.0
    assert "No answer submitted" in feedback
def test_strong_answer_scores_high():
    answer = (
        "Lists are mutable and can be changed after creation, while tuples "
        "are immutable and cannot be modified once created. Both are ordered collections."
    )
    score, _ = score_answer(answer, KEYWORDS, REFERENCE)
    assert score >= 80, f"Expected a high score for a near-perfect answer, got {score}"
def test_paraphrased_answer_scores_reasonably():
    """Same meaning, different words — semantic similarity should still credit this."""
    answer = "You can change a list but not a tuple. Both keep items in order."
    score, _ = score_answer(answer, KEYWORDS, REFERENCE)
    assert score >= 40, f"Paraphrased correct answer scored too low: {score}"
def test_keyword_stuffing_scores_lower_than_real_explanation():
    """A word dump with all keywords should NOT beat a real explanation."""
    stuffed = "Mutable immutable list tuple ordered."
    real_answer = (
        "Lists are mutable and can be changed after creation, while tuples "
        "are immutable and cannot be modified once created. Both are ordered collections."
    )
    stuffed_score, _ = score_answer(stuffed, KEYWORDS, REFERENCE)
    real_score, _ = score_answer(real_answer, KEYWORDS, REFERENCE)
    assert stuffed_score < real_score, (
        f"Keyword stuffing ({stuffed_score}) should score lower than a real "
        f"explanation ({real_score}) — scoring may be gameable."
    )
def test_irrelevant_answer_scores_low():
    answer = "I like pizza and going for walks on the weekend."
    score, _ = score_answer(answer, KEYWORDS, REFERENCE)
    assert score < 40, f"Irrelevant answer scored too high: {score}"
def test_missing_reference_answer_does_not_crash():
    """If reference_answer is blank (e.g. old CSV rows), scoring should still work."""
    answer = "Lists are mutable, tuples are immutable, both are ordered."
    score, feedback = score_answer(answer, KEYWORDS, "")
    assert 0 <= score <= 100
    assert feedback