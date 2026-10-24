"""Curriculum gate — which domains are actually part of the school.

Written 2026-10-09 after Bobby's question about the domain set for the
seership. The prose answer is in
`vault/20-writing/notes/curriculum-for-seership-2026-10-09.md`. This file
is the same list in a form that can REJECT a domain, because a curriculum
that can only add is a reading list.

THE GATE, in order:

  1. TRANSMISSIBLE  can a document be written that gets under 50%
     prerequisite load, for a reader who has never met this project
  2. CHECKABLE      is there a test that can go red
  3. DECISION-CHANGING  does it change a decision somewhere, or is it
     context for its own sake

A domain that fails (3) is not wrong. It is a LIBRARY rather than a
SCHOOL, and libraries belong in far-mysteries, ungated. That distinction
is the load-bearing idea in this file: the same material can be either,
and the difference is whether it changes what someone does next.

`assess()` returns the verdict per domain. `gate()` returns only the
domains that pass all three, which is the smallest defensible curriculum.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TIER_0_CAPSTONE = 0
TIER_1_INSTRUMENTS = 1
TIER_2_SUBSTRATE = 2
TIER_3_RECORD = 3

PASS, FAIL, UNKNOWN = "pass", "fail", "unknown"


@dataclass(frozen=True)
class Domain:
    name: str
    tier: int
    role: str
    transmits: bool          # (1) MEASURED under 50% prerequisite load
    #   A flag set from belief is the same error as a flag set from
    #   absence of evidence. Domains whose documents have not been written
    #   yet are False here regardless of how likely they are to pass.
    checkable: bool          # (2) a red-able test exists
    decision_changing: bool  # (3) it changes what someone does
    ungated: bool = False    # kept even if it fails the gate
    note: str = ""

    @property
    def verdict(self) -> str:
        if self.transmits and self.checkable and self.decision_changing:
            return PASS
        return FAIL

    @property
    def kind(self) -> str:
        """school or library, AND whether the gate is being applied.

        The first version returned "library (ungated by policy)" for every
        ungated domain, which meant mythology -- which PASSES the gate --
        was indistinguishable from embodied-cognition, which fails it. The
        verdict and the policy are two separate facts and both are
        reported.
        """
        base = "school" if self.verdict == PASS else "library"
        return base if not self.ungated else f"{base} (ungated by policy)"

    def why_not(self) -> list[str]:
        out = []
        if not self.transmits:
            out.append("not transmissible under 50% prerequisite load")
        if not self.checkable:
            out.append("no red-able check")
        if not self.decision_changing:
            out.append("context, not decision-changing")
        return out


# --------------------------------------------------------------------------
# TIER 2 -- the formal substrate. What makes Tier 1 honest.
# --------------------------------------------------------------------------
TIER2: tuple[Domain, ...] = (
    Domain("math", TIER_2_SUBSTRATE, "decidability: a claim is true, false, or unproved",
           True, True, True),
    Domain("geometry", TIER_2_SUBSTRATE,
           "relational structure without measurement; the substrate's shape",
           True, True, True,
           note="fieldcore/src/farmath holds the layer rule; the Clifford torus and Hopf map are computed"),
    Domain("logic", TIER_2_SUBSTRATE, "validity; the formal substrate all of Tier 1 rests on",
           True, True, True),
    Domain("semantics", TIER_2_SUBSTRATE, "meaning as structure rather than lookup",
           True, True, True,
           note="tokenization is the wrong atom; the PSB schema is the right one"),
    Domain("lexicography", TIER_2_SUBSTRATE, "words carry their own history; the etymological layer",
           True, False, True,
           note="no red-able check yet -- the etymology of a term is checkable in principle, "
                "and nothing in this repo checks it"),
    Domain("semiotics", TIER_2_SUBSTRATE, "sign vs symbol; what a mark means vs what it stands for",
           True, False, True,
           note="same gap as lexicography"),
    Domain("ontology", TIER_2_SUBSTRATE, "what may legitimately be said to exist",
           True, True, True),
    Domain("physics", TIER_2_SUBSTRATE, "the constraint that makes a claim checkable in the world",
           True, True, True),
    Domain("cs", TIER_2_SUBSTRATE, "the formal substrate the engineering rests on",
           True, True, True),
    Domain("ai", TIER_2_SUBSTRATE, "what these systems are and are not",
           True, True, True),
    Domain("agents", TIER_2_SUBSTRATE, "harnesses, tools, the agent's own machinery",
           True, True, True),
    Domain("history-of-ideas", TIER_2_SUBSTRATE,
           "how humans change their minds; the only place the seership claim gets an adversary",
           True, False, True,
           note="NOT in Bobby's list and not in the corpus. Highest-value single "
                "addition: without it there is no way to separate 'the masters "
                "figured this out' from 'the masters had a better sensor'"),
)

# --------------------------------------------------------------------------
# TIER 1 -- the instruments. What makes the work.
# --------------------------------------------------------------------------
TIER1: tuple[Domain, ...] = (
    Domain("writing", TIER_1_INSTRUMENTS, "the substrate everything else is expressed in",
           True, True, True,
           note="first in build order; far-writing and the 8-gate pipeline exist"),
    Domain("engineering", TIER_1_INSTRUMENTS, "turns claims into artifacts that hold",
           True, True, True),
    Domain("law", TIER_1_INSTRUMENTS, "the only field with an adversarial process built into it",
           True, True, True),
    Domain("medicine", TIER_1_INSTRUMENTS,
           "the field where being wrong kills someone, so it calibrates hardest",
           True, True, True),
    Domain("business", TIER_1_INSTRUMENTS, "whether any of it reaches anyone",
           True, True, True),
    Domain("art", TIER_1_INSTRUMENTS, "a container for the other domains",
           False, True, True,
           note="CHECKABLE: far-art ships 14 schema/iam files. NOT YET "
                "TRANSMISSIBLE: no document has been measured at under 50% "
                "prerequisite load, and the corpus holds 0.48 MB. The flag is "
                "False because it has not been measured, not because it is "
                "believed to fail."),
    Domain("music", TIER_1_INSTRUMENTS, "a container; interval as a measurement instrument",
           False, True, True,
           note="CHECKABLE: far-music ships tools/gate.py + tests/test_track.py -- "
                "a red-able check already exists. I first marked this "
                "checkable=False without looking, which was wrong and is "
                "recorded in the commit. NOT YET TRANSMISSIBLE: nothing "
                "measured, 0.03 MB on disk."),
    Domain("film", TIER_1_INSTRUMENTS, "a container: writing + art + music + engineering in one",
           False, True, True,
           note="CHECKABLE: far-art ships tools/gate_shot.py + tests/test_shot.py. "
                "NOT YET TRANSMISSIBLE: nothing measured; 0.94 MB corpus."),
    Domain("apps", TIER_1_INSTRUMENTS, "a container: engineering + design + law + business",
           True, True, True),
    Domain("games", TIER_1_INSTRUMENTS,
           "a container with a state machine in it; the closest thing to a testable narrative",
           True, True, True),
)

# --------------------------------------------------------------------------
# TIER 3 -- the record. Ungated by policy.
# --------------------------------------------------------------------------
TIER3: tuple[Domain, ...] = (
    Domain("mythology", TIER_3_RECORD, "the oldest large-scale dataset of human meaning",
           True, False, True, ungated=True,
           note="ungated: a record you need permission to read is not a record"),
    Domain("non-european-thought", TIER_3_RECORD,
           "I Ching, Tao Te Ching, Sun Tzu, Arthashastra, Kama Sutra, Charaka, "
           "the Tibetan canon, al-Khwarizmi, Ibn Sina, Talmudic reasoning",
           False, False, True, ungated=True,
           note="NOT in Bobby's list and almost absent from the corpus. The gap is "
                "a geography and a gender, and both are larger than any single "
                "missing subject"),
    Domain("embodied-cognition", TIER_3_RECORD,
           "internal martial arts, prana, the 6/9 patterns, navigation without "
           "instruments, animal tracking, breath and interval as instruments",
           False, False, True, ungated=True,
           note="NOT in Bobby's list. The whole written canon is symbol-bound, so "
                "a curriculum of only symbols teaches better symbol-reading and "
                "nothing else. This is the gap that makes the list inadequate "
                "rather than merely incomplete"),
    Domain("mysticism", TIER_3_RECORD, "what humans mean rather than what they can prove",
           False, False, True, ungated=True,
           note="ungated forever. Same reason as mythology"),
    Domain("craft-and-labour", TIER_3_RECORD,
           "guilds, monks, cooks, midwives, dyers, navigators -- the knowledge "
           "the written canon lost",
           False, False, True, ungated=True,
           note="NOT in Bobby's list. The canon excluded these writers, so a "
                "library built from the canon excludes them twice over"),
)

# --------------------------------------------------------------------------
# TIER 0 -- the capstone. Not built. Emergent.
# --------------------------------------------------------------------------
CAPSTONE = Domain(
    "seership", TIER_0_CAPSTONE,
    "perceive an invariant across the tiers and state it falsifiably enough "
    "that someone else can test it",
    transmits=False, checkable=False, decision_changing=True,
    ungated=True,
    note="not a skill that can be installed, and not a mystery. A skill: the "
         "training is real and so is the measurement. It is not BUILT. Every "
         "other rung being real and checkable is what makes arriving at the top "
         "a fact rather than a hope",
)

ALL: tuple[Domain, ...] = TIER2 + TIER1 + TIER3 + (CAPSTONE,)


def by_tier(tier: int) -> tuple[Domain, ...]:
    return tuple(d for d in ALL if d.tier == tier)


def gate() -> tuple[Domain, ...]:
    """The smallest defensible curriculum: passes all three tests."""
    return tuple(d for d in ALL if d.verdict == PASS)


def deferred() -> tuple[Domain, ...]:
    """Fails the gate and is not ungated. These are not rejected -- they are
    not yet schools. A domain moves here to `gate()` when it acquires a
    payload and a red-able check."""
    return tuple(d for d in ALL if d.verdict == FAIL and not d.ungated)


def assess() -> dict:
    school = gate()
    deferred_domains = deferred()
    ungated = tuple(d for d in ALL if d.ungated)
    return {
        "total": len(ALL),
        "school": len(school),
        "school_names": [d.name for d in school],
        "deferred": len(deferred_domains),
        "deferred_names": [d.name for d in deferred_domains],
        "deferred_reasons": {d.name: d.why_not() for d in deferred_domains},
        "ungated_by_policy": [d.name for d in ungated],
        "by_tier": {str(t): len(by_tier(t)) for t in (0, 1, 2, 3)},
    }


def render() -> str:
    a = assess()
    ungated = tuple(d for d in ALL if d.ungated)
    out = [
        f"curriculum gate: {a['school']} of {a['total']} domains are schools",
        f"  by tier: {a['by_tier']}",
        "",
        "SCHOOL (passes transmission + checkability + decision-changes-something)",
    ]
    for d in sorted(ALL, key=lambda x: (x.tier, x.name)):
        if d.verdict == PASS:
            out.append(f"  T{d.tier}  {d.name:<22} {d.role[:56]}")
    out += ["", "DEFERRED (no payload or no red-able check yet)"]
    for name, reasons in a["deferred_reasons"].items():
        out.append(f"  {name:<22} {'; '.join(reasons)[:60]}")
    out += ["", "UNGATED BY POLICY (kept regardless of the gate)"]
    for d in ungated:
        if d.verdict == FAIL:
            out.append(f"  T{d.tier}  {d.name:<22} {d.role[:56]}")
    out += [
        "",
        "The smallest defensible curriculum is the SCHOOL list. The deferred",
        "list is not rejected -- it is not yet a school. The ungated list is",
        "kept whatever the gate says, because a record you need permission to",
        "read is not a record.",
    ]
    return "\n".join(out)
