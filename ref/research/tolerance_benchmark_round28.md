# Tolerance benchmark — round 28: measuring the count class instead of gating it again

Round 27 closed by asserting *"nine miscounts across four rounds, and the gate now catches two of
their shapes."* Both halves were assertions. **Nine** was a tally of what review happened to notice;
nothing had ever swept for wrong numbers systematically, so it was a lower bound of unknown tightness.

The instinct was to add a third literal→derivation pair. Predictions were registered first
(`tolerance_benchmark_round28_preregistration.md`, in a commit containing no results), and **two of
the four were falsified — the two that would have justified building that third gate.**

**No tolerance, band or measurement changed.** Seven wrong figures were verified and corrected; one more is flagged at low confidence and left filed.

## The measurement

Every numeric claim about the work, in seven documents, verified by hand against its source.
Excluded by the registered method: tolerance values, entry resolutions, ids, issue numbers, dates.

**The counting rule, stated first**, because not stating it is what produced #164 and #169: a *wrong
figure* is **one distinct numeric statement that was wrong**. Two numbers in one sentence corrected
together count once; the same quantity restated in two places counts once.

| documents | claims | verifiable | correct | **wrong** | contested |
|---|---:|---:|---:|---:|---:|
| `ref/thresholds_and_standards.md` + `lessons.md` | ~227 | ~223 | ~220 | **2** | 1 |
| `NEXT_TASKS.md` + round 24–27 trails | ~99 | ~84 | ~77 | **5** | 2 |
| **total** | **~326** | **~307** | **~297** | **7** | **3** |

