from pathlib import Path
import datetime
import hashlib
import streamlit as st
import extra_streamlit_components as stx
import plotly.express as px

from modules.database import init_db, seed_questions_from_csv
from modules.auth import (
    register_user, login_user,
    create_remember_token, get_user_by_remember_token, delete_remember_token,
)
from modules.questions import SUGGESTED_ROLES, get_next_question, save_result, get_user_results
from modules.scoring import score_answer_with_details
from modules.llm_feedback import generate_llm_feedback
from modules.code_evaluator import evaluate_code_answer
from modules.media_evaluator import evaluate_media_answer
from modules.speech_to_text import transcribe_audio
from modules.resume_parser import extract_resume_text
from modules.dashboard import (
    results_to_dataframe, compute_summary, average_by_role,
    average_by_category, compute_topic_stats,
)

DATA_CSV = Path(__file__).resolve().parent / "data" / "questions.csv"

st.set_page_config(page_title="PrepPilot", page_icon="🎯", layout="centered")

cookie_manager = stx.CookieManager()

init_db()
seed_questions_from_csv(DATA_CSV)

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    remembered_token = cookie_manager.get("remember_token")
    if remembered_token:
        remembered_user = get_user_by_remember_token(remembered_token)
        if remembered_user:
            st.session_state.user = remembered_user

if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = None
if "active_role" not in st.session_state:
    st.session_state.active_role = None
if "active_category" not in st.session_state:
    st.session_state.active_category = None
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "resume_filename" not in st.session_state:
    st.session_state.resume_filename = None


def logout():
    token = cookie_manager.get("remember_token")
    if token:
        delete_remember_token(token)
        cookie_manager.delete("remember_token", key="delete_remember_cookie")
    st.session_state.user = None
    st.session_state.current_question = None
    st.session_state.last_feedback = None


def show_auth_screen():
    st.title("🎯 PrepPilot")
    st.caption("Practice technical, coding, and HR interviews with instant feedback.")

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
                    token = create_remember_token(user["user_id"])
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("remember_token", token, expires_at=expires, key="set_remember_cookie")
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


def render_sidebar_resume_upload():
    st.sidebar.subheader("Resume (optional)")

    uploaded = st.sidebar.file_uploader("Upload PDF resume", type=["pdf"], key="resume_upload")

    if uploaded is not None and st.session_state.get("resume_filename") != uploaded.name:
        with st.spinner("Reading your resume..."):
            try:
                text = extract_resume_text(uploaded)
                st.session_state.resume_text = text
                st.session_state.resume_filename = uploaded.name
                st.sidebar.success(f"Resume loaded ({len(text)} characters).")
            except Exception as e:
                st.sidebar.error(f"Couldn't read that PDF: {e}")
                st.session_state.resume_text = ""
                st.session_state.resume_filename = None

    if st.session_state.get("resume_text"):
        st.sidebar.caption(f"Using resume: {st.session_state.get('resume_filename', 'uploaded file')}")
        if st.sidebar.button("Clear resume"):
            st.session_state.resume_text = ""
            st.session_state.resume_filename = None
            st.rerun()


def render_sidebar_role_picker(user):
    st.sidebar.subheader("Choose Role")

    role_choice = st.sidebar.selectbox(
        "Job Role", SUGGESTED_ROLES + ["Other (type your own)"], key="role_select"
    )
    if role_choice == "Other (type your own)":
        job_role = st.sidebar.text_input("Type any job role", key="custom_role")
    else:
        job_role = role_choice

    category = st.sidebar.selectbox("Interview Type", ["Technical", "HR", "Coding"], key="category_select")

    start_disabled = not job_role or not job_role.strip()

    if st.sidebar.button("Start / Change Role", type="primary", disabled=start_disabled):
        st.session_state.active_role = job_role
        st.session_state.active_category = category
        st.session_state.last_feedback = None
        with st.spinner("Loading your first question..."):
            st.session_state.current_question, generated = get_next_question(
                job_role, category, user["user_id"], resume_text=st.session_state.get("resume_text", "")
            )
        if generated:
            st.toast("Generated a fresh question with AI for this role.")
        st.rerun()

    if st.session_state.active_role:
        st.sidebar.caption(f"Currently practicing: **{st.session_state.active_role}** ({st.session_state.active_category})")


