from collections import defaultdict
import pandas as pd


def results_to_dataframe(results: list) -> pd.DataFrame:
    if not results:
        return pd.DataFrame(columns=["result_id", "job_role", "category", "question", "score", "date"])

    df = pd.DataFrame(results)

    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    dropped = df["score"].isna().sum()
    if dropped > 0:
        print(f"[dashboard] Dropped {dropped} row(s) with non-numeric score values.")
    df = df.dropna(subset=["score"])

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


def compute_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"total_attempts": 0, "average_score": 0.0, "best_role": None, "weakest_role": None}

    by_role = df.groupby("job_role")["score"].mean()

    return {
        "total_attempts": len(df),
        "average_score": round(float(df["score"].mean()), 1),
        "best_role": by_role.idxmax() if not by_role.empty else None,
        "weakest_role": by_role.idxmin() if not by_role.empty else None,
    }


def average_by_role(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["job_role", "score"])
    return df.groupby("job_role", as_index=False)["score"].mean().round(1)


def average_by_category(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["category", "score"])
    return df.groupby("category", as_index=False)["score"].mean().round(1)


def compute_topic_stats(results: list, min_occurrences: int = 2) -> dict:
    matched_count = defaultdict(int)
    missing_count = defaultdict(int)

    for r in results:
        for kw in (r.get("matched_keywords") or "").split(","):
            kw = kw.strip().lower()
            if kw:
                matched_count[kw] += 1
        for kw in (r.get("missing_keywords") or "").split(","):
            kw = kw.strip().lower()
            if kw:
                missing_count[kw] += 1

    all_topics = set(matched_count) | set(missing_count)
    stats = []
    for topic in all_topics:
        total = matched_count[topic] + missing_count[topic]
        if total < min_occurrences:
            continue
        weakness_rate = missing_count[topic] / total
        stats.append({
            "topic": topic, "matched": matched_count[topic],
            "missing": missing_count[topic], "weakness_rate": weakness_rate, "total": total,
        })

    weak_topics = sorted([s for s in stats if s["weakness_rate"] > 0.5],
                          key=lambda x: (-x["weakness_rate"], -x["total"]))
    strong_topics = sorted([s for s in stats if s["weakness_rate"] <= 0.3],
                            key=lambda x: (x["weakness_rate"], -x["total"]))

    return {"weak_topics": weak_topics[:5], "strong_topics": strong_topics[:5]}