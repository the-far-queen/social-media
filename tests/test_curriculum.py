"""Tests for the curriculum gate.

The gate exists so the curriculum can REJECT a domain. A list that can
only add is a reading list. These tests therefore spend most of their
effort proving the gate can say no.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from curriculum import (  # noqa: E402
    ALL, CAPSTONE, FAIL, PASS, TIER_0_CAPSTONE, TIER_1_INSTRUMENTS,
    TIER_2_SUBSTRATE, TIER_3_RECORD, Domain, assess, by_tier, deferred, gate,
    render,
)


# --------------------------------------------------------------------- shape


def test_every_domain_states_its_role():
    for d in ALL:
        assert d.name and d.role, d.name


def test_names_are_unique():
    names = [d.name for d in ALL]
    assert len(names) == len(set(names))


def test_tiers_are_0_to_3():
    for d in ALL:
        assert d.tier in (0, 1, 2, 3), d.name


def test_every_domain_states_whether_it_is_a_school_or_a_library():
    for d in ALL:
        assert d.kind.startswith("school") or d.kind.startswith("library"), d.name


def test_by_tier_partitions_everything():
    assert sum(len(by_tier(t)) for t in (0, 1, 2, 3)) == len(ALL)


# --------------------------------------------------------------------- the gate


def test_the_gate_can_reject():
    """If nothing is deferred the gate is decorative. art, music, film,
    lexicography, semiotics and history-of-ideas must all be outside it.
    """
    d = deferred()
    assert len(d) > 0
    names = {x.name for x in d}
    for must_be_out in ("art", "music", "film", "lexicography",
                        "semiotics", "history-of-ideas"):
        assert must_be_out in names, must_be_out


def test_no_deferred_domain_is_ungated():
    for d in deferred():
        assert not d.ungated, d.name


def test_gate_and_deferred_and_ungated_account_for_everything():
    school = {d.name for d in gate()}
    defer = {d.name for d in deferred()}
    ungated = {d.name for d in ALL if d.ungated}
    assert not (school & defer)
    assert not (school & ungated)
    assert not (defer & ungated)
    assert len(school) + len(defer) + len(ungated) == len(ALL)


def test_a_passing_domain_is_in_the_gate():
    for d in ALL:
        if d.verdict == PASS and not d.ungated:
            assert d in gate(), d.name


def test_ungated_and_verdict_are_reported_separately():
    """Ungated does not mean excluded from teaching; it means not subject
    to the gate. The two facts must be visible separately, or a domain
    that passes while ungated is indistinguishable from one that fails.

    mythology is the case: ungated, and it FAILS on checkability (there
    is no red-able check for what a myth means), so it is a library kept
    by policy rather than a school.
    """
    myth = next(d for d in ALL if d.name == "mythology")
    assert myth.ungated is True
    assert myth.verdict == FAIL          # no red-able check exists
    assert myth not in gate()            # correctly excluded from the school
    assert myth not in deferred()        # and not listed as a failure
    assert myth.kind == "library (ungated by policy)"


# --------------------------------------------------------------------- the three tests


def test_transmission_is_required():
    d = Domain("x", 2, "r", transmits=False, checkable=True, decision_changing=True)
    assert d.verdict == FAIL
    assert any("transmiss" in r for r in d.why_not())


def test_checkability_is_required():
    d = Domain("x", 2, "r", transmits=True, checkable=False, decision_changing=True)
    assert d.verdict == FAIL
    assert any("check" in r for r in d.why_not())


def test_decision_relevance_is_required():
    d = Domain("x", 2, "r", transmits=True, checkable=True, decision_changing=False)
    assert d.verdict == FAIL
    assert any("context" in r for r in d.why_not())


def test_all_three_failing_lists_every_reason():
    d = Domain("x", 2, "r", transmits=False, checkable=False, decision_changing=False)
    assert len(d.why_not()) == 3


def test_a_passing_domain_lists_no_reasons():
    d = Domain("x", 2, "r", transmits=True, checkable=True, decision_changing=True)
    assert d.why_not() == []
    assert d.verdict == PASS


# --------------------------------------------------------------------- the additions


def test_the_four_additions_bobby_did_not_list_are_present():
    """history-of-ideas, non-european-thought, embodied-cognition and
    craft-and-labour were all absent from his list. They are the answer,
    so their absence would make the answer wrong.
    """
    names = {d.name for d in ALL}
    for addition in ("history-of-ideas", "non-european-thought",
                     "embodied-cognition", "craft-and-labour"):
        assert addition in names, addition


def test_the_additions_are_never_silently_demoted_to_library():
    """Each carries a note explaining why it is there."""
    for name in ("history-of-ideas", "non-european-thought",
                 "embodied-cognition", "craft-and-labour"):
        d = next(x for x in ALL if x.name == name)
        assert d.note, f"{name} has no rationale recorded"


def test_containers_are_deferred_on_transmission_not_rigor():
    """art, music, film are deferred because nothing has been MEASURED,
    not because art is unrigorous.

    The first version of the gate marked them checkable=False. That was
    wrong: far-art ships tools/gate.py and tools/gate_shot.py plus tests,
    and 14 schema files. A red-able check exists. The honest
    reason is transmission -- no document has been measured under 50%
    prerequisite load, and the corpus holds 0.03-0.94 MB.

    A flag set from absence of evidence is the same error as one set from
    belief. This test pins the corrected reason so it cannot drift back.
    """
    for name in ("art", "music", "film"):
        d = next(x for x in ALL if x.name == name)
        assert d.verdict == FAIL, name
        assert d.checkable is True, f"{name} DOES have a checkable gate"
        assert d.transmits is False, f"{name} must fail on unmeasured transmission"
        assert any("transmiss" in r for r in d.why_not()), name
        assert d.note, f"{name} is deferred with no stated reason"


# --------------------------------------------------------------------- the capstone


def test_the_capstone_is_not_built():
    assert CAPSTONE.tier == TIER_0_CAPSTONE
    assert CAPSTONE.transmits is False
    assert CAPSTONE.ungated is True
    assert "not" in CAPSTONE.note.lower()


def test_the_capstone_is_not_in_the_gate():
    assert CAPSTONE not in gate()


def test_the_capstone_is_decision_changing_anyway():
    """It is not built and it is not checkable, and it is still the point.
    The gate refusing it is correct, not a failure of the gate.
    """
    assert CAPSTONE.decision_changing is True


# --------------------------------------------------------------------- report


def test_assess_counts_are_consistent():
    a = assess()
    assert a["total"] == len(ALL)
    assert a["school"] == len(a["school_names"]) == len(gate())
    assert a["deferred"] == len(a["deferred_names"]) == len(deferred())
    ungated_names = set(a["ungated_by_policy"])
    ungated_and_school = {d.name for d in gate()} & ungated_names
    assert (a["school"] + a["deferred"]
            + len(ungated_names) - len(ungated_and_school)
            == a["total"])


def test_assess_gives_a_reason_for_every_deferral():
    a = assess()
    assert set(a["deferred_reasons"]) == set(a["deferred_names"])
    for name, reasons in a["deferred_reasons"].items():
        assert reasons, name


def test_render_names_every_section():
    text = render()
    for heading in ("SCHOOL", "DEFERRED", "UNGATED BY POLICY"):
        assert heading in text


def test_render_states_what_deferred_means():
    """'deferred' must not read as 'rejected'. That distinction is the
    whole point of having two lists instead of one.
    """
    text = render().lower()
    assert "not rejected" in text
    assert "not yet a school" in text


def test_tier_counts_match_the_lists():
    assert len(by_tier(TIER_1_INSTRUMENTS)) == 10
    assert len(by_tier(TIER_2_SUBSTRATE)) == 12
    assert len(by_tier(TIER_3_RECORD)) == 5
    assert len(by_tier(TIER_0_CAPSTONE)) == 1
