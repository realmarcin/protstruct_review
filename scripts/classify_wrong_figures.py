#!/usr/bin/env python3
"""Round 30's classification of every figure found wrong in rounds 24-29.

Committed so the round's headline figures come from a re-runnable script rather than
from prose -- which is the rule 62 %% of those very figures broke.

S = stale (correct when written, the source moved), W = wrong at write time,
U = undecidable from the committed record. The evidence column names what settles it.
"""
# S = stale (correct when written), W = wrong at write time, U = undecidable.
rows = [
 ("#130","'three high' (round25 doc)","W","#116–#127 always held 4 high; the issues are committed and unchanged"),
 ("#135","'20-file audit round'","W","the round's own diff was 19 files; `git diff main..` on the merged commit still shows 19"),
 ("#147","'42 guard checks' (PR body)","U","the count lived in a PR body and the intermediate commits were squashed"),
 ("#150","'all 7 checkable' (round26)","S","the gate's count grows with citations; 7 -> 12 -> 15 as later rounds added claims"),
 ("#155","'15 defects' (#139–#153)","W","#141 is a PR and always was; the record excludes PRs by construction"),
 ("#156","'three earlier' reconciles","W","5 prior reconciles are in `git log` and were before the claim was written"),
 ("#158a","'5 more with a different lens'","W","round 26's own trail says two, and that trail was committed first"),
 ("#158b","staleness 'four times'","W","round 26's body said three; the claim was written after it"),
 ("#163a","'12, then 5, then 5'","W","the same file said 12/2/5 forty lines below, already committed"),
 ("#163b","'3 of 60' at the 1.074 fence","W","the TSV held 4 above 1.074 when round 23 wrote it; the data is unchanged"),
 ("#164","tally 'eight'/'nine'","W","#150 carried two wrong numbers from the moment it was filed"),
 ("#165","'Twenty-four rounds'","S","correct at round 24; rounds accrued underneath it"),
 ("#166a","'four figures are derived'","W","the script returned three derivations when the claim was written"),
 ("#166b","round26's '12 checked'/'10 of 21'","S","correct when printed; later citations moved the gate's own output"),
 ("#167a","10RI '+0.45 %'","U","round 15's TSV state for 10RI is not retrievable; rounds 16–17 refreshed it"),
 ("#167b","'2.2–6.1 Å' range","S","correct for round 12's 21-entry set; the set grew to 36"),
 ("#167c","6.10 Å ceiling (9VAM)","U","9VAM has no recorded pre value in any committed version"),
 ("#169","measurement table not balancing","W","the rows did not add up on the day they were written"),
 ("#170a","registry caveat left behind","W","the contradiction was created by the fix itself"),
 ("#170b","round27 tally 'Eight' left","W","same: created by a fix that changed its pair"),
 ("#170c","round28 scope limits stale","W","the headline moved in the same commit"),
 ("#170d","merged table row (round 26's two)","W","the two figures were distinct when the row was written"),
 ("#170e","lessons.md round-28 para","W","never updated in the commit that moved its siblings"),
 ("#171","round-12 figure rewritten","W","the edit made a true sentence false at the moment it landed"),
 ("#172","header 'ninth' vs body 'Tenth'","S","header was correct until `fa89a2a` moved its pair — rotted by a SIBLING edit, not a data change"),
 ("#173","'fourth instance'","W","#170's table already listed four when the claim was written"),
 ("#174","'nine' meaning three things","W","all three senses were present in the document as written"),
 ("#176","'fifteen'","W","the document's own table gave #166 three rows at the time"),
 ("#177a","round table 24,25,26,28,27","W","the row was inserted out of order"),
 ("#177b","'Ten issues' excluded #176","S","correct when written; #176 was filed during review of that very fix"),
 ("#177c","third 'nine' unenumerated","U","no derivation was ever recorded for it"),
 ("#177d","lesson with no index row","W","the paragraph and the index were written in the same commit"),
 ("#179","'Eleven' excluded #177","W","#177 already existed when 'Eleven' was written"),
 ("#182","P2 'confirmed'","W","the classification flipped under a method available at the time"),
]
from collections import Counter
c = Counter(r[2] for r in rows)
print(f"{'issue':<7} {'figure':<38} {'kind':<4} evidence")
for i,f,k,e in rows:
    print(f"{i:<7} {f[:38]:<38} {k:<4} {e[:74]}")
tot = len(rows); dec = c['S']+c['W']
print(f"\n  total {tot}   STALE {c['S']}   WRONG-AT-WRITE {c['W']}   UNDECIDABLE {c['U']}")
print(f"  of {dec} decidable: stale {100*c['S']/dec:.0f} %, wrong-at-write {100*c['W']/dec:.0f} %")
print(f"  P1 (stale NOT a majority): {c['S'] < dec/2}")
print(f"  P3 (undecidable > 2): {c['U'] > 2}")
