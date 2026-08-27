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