#!/usr/bin/env python3
"""Unit tests for t17_restraint_summary pure logic (no network / real report needed).

The end-to-end parse is exercised manually against a real wwPDB report
(2N54); this covers extraction, the headline, and the empty-report guard on a
small synthetic XML so it runs anywhere.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t17_restraint_summary as t17r  # noqa: E402

_WITH_RESTRAINTS = """
<wwPDB-validation-information>
  <Entry>
    <NMR_restraints_analysis>
      <distance_restraints_analysis>
        <restraint_summary description="Total distance restraints" value="1301"/>
        <restraint_summary description="Long range (|i-j|>=5)" value="618"/>
        <residual_distance_violations>
          <residual_distance_violation bins="0.1-0.2" violations_per_model="17.4"/>
          <residual_distance_violation bins="&gt;0.5" violations_per_model="0.0"/>
        </residual_distance_violations>
        <distance_violations_in_models>
          <distance_violations_in_model model="1" mean_violation="0.15"/>
          <distance_violations_in_model model="2" mean_violation="0.13"/>
        </distance_violations_in_models>
      </distance_restraints_analysis>
      <dihedralangle_restraints_analysis>
        <restraint_summary description="Total dihedral-angle restraints" value="108"/>
      </dihedralangle_restraints_analysis>
    </NMR_restraints_analysis>
  </Entry>
</wwPDB-validation-information>
"""

_NO_RESTRAINTS = "<wwPDB-validation-information><Entry/></wwPDB-validation-information>"


def _check(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL  {msg}")
        raise SystemExit(1)
    print(f"PASS  {msg}")


def test_summarize() -> None:
    r = t17r.summarize(ET.fromstring(_WITH_RESTRAINTS))
    _check(r["summary"]["Total distance restraints"] == "1301", "extracts total distance restraints")
    _check(r["mean_distance_violation"] == round((0.15 + 0.13) / 2, 3),
           f"averages per-model mean violation (got {r['mean_distance_violation']})")
    _check(len(r["bins"]) == 2, f"extracts violation bands (got {len(r['bins'])})")
    head = t17r._headline(r)
    _check("1301 distance restraints (618 long-range), 108 dihedral" in head,
           f"headline names totals (got {head})")


def test_empty_report_fails() -> None:
    try:
        t17r.summarize(ET.fromstring(_NO_RESTRAINTS))
    except SystemExit:
        print("PASS  report without restraint data fails loudly")
        return
    print("FAIL  empty report did not fail")
    raise SystemExit(1)


def main() -> int:
    test_summarize()
    test_empty_report_fails()
    print("\nall t17_restraint_summary unit tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
