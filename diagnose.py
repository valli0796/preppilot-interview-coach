import sqlite3
from pathlib import Path
DB_PATH = Path(__file__).resolve().parent / "database" / "interview_prep.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT result_id, score FROM interview_results")
rows = cur.fetchall()
fixed_count = 0
cleared_count = 0
for result_id, score in rows:
    if isinstance(score, (int, float)):
        continue 
    print(f"result_id={result_id}: bad score value = {score!r} (type: {type(score)})")
    recovered = None
    try:
        if isinstance(score, bytes):
            recovered = float(score.decode("utf-8", errors="ignore"))
        elif isinstance(score, str):
            recovered = float(score)
    except (ValueError, UnicodeDecodeError):
        recovered = None
    if recovered is not None:
        cur.execute("UPDATE interview_results SET score = ? WHERE result_id = ?", (recovered, result_id))
        print(f"  -> Recovered as {recovered}")
        fixed_count += 1
    else:
        cur.execute("UPDATE interview_results SET score = 0.0 WHERE result_id = ?", (result_id,))
        print(f"  -> Could not recover, set to 0.0")
        cleared_count += 1
conn.commit()
conn.close()
print()
print(f"Done. Recovered: {fixed_count}, Reset to 0.0: {cleared_count}, Total rows checked: {len(rows)}")