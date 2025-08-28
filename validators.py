import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft7Validator

SCHEMA_DIR = Path("assets/schema")

@lru_cache(maxsize=2)
def _load_schema(kind: str) -> Dict[str, Any]:
    path = SCHEMA_DIR / f"{kind}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))

def validate_problem_dict(data: Dict[str, Any]) -> None:
    schema = _load_schema("problem")
    Draft7Validator(schema).validate(data)

def validate_grade_dict(data: Dict[str, Any]) -> None:
    schema = _load_schema("grade")
    Draft7Validator(schema).validate(data)

def collect_validation_errors(data: Dict[str, Any], *, kind: str) -> List[str]:
    schema = _load_schema(kind)
    v = Draft7Validator(schema)
    return [e.message for e in v.iter_errors(data)]