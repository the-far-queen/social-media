"""
test_publish.py -- stage 3, the format stage, pinned.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. THE GATE IS IN FRONT OF THE FORMATTER. A formatter that will
   format anything is a formatter that will publish slop, and that is
   the exact failure the whole pipeline exists to prevent.

2. THE FREE CHAPTERS ARE THE FUNNEL. Bobby's model, 2026-10-31:
   "write free chapters then book offer, any % flow is money even
   2%". So the free chapters must be IN the ebook (not merely
   alongside it), and the offer must be at the front and the back.

3. THE ROYALTY IS COMPUTED, NOT PRINTED. A pipeline that shows a
   price without showing what it earns cannot report income. KDP's
   ebook royalty is 70%.

4. THE WITNESS IS ON EVERY ARTIFACT. Stage 4 fingerprints; stage 3
   records the same fingerprint, so the chain from the gated source
   to the published file is checkable.

5. EVERY ARTIFACT EXISTS FOR EVERY CHANNEL. The skill names four:
   Amazon ebook, X Article, Substack, TikTok teaser. A formatter that
   quietly drops one of them is a funnel with a hole.

6. THE SIMPLEST INPUT IS ACCEPTED. The first version only accepted
   chapters as objects, so a list of chapter strings -- the simplest
   possible input -- was refused. A pipeline whose simplest input is
   rejected is a pipeline nobody runs.

Run:
    python -m pytest tests/test_publish.py -q
"""

from __future__ import annotations

import json
import os
import sys

import pytest

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "tools")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import publish as P  # noqa: E402


def _book(**kw):
    """a minimal gated book."""
    base = dict(
        title="Working Out With Bad Knees At 40+",
        subtitle="A 12-week plan",
        description="Your knees ache on stairs. Here is what to do.",
        voice="didactic",
        sheet="not-yet",
        subject_area="humanities",
        level="k-12",
        price=9.99,
        offer_url="https://example.com/knees",
        chapters=[
            P.Chapter(1, "Why Your Knees Ache", "The ache is not wear.",
                       free=True),
            P.Chapter(2, "The Days It Hurts", "Three options, one wrong.",
                       free=True),
            P.Chapter(3, "The Twelve-Week Plan", "Twelve weeks, three phases."),
        ],
    )
    base.update(kw)
    return P.Book(**base)


# ===========================================================================
# 1. THE GATE IS IN FRONT OF THE FORMATTER
# ===========================================================================

def test_a_course_the_gate_refuses_is_not_formatted(tmp_path):
    """The gate refuses, so nothing is written.

    The gate refuses a course with no voice (`no_voice`) -- and a book
    with no voice has no voice gate, which is the whole point.
    """
    book = _book(voice="")
    res = P.publish(book, str(tmp_path))
    assert not res.ok, "the publisher formatted an artifact the gate refused"
    assert res.reason == "no_voice", res.reason
    assert not res.artifacts, "files were written for a refused artifact"
    assert not os.listdir(str(tmp_path)), (
        "the output directory is not empty after a refusal")


def test_a_gated_course_is_formatted(tmp_path):
    book = _book()
    res = P.publish(book, str(tmp_path))
    assert res.ok, res.reason
    assert res.artifacts


# ===========================================================================
# 2. THE FREE CHAPTERS ARE THE FUNNEL
# ===========================================================================

def test_the_free_chapters_are_inside_the_ebook():
    """Bobby's model: "write free chapters then book offer".

    The free chapters are not a sample alongside the book -- they are
    IN the book. A reader who read them free and finds them inside is
    confirming they were worth reading, which is the buyer's exact
    objection at the preview.
    """
    book = _book()
    text = P.format_ebook(book)
    for c in book.free_chapters:
        assert c.title in text, (
            "the free chapter %r is not in the ebook" % (c.title,))
    for c in book.paid_chapters:
        assert c.title in text, (
            "the paid chapter %r is not in the ebook" % (c.title,))


def test_the_offer_appears_at_the_front_and_the_back():
    """the two places a reader can be converted.

    AND THE ORDER IS MEASURED ON THE CHAPTER HEADINGS, not on the
    titles. The first version of this test used
    `text.index(book.paid_chapters[0].title)` -- and that finds the
    title in the TABLE OF CONTENTS, which comes before everything. So
    the test was measuring the contents list, not the offer's position,
    and it failed on a formatter that was right. The marker for a
    chapter's position in the body is its HEADING ("# Chapter N:"), not
    its title.
    """
    book = _book()
    text = P.format_ebook(book)
    assert text.count(book.offer_url) >= 2, (
        "the offer appears %d times; a reader needs it before the paid "
        "chapters and after the last one" % (text.count(book.offer_url),))

    # the first paid chapter's HEADING, in the body
    first_paid = text.index("# Chapter %d:" % book.paid_chapters[0].number)
    # the front offer: the first occurrence of the url
    first_offer = text.index(book.offer_url)
    assert first_offer < first_paid, (
        "the first offer is at %d and the first paid chapter is at %d, so "
        "the offer comes after the reader has already paid up"
        % (first_offer, first_paid))

    # and the back offer, after the LAST chapter
    last_chapter = text.index("# Chapter %d:" % book.chapters[-1].number)
    assert text.rindex(book.offer_url) > last_chapter, (
        "the last offer is before the last chapter")


