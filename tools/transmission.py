"""Transmission — can the schools carry the Tier 2 content to a newcomer?

Written 2026-10-09 after Bobby's question about the domain set and the
seership as capstone. If seership is a skill rather than a mystical gift,
then in principle the curriculum is a transmission path. That claim is
testable in one direction immediately, and this module is that test:

    if the schools cannot carry the formal (Tier 2) content to someone
    who has never met this project, the transmission fails, and every
    other argument in the curriculum is decoration.

WHAT IS MEASURED. For a body of text, the ratio of content a reader must
already know in order to read it. Concretely:

  PREREQUISITE LOAD  the fraction of domain terms used without definition
  SELF-CONTAINMENT  the fraction of content carrying its own definitions
  GLOSSARY COVER    of used terms, how many are defined somewhere in the corpus

This is not a proxy for comprehension and does not claim to be. It is a
floor: a text that fails this cannot be read by a newcomer at all, whatever
the author's intent.

WHY IT MATTERS HERE. social-media, far-writing, fieldcore and the rest are
the medium the curriculum travels in. If they only work for people already
inside the project, the "free schools without a price" framing is a
distribution claim rather than a transmission claim, and those are very
different things to have built.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Term:
    """A domain term and, when known, its definition."""

    term: str
    definition: str = ""
    domain: str = ""
    aliases: list[str] = field(default_factory=list)

    @property
    def surface_forms(self) -> list[str]:
        return [self.term, *self.aliases]


def find_definitions(text: str) -> dict[str, str]:
    """Terms defined in this text, and where.

    Four shapes occur in practice, and the first version recognised only
    two of them, which is why a real glossary scored as containing three
    definitions out of twenty:

      "term: definition"                 plain colon
      "**term** - definition"            markdown bold with a dash
      "term - definition"                plain dash
      "- **term** - definition"          bulleted, bold, dashed

    The glossary uses the bold-dash form, so it registered as almost
    undefined and every document measured at 100% load. A measurement
    instrument that cannot read the artifact it measures is worse than no
    instrument, because the number is confidently wrong.
    """
    out: dict[str, str] = {}
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith(("#", "|", ">", "`")):
            continue
        # **AND THE AXIS FORM, WHICH IS A DEFINITION SITE.** MEASURED
        # 2026-10-31: the sacred library's five-part qualifications
        # write their axis as
        #
        #     **Axis moved:** `truth_before_comfort`.
        #     **Current value:** I treat a text's value as ...
        #     **Intended value:** I treat a text's value as ...
        #
        # The "Current value" and "Intended value" lines ARE the
        # definition -- they say what the term MEANS here -- but the
        # term itself is named on the "Axis moved" line, in a form the
        # regex below did not match. So every one of the 27
        # qualifications measured at 100% load, with the axis name as
        # the single missing term, while the definition sat two lines
        # above it.
        #
        # **A measurement instrument that cannot read the artifact it
        # measures is worse than no instrument, because the number is
        # confidently wrong** -- which is the same failure the glossary
        # bold-dash form caused above, in a different shape.
        axis = _AXIS_MOVED.match(s)
        if axis:
            term = axis.group(1).strip().lower()
            body = _axis_body(text, raw)
            if body:
                out.setdefault(term, body)
            continue
        # Strip a leading bullet, because a glossary entry is written as
        # a bullet. The table and heading filters above are what exclude
        # structural lines; a length floor was tried and removed because
        # it also rejected short real definitions like "- manifold: bullet".
        s = re.sub(r"^[-*+]\s+", "", s)
        m = re.match(
            r"^\*{0,2}([A-Za-z][A-Za-z0-9 _\-/'()]{1,48}?)\*{0,2}\s*"
            r"(?:—|–|::|:|-)\s+(\S.{3,})$", s)
        if m:
            term = m.group(1).strip().lower()
            body = m.group(2).strip()
            # A table cell or a heading fragment is not a definition. The
            # bullet form `- **term** - definition` IS one, because that is
            # how a glossary is written; but a body that is a single bare
            # word, or that is itself the start of another clause, is not.
            if len(term) >= 3:
                out.setdefault(term, body[:200])
    return out


#: THE AXIS FORM. `**Axis moved:** `term`` -- the term is named here and
#: defined on the two lines below it.
#:
#: **AND THE COLON IS INSIDE THE BOLD MARKERS.** MEASURED 2026-10-31:
#: the first version of this pattern was `\*{0,2}Axis moved\*{0,2}\s*:`,
#: which asks for the colon AFTER the closing `**`. The real form is
#: `**Axis moved:**`, so the pattern never matched and the fix was
#: invisible -- the module imported, the function ran, and it returned
#: the same three definitions as before.
_AXIS_MOVED = re.compile(
    r"^\*{0,2}Axis moved\s*:\s*\*{0,2}\s*`?([A-Za-z0-9_ -]{3,48}?)`?"
    r"\s*\.?\s*\*{0,2}\s*$",
    re.IGNORECASE)

#: The two value lines that follow the axis name. Same shape: the colon
#: is inside the bold markers.
_CURRENT = re.compile(
    r"^\*{0,2}Current value\s*:\s*\*{0,2}\s*(.+?)\s*\*{0,2}\s*$",
    re.IGNORECASE)
_INTENDED = re.compile(
    r"^\*{0,2}Intended value\s*:\s*\*{0,2}\s*(.+?)\s*\*{0,2}\s*$",
    re.IGNORECASE)


def _axis_body(text: str, axis_line: str) -> str:
    """the definition that follows the "Axis moved" line.

    **AND THE BODY IS THE INTENDED VALUE, WITH THE CURRENT VALUE BOTH
    PLACED -- because the axis is a MOVE, and a definition of only one
    side of a move is not a definition of the term.**
    """
    lines = text.splitlines()
    try:
        start = lines.index(axis_line)
    except ValueError:
        return ""
    current = intended = ""
    for raw in lines[start + 1:start + 8]:
        s = raw.strip()
        m = _CURRENT.match(s)
        if m:
            current = m.group(1).strip()
            continue
        m = _INTENDED.match(s)
        if m:
            intended = m.group(1).strip()
            break
    if current and intended:
        return ("currently %s; intended %s" % (current, intended))[:200]
    return (current or intended)[:200]


@dataclass
class Readability:
    terms_used: list[str]
    terms_defined: list[str]
    undefined: list[str]
    load: float          # fraction of used terms with no definition anywhere
    words: int

    @property
    def self_contained(self) -> bool:
        return self.load <= 0.5

    def render(self) -> str:
        return (f"words={self.words} terms={len(self.terms_used)} "
                f"defined={len(self.terms_defined)} "
                f"undefined={len(self.undefined)} load={self.load:.1%}")


def count_terms(text: str, glossary: list[Term], min_len: int = 4) -> list[str]:
    """Every glossary surface form that appears in the text."""
    low = text.lower()
    found: set[str] = set()
    for t in glossary:
        for form in t.surface_forms:
            f = form.lower()
            if len(f) < min_len:
                continue
            if re.search(rf"(?<![a-z]){re.escape(f)}(?![a-z])", low):
                found.add(f)
    return sorted(found)


def measure(text: str, glossary: list[Term]) -> Readability:
    """Prerequisite load of ONE text, judged only on what that text says.

    The first version counted a term as "defined" if the glossary held a
    definition for it, which made every document score 0% load no matter
    how much it assumed. A newcomer reading that document alone still has
    nowhere to look up a word, so the glossary must not rescue it.

    `inline` terms are those the text itself defines. A term is loaded
    when the text uses it and does not define it here. `glossary` is still
    used -- to know WHICH words are domain terms worth checking -- but not
    to supply the definitions that decide the score.
    """
    inline = find_definitions(text)
    known = {form.lower() for t in glossary for form in t.surface_forms}

    used = [t for t in count_terms(text, glossary) if t in known or t in inline]
    defined = [t for t in used if t in inline]
    undefined = [t for t in used if t not in inline]
    load = (len(undefined) / len(used)) if used else 0.0
    return Readability(terms_used=used, terms_defined=defined,
                       undefined=undefined, load=load,
                       words=len(text.split()))


def corpus_report(paths: list[Path], glossary: list[Term]) -> dict:
    """Measure every document and report both levels.

    A corpus can be self-contained as a whole while no single document is:
    a term defined once in the front door and used unstated in nine other
    files still requires the reader to start at the beginning. Both the
    per-document figure and the corpus-union figure are reported for
    exactly that reason, and they are different numbers.
    """
    corpus_defined: set[str] = set()
    rows = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            rows.append({"path": str(p), "error": str(exc)})
            continue
        r = measure(text, glossary)
        corpus_defined |= set(r.terms_defined)
        rows.append({
            "path": p.name,
            "words": r.words,
            "terms": len(r.terms_used),
            "undefined": len(r.undefined),
            "load": round(r.load, 4),
            "missing": r.undefined[:12],
        })

    measured = [r for r in rows if "load" in r]
    corpus_undefined: set[str] = set()
    for r in measured:
        corpus_undefined |= set(r["missing"])

    return {
        "documents": len(measured),
        "mean_load": round(sum(r["load"] for r in measured) / len(measured), 4) if measured else 0.0,
        "self_contained_docs": sum(1 for r in measured if r["load"] <= 0.5),
        "terms_defined_somewhere": len(corpus_defined),
        "terms_never_defined": len(corpus_undefined),
        "never_defined_sample": sorted(corpus_undefined)[:20],
        "rows": rows,
    }