def render_sidebar_history(user):
    results = get_user_results(user["user_id"])
    if not results:
        return

    st.sidebar.divider()
    st.sidebar.subheader("History")

    for r in results[:20]:
        label = f"{r['job_role']} · {r['score']}/100"
        with st.sidebar.expander(label):
            st.caption(r["question"])
            st.write(f"**Your answer:** {r['answer']}")
            st.write(f"**Feedback:** {r['feedback']}")
            st.caption(f"Date: {r['date']}")


def show_main_app():
    user = st.session_state.user

    with st.sidebar:
        st.markdown("## 🎯 PrepPilot")
        st.markdown(f"**Logged in as:** {user['name']}")
        st.caption(user["email"])
        if st.button("Log Out"):
            logout()
            st.rerun()
        st.divider()

    render_sidebar_resume_upload()
    render_sidebar_role_picker(user)
    render_sidebar_history(user)

    tab_practice, tab_history, tab_dashboard = st.tabs(["Practice", "My History", "Dashboard"])

    with tab_practice:
        run_practice_tab(user)

    with tab_history:
        run_history_tab(user)

    with tab_dashboard:
        run_dashboard_tab(user)


def run_practice_tab(user):
    q = st.session_state.current_question

    if not q:
        st.info("Pick a job role and interview type in the sidebar, then click 'Start / Change Role' to begin.")
        return

    if st.session_state.last_feedback:
        score, feedback = st.session_state.last_feedback
        st.metric("Last Score", f"{score}/100")
        if score >= 80:
            st.success(feedback)
        elif score >= 40:
            st.warning(feedback)
        else:
            st.error(feedback)
        st.divider()

    st.subheader("Question")
    st.write(q["question"])
    st.caption(f"Role: {st.session_state.active_role} · Difficulty: {q.get('difficulty', '—')}")

    is_coding = q.get("category") == "Coding"
    answer_label = "Your Answer" if not is_coding else "Your Code"
    answer_height = 250 if is_coding else 150

    media_file = None

    if not is_coding:
        col_mic, col_attach = st.columns([1, 1])

        with col_mic:
            with st.popover("🎙️ Speak"):
                audio_value = st.audio_input("Record your answer", key=f"audio_{q['question_id']}")
                if audio_value is not None:
                    audio_bytes = audio_value.getvalue()
                    audio_hash = hashlib.md5(audio_bytes).hexdigest()
                    last_hash_key = f"last_transcribed_hash_{q['question_id']}"

                    if st.session_state.get(last_hash_key) != audio_hash:
                        with st.spinner("Transcribing..."):
                            transcribed = transcribe_audio(audio_bytes, audio_value.type or "audio/wav")
                        if transcribed:
                            st.session_state[f"answer_{q['question_id']}"] = transcribed
                            st.session_state[last_hash_key] = audio_hash
                            st.rerun()
                        else:
                            st.warning("Couldn't transcribe that recording. Try again.")

        with col_attach:
            with st.popover("📎 Attach"):
                media_file = st.file_uploader(
                    "Image or short video",
                    type=["png", "jpg", "jpeg", "mp4", "mov", "webm"],
                    key=f"media_{q['question_id']}",
                )
                if media_file is not None:
                    st.caption(f"Attached: {media_file.name}")

    answer = st.text_area(answer_label, height=answer_height, key=f"answer_{q['question_id']}")

    if st.button("Submit Answer", type="primary"):
        matched_kw_str = ""
        missing_kw_str = ""

        if media_file is not None:
            with st.spinner("Reviewing your uploaded file..."):
                media_bytes = media_file.read()
                score, feedback = evaluate_media_answer(
                    q["question"], media_bytes, media_file.type,
                    text_answer=answer, expected_keywords=q["expected_keywords"],
                )
            saved_answer = f"[Attached: {media_file.name}] {answer}".strip()
        elif is_coding:
            with st.spinner("Reviewing your code..."):
                score, feedback = evaluate_code_answer(
                    q["question"], answer, q.get("reference_answer", ""), q["expected_keywords"]
                )
            saved_answer = answer
        else:
            score, rule_feedback, matched, missing = score_answer_with_details(
                answer, q["expected_keywords"], q.get("reference_answer", "")
            )
            feedback = generate_llm_feedback(
                q["question"], answer, score, matched, missing, rule_feedback
            )
            saved_answer = answer
            matched_kw_str = ",".join(matched)
            missing_kw_str = ",".join(missing)

        save_result(user["user_id"], q["question_id"], saved_answer, score, feedback,
                    matched_keywords=matched_kw_str, missing_keywords=missing_kw_str)
        st.session_state.last_feedback = (score, feedback)

        with st.spinner("Loading your next question..."):
            next_q, generated = get_next_question(
                st.session_state.active_role, st.session_state.active_category, user["user_id"],
                resume_text=st.session_state.get("resume_text", "")
            )
            st.session_state.current_question = next_q
            if generated:
                st.toast("Generated a fresh question with AI.")

        st.rerun()


