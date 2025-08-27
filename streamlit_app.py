import streamlit as st
from problem_service import generate_problem, grade_problem

st.set_page_config(page_title="Math Problem Agent", layout="centered")
st.title("📘 Math Problem Agent")

with st.sidebar:
    st.header("Generate a Problem")
    problem_type = st.selectbox("Problem type", ["arithmetic", "algebra", "geometry"])
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    if st.button("Generate Problem", use_container_width=True):
        try:
            prob = generate_problem(problem_type, difficulty)
            st.session_state["problem"] = prob
            st.session_state["graded"] = None
        except Exception as e:
            st.error(f"Generation failed: {e}")

# Show the current problem
prob = st.session_state.get("problem")
if prob:
    st.subheader("Problem")
    st.write(prob["prompt"])

    with st.form("answer_form", clear_on_submit=False):
        work = st.text_area("Show your work:", height=180, key="work")
        ans = st.text_input("Final answer:", key="answer")
        submitted = st.form_submit_button("Check Answer")
        if submitted:
            try:
                result = grade_problem(prob["id"], work, ans)
                st.session_state["graded"] = result
            except Exception as e:
                st.error(f"Grading failed: {e}")

    res = st.session_state.get("graded")
    if res:
        verdict = res["result"]["correct"]
        feedback = res["result"]["feedback"]
        hint = res["result"].get("hint")
        if verdict:
            st.success("✅ Correct! " + feedback)
        else:
            st.error("❌ Incorrect. " + feedback)
            if hint:
                st.info("Hint: " + hint)
else:
    st.info("Use the sidebar to generate your first problem.")
