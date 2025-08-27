import uuid
from llm_utils import json_chat
import prompts

MODEL = "gpt-4o-mini"

# In-memory store of problems (server-side only).
# Keys are problem_id; values hold everything needed for grading.
_STORE: dict[str, dict] = {}


def _coalesce(payload: dict, *keys: str, default: str = "") -> str:
    """Return the first non-empty value among payload[key] for keys."""
    for k in keys:
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return default


def generate_problem(problem_type: str, difficulty: str) -> dict:
    """
    Returns: {"id": <uuid>, "prompt": <display_md>}
    - 'prompt' is a fully formatted Markdown+LaTeX block (consistent every time)
      because the generator prompt now produces `display_md`.
    """
    payload = json_chat(
        MODEL,
        prompts.GENERATOR_SYSTEM,
        prompts.GENERATOR_USER.format(problem_type=problem_type, difficulty=difficulty),
    )

    # Defensive mapping in case the model ever omits a field.
    display_md     = _coalesce(payload, "display_md", "prompt")
    solution_md    = _coalesce(payload, "solution_md", "solution")
    final_answer   = _coalesce(payload, "final_answer_tex", "final_answer")
    rubric_md      = _coalesce(payload, "rubric_md", "rubric")

    pid = str(uuid.uuid4())
    _STORE[pid] = {
        "id": pid,
        # What the UI should show (textbook-style block):
        "display_md": display_md,
        # Hidden references for grading:
        "solution": solution_md,
        "final_answer": final_answer,
        "rubric": rubric_md,
        # Optional metadata if you want later:
        "title": payload.get("title", ""),
        "topic": payload.get("topic", problem_type),
        "difficulty": payload.get("difficulty", difficulty),
    }

    # Keep the same UI contract as before: return {id, prompt}
    # but set 'prompt' to the formatted block so your existing UI just works.
    return {"id": pid, "prompt": display_md}


def grade_problem(problem_id: str, user_work: str, user_answer: str) -> dict:
    """
    Returns:
    {
      "problem_id": <id>,
      "result": {"correct": bool, "feedback": str, "hint": Optional[str]}
    }
    """
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

    # Be defensive in case the LLM omits a field
    result = {
        "correct": bool(payload.get("correct", False)),
        "feedback": payload.get("feedback", "").strip(),
        "hint": payload.get("hint", None),
    }

    return {
        "problem_id": problem_id,
        "result": result,
    }