def test_the_ebook_declares_the_ai_disclosure():
    """KDP asks for it and the study detects AI text.

    Undisclosed AI is the risk, not the disclosure. So the disclosure
    is in the copyright page of the book itself.
    """
    book = _book()
    text = P.format_ebook(book)
    assert book.ai_disclosure[:40] in text, (
        "the AI disclosure is not in the ebook's copyright page")


# ===========================================================================
# 3. THE ROYALTY IS COMPUTED
# ===========================================================================

def test_the_royalty_is_computed_from_the_price():
    """KDP's ebook royalty is 70%, so a price becomes income."""
    book = _book(price=9.99)
    assert book.royalty == pytest.approx(6.99, abs=0.005), book.royalty
    meta = P.format_kdp_metadata(book)
    assert meta["royalty_per_sale"] == pytest.approx(6.99, abs=0.005)
    assert meta["royalty_rate"] == 0.70


def test_the_royalty_tracks_the_price():
    """a pipeline that prints one price and one royalty is a constant."""
    cheap = P.format_kdp_metadata(_book(price=4.99))
    dear = P.format_kdp_metadata(_book(price=16.99))
    assert dear["royalty_per_sale"] > cheap["royalty_per_sale"]
    assert dear["royalty_per_sale"] == pytest.approx(16.99 * 0.70, abs=0.005)


# ===========================================================================
# 4. THE WITNESS IS ON EVERY ARTIFACT
# ===========================================================================

def test_every_written_artifact_carries_a_witness(tmp_path):
    book = _book()
    res = P.publish(book, str(tmp_path))
    assert res.ok, res.reason
    for a in res.artifacts:
        assert a.witness.startswith("sha256:"), (
            "the artifact %r has no witness" % (a.kind,))
        assert len(a.witness) == len("sha256:") + 32, a.witness


def test_the_witness_is_the_hash_of_the_file_on_disk(tmp_path):
    """the witness must be CHECKABLE against what was written."""
    book = _book()
    res = P.publish(book, str(tmp_path))
    assert res.ok, res.reason
    for a in res.artifacts:
        if a.kind == "kdp.json":
            continue
        with open(a.path, encoding="utf-8") as fh:
            text = fh.read()
        assert P.witness(text) == a.witness, (
            "the witness of %r does not match the file on disk" % (a.kind,))


def test_two_different_books_have_different_witnesses():
    """a witness that is constant is not a witness."""
    a = P.witness(_book().describe())
    b = P.witness(_book(title="Something Else").describe())
    assert a != b


# ===========================================================================
# 5. EVERY ARTIFACT EXISTS FOR EVERY CHANNEL
# ===========================================================================

def test_all_four_channels_are_produced(tmp_path):
    """the skill names four: Amazon ebook, X Article, Substack, TikTok."""
    book = _book()
    res = P.publish(book, str(tmp_path))
    assert res.ok, res.reason
    kinds = {a.kind for a in res.artifacts}
    for want in ("ebook.md", "x-article.md", "substack.md", "teaser.md"):
        assert want in kinds, (
            "the pipeline did not produce %r; the channels are %s"
            % (want, sorted(kinds)))
    assert "kdp.json" in kinds


def test_the_x_article_carries_a_free_chapter_and_the_offer():
    """the X Article is the funnel's mouth."""
    book = _book()
    text = P.format_x_article(book)
    assert book.free_chapters[0].body[:30] in text, (
        "the X Article does not carry the free chapter")
    assert book.offer_url in text, "the X Article carries no offer"


def test_the_teaser_does_not_give_away_the_argument():
    """the teaser carries the PROBLEM and the PROMISE.

    It must not carry the argument, or the funnel gives the book away
    for free. So the paid chapters' bodies must not appear in it.
    """
    book = _book()
    text = P.format_teaser(book)
    assert book.description[:40] in text, (
        "the teaser does not name the problem")
    for c in book.paid_chapters:
        assert c.body[:40] not in text, (
            "the teaser gives away the paid chapter %r" % (c.title,))


# ===========================================================================
# 6. THE SIMPLEST INPUT IS ACCEPTED
# ===========================================================================

def test_a_list_of_chapter_strings_is_accepted(tmp_path):
    """the simplest possible input.

    The first version only accepted chapters as objects, so
    ["chapter one", "chapter two"] was refused. A pipeline whose
    simplest input is rejected is a pipeline nobody runs.
    """
    path = tmp_path / "simple.json"
    path.write_text(json.dumps({
        "title": "A Simple Book",
        "subject_area": "humanities",
        "level": "k-12",
        "voice": "lean",
        "sheet": "s",
        "chapters": ["First chapter body.", "Second chapter body."],
    }), encoding="utf-8")
    book = P.load_book(str(path))
    assert len(book.chapters) == 2
    assert book.chapters[0].body == "First chapter body."
    res = P.publish(book, str(tmp_path / "out"))
    assert res.ok, res.reason


def test_a_chapter_may_be_marked_free_in_the_json(tmp_path):
    path = tmp_path / "b.json"
    path.write_text(json.dumps({
        "title": "B", "subject_area": "humanities", "level": "k-12",
        "voice": "lean", "sheet": "s",
        "chapters": [
            {"title": "One", "body": "b1", "free": True},
            {"title": "Two", "body": "b2"},
        ],
    }), encoding="utf-8")
    book = P.load_book(str(path))
    assert len(book.free_chapters) == 1
    assert book.free_chapters[0].title == "One"
    assert len(book.paid_chapters) == 1
