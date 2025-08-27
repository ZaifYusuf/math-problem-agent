# streamlit_app.py
import time
import streamlit as st
from problem_service import generate_problem, grade_problem

# ---------- Page setup ----------
st.set_page_config(page_title="SumRise - Math Problem Agent", page_icon="assets/SumRiseLogo.png", layout="centered")

# ---------- State init ----------
def _init_state():
    st.session_state.setdefault("problem", None)         
    st.session_state.setdefault("graded", None)          
    st.session_state.setdefault("total_attempts", 0)     
    st.session_state.setdefault("total_correct", 0)
    st.session_state.setdefault("start_time", None)      
_init_state()

# ---------- Small UI components ----------
def render_header():
    st.title("📘 Math Problem Agent")
    st.caption("Generate problems, show your work, get targeted feedback. Built with Streamlit + OpenAI.")

def render_metric_bar():
    total_attempts = st.session_state["total_attempts"]
    total_correct = st.session_state["total_correct"]
    acc = (100.0 * total_correct / total_attempts) if total_attempts else 0.0
    st.metric("Total Attempts", total_attempts)
    st.metric("Correct", total_correct)
    st.metric("Accuracy", f"{acc:.0f}%")

def render_sidebar():
    with st.sidebar:
        st.image("assets/SumRiseLogo.png", width=140, caption=None, output_format="PNG",
             use_container_width=False, clamp=False)
        st.header("Generate a Problem")
        problem_type = st.selectbox("Problem type", ["arithmetic", "algebra", "geometry"], key="ptype")
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key="pdiff")
        render_metric_bar()

        if st.button("Generate Problem", type="primary", use_container_width=True):
            try:
                with st.spinner("Thinking up a good problem..."):
                    prob = generate_problem(problem_type, difficulty)
                st.session_state["problem"] = prob
                st.session_state["graded"] = None
                st.session_state["start_time"] = time.time()
                st.toast("New problem ready!", icon="🎯")
            except Exception as e:
                st.error(f"Generation failed: {e}")

def render_problem_card(prob_or_text):
    with st.container(border=True):
        st.subheader("Problem")

        # Determine the content robustly
        if isinstance(prob_or_text, dict):
            content = prob_or_text.get("prompt") or prob_or_text.get("display_md") or ""
        elif hasattr(prob_or_text, "prompt"):
            content = getattr(prob_or_text, "prompt") or ""
        elif isinstance(prob_or_text, str):
            content = prob_or_text
        else:
            content = str(prob_or_text)

        st.markdown(content)

def render_timer():
    start_time = st.session_state.get("start_time")
    if start_time:
        elapsed = int(time.time() - start_time)
        st.caption(f"⏱️ Time on this problem: {elapsed}s")

def render_answer_form(problem_id: str):
    st.markdown("### Your Work & Answer")
    with st.form("answer_form", clear_on_submit=False, border=True):
        work = st.text_area("Show your work:", height=160, key="work")
        ans = st.text_input("Final answer:", key="answer")

        col_a, col_b = st.columns([1, 1])
        submit = col_a.form_submit_button("Check Answer", use_container_width=True)
        clear = col_b.form_submit_button("Clear Fields", use_container_width=True)

        if clear:
            st.session_state["work"] = ""
            st.session_state["answer"] = ""
            st.rerun()

        if submit:
            try:
                with st.spinner("Grading your submission..."):
                    res = grade_problem(problem_id, work, ans if ans else "(no answer)")
                st.session_state["graded"] = res
                st.session_state["total_attempts"] += 1
                if res["result"]["correct"]:
                    st.session_state["total_correct"] += 1
                    st.balloons()
            except Exception as e:
                st.error(f"Grading failed: {e}")

def render_result_panel():
    res = st.session_state.get("graded")
    if not res:
        return

    verdict = res["result"]["correct"]
    feedback = res["result"]["feedback"]
    hint = res["result"].get("hint")

    with st.container(border=True):
        st.subheader("Result")
        if verdict:
            st.success("✅ Correct! " + feedback)
        else:
            st.error("❌ Incorrect. " + feedback)
            if hint:
                st.info("Hint: " + hint)

# ---------- Page render ----------
render_header()
render_sidebar()

# Single main tab (keeps it simple & clean)
tab, = st.tabs(["Current Problem"])

with tab:
    prob = st.session_state.get("problem")
    if not prob:
        st.info("Use the sidebar to generate your first problem.")
    else:
        render_problem_card(prob)
        render_timer()
        # Support either dict or dataclass-like object from your service
        pid = prob["id"] if isinstance(prob, dict) else prob.id
        render_answer_form(pid)
        render_result_panel()

