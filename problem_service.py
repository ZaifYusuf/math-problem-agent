import uuid
from llm_utils import json_chat
import prompts

MODEL = "gpt-4o-mini"
_STORE = {}  # in-memory store (swap for DB later)

def generate_problem(problem_type: str, difficulty: str) -> dict:
    payload = json_chat(
        MODEL,
        prompts.GENERATOR_SYSTEM,
        prompts.GENERATOR_USER.format(problem_type=problem_type, difficulty=difficulty),
    )
    pid = str(uuid.uuid4())
    problem = {
        "id": pid,
        "prompt": payload["prompt"],
        "solution": payload["solution"],
        "final_answer": payload["final_answer"],
        "rubric": payload["rubric"],
    }
    _STORE[pid] = problem
    return {"id": pid, "prompt": problem["prompt"]}

def grade_problem(problem_id: str, user_work: str, user_answer: str) -> dict:
    ref = _STORE.get(problem_id)
    if not ref:
        raise ValueError("Unknown problem_id")
    payload = json_chat(
        MODEL,
        prompts.GRADER_SYSTEM,
        prompts.GRADER_USER.format(
            solution=ref["solution"],
            final_answer=ref["final_answer"],
            rubric=ref["rubric"],
            user_work=user_work,
            user_answer=user_answer,
        ),
    )
    return {"problem_id": problem_id, "result": payload}
