#!/usr/bin/env python3
"""Round 30's classification of every figure found wrong in rounds 24-29.

Committed so the round's headline figures come from a re-runnable script rather than
from prose -- which is the rule 62 %% of those very figures broke.

S = stale (correct when written, the source moved), W = wrong at write time,
U = undecidable from the committed record. The evidence column names what settles it.
"""
# S = stale (correct when written), W = wrong at write time, U = undecidable.
rows = [
 ("#130","'three high' (round25 doc)","W","#116–#127 always held 4 high; the issues are committed and unchanged","m"),
 ("#135","'20-file audit round'","W","the round's own diff was 19 files; `git diff main..` on the merged commit still shows 19","m"),
 ("#147","'42 guard checks' (PR body)","S","dangling commit 8bdad88 re-run: `all guard unit tests passed (42 checks)` (#187)"),
 ("#150","'all 7 checkable' (round26)","W","the count was outrun by round 26's OWN development, never right at a committed moment (#187)","e"),
 ("#155","'15 defects' (#139–#153)","W","#141 is a PR and always was; the record excludes PRs by construction","m"),
 ("#156","'three earlier' reconciles","W","5 prior reconciles are in `git log` and were before the claim was written","m"),
 ("#158a","'5 more with a different lens'","W","round 26's own trail says two, and that trail was committed first","m"),
 ("#158b","staleness 'four times'","W","round 26's body said three; the claim was written after it","m"),
 ("#163a","'12, then 5, then 5'","W","the same file said 12/2/5 forty lines below, already committed","m"),
 ("#163b","'3 of 60' at the 1.074 fence","W","the TSV held 4 above 1.074 when round 23 wrote it; the data is unchanged","m"),
 ("#164","tally 'eight'/'nine'","W","#150 carried two wrong numbers from the moment it was filed","m"),
 ("#165","'Twenty-four rounds'","S","correct at round 24; rounds accrued underneath it"),
 ("#166a","'four figures are derived'","W","the script returned three derivations when the claim was written","m"),
 ("#166b","round26's '12 checked'/'10 of 21'","W","the gate already printed 15 at round 26's own squash commit 2b1fe15 (#187)","e"),
 ("#167a","10RI '+0.45 %'","S","dangling commit 3d6e5453: round 15's trail states 10RI +0.0115 / +0.45 % (#187)"),
 ("#167b","'2.2–6.1 Å' range","S","correct for round 12's 21-entry set; the set grew to 36"),
 ("#167c","6.10 Å ceiling (9VAM)","S","tolerance_benchmark_round12.md holds 9VAM at 6.1020, on main (#187)"),
 ("#169","measurement table not balancing","W","the rows did not add up on the day they were written","e"),
 ("#170a","registry caveat left behind","W","the contradiction was created by the fix itself","e"),
 ("#170b","round27 tally 'Eight' left","W","same: created by a fix that changed its pair","e"),
 ("#170c","round28 scope limits stale","W","the headline moved in the same commit","e"),
 ("#170d","merged table row (round 26's two)","W","the two figures were distinct when the row was written","e"),
 ("#170e","lessons.md round-28 para","W","never updated in the commit that moved its siblings","e"),
 ("#171","round-12 figure rewritten","W","the edit made a true sentence false at the moment it landed","e"),
 ("#172","header 'ninth' vs body 'Tenth'","S","header was correct until `fa89a2a` moved its pair — rotted by a SIBLING edit, not a data change"),
 ("#173","'fourth instance'","W","#170's table already listed four when the claim was written","m"),
 ("#174","'nine' meaning three things","W","all three senses were present in the document as written","m"),
 ("#176","'fifteen'","W","the document's own table gave #166 three rows at the time","m"),
 ("#177a","round table 24,25,26,28,27","W","the row was inserted out of order","e"),
 ("#177b","'Ten issues' excluded #176","W","#176 was fixed in the SAME commit that wrote the count excluding it (#187)","e"),
 ("#177c","third 'nine' unenumerated","N","#177's body records the derivation and nine was RIGHT — not a wrong figure (#187)"),
 ("#177d","lesson with no index row","W","the paragraph and the index were written in the same commit","e"),
 ("#179","'Eleven' excluded #177","W","#177 already existed when 'Eleven' was written","m"),
 ("#182","P2 'confirmed'","W","the classification flipped under a method available at the time","m"),
]
from collections import Counter
rows = [r for r in rows if r[2] != "N"]        # N = not a wrong figure; see #187
c = Counter(r[2] for r in rows)
print(f"{'issue':<7} {'figure':<38} {'kind':<4} evidence")
for r in rows:
    i, f, k, e = r[0], r[1], r[2], r[3]
    cause = f"[{r[4]}]" if len(r) > 4 else "   "
    print(f"{i:<7} {f[:36]:<36} {k:<3}{cause} {e[:66]}")
causes = Counter(r[4] for r in rows if r[2] == "W" and len(r) > 4)
tot = len(rows); dec = c['S']+c['W']
print(f"\n  total {tot}   STALE {c['S']}   WRONG-AT-WRITE {c['W']}   UNDECIDABLE {c['U']}")
print(f"  of {dec} decidable: stale {100*c['S']/dec:.0f} %, wrong-at-write {100*c['W']/dec:.0f} %")
print(f"  P1 (stale NOT a majority): {c['S'] < dec/2}")
print(f"  P3 (undecidable > 2): {c['U'] > 2}")
w = c['W']
print(f"\n  cause of the {w} WRONG-AT-WRITE:")
print(f"    restated from memory : {causes['m']:>2}  ({100*causes['m']/w:.0f} %)")
print(f"    incomplete edit      : {causes['e']:>2}  ({100*causes['e']/w:.0f} %)")
print(f"  P2 (memory is the dominant cause): {causes['m'] > causes['e']}")