**The `contested` column is load-bearing and was missing from the first version of this table** — both
sweeps reported a third category (one *low-confidence*, two *contested/ambiguous*) which was folded
into `wrong` for one row and dropped from the other. The rows then failed to balance by +1 and −1, and
the total balanced only because the two errors cancelled (#169). That is #115's shape — figures
individually plausible, the relationship broken, invisible unless you add across a row — in the round
whose subject is that class.

**The exact figures, as distinct from the approximate ones:** **7 wrong statements verified by hand
and corrected** — registry 2 (10RI; the range sentence), round 27 doc 2 (the tally; "four figures"),
round 26 doc 2 (the quoted gate output; the scope-limits figure), `NEXT_TASKS` 1 (the round count).
Three further are **contested**: `lessons.md`'s round-9 *"19/19 at 1.4–2.9 Å"* and two ambiguous
attributions in the trails, none independently settled, all left filed. The aggregate
`claims`/`verifiable`/`correct` counts are approximate to ±2; both sweeps reported them with "≈".

7 of ~307 verifiable is **~2.3 %**.

## P1 — "the class is not closed": **confirmed**

Seven wrong statements were sitting on `main` and are now corrected, plus three contested — none previously filed, and every one had passed through at least one review pass at the
time it was written.

## P2 — "self-contradiction is the dominant shape": **falsified**

Registered because three of the historical nine were internal contradictions, and because a
contradiction is checkable **without knowing the right answer** — which would have made a cheap,
general guard.

Of the seven established, **two** are self-contradictions. **Five are a figure that is simply wrong or stale
against its source, with no second statement anywhere to contradict it.** The registry sweep found
**zero** live self-contradictions in 227 claims.

A contradiction-checker would therefore have caught **two of seven** — under a third of what is
actually there. The shape I was about to mechanise is the minority shape.

## P3 — "the errors are in the gate-covered files": **falsified**

Registered on the reasoning that the registry has had a derivation gate since round 24 while the
summary files got theirs two commits ago, so coverage should be the constraint.

The opposite holds:

| | verifiable | wrong | rate |
|---|---:|---:|---:|
| registry (gated since round 24, re-read every round) | ~185 | 2 | **~1.1 %** |
| round trails 24–27 (written once, never revisited) | ~65 | 4 | **~6.2 %** |

**The registry is roughly five times cleaner than the round trails**, and the trails have no gate at
all. Coverage is not the constraint; **being re-read is**. The registry's figures are wrong less often
not because they are checked more, but because every round rereads that file and nobody ever rereads a
finished trail.

## P4 — "the true count is higher than nine": **confirmed**

It is **ten**, and the error is exact: **#150 carried two distinct wrong numbers and was tallied as
one**, because the list counted *issues* while calling them *miscounts*. That is #155's shape — a
count wrong because of what sat inside the range being counted — reproduced in the tally of the class
#155 belongs to (#164).

The counting rule had never been stated. Three defensible readings existed: 11 wrong numbers, 10
shipped in the 24–27 window, 8 issues filed. Round 27's text now states the rule and the number under
it.

## What was actually wrong

| | figure | truth |
|---|---|---|
| #164 | the miscount tally, "nine" | ten, counting distinct wrong numbers |
| #165 | `NEXT_TASKS` opens *"**Twenty-four** rounds"* while line 66 said twenty-seven | both now twenty-eight |
| #166 | round 27: *"only **four** figures are derived"* | three |
| #166 | round 26: *"**12** checked, 11 not"* | 15 |
| #166 | round 26 scope limits: *"**10** are checked ... of **21**"* | 13 |
| #167 | registry: 10RI degraded *"+0.45 %"* | **0.4441 %** — the TSV's own column says so |
| #167 | registry: *"the quantity ranges **2.2–6.1 Å**"* | 2.06–4.35 Å over the 36 benchmark crossings |
| #167 | that range's 6.1 Å ceiling, attributed to 9VAM | **unverifiable** — 9VAM is a `delta-only` row with no recorded `d_fsc_model_pre` |
| — | `lessons.md` round-9: *"held on 19/19 at 1.4–2.9 Å"* | unsupported; 19 is the widened total, only 8 sit in that range (low confidence, left filed) |

**#165 is the one worth dwelling on.** The gate built for exactly that claim is blind to it twice
over: `round_count_claim` is **case-sensitive** (line 14 begins a sentence, so it reads `Twenty-four`)
and uses **`re.search`**, checking only the first match. #149 corrected precisely this case-sensitivity
in `_SEVERITY_CLAIM` — *in the same file, days earlier* — and its sibling was never touched. Fix
applied to one function and not its neighbour, again.

## What this argues for, and what it argues against

**Against** the third gate. P2 says a contradiction-checker addresses two of seven. P3
says extending coverage addresses the wrong files. Both were the plausible next moves and both are
now measured to be poor ones — which is what the pre-registration was for.

**For** something the measurement makes obvious and no gate expresses: **a round trail is a
write-once document that nobody ever rereads.** Its figures are correct when written and rot silently
because there is no occasion to look again. The registry does not rot at the same rate because every
round opens it.

That suggests the cheap intervention is not another checker but a **convention**: a figure in a
finished trail is a historical snapshot and should be written as one — stated with its denominator and
its date, not as a live quantity — so that a later reader knows it describes the moment it was written
rather than the present. Round 26's *"12 checked, 11 not"* was true the day it was written and is now
wrong; nothing about it announced that it would age.

**That is a proposal, not a result, and it is not implemented here.** This round measured; deciding
what to build on the measurement is the next one's job, and doing both would repeat exactly the
mistake the pre-registration caught.

## #170 — every fix in this round corrected the headline and left the body

Review found **five live defects**, and they are one behaviour:

| | what was left behind |
|---|---|
| **#167's fix created a NEW registry self-contradiction** | the cell's later *"Caveat: the 2.2–6.1 Å range…"* was untouched, so the file now disagreed with itself where on `main` it had agreed — **and the surviving sentence asserts 9VAM = 6.10 Å, which this round established is unverifiable** |
| #164's fix | round 27 stated its tally three ways: "Nine" (line 3), "Tenth" (179), **"Eight miscounts shipped"** (196) — plus `NEXT_TASKS` echoing the stale 8 |
| #169's fix | round 28's *own* scope limits still read ~299 / "eight wrong" / "~4×" after the headline moved to ~297 / seven / ~5.7× |
| the "what was wrong" table | merged round 26's **two** figures under one truth value — **#150's exact shape**, in this round's report about #150's shape |
| `lessons.md` | its round-28 paragraph never updated: "six", "a quarter", "~4.6 %" |

The first is the serious one. **It falsifies two of this round's own published claims** — *"the registry
sweep found zero live self-contradictions"* and P2's *"self-contradiction is the minority shape"* —
because the round created one in the file it was correcting.

### The fix had to change method, and the verification is what mattered

Spot-fixing had failed five times, so the repair was a **sweep**: enumerate every superseded value and
grep all seven documents until none survives.

**Two of the five replacements then silently did nothing** — the registry caveat uses a colon where I
had written an em-dash, and round 27's sentence wraps across lines. Both `str.replace` calls matched
zero characters and returned successfully. **A spot fix that silently misses is indistinguishable from
one that worked**, which is why five of these accumulated in the first place; only grepping for the
*old* value afterwards tells the two apart. That verification, not the edit, is the transferable part.

One occurrence of `2.2–6.1` remains by design: the "what was actually wrong" table quotes it as the
value that *was* wrong.

## #171 — the sweep's blind spot, found by the sweep's own verification step

Checking the replacement text I had just written found that the #170 sweep changed **round 12's**
lesson paragraph:

> *"…broke anyway at 3 of 21 entries — because the quantity ranges ~~2.2–6.1 Å~~ **2.06–4.35 Å**…"*

`2.06–4.35 Å` is the range over **today's 36 crossings**. Round 12 had 21 entries and could not have
observed it. The edit replaced a correct historical statement with one that is **true of no moment at
all** — worse than the staleness it replaced, which was at least true when written.

**This is the convention this round proposes, violated inside this round, while fixing something
else.** The document argues four sections above that a finished trail's figures are *snapshots* and
should carry their denominator and date. I then treated one as a live quantity and "corrected" it.

**It also marks a real limit of the sweep method #170 introduced.** "Grep for the superseded value and
replace it everywhere" is right for a figure asserted as *current* and wrong for one asserted as
*historical*, and the sweep cannot distinguish them. Worse, #170's verification step — *confirm the
old value no longer appears anywhere* — **actively rewards** deleting legitimate historical
occurrences. The check that made the sweep trustworthy is the same check that made this defect
invisible.

Restored as the convention would have it: *"the quantity ranged 2.2–6.1 Å across round 12's 21
entries (2.06–4.35 Å over the 36 recorded crossings today)"* — the snapshot, its denominator, and the
present value beside it.

## #172 — the sweep's third failure mode: blind to synonyms

A third review pass found one more, and it is the **fifth** instance of the headline-vs-body shape
in this round — #170's table above lists four (the merged-table row is #150's conflation shape, not
this one), and this is the next:

