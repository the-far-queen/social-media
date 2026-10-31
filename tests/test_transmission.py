"""Tests for the transmission instrument.

The claim under test (2026-10-09): if seership is a skill, the far-*
schools are a transmission path. A corpus that assumes the reader already
knows its vocabulary is not transmitting, it is only reachable from inside
the project.

These tests guard the two ways the instrument was wrong before:
  - it counted glossary definitions as if the TEXT were self-contained,
    so every document scored 0% load
  - it now measures only what a single text defines on its own
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from transmission import (  # noqa: E402
    Readability, Term, corpus_report, count_terms, find_definitions, measure,
)

GLOSSARY = [
    Term("manifold", "a space locally like Euclidean space", "math"),
    Term("harmonic", "the invariant part under gradient flow", "math"),
    Term("twin prime", "primes differing by two", "math"),
]


# --------------------------------------------------------------------- defs


def test_find_definitions_em_dash_and_colon():
    text = "manifold — a space locally like Euclidean space\nPSB: refuse a"
    d = find_definitions(text)
    assert "manifold" in d
    assert "psb" in d


def test_find_definitions_ignores_structural_lines():
    """Table cells and headings are structure, not definitions.

    A bullet IS a definition site -- that is how a glossary is written --
    so this test changed when the bullet form was added: the old version
    asserted that `- manifold: bullet` was NOT a definition, which
    contradicted the corpus's own glossary style.
    """
    d = find_definitions("| manifold | thing |\n# heading")
    assert "manifold" not in d
    # and a bullet with a real clause IS a definition
    assert "manifold" in find_definitions("- **manifold** - a space locally like Euclidean space")


def test_find_definitions_of_empty_text():
    assert find_definitions("") == {}


def test_find_definitions_reads_the_axis_form():
    """**THE AXIS FORM IS A DEFINITION SITE.**

    MEASURED 2026-10-31: the sacred library's five-part qualifications
    name their axis like this --

        **Axis moved:** `truth_before_comfort`.
        **Current value:** I treat a text's value as what it tells me to believe.
        **Intended value:** I treat a text's value as what it makes me able to do.

    The two value lines ARE the definition -- they say what the term
    means here -- but the TERM is named on the "Axis moved" line, in a
    form the instrument did not recognise. So all 27 qualifications
    measured at 100% load, with the axis name as the single missing
    term, while the definition sat two lines above it.

    **A measurement instrument that cannot read the artifact it
    measures is worse than no instrument, because the number is
    confidently wrong.** This is the same failure as the bold-dash
    glossary form, in a different shape.
    """
    text = (
        "**Axis moved:** `truth_before_comfort`.\n"
        "\n"
        "**Current value:** I treat a text's value as what it tells me to believe.\n"
        "\n"
        "**Intended value:** I treat a text's value as what it makes me able to do.\n"
    )
    d = find_definitions(text)
    assert "truth_before_comfort" in d, (
        "the axis form was not read as a definition; the terms found: %s"
        % sorted(d))
    body = d["truth_before_comfort"]
    assert "tells me to believe" in body, body
    assert "makes me able to do" in body, (
        "the definition carries only one side of the move: %r" % body)


def test_the_axis_form_makes_a_qualification_self_contained():
    """**AND THE DOCUMENT MEASURES AT 0% LOAD, NOT 100%.**

    The end-to-end version of the check above: with the axis defined
    inline, the term is no longer an undefined prerequisite, so the
    load falls to zero. Before the fix this document measured 100%.
    """
    glossary = [Term("truth_before_comfort", "", "axis")]
    text = (
        "**Axis moved:** `truth_before_comfort`.\n"
        "**Current value:** I treat a text's value as what it tells me to believe.\n"
        "**Intended value:** I treat a text's value as what it makes me able to do.\n"
        "The axis `truth_before_comfort` is what this text moves.\n"
    )
    r = measure(text, glossary)
    assert r.terms_used, "the term was not seen as used at all"
    assert r.undefined == [], (
        "the axis is undefined even though the document defines it: %s"
        % r.undefined)
    assert r.load == 0.0, (
        "the document measured %.1f%% load; it should be 0%%" % (100 * r.load))


# --------------------------------------------------------------------- measure


def test_a_text_that_defines_everything_is_self_contained():
    text = ("manifold — a space locally like Euclidean space.\n"
            "harmonic — the invariant part under gradient flow.\n"
            "The manifold and its harmonic part are both defined above.")
    r = measure(text, GLOSSARY)
    assert r.undefined == [], r.undefined
    assert r.self_contained


def test_a_text_that_assumes_the_reader_knows_is_not():
    """The measured finding on the math docs (fieldcore/docs/Math/02): a 713-word document
    using six domain terms and defining none of them.
    """
    text = ("The manifold carries the state. The heegaard splitting gives the "
            "interface. The clifford torus is the flat one. The hopf fibration "
            "names the stalks, and the seifert genus is unrelated. The solid "
            "torus completes the picture.")
    r = measure(text, GLOSSARY + [Term("heegaard splitting", "x", "math"),
                                  Term("clifford torus", "x", "math"),
                                  Term("hopf fibration", "x", "math"),
                                  Term("seifert genus", "x", "math"),
                                  Term("solid torus", "x", "math")])
    assert r.undefined
    assert r.load > 0.5
    assert not r.self_contained


def test_glossary_does_not_rescue_the_text():
    """The first version's bug: a glossary with a definition for every
    term made every document score 0% regardless of its content.
    """
    text = "The manifold is the manifold. The manifold matters."
    rich = [Term(t, "a definition", "math") for t in
            ("manifold", "harmonic", "twin prime", "seifert genus")]
    r = measure(text, rich)
    assert r.terms_used, "should still detect the terms"
    assert r.undefined, "but they are undefined in the text itself"
    assert r.load > 0.0


def test_measure_reports_word_count():
    r = measure("manifold — defined here. harmonic follows.", GLOSSARY)
    assert r.words > 0


def test_measure_of_text_with_no_terms():
    r = measure("the quick brown fox jumps over the lazy dog", GLOSSARY)
    assert r.terms_used == []
    assert r.load == 0.0


# --------------------------------------------------------------------- counting


def test_count_terms_matches_whole_words_only():
    """'manifold' must not match inside 'manifoldlike' or 'submanifoldx'.
    """
    assert count_terms("manifold", GLOSSARY) == ["manifold"]
    assert count_terms("submanifolds", GLOSSARY) == []
    assert count_terms("a manifold, a manifold.", GLOSSARY) == ["manifold"]


def test_aliases_are_counted():
    """An alias whose surface form contains the base term registers both.
    The base term IS present in the text, so counting it is correct rather
    than a double-count bug.
    """
    gl = [Term("manifold", "x", "math", aliases=["manifold space"])]
    found = count_terms("the manifold space", gl)
    assert "manifold space" in found


def test_short_terms_are_skipped():
    assert count_terms("a cat sat", [Term("cat", "x", "any")]) == []


# --------------------------------------------------------------------- corpus


def test_corpus_report_across_documents(tmp_path):
    (tmp_path / "a.md").write_text(
        "manifold — a space locally like Euclidean space.\nThe manifold is real.",
        encoding="utf-8")
    (tmp_path / "b.md").write_text(
        "The manifold and the harmonic part carry the state.", encoding="utf-8")
    rep = corpus_report(sorted(tmp_path.glob("*.md")), GLOSSARY)
    assert rep["documents"] == 2
    assert rep["rows"][0]["load"] == 0.0          # a.md defines it
    assert rep["rows"][1]["load"] > 0.0           # b.md does not
    assert rep["mean_load"] > 0.0


def test_corpus_union_differs_from_per_document(tmp_path):
    """The distinction that matters: a term defined once somewhere in the
    corpus still leaves every other document assuming it.
    """
    (tmp_path / "front.md").write_text("manifold — defined here.", encoding="utf-8")
    (tmp_path / "chapter.md").write_text(
        "The manifold is used freely here with no gloss at all, repeatedly.",
        encoding="utf-8")
    rep = corpus_report(sorted(tmp_path.glob("*.md")), GLOSSARY)
    per_doc_defined = [r["load"] for r in rep["rows"]]
    assert max(per_doc_defined) > 0.0
    assert rep["terms_defined_somewhere"] >= 1


def test_corpus_report_handles_missing_file(tmp_path):
    rep = corpus_report([tmp_path / "nope.md"], GLOSSARY)
    assert rep["documents"] == 0
    assert "error" in rep["rows"][0]


def test_corpus_report_of_empty_set():
    rep = corpus_report([], GLOSSARY)
    assert rep["documents"] == 0
    assert rep["mean_load"] == 0.0


# --------------------------------------------------------------------- real corpus


def test_far_math_tier2_docs_are_self_contained():
    """This asserted load > 50% and was written when the measurement said
    100%. After the glossary and inline glosses it measures 0-17%, so the
    assertion is now the CORRECT direction: a regression in documentation
    quality fails here.

    Kept as a test against the real artifact rather than a fixture,
    because the artifact is what actually gets read.
    """
    doc = (Path(__file__).resolve().parents[2] / "fieldcore" / "docs" / "Math"
           / "02-geometry-reconciled.md")
    if not doc.exists():
        pytest.skip("fieldcore not present beside this repo")
    text = doc.read_text(encoding="utf-8")
    gl = [Term(t, "x", "math") for t in
          ("manifold", "harmonic", "clifford torus", "heegaard splitting",
           "hopf fibration", "seifert genus", "solid torus")]
    r = measure(text, gl)
    assert len(r.terms_used) >= 5      # it really does use domain vocabulary
    assert r.load <= 0.5, f"prerequisite load regressed to {r.load:.0%}: {r.undefined}"