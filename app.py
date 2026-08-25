"""
app.py
------
AI-Based Interview Preparation System — main Streamlit entry point.
"""

from pathlib import Path
import streamlit as st

from modules.database import init_db, seed_questions_from_csv
from modules.auth import register_user, login_user
from modules.questions import JOB_ROLES, get_questions, save_result, get_user_results
from modules.scoring import score_answer

DATA_CSV = Path(__file__).resolve().parent / "data" / "questions.csv"

st.set_page_config(page_title="AI Interview Prep", page_icon="🎯", layout="centered")

init_db()
seed_questions_from_csv(DATA_CSV)

if "user" not in st.session_state:
    st.session_state.user = None
if "current_question" not in st.session_state:
    st.session_state.current_question = None


def logout():
    st.session_state.user = None
    st.session_state.current_question = None


def show_auth_screen():
    st.title("🎯 AI Interview Prep")
    st.caption("Practice technical and HR interviews with instant feedback.")

    tab_login, tab_register = st.tabs(["Log In", "Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In")
            if submitted:
                success, message, user = login_user(email, password)
                if success:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error(message)

    with tab_register:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email_r = st.text_input("Email", key="reg_email")
            password_r = st.text_input("Password", type="password", key="reg_pw")
            skills = st.text_input("Skills (comma-separated, optional)")
            qualification = st.text_input("Qualification (optional)")
            submitted_r = st.form_submit_button("Register")
            if submitted_r:
                success, message = register_user(name, email_r, password_r, skills, qualification)
                if success:
                    st.success(message)
                else:
                    st.error(message)


def show_main_app():
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"**Logged in as:** {user['name']}")
        st.caption(user["email"])
        if st.button("Log Out"):
            logout()
            st.rerun()

    st.title("🎯 AI Interview Prep")

    tab_practice, tab_history = st.tabs(["Practice Interview", "My History"])

    with tab_practice:
        run_practice_tab(user)

    with tab_history:
        run_history_tab(user)


def run_practice_tab(user):
    col1, col2 = st.columns(2)
    with col1:
        job_role = st.selectbox("Select Job Role", JOB_ROLES)
    with col2:
        category = "HR" if job_role == "HR Interview" else st.selectbox(
            "Interview Type", ["Technical"]
        )

    if st.button("Get a Question", type="primary"):
        questions = get_questions(job_role, category=category)
        if not questions:
            st.warning("No questions found for this role yet.")
        else:
            import random
            st.session_state.current_question = random.choice(questions)

    q = st.session_state.current_question
    if q:
        st.divider()
        st.subheader("Question")
        st.write(q["question"])
        st.caption(f"Role: {q['job_role']} · Difficulty: {q['difficulty']}")

        answer = st.text_area("Your Answer", height=150, key=f"answer_{q['question_id']}")

        if st.button("Submit Answer"):
            score, feedback = score_answer(answer, q["expected_keywords"])
            save_result(user["user_id"], q["question_id"], answer, score, feedback)

            st.metric("Score", f"{score}/100")
            if score >= 80:
                st.success(feedback)
            elif score >= 40:
                st.warning(feedback)
            else:
                st.error(feedback)

            st.info(
                "Note: this is a placeholder keyword-based score. "
                "Real NLP-based semantic scoring is planned for Week 2."
            )


def run_history_tab(user):
    results = get_user_results(user["user_id"])
    if not results:
        st.info("No interview attempts yet. Head to the Practice tab to get started.")
        return

    st.metric("Total Attempts", len(results))
    avg_score = sum(r["score"] for r in results) / len(results)
    st.metric("Average Score", f"{avg_score:.1f}/100")

    for r in results:
        with st.expander(f"{r['job_role']} · {r['question'][:60]}... — {r['score']}/100"):
            st.write(f"**Your answer:** {r['answer']}")
            st.write(f"**Feedback:** {r['feedback']}")
            st.caption(f"Date: {r['date']}")


if st.session_state.user is None:
    show_auth_screen()
else:
    show_main_app()