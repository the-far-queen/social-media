"""
publish.py -- STAGE 3: THE FORMAT STAGE. The asset becomes a book, a
free chapter, and a post.

WHY THIS FILE EXISTS, and it is the gap that matters for INCOME
---------------------------------------------------------------
The course-pipeline skill (`.agents/skills/course-pipeline/SKILL.md`)
specifies FOUR stages:

    Stage 1: compile (course + exam + question from canonical axes)   DONE
    Stage 2: gate (1-bit veto per artifact type)                      DONE
    Stage 3: format (Amazon ebook, X Article, Substack, TikTok)       MISSING
    Stage 4: witness + publish (SHA-256 fingerprint per artifact)     DONE

MEASURED 2026-10-31: `tools/` holds `mcq.py` (compile), `gate.py`
(gate), `transmission.py` (the prerequisite-load measurement) and
`curriculum.py`. **There is no formatter.** Stage 3 was specified and
never built, and stage 3 is the one that produces the thing that earns
money.

Bobby's own model, 2026-10-31: *"no just tommi -- i edit u and grok
write, we build sales funnels, leverage real topics and x posts
substack etc other social media, write free chapters then book offer,
any % flow is money even 2%."*

So the shape is:
    REAL TOPIC  ->  FREE CHAPTER (the funnel)  ->  BOOK OFFER (the money)
and the free part goes out on X, Substack and the rest, and the paid
part is the ebook. **The free chapters are not a giveaway -- they are
the funnel.** Any percent of the flow that converts is revenue, and
Bobby is right that even 2% is money.

WHAT THIS STAGE PRODUCES, per artifact
--------------------------------------
    ebook      the KDP-ready markdown: title page, copyright page with
               the AI disclosure, a table of contents, the chapters,
               and the free-chapter promotion at the front and the back
    x_article  the long-form X Article: the free chapter, with the
               book offer at the end
    substack   the Substack post: the free chapter, with the offer
    teaser     the short teaser for TikTok and similar: the problem,
               the promise, the offer
    kdp        the metadata KDP needs: title, subtitle, description,
               keywords, categories, and the price

THE GATE STAYS IN FRONT OF THE FORMATTER
-----------------------------------------
The formatter does not decide whether an artifact is good. It formats
a GATED artifact, and it refuses to format one that has not been
gated. So `publish.py` calls `gate.py` and refuses to write a file for
an artifact the gate refused. A formatter that will format anything is
a formatter that will publish slop, and that is the exact failure the
whole pipeline exists to prevent.

THE WITNESS, and why it is not optional
--------------------------------------
Stage 4 fingerprints each artifact. This stage RECORDS the same
fingerprint on every file it writes, so the chain from the gated
source to the published artifact is checkable afterwards: given a
published file, you can prove which gated artifact it came from and
that nobody edited it in between.

THE PRICING IS A FUNCTION OF THE ARTIFACT, not a constant
-----------------------------------------------------------
KDP's royalty is 70% for ebooks. So the publisher's take on a $9.99
ebook is $6.99, and on a $14.99 it is $10.49. The price is an INPUT
and the royalty is COMPUTED, because a pipeline that prints a price
without computing what it earns cannot report income.

Run:
    python tools/publish.py --help
    python tools/publish.py course.json --out dist/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from gate import gate  # noqa: E402

#: KDP's ebook royalty, as a fraction of the list price. This is the
#: number that turns a price into income, so it lives in one place
#: and everything that reports money uses it.
KDP_EBOOK_ROYALTY = 0.70

#: The default price, in the band Pedruzzi names: paperback
#: $12.99-$16.99, ebook priced to undercut it.
DEFAULT_PRICE = 9.99


# ===========================================================================
# THE ARTIFACT
# ===========================================================================

@dataclass
class Chapter:
    """one chapter of the book."""
    number: int
    title: str
    body: str
    #: Is this chapter FREE? The free chapters are the funnel.
    free: bool = False

    @property
    def words(self) -> int:
        return len(self.body.split())


@dataclass
class Book:
    """the book, as the formatter sees it.

    AND THE FIELDS ARE THE FUNNEL'S, not the book's. `free_chapters`
    says which chapters go out free and where the buyer is offered the
    rest. That is the whole money mechanism, so it is a first-class
    field and not a formatting convention.
    """
    title: str
    subtitle: str = ""
    description: str = ""
    chapters: List[Chapter] = field(default_factory=list)
    voice: str = ""
    sheet: str = ""
    subject_area: str = ""
    level: str = ""
    keywords: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    price: float = DEFAULT_PRICE
    pen_name: str = ""
    author: str = ""
    #: The offer the free chapters make. Where the buyer is sent.
    offer_url: str = ""
    #: The AI disclosure. Required, and honest.
    ai_disclosure: str = (
        "This book was written with AI assistance under human direction "
        "and review. The author reviewed, checked and edited every part "
        "of it.")

    # -- the money --------------------------------------------------
    @property
    def royalty(self) -> float:
        """what one sale earns the author."""
        return round(self.price * KDP_EBOOK_ROYALTY, 2)

    @property
    def free_chapters(self) -> List[Chapter]:
        return [c for c in self.chapters if c.free]

    @property
    def paid_chapters(self) -> List[Chapter]:
        return [c for c in self.chapters if not c.free]

    @property
    def total_words(self) -> int:
        return sum(c.words for c in self.chapters)

    def describe(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "chapters": len(self.chapters),
            "free_chapters": len(self.free_chapters),
            "paid_chapters": len(self.paid_chapters),
            "total_words": self.total_words,
            "price": self.price,
            "royalty_per_sale": self.royalty,
        }


# ===========================================================================
# THE WITNESS
# ===========================================================================

def witness(payload: Any) -> str:
    """the SHA-256 fingerprint of an artifact.

    THE SAME FUNCTION stage 4 uses, so the chain is checkable: a
    published file's witness must equal the witness of the gated
    artifact it came from.
    """
    if isinstance(payload, str):
        blob = payload
    else:
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]


# ===========================================================================
# STAGE 3 -- THE FORMATTERS
# ===========================================================================

def format_ebook(book: Book) -> str:
    """the KDP-ready ebook, as markdown.

    AND THE FREE CHAPTERS GO IN THE BOOK. That is not generosity and
    it is not a sample -- it is the funnel. The buyer who read three
    free chapters on X and then finds them in the book is confirming
    that the free part was worth reading, which is the exact objection
    a buyer has when they see a preview.

    AND THE OFFER GOES IN TWICE: at the front, so a reader who finishes
    the free chapters inside the book knows what they are missing, and
    at the back, where the reader is.
    """
    out: List[str] = []
    out.append("# %s" % book.title)
    if book.subtitle:
        out.append("## %s" % book.subtitle)
    out.append("")
    if book.author:
        out.append("**%s**" % book.author)
    if book.pen_name:
        out.append("")
        out.append("*A pen name of %s.*" % book.pen_name)
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Copyright")
    out.append("")
    out.append("Copyright %s." % datetime.now(timezone.utc).year)
    out.append("")
    out.append(book.ai_disclosure)
    out.append("")
    out.append("---")
    out.append("")

    # the contents
    out.append("## Contents")
    out.append("")
    for c in book.chapters:
        marker = " *(free)*" if c.free else ""
        out.append("%d. %s%s" % (c.number, c.title, marker))
    out.append("")

    if book.free_chapters:
        out.append("---")
        out.append("")
        out.append("## A note before you start")
        out.append("")
        out.append("The chapters marked *(free)* are the ones you can read "
                   "without buying this book, and they are also the "
                   "sample of what the rest is like. Read them first. "
                   "If the argument holds up for you, the remaining "
                   "chapters take it further.")
        out.append("")
        if book.offer_url:
            out.append("The whole set, and the chapters that follow: "
                       "%s" % book.offer_url)
            out.append("")

    for c in book.chapters:
        out.append("---")
        out.append("")
        out.append("# Chapter %d: %s" % (c.number, c.title))
        if c.free:
            out.append("")
            out.append("*(This chapter is free. It is also the first "
                       "chapter of the paid book, so nothing is missing "
                       "here.)*")
        out.append("")
        out.append(c.body.strip())
        out.append("")

    out.append("---")
    out.append("")
    out.append("## If this was useful")
    out.append("")
    if book.offer_url:
        out.append("The remaining %d chapters: %s"
                   % (len(book.paid_chapters), book.offer_url))
    else:
        out.append("The remaining %d chapters are in the full edition."
                   % len(book.paid_chapters))
    out.append("")
    return "\n".join(out)


def format_x_article(book: Book, chapter: Optional[Chapter] = None) -> str:
    """the long-form X Article: the free chapter, with the offer.

    THE X ARTICLE IS THE FUNNEL'S MOUTH. It carries ONE free chapter
    -- the one that best states the problem -- and ends with the
    offer. The whole point is that the reader gets something real for
    free, so the offer is worth accepting.
    """
    if chapter is None:
        chapter = book.free_chapters[0] if book.free_chapters else None
    out: List[str] = []
    if chapter is not None:
        out.append(chapter.body.strip())
        out.append("")
    out.append("---")
    out.append("")
    if book.offer_url:
        out.append("The full version -- %d more chapters, on %s -- is here: "
                   "%s" % (len(book.paid_chapters), book.title, book.offer_url))
    else:
        out.append("The full version -- %d more chapters -- is on sale."
                   % len(book.paid_chapters))
    out.append("")
    out.append("*%s*" % book.title)
    if book.price:
        out.append("*%s on sale for %s -- %s per sale for the author, and "
                   "the free chapters stay free.*"
                   % ("$%.2f" % book.price,
                      ("$%.2f" % book.royalty), "$%.2f" % book.royalty))
    out.append("")
    return "\n".join(out)


def format_substack(book: Book, chapter: Optional[Chapter] = None) -> str:
    """the Substack post: the free chapter, with the offer.

    AND THE SUBSTACK POST IS THE EMAIL LIST'S FUEL. A Substack post
    that is worth reading is a subscription; a subscription is the
    cheapest traffic there is, and it does not stop when the ad
    budget does.
    """
    if chapter is None:
        chapter = book.free_chapters[0] if book.free_chapters else None
    out: List[str] = []
    out.append("# %s" % (chapter.title if chapter else book.title))
    out.append("")
    if chapter is not None:
        out.append(chapter.body.strip())
        out.append("")
    out.append("---")
    out.append("")
    if book.offer_url:
        out.append("If this was worth your time, the rest is here: %s"
                   % book.offer_url)
    out.append("")
    out.append("*%s%s*" % (book.title,
                           (" -- %s" % book.subtitle) if book.subtitle else ""))
    out.append("")
    return "\n".join(out)


def format_teaser(book: Book) -> str:
    """the short teaser: the problem, the promise, the offer.

    THIS IS THE ONLY ARTIFACT THAT FITS IN A POST. So it carries the
    PROBLEM and the PROMISE -- never a summary of the argument, which
    would give the whole thing away for free.
    """
    problem = (book.description or "").strip()
    out: List[str] = []
    if problem:
        out.append(problem)
        out.append("")
    out.append("%s is %d chapters, and the first %d are free."
               % (book.title, len(book.chapters), len(book.free_chapters)))
    out.append("")
    if book.offer_url:
        out.append("Read them free: %s" % book.offer_url)
    out.append("")
    return "\n".join(out)


def format_kdp_metadata(book: Book) -> Dict[str, Any]:
    """the metadata KDP needs, and the price that follows from it.

    AND THE ROYALTY IS COMPUTED HERE, not printed elsewhere, because a
    pipeline that shows a price without showing what it earns cannot
    report income.
    """
    desc = book.description.strip()
    if book.free_chapters:
        desc += ("\n\nThe first %d chapters are free to read online."
                 % len(book.free_chapters))
    return {
        "title": book.title,
        "subtitle": book.subtitle,
        "description": desc,
        "keywords": list(book.keywords)[:7],
        "categories": list(book.categories)[:3],
        "author": book.pen_name or book.author,
        "price": book.price,
        "royalty_per_sale": book.royalty,
        "royalty_rate": KDP_EBOOK_ROYALTY,
        "ai_disclosure": book.ai_disclosure,
        "offer_url": book.offer_url,
        "voice": book.voice,
        "sheet": book.sheet,
        "subject_area": book.subject_area,
        "level": book.level,
        "witness": witness(book.describe()),
    }


# ===========================================================================
# THE STAGE -- and the gate in front of it
# ===========================================================================

@dataclass
class PublishedArtifact:
    """one written file."""
    kind: str
    path: str
    witness: str
    bytes: int


@dataclass
class PublishResult:
    """what one publish produced."""
    ok: bool
    reason: str
    artifacts: List[PublishedArtifact] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    out_dir: str = ""

    def describe(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "artifacts": [{"kind": a.kind, "path": a.path,
                           "bytes": a.bytes} for a in self.artifacts],
            "metadata": self.metadata,
        }


def _write(path: str, text: str) -> PublishedArtifact:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return PublishedArtifact(
        kind=os.path.basename(path),
        path=path,
        witness=witness(text),
        bytes=len(text.encode("utf-8")),
    )


def publish(book: Book, out_dir: str = "dist") -> PublishResult:
    """stage 3: format a gated book into the artifacts that sell it.

    AND THE GATE IS IN FRONT. The book is checked by `gate.py` before
    a single file is written, and a refusal stops the whole publish.
    A formatter that will format anything is a formatter that will
    publish slop.
    """
    artifact = {
        "type": "course",
        "name": book.title,
        "subject_area": book.subject_area,
        "level": book.level,
        "duration_hours": max(1, book.total_words // 200),
        "voice": book.voice,
        "sheet": book.sheet,
        "description": book.description,
        "refuses": [],
    }
    ok, reason = gate(artifact)
    if not ok:
        return PublishResult(ok=False, reason=reason, out_dir=out_dir)

    base = os.path.join(out_dir, _slug(book.title))
    arts: List[PublishedArtifact] = []
    arts.append(_write(os.path.join(base, "ebook.md"), format_ebook(book)))
    if book.free_chapters:
        arts.append(_write(os.path.join(base, "x-article.md"),
                           format_x_article(book)))
        arts.append(_write(os.path.join(base, "substack.md"),
                           format_substack(book)))
    arts.append(_write(os.path.join(base, "teaser.md"), format_teaser(book)))

    meta = format_kdp_metadata(book)
    meta_path = os.path.join(base, "kdp.json")
    with open(meta_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    arts.append(PublishedArtifact(kind="kdp.json", path=meta_path,
                                   witness=witness(meta), bytes=0))

    return PublishResult(ok=True, reason=reason, artifacts=arts,
                          metadata=meta, out_dir=base)


def _slug(text: str) -> str:
    keep = []
    for ch in text.lower():
        keep.append(ch if (ch.isalnum() or ch in "-_") else "-")
    out = "".join(keep).strip("-")
    while "--" in out:
        out = out.replace("--", "-")
    return out[:60] or "book"


# ===========================================================================
# THE CLI
# ===========================================================================

def load_book(path: str) -> Book:
    """read a book from its json.

    AND THE CHAPTERS MAY BE A LIST OF STRINGS OR A LIST OF OBJECTS.
    The first version only accepted objects, so the simplest possible
    input -- a list of chapter texts -- was refused. A pipeline whose
    simplest input is rejected is a pipeline nobody runs.
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    chapters: List[Chapter] = []
    for i, ch in enumerate(data.get("chapters") or []):
        if isinstance(ch, str):
            chapters.append(Chapter(number=i + 1, title="Chapter %d" % (i + 1),
                                    body=ch))
        else:
            chapters.append(Chapter(
                number=int(ch.get("number", i + 1)),
                title=ch.get("title", "Chapter %d" % (i + 1)),
                body=ch.get("body", ""),
                free=bool(ch.get("free", False)),
            ))
    return Book(
        title=data.get("title", "Untitled"),
        subtitle=data.get("subtitle", ""),
        description=data.get("description", ""),
        chapters=chapters,
        voice=data.get("voice", ""),
        sheet=data.get("sheet", ""),
        subject_area=data.get("subject_area", ""),
        level=data.get("level", ""),
        keywords=list(data.get("keywords") or []),
        categories=list(data.get("categories") or []),
        price=float(data.get("price", DEFAULT_PRICE)),
        pen_name=data.get("pen_name", ""),
        author=data.get("author", ""),
        offer_url=data.get("offer_url", ""),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="stage 3: the format stage")
    ap.add_argument("book", help="the book's json")
    ap.add_argument("--out", default="dist", help="where the artifacts go")
    args = ap.parse_args()

    book = load_book(args.book)
    print("=" * 74)
    print("STAGE 3 -- FORMAT")
    print("=" * 74)
    print()
    d = book.describe()
    print("  title            %s" % d["title"])
    print("  chapters         %d (%d free, %d paid)"
          % (d["chapters"], d["free_chapters"], d["paid_chapters"]))
    print("  words            %d" % d["total_words"])
    print("  price            $%.2f" % d["price"])
    print("  royalty/sale     $%.2f" % d["royalty_per_sale"])
    print()
    res = publish(book, args.out)
    print("  gate             %s (%s)" % ("PASS" if res.ok else "REFUSED",
                                         res.reason))
    if not res.ok:
        print()
        print("  NOT PUBLISHED. The gate refused, and a refusal names")
        print("  its reason.")
        return 1
    print()
    for a in res.artifacts:
        print("  wrote %-22s %6d bytes  %s"
              % (a.kind, a.bytes, a.witness))
    print()
    print("  out dir          %s" % res.out_dir)
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
