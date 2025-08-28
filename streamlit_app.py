import time
import streamlit as st
from problem_service import generate_problem, grade_problem
from streamlit_drawable_canvas import st_canvas
import base64
import io
from PIL import Image
import numpy as np

# ---------- Page setup ----------
st.set_page_config(page_title="SumRise - Math Problem Agent", page_icon="assets/SumRiseLogo.png", layout="centered")

# ---------- State init ----------
def _init_state():
    st.session_state.setdefault("problem", None)
    st.session_state.setdefault("graded", None)
    st.session_state.setdefault("total_attempts", 0)
    st.session_state.setdefault("total_correct", 0)
    st.session_state.setdefault("start_time", None)
    # nonce used to generate fresh widget keys when clearing / generating new problems
    st.session_state.setdefault("widget_nonce", 0)
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
        st.image("assets/SumRiseLogo.png", width=140, caption=None, output_format="PNG", clamp=False)
        st.header("Generate a Problem")
        problem_type = st.selectbox("Problem type", ["arithmetic", "algebra", "geometry"], key="ptype")
        difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"], key="pdiff")
        render_metric_bar()

        if st.button("Generate Problem", type="primary", width="stretch"):
            try:
                with st.spinner("Thinking up a good problem..."):
                    prob = generate_problem(problem_type, difficulty)
                st.session_state["problem"] = prob
                st.session_state["graded"] = None
                st.session_state["start_time"] = time.time()
                # bump nonce to recreate widgets fresh if needed
                st.session_state["widget_nonce"] += 1
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

    input_mode = st.radio("Input mode", ["Type", "Draw"], key="input_mode", horizontal=True)

    # use nonce to create unique widget keys so we can safely clear/reset by bumping the nonce
    nonce = st.session_state["widget_nonce"]
    work_key = f"work_{nonce}"
    canvas_key = f"canvas_{nonce}"
    ans_key = f"answer_{nonce}"

    with st.form("answer_form", clear_on_submit=False, border=True):
        if input_mode == "Type":
            work_widget = st.text_area("Show your work:", height=160, key=work_key,
                                       value=st.session_state.get("work", ""))
        else:
            st.write("Draw your work below:")
            # Use fixed integer width to avoid passing non-serializable objects
            canvas_result = st_canvas(
                fill_color=None,
                stroke_width=2,
                stroke_color="#000000",
                background_color="#ffffff",
                height=400,
                width=700,
                drawing_mode="freedraw",
                key=canvas_key,
            )
            work_widget = ""  # encode canvas to base64 below if present

        # answer widget uses unique key and initial value read from canonical session_state if present
        ans_widget = st.text_input("Final answer:", key=ans_key, value=st.session_state.get("answer", ""))

        submit = st.form_submit_button("Check Answer", width="stretch")

    col1, col2 = st.columns([1, 1])
    clear = col1.button("Clear Fields", width="stretch")
    new_prob = col2.button("Generate New Problem", width="stretch")

    # Handle form submission
    if submit:
        # Determine user work: prefer typed widget value if Type mode; otherwise use canvas image
        user_work = ""
        if input_mode == "Type":
            user_work = st.session_state.get(work_key, "")
        else:
            # convert canvas image data to base64 PNG if available
            canvas_obj = st.session_state.get(canvas_key) if canvas_key in st.session_state else None
            
            if canvas_key in st.session_state and isinstance(st.session_state[canvas_key], dict):
                img_data = st.session_state[canvas_key].get("image_data")
            else:
                # fallback: try to read from a temporary place if available
                img_data = None
            if img_data is None:
                img_data = None
            if img_data is not None:
                try:
                    arr = np.array(img_data).astype("uint8")
                    img = Image.fromarray(arr)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    user_work = base64.b64encode(buf.getvalue()).decode("utf-8")
                except Exception:
                    user_work = ""
            else:
                user_work = ""

        user_answer = st.session_state.get(ans_key, "")

        try:
            with st.spinner("Grading your submission..."):
                res = grade_problem(problem_id, user_work, user_answer if user_answer else "(no answer)")
            st.session_state["graded"] = res
            st.session_state["total_attempts"] += 1
            if res["result"].get("correct"):
                st.session_state["total_correct"] += 1
                st.balloons()
        except Exception as e:
            st.error(f"Grading failed: {e}")

    # Clear fields button behavior: bump nonce then rerun so widgets are recreated cleared
    if clear:
        st.session_state["work"] = ""
        st.session_state["answer"] = ""
        st.session_state["widget_nonce"] += 1

    # Generate new problem: create problem, update state, bump nonce, rerun
    if new_prob:
        problem_type = st.session_state.get("ptype", "arithmetic")
        difficulty = st.session_state.get("pdiff", "easy")
        try:
            with st.spinner("Generating new problem..."):
                prob = generate_problem(problem_type, difficulty)
            st.session_state["problem"] = prob
            st.session_state["graded"] = None
            st.session_state["start_time"] = time.time()
            st.session_state["work"] = ""
            st.session_state["answer"] = ""
            st.session_state["widget_nonce"] += 1
            st.toast("New problem ready!", icon="🎯")
        except Exception as e:
            st.error(f"Generation failed: {e}")

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