```
round27.md:172 (header)  ## #163 — the ninth miscount, and what the gate does not reach
round27.md:179 (body)    ... Tenth of the class, under that rule.
```

`fa89a2a` bumped the body to "Tenth" — correctly, per P4 — and left the header seven lines above.

**#170's sweep read the "Tenth" and never looked up.** Its commit message states it enumerated round
27's tally as *"stated three ways (Nine / Tenth / 'Eight miscounts shipped')"* and fixed the "Eight",
treating "Tenth" as the correct target. The header was not in the list because **`ninth` was never a
value I had changed** — it had been correct until `fa89a2a` moved its pair.

> **A sweep hunts the value you changed *from*. It is blind to a sibling asserting the same quantity
> in words that were never on your list.** Verify-by-absence confirms the old string is gone; it says
> nothing about whether a different form of the same claim now disagrees.

**That is the third distinct failure mode found in this one method, inside one round:** it no-ops
silently (#170), it deletes correctly-dated history (#171), and it cannot see synonyms of the quantity
it is fixing (#172). The repair is to verify by **quantity, not by string** — grep every statement of
the ordinal regardless of wording, which is how this fix was checked.

The rest of the pass was clean: every surviving occurrence of a superseded value is a legitimate
historical quotation, the new registry caveat verifies against the TSV (9VAM has no
`d_fsc_model_pre`; 10BU's 4.3513 is the largest recorded crossing), both tables balance exactly, round
26's 15-vs-13 split is a genuine two-denominator distinction rather than an error, and all four gates
exit 0.

## #173 — and the sentence counting the instances miscounted them

Reviewing the #172 fix found that its own opening sentence called #172 the *"fourth instance"* of the
headline-vs-body shape. #170's table, four lines above in the same document, lists **four** such
instances already — so #172 is the **fifth**. The count skipped the `lessons.md` row and appears to
have substituted the merged-table row, which that table explicitly labels as #150's *conflation*
shape rather than this one.

It understates by one, in the direction that makes the problem look smaller — the bias this repo says
to check hardest — inside a sentence whose only job is counting instances of a defect class.

**Nine issues — fifteen distinct wrong statements, under the counting rule stated above — were found
in the round's own work across three review passes, every one in the prose and none in the
measurement.** That split is the round's most durable result and is worth
stating as such: the measurement (P1–P4, the sweep, the seven corrected figures) has not moved through
any pass. What keeps failing is the writing *about* it — and each failure has been a count, in a round
whose subject is that counts fail.

## #174 — three quantities, one word, and a rule the summary did not follow

A post-merge review found `nine` doing three jobs in this document: round 27's historical tally
(corrected here to ten), the count of **issues** filed during round 28, and the count of **occurrences**
the #170 sweep judged. Each was individually right; nothing said they counted different things.

The substantive half is that the summary counted **issues** while this document's own rule, stated at
the top of the measurement section, counts **statements**:

> a *wrong figure* is one distinct numeric statement that was wrong

Under that rule the same set is **fifteen**, not nine — `#164:1 #165:1 #166:2 #167:2 #169:1 #170:5
#171:1 #172:1 #173:1`. **That is #164 exactly**, whose diagnosis was *"the list counted issues while
calling them miscounts"*, recurring in this round's own summary of that defect. And nine reads better
than fifteen, so it erred in the flattering direction again.

Both figures now carry their unit. The wider point is unflattering and worth keeping: **stating a
counting rule is not the same as following it.** This document defined the rule, applied it correctly
to the measurement, and abandoned it two sections later when summarising itself — which is why the
rule needs to be restated at each use rather than declared once.

## Scope limits

- **One sweep, seven documents, by hand.** The same "lower bound, not a total" caveat that applies to
  the `scripts/` audit applies here. ~326 claims is what two readers found, not what exists.
- **PR bodies are excluded** because they are not files in the repo — and #147 and #150 both lived
  there, so the sweep structurally cannot see that shape. Two of the historical ten are invisible to
  the method that measured them.
- **The ~326 / ~307 / ~297 figures are approximate to ±2.** The seven wrong ones are exact, under
  the counting rule stated above.
- **The error rates compare unequal denominators.** The registry's 185 claims are concentrated in a
  few very long rows; the trails' 65 are spread across four documents. The ~5.7× ratio is a real
  signal, not a precise measurement.
- **The sweep method cannot tell a stale figure from a historical one** (#171), and its
  verify-by-absence step rewards removing the latter. Any future sweep needs the distinction made by a
  human per occurrence; this round judged nine occurrences and got one of them wrong (#171).
- **`lessons.md`'s round-9 claim is left unfixed**, marked low-confidence by the sweep and not
  independently settled here. Recorded rather than silently corrected.
