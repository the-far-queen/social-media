"""
gate.py - 1-bit veto gate for social-media assets.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple


SUBJECT_AREAS = {
    "humanities", "sciences", "math", "languages", "business",
    "law", "medicine", "engineering", "arts",
}
LEVELS = {
    "k-12", "ap-high", "college-undergrad", "college-grad",
    "certification", "professional", "language-cert",
}


def gate_question(q: dict) -> Tuple[bool, str]:
    if not q.get("stem"):  return False, "no_stem"
    if not q.get("answer"): return False, "no_answer"
    if not q.get("choices"): return False, "no_choices"
    if len(q["choices"]) < 2: return False, "choices_lt_2"
    sa = q.get("subject_area", "")
    if sa and sa not in SUBJECT_AREAS: return False, "unknown_subject_area"
    lvl = q.get("level", "")
    if lvl and lvl not in LEVELS: return False, "unknown_level"
    return True, "ok"


def gate_course(c: dict) -> Tuple[bool, str]:
    if not c.get("name"): return False, "no_name"
    if not c.get("subject_area"): return False, "no_subject_area"
    if c["subject_area"] not in SUBJECT_AREAS: return False, "unknown_subject_area"
    if not c.get("level"): return False, "no_level"
    if c["level"] not in LEVELS: return False, "unknown_level"
    if c.get("duration_hours", 0) <= 0 or c.get("duration_hours", 0) > 1000:
        return False, "bad_duration"
    if not c.get("voice"): return False, "no_voice"
    if not c.get("sheet"): return False, "no_sheet"
    if c.get("refuses"):
        for r in c["refuses"]:
            if r.lower() in c.get("description", "").lower():
                return False, "refuses_violated"
    return True, "ok"


def gate(artifact: dict) -> Tuple[bool, str]:
    kind = artifact.get("type") or artifact.get("kind") or "question"
    if kind == "course":
        return gate_course(artifact)
    elif kind == "question":
        return gate_question(artifact)
    return False, "unknown_kind"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        artifact = json.loads(sys.argv[1])
        ok, reason = gate(artifact)
        print(json.dumps({"ok": ok, "reason": reason}))
        sys.exit(0 if ok else 1)
    print("usage: python gate.py '<json>'")
