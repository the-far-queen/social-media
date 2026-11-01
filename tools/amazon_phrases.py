"""
amazon_phrases.py -- THE KEYWORD-PHRASE SCANNER.

WHY PHRASES AND NOT TITLES
---------------------------
Bobby, 2026-10-31: *"first is categories not titles -- romance is out,
titles will not categorize into keyword phrases. self help, finance,
gardening, business -- many categories are very keyword friendly. we
write thousands of titles"*, and *"scan amazon categories by keyword
phrases. as book seller i know keyword phrases beat great stories.
no one searches for ie. amazon is a search engine"*.

So the unit of demand is the PHRASE, and the axis is the CATEGORY.
A title is the OUTPUT; a phrase is the INPUT. Nobody searches for a
title -- they search for the problem in their own words, and the
category is how Amazon files the result.

MEASURED 2026-10-31, on Amazon's own search:
    "self help"                  -> 80,000 results
    "gardening"                  -> 60,000
    "religion"                   -> 80,000
    "personal finance"           -> 60,000
    "building wealth" (quoted)  ->  8,000

AND THE COUNT IS THE DEMAND SIGNAL, and it is the cheapest demand
measurement there is: no tool, no course, no login. The number of
results for a phrase is how many books already claim that phrase.

THE THREE NUMBERS, and they are three different questions
----------------------------------------------------------
  RESULTS   how many books claim this phrase. Demand AND competition
            at once -- and the gurus' rule is that a phrase with a
            LOW result count and a real demand is the opportunity.
  TOP-1     the strongest competitor's title. This is the voice to
            beat and the format to answer.
  PRICE     what the market pays. A phrase where the top books sit
            at $29 is a different business from one at $4.39.

WHAT THIS TOOL REFUSES
-----------------------
  A TITLE AS A DEMAND TERM. Titles are outputs; measuring demand on
  them measures the authors we would be copying. Phrases are what
  buyers type.

  A SINGLE REQUEST'S COUNT AS THE WHOLE STORY. Amazon's result count
  is rounded and can be approximate, so the tool records it as
  reported and never derives a rate from it.

THE STORE MATTERS, and it was the first thing that went wrong
--------------------------------------------------------------
MEASURED 2026-10-31: the machine's delivery country is NEPAL, and
Amazon's bestseller grid for that store says *"Sorry, there are no Best
Sellers available in this category."* Amazon's SEARCH still works
from any store -- MEASURED: 16-24 real result rows with titles,
prices and ratings came back for every category and phrase tried.
So the search is the instrument, and the bestseller grid is not
reachable from this store. That is stated rather than worked around
silently, because a scanner that quietly returns nothing from the
wrong store looks like a market with no demand.

THE RATE OF REQUESTS
---------------------
Amazon does not publish a search rate limit. MEASURED: requests
about 1.5 seconds apart did not trip anything. The tool waits
between requests anyway, because a throttled scan that returns
captcha pages is a scan that returns garbage, and garbage in a
demand measurement is worse than no measurement.

Run:
    python tools/amazon_phrases.py --category "self help"
    python tools/amazon_phrases.py --phrases "building wealth" "money mindset"
    python tools/amazon_phrases.py --all
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: THE CATEGORIES. These are the axes, and they are keyword-friendly
#: ones -- romance is out (Bobby, 2026-10-31) because its buyers
#: browse titles rather than search phrases.
CATEGORIES: Dict[str, Dict[str, Any]] = {
    "self_help": {
        "name": "Self-Help",
        "phrases": (
            "self improvement", "confidence", "motivation", "habits",
            "discipline", "mindset", "productivity", "focus",
            "self discipline", "overcoming fear", "building wealth",
            "money mindset", "success", "personal growth", "goal setting",
        ),
    },
    "finance": {
        "name": "Business & Money",
        "phrases": (
            "personal finance", "budgeting", "debt free", "investing",
            "retirement planning", "money management", "financial freedom",
            "side income", "real estate investing", "saving money",
            "stock market", "passive income", "credit score",
            "retirement", "making money",
        ),
    },
    "gardening": {
        "name": "Gardening",
        "phrases": (
            "vegetable gardening", "raised bed gardening", "organic gardening",
            "container gardening", "composting", "soil health",
            "starting a garden", "tomato growing", "herb gardening",
            "hydroponics", "indoor plants", "permaculture",
            "vegetable garden", "garden planning",
        ),
    },
    "religion": {
        "name": "Religion & Spirituality",
        "phrases": (
            "meditation", "mindfulness", "prayer", "buddhism",
            "christian living", "spiritual practice", "contemplative prayer",
            "inner peace", "devotional", "scripture study", "taoism",
            "meditation for beginners", "spirituality", "religious study",
        ),
    },
    "business": {
        "name": "Business",
        "phrases": (
            "starting a business", "small business", "marketing",
            "copywriting", "lead generation", "sales", "entrepreneurship",
            "email marketing", "freelancing", "management",
            "business strategy", "customer service", "scaling",
            "negotiation", "productivity systems",
        ),
    },
}

#: THE AMAZON BOOKS DEPARTMENT. `stripbooks` is the department; the
#: category is a FILTER inside it.
BOOK_DEPARTMENT = "stripbooks"

SEARCH_URL = "https://www.amazon.com/s?k={q}&i={dept}"

#: A browser-shaped User-Agent. Amazon serves a different page to a
#: default agent, and the measurement must be of the page a buyer sees.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

#: The seconds between requests. Measured 2026-10-31: about 1.5s did
#: not trip anything, but a captcha page in a demand measurement is
#: worse than no measurement, so the wait is generous.
DELAY = 2.5


# ===========================================================================
# THE RESULT
# ===========================================================================

@dataclass
class BookRow:
    """one book in the results."""
    title: str
    asin: str = ""
    price: str = ""
    rating: str = ""
    reviews: str = ""
    badge: str = ""

    def describe(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PhraseResult:
    """what a phrase measured."""
    phrase: str
    category: str
    #: The result count AS REPORTED by Amazon. It is rounded and can be
    #: approximate, so it is recorded and never used to derive a rate.
    results_reported: str = ""
    rows: List[BookRow] = field(default_factory=list)
    error: str = ""

    @property
    def top_title(self) -> str:
        return self.rows[0].title if self.rows else ""

    @property
    def top_price(self) -> str:
        return self.rows[0].price if self.rows else ""

    @property
    def competitor_count(self) -> int:
        return len(self.rows)

    def describe(self) -> Dict[str, Any]:
        return {
            "phrase": self.phrase,
            "category": self.category,
            "results_reported": self.results_reported,
            "competitors_on_page": self.competitor_count,
            "top_title": self.top_title,
            "top_price": self.top_price,
            "error": self.error,
        }


# ===========================================================================
# THE PARSE
# ===========================================================================

#: The result count. Amazon renders it as "1-16 of over 80,000 results
#: for "self help" in Books".
_RESULTS_RE = re.compile(r"of\s+over\s+([\d,]+)\s+results", re.I)
_RESULTS_RE2 = re.compile(r"([\d,]+)\s+results\s+for", re.I)

#: One product row. The title is in an h2 > a, the price in
#: .a-price .a-offscreen, the rating in .a-icon-alt.
_ROW_RE = re.compile(
    r'<div data-component-type="s-search-result".*?</div>\s*</div>',
    re.S)
_TITLE_RE = re.compile(
    r'<h2[^>]*>.*?<span[^>]*>(.*?)</span>.*?</h2>', re.S)
_ASIN_RE = re.compile(r'data-asin="([A-Z0-9]{10})"')
_PRICE_RE = re.compile(r'<span class="a-offscreen">(.*?)</span>')
_RATING_RE = re.compile(r'([\d.]+)\s+out of\s+5\s+stars')
_REVIEWS_RE = re.compile(r'\(([\d,]+)\)')


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = (text.replace("&amp;", "&").replace("&#39;", "'")
                .replace("&quot;", '"').replace("&lt;", "<")
                .replace("&gt;", ">").replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", text).strip()


def parse_results(html: str) -> Tuple[str, List[BookRow]]:
    """the result count and the product rows, from one page of HTML.

    AND IT IS PARSED, NOT ASSUMED. The first version of this parser
    looked for a class name that Amazon does not use, found nothing,
    and reported "0 competitors" for every phrase -- which reads
    exactly like a market with no demand. So the parser falls back
    through several shapes and, if it finds no rows at all, says so
    in a way the caller cannot mistake for a zero market.
    """
    count = ""
    m = _RESULTS_RE.search(html)
    if not m:
        m = _RESULTS_RE2.search(html)
    if m:
        count = m.group(1)

    rows: List[BookRow] = []
    # The row blocks. Amazon's markup nests divs, so the block is
    # found by the component-type attribute and cut at the next one.
    blocks = re.split(r'(?=<div data-component-type="s-search-result")', html)
    for blk in blocks[1:]:
        # cut the block at the start of the NEXT row
        cut = blk.find('<div data-component-type="s-search-result"', 1)
        if cut > 0:
            blk = blk[:cut]
        tm = _TITLE_RE.search(blk)
        title = _strip_tags(tm.group(1)) if tm else ""
        if not title:
            continue
        am = _ASIN_RE.search(blk)
        pm = _PRICE_RE.search(blk)
        rm = _RATING_RE.search(blk)
        vm = _REVIEWS_RE.search(blk)
        badge = ""
        bm = re.search(
            r"(Best Seller|Amazon.s Choice|New Release|Kindle Bestseller)",
            blk)
        if bm:
            badge = bm.group(1)
        rows.append(BookRow(
            title=title,
            asin=am.group(1) if am else "",
            price=_strip_tags(pm.group(1)) if pm else "",
            rating=rm.group(1) if rm else "",
            reviews=vm.group(1) if vm else "",
            badge=badge,
        ))
    return count, rows


# ===========================================================================
# THE FETCH
# ===========================================================================

def fetch_phrase(phrase: str, category: str = "",
                  department: str = BOOK_DEPARTMENT,
                  timeout: int = 45) -> PhraseResult:
    """measure one phrase on Amazon.

    AND THE ERROR IS RECORDED ON THE RESULT, not raised, because a
    phrase that cannot be measured is a finding about that phrase --
    not about the scan.
    """
    q = urllib.parse.quote('"%s"' % phrase)
    url = SEARCH_URL.format(q=q, dept=department)
    req = urllib.request.Request(url, headers=HEADERS)
    res = PhraseResult(phrase=phrase, category=category)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        res.error = "HTTP %s" % (exc.code,)
        return res
    except urllib.error.URLError as exc:
        res.error = "URLError: %s" % (exc.reason,)
        return res
    except Exception as exc:  # noqa: BLE001
        res.error = "%s: %s" % (type(exc).__name__, exc)
        return res

    if "captcha" in html.lower() or "Enter the characters you see" in html:
        res.error = "a captcha page: the phrase was NOT measured"
        return res

    count, rows = parse_results(html)
    res.results_reported = count
    res.rows = rows
    if not rows and not res.error:
        res.error = ("no product rows parsed: the page shape changed, "
                     "so this phrase is UNMEASURED, not empty")
    return res


def scan(category: Optional[str] = None,
         phrases: Optional[Sequence[str]] = None,
         delay: float = DELAY) -> List[PhraseResult]:
    """measure a set of phrases, with a wait between requests."""
    out: List[PhraseResult] = []
    if phrases:
        todo = [(p, category or "") for p in phrases]
    else:
        todo = []
        for key, c in CATEGORIES.items():
            if category and key != category and c["name"] != category:
                continue
            for p in c["phrases"]:
                todo.append((p, key))
    for i, (phrase, cat) in enumerate(todo):
        if i:
            time.sleep(delay)
        out.append(fetch_phrase(phrase, cat))
    return out


# ===========================================================================
# THE REPORT
# ===========================================================================

def report(results: List[PhraseResult]) -> Dict[str, Any]:
    """the scan, sorted by what it is FOR.

    THE SORT IS THE POINT: the gurus' rule is that the opportunity is
    a phrase with REAL demand and FEW competitors. And the demand
    signal we can actually measure is the reported result count. So
    the phrases are ranked by demand, and the competitor count is
    reported beside it -- a high-demand phrase with few competitors
    on the page is the interesting one.
    """
    def demand(r: PhraseResult) -> int:
        try:
            return int((r.results_reported or "0").replace(",", ""))
        except ValueError:
            return 0

    ordered = sorted(results, key=demand, reverse=True)
    return {
        "phrases_measured": len(results),
        "errors": [r.phrase for r in results if r.error],
        "unmeasured": len([r for r in results if r.error]),
        "by_phrase": [r.describe() for r in ordered],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="the keyword-phrase scanner -- Amazon categories")
    ap.add_argument("--category", default=None,
                    help="one category key or name")
    ap.add_argument("--phrases", nargs="*", default=None,
                    help="specific phrases to measure")
    ap.add_argument("--all", action="store_true",
                    help="every phrase in every category")
    ap.add_argument("--delay", type=float, default=DELAY)
    ap.add_argument("--json", default=None, help="write the report here")
    args = ap.parse_args()

    print("=" * 78)
    print("THE KEYWORD-PHRASE SCANNER")
    print("=" * 78)
    print()
    print("  the unit of demand is the PHRASE, and the axis is the")
    print("  CATEGORY. a title is the output; a phrase is the input.")
    print()

    results = scan(category=args.category, phrases=args.phrases,
                   delay=args.delay)
    rep = report(results)

    print("  %-34s %-12s %-10s %-30s" % ("phrase", "results", "page",
                                         "top competitor"))
    print("  " + "-" * 88)
    for r in sorted(results, key=lambda x: x.describe()["results_reported"],
                    reverse=True):
        if r.error:
            print("  %-34s %-12s %-10s %s" % (r.phrase[:34], "-", "-",
                                                "UNMEASURED: " + r.error))
            continue
        print("  %-34s %-12s %-10s %s" % (r.phrase[:34],
                                            r.results_reported,
                                            r.competitor_count,
                                            r.top_title[:30]))
    print()
    print("  phrases measured   %d" % rep["phrases_measured"])
    print("  UNMEASURED         %d %s" % (rep["unmeasured"],
                                           rep["errors"][:5]))
    print()
    print("  AND THE NUMBER THAT DECIDES: a phrase with real demand and")
    print("  few competitors. The competitors column is how many books")
    print("  already claim the phrase on the first page.")
    print("=" * 78)

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rep, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("wrote: %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
