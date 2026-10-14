"""
mcq.py - MC question compiler for social-media.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SUBJECT_AREAS = {
    "humanities", "sciences", "math", "languages", "business",
    "law", "medicine", "engineering", "arts",
}

LEVELS = {
    "k-12", "ap-high", "college-undergrad", "college-grad",
    "certification", "professional", "language-cert",
}


@dataclass(frozen=True)
class MCQuestion:
    question_id: str
    stem: str
    choices: Tuple[str, ...]
    answer: str
    explanation: str = ""
    source: str = ""
    subject_area: str = ""
    level: str = ""

    def canonical(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "stem": self.stem,
            "choices": list(self.choices),
            "answer": self.answer,
            "explanation": self.explanation,
            "source": self.source,
            "subject_area": self.subject_area,
            "level": self.level,
        }

    def gate(self, course: str, exam: str) -> Tuple[bool, str]:
        if not self.answer:
            return False, "no_answer"
        if not self.stem or len(self.stem) < 5:
            return False, "no_stem"
        if not self.choices or len(self.choices) < 2:
            return False, "no_choices"
        if self.subject_area and self.subject_area not in SUBJECT_AREAS:
            return False, "unknown_subject_area"
        if self.level and self.level not in LEVELS:
            return False, "unknown_level"
        return True, "ok"


def question_hash(stem: str, answer: str, source: str) -> str:
    canonical = f"{stem}|{answer}|{source}".encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()[:16]


def ingest_csv(path: str, subject_area: str = "", level: str = "") -> List[MCQuestion]:
    questions = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            stem = row.get("question") or row.get("stem") or row.get("q") or ""
            choices = []
            for key in ("A", "B", "C", "D", "E", "F"):
                v = row.get(key) or row.get(key.lower())
                if v:
                    choices.append(v)
            answer = row.get("answer") or row.get("correct") or ""
            explanation = row.get("explanation") or row.get("explain") or ""
            if not stem or not choices or not answer:
                continue
            q = MCQuestion(
                question_id=question_hash(stem, answer, f"{path}:{i}"),
                stem=stem,
                choices=tuple(choices),
                answer=answer,
                explanation=explanation,
                source=f"{os.path.basename(path)}:{i+1}",
                subject_area=subject_area or row.get("subject_area", ""),
                level=level or row.get("level", ""),
            )
            questions.append(q)
    return questions


def ingest_php_test_page(path: str) -> List[MCQuestion]:
    src = open(path, encoding="utf-8", errors="replace").read()
    questions = []
    q_blocks = re.split(r'(?=\d+\.\s)', src)
    for block in q_blocks:
        m_stem = re.search(r'\d+\.\s+(.*?)(?=&nbsp;|\s*<br>)', block, re.DOTALL)
        if not m_stem:
            continue
        stem = m_stem.group(1).strip()
        choices = re.findall(r'value="([A-Z])\.\s*([^"<>]+?)(?=">|"\s|\s<|$)', block)
        if not choices:
            continue
        choice_texts = [c[1].strip() for c in choices]
        m_ans = re.search(r'name="key\d+"\s+value="([A-Z])', block)
        if not m_ans:
            continue
        answer = m_ans.group(1)
        questions.append(MCQuestion(
            question_id=question_hash(stem, answer, f"{os.path.basename(path)}:{len(questions)+1}"),
            stem=stem,
            choices=tuple(choice_texts),
            answer=answer,
            explanation="",
            source=f"{os.path.basename(path)}:{len(questions)+1}",
            subject_area="",
            level="",
        ))
    return questions


def write_jsonl(questions: List[MCQuestion], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q.canonical()) + "\n")


def main():
    import argparse
    p = argparse.ArgumentParser(description="MC question compiler for social-media")
    sub = p.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingest", help="ingest a CSV file")
    ing.add_argument("path")
    ing.add_argument("--subject-area", default="")
    ing.add_argument("--level", default="")
    ing.add_argument("--out", required=True)

    par = sub.add_parser("parse", help="parse a PHP test page")
    par.add_argument("path")
    par.add_argument("--out", required=True)

    args = p.parse_args()

    if args.cmd == "ingest":
        qs = ingest_csv(args.path, args.subject_area, args.level)
        write_jsonl(qs, args.out)
        print(f"ingested {len(qs)} questions -> {args.out}")
    elif args.cmd == "parse":
        qs = ingest_php_test_page(args.path)
        write_jsonl(qs, args.out)
        print(f"parsed {len(qs)} questions -> {args.out}")


if __name__ == "__main__":
    main()