def run_history_tab(user):
    results = get_user_results(user["user_id"])
    if not results:
        st.info("No interview attempts yet. Head to the Practice tab to get started.")
        return

    valid_scores = [float(r["score"]) for r in results if isinstance(r["score"], (int, float))]
    st.metric("Total Attempts", len(results))
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
    st.metric("Average Score", f"{avg_score:.1f}/100")

    for r in results:
        with st.expander(f"{r['job_role']} · {r['question'][:60]}... — {r['score']}/100"):
            st.write(f"**Your answer:** {r['answer']}")
            st.write(f"**Feedback:** {r['feedback']}")
            st.caption(f"Date: {r['date']}")


def run_dashboard_tab(user):
    results = get_user_results(user["user_id"])
    df = results_to_dataframe(results)

    if df.empty:
        st.info("No data yet — complete a few practice interviews to see your dashboard.")
        return

    summary = compute_summary(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Attempts", summary["total_attempts"])
    col2.metric("Average Score", f"{summary['average_score']}/100")
    col3.metric("Strongest Role", summary["best_role"] or "—")
    col4.metric("Weakest Role", summary["weakest_role"] or "—")

    st.divider()

    st.subheader("Score Over Time")
    fig_trend = px.line(df, x="date", y="score", markers=True)
    fig_trend.update_layout(yaxis_range=[0, 100], xaxis_title="Date", yaxis_title="Score")
    st.plotly_chart(fig_trend, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Average by Job Role")
        role_df = average_by_role(df)
        fig_role = px.bar(role_df, x="job_role", y="score")
        fig_role.update_layout(yaxis_range=[0, 100], xaxis_title="", yaxis_title="Avg Score")
        st.plotly_chart(fig_role, use_container_width=True)

    with col_b:
        st.subheader("Average by Category")
        cat_df = average_by_category(df)
        fig_cat = px.bar(cat_df, x="category", y="score")
        fig_cat.update_layout(yaxis_range=[0, 100], xaxis_title="", yaxis_title="Avg Score")
        st.plotly_chart(fig_cat, use_container_width=True)

    topic_stats = compute_topic_stats(results)
    if topic_stats["weak_topics"] or topic_stats["strong_topics"]:
        st.divider()
        col_weak, col_strong = st.columns(2)
        with col_weak:
            st.subheader("Weak Topics")
            if topic_stats["weak_topics"]:
                for t in topic_stats["weak_topics"]:
                    st.write(f"🔴 **{t['topic']}** — missed {t['missing']}/{t['total']} times")
            else:
                st.caption("Not enough data yet.")
        with col_strong:
            st.subheader("Strong Topics")
            if topic_stats["strong_topics"]:
                for t in topic_stats["strong_topics"]:
                    st.write(f"🟢 **{t['topic']}** — nailed {t['matched']}/{t['total']} times")
            else:
                st.caption("Not enough data yet.")

    if summary["weakest_role"]:
        st.info(f"Your weakest area right now is **{summary['weakest_role']}** — consider practicing more questions there.")


if st.session_state.user is None:
    show_auth_screen()
else:
    show_main_app()