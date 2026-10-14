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

WHY IT MATTERS HERE. social-media, far-writing, far-math and the rest are
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
