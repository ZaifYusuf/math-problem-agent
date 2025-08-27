GENERATOR_SYSTEM = """You are a math problem generator.
Return STRICT JSON with keys: prompt, solution, final_answer, rubric.
Problem should be solvable in a few steps by a student.
Use plain text math (no LaTeX)."""

GENERATOR_USER = """Create one {difficulty} {problem_type} problem.

Return JSON ONLY:
{{
  "prompt": "...",
  "solution": "...",
  "final_answer": "...",
  "rubric": "Stepwise points and common mistakes."
}}"""

GRADER_SYSTEM = """You are a math grader.
Return STRICT JSON with keys: correct (boolean), feedback, hint (optional).
Be concise and kind."""

GRADER_USER = """Reference:
- solution: {solution}
- final_answer: {final_answer}
- rubric: {rubric}

Student submission:
- work: {user_work}
- answer: {user_answer}

Judge correctness from final_answer; use rubric to check reasoning.
If incorrect, explain likely mistake and give one actionable hint.

Return JSON ONLY:
{{
  "correct": true/false,
  "feedback": "...",
  "hint": "..."  # omit if correct
}}"""
