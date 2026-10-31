"""
mutation_check_transmission.py -- prove the axis-form checks can go RED.

THE RULE (CENTRAL-RULES 7): a test that cannot fail is not a test.

THE DEFECT BEING PROVEN
------------------------
`tools/transmission.py` did not recognise the sacred library's
qualification form

    **Axis moved:** `truth_before_comfort`.
    **Current value:** ...
    **Intended value:** ...

as a definition site, so all 27 qualifications measured at 100%
prerequisite load -- with the axis name as the single missing term,
while the definition sat two lines above it.

THE MUTATIONS
-------------
Each reverts one piece of the mechanism, and each must make the suite
RED:

  the axis line is not matched at all   -> the definition checks
  the current value is dropped           -> the body checks
  the intended value is dropped          -> the body checks

AND THE HARNESS ASSERTS THE UNMUTATED SUITE IS GREEN FIRST, and it
RAISES LOUDLY IF A MUTATION DOES NOT APPLY -- the failure mode the
previous session's harness had, where the mutations silently stopped
applying and the script reported "0 of 8 RED", which reads as a result
and is the opposite of one.

Run: python tools/mutation_check_transmission.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from typing import Callable, List, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "tools")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

TARGET = os.path.join(_SRC, "transmission.py")
TEST_FILE = os.path.join(_ROOT, "tests", "test_transmission.py")


def run_tests() -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_FILE, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=_ROOT, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def with_mutated_source(mutate: Callable[[str], str]) -> Tuple[int, str]:
    """write a mutated source, run the checks, restore the original.

    **AND THE ORIGINAL IS RESTORED IN A FINALLY BLOCK**, so a mutation
    that breaks the harness cannot leave a broken source behind.
    """
    backup = TARGET + ".backup"
    shutil.copy2(TARGET, backup)
    try:
        with open(TARGET, encoding="utf-8") as fh:
            original = fh.read()
        mutated = mutate(original)
        if mutated == original:
            raise RuntimeError("the mutation did not change the source")
        with open(TARGET, "w", encoding="utf-8") as fh:
            fh.write(mutated)
        return run_tests()
    finally:
        shutil.move(backup, TARGET)


def m_axis_not_matched(p: str) -> str:
    """the axis line is not recognised as a definition site"""
    return p.replace(
        "        axis = _AXIS_MOVED.match(s)\n        if axis:",
        "        axis = None\n        if axis:", 1)


def m_current_value_dropped(p: str) -> str:
    """the current value is not read -- only one side of the move"""
    return p.replace(
        '        m = _CURRENT.match(s)\n        if m:\n'
        '            current = m.group(1).strip()\n            continue',
        "        if False:\n            pass", 1)


def m_intended_value_dropped(p: str) -> str:
    """the intended value is not read"""
    return p.replace(
        "        m = _INTENDED.match(s)\n        if m:\n"
        "            intended = m.group(1).strip()\n            break",
        "        if False:\n            pass", 1)


def m_colon_outside_the_bold(p: str) -> str:
    """the pattern asks for the colon AFTER the closing `**` -- the
    first version's mistake, which never matched anything"""
    return p.replace(
        'r"^\\*{0,2}Axis moved\\s*:\\s*\\*{0,2}\\s*`?([A-Za-z0-9_ -]{3,48}?)`?"',
        'r"^\\*{0,2}Axis moved\\*{0,2}\\s*:\\s*`?([A-Za-z0-9_ -]{3,48}?)`?"', 1)


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("the axis line is not matched", m_axis_not_matched),
    ("the current value is dropped", m_current_value_dropped),
    ("the intended value is dropped", m_intended_value_dropped),
    ("the colon is looked for outside the bold", m_colon_outside_the_bold),
]


def main() -> int:
    print("=" * 74)
    print("THE MUTATION CHECK -- each mutation must make the suite RED")
    print("=" * 74)
    print()

    code, out = run_tests()
    if code != 0:
        print("  THE UNMUTATED SUITE IS NOT GREEN -- the harness is")
        print("  broken, and no mutation result would mean anything.")
        print()
        print(out[-3000:])
        return 1
    print("  the unmutated suite is GREEN (%d checks)" % _count(out))
    print()

    went_red = 0
    for name, mutate in MUTATIONS:
        try:
            code, out = with_mutated_source(mutate)
        except RuntimeError as exc:
            print("  %-46s HARNESS BROKEN: %s" % (name, exc))
            continue
        red = code != 0
        went_red += 1 if red else 0
        print("  %-46s %s" % (name, "RED" if red else "GREEN  <-- NOT CAUGHT"))
        if not red:
            print("      (the suite still passed with this corruption)")

    print()
    print("  %d of %d mutations went RED" % (went_red, len(MUTATIONS)))
    if went_red != len(MUTATIONS):
        print("  A SURVIVING MUTATION MEANS THE CORRESPONDING CHECK IS")
        print("  DECORATIVE. Say so, or fix it.")
        return 1
    return 0


def _count(out: str) -> int:
    m = re.search(r"(\d+) passed", out)
    return int(m.group(1)) if m else 0


if __name__ == "__main__":
    sys.exit(main())
