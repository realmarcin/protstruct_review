<task>
Scientific-accuracy review of a MERGED pull request in the structural-biology evaluation harness at
/Users/marcin/Documents/VIMSS/ontology/protstruct_review (GitHub repo CultureBotAI/protstruct_review).

PR #16 ("domain-expert review of [template] tolerances") changed crystallographic pass/agreement
criteria based on a literature review. Verify the SCIENCE, not the code. Read:
  gh pr diff 16
and the audit trail it is based on:
  ref/research/template_tolerance_review.md
  ref/thresholds_and_standards.md   (sections 2 and 3, and the "Method-dependence preconditions" note)
Also spot-check the driver rubrics it touched: ref/driving_example_T05.md, _T10.md, _T11.md, _T13.md.

This is NOT a code-style review — scripts/validate.sh already gates mechanics. Judge whether each
scientific claim, citation, and number is CORRECT against the primary literature. The harness's whole
premise is not trusting unverified numbers, so a wrong citation or an overstated magnitude is a real
defect even if it "sounds right."

Verify each of these load-bearing claims independently against primary sources:

1. BOND-ANGLE. Claim: restraint-library choice alone shifts bond-angle RMSD by ~0.3-0.4°
   (resolution-independent), so a PHENIX-vs-gemmi comparison needs a matched library or a widened
   ±0.4° band. Sub-claims to check: PHENIX defaults to the conformation-dependent library (CDL) since
   ~2016 (Moriarty, Tronrud, Adams & Karplus 2016, Acta D72); gemmi/CCP4-Refmac use Engh & Huber /
   CCP4 monomer library targets; the 0.3-0.4° magnitude. Is the magnitude and its direction right? Is
   bond-LENGTH correctly characterised as nearly library-insensitive (so ±0.003 Å can stay)?

2. CC-HALF. Claim: the CC½ high-resolution cutoff of ~0.1-0.2 is from DIEDERICHS & KARPLUS 2013
   (Acta D69:1215-1222, "Better models by discarding data?"), NOT "Karplus & Diederichs 2012"
   (Science 336:1030-1033, which defines CC½/CC*). And significance is sample-size-dependent
   (CC>0.3 at n>100; CC>0.08 at n>1000). Confirm the attribution split and the significance numbers;
   confirm the registry's corrected citation is right and the old fixed-0.3 floor was too conservative.

3. RSCC. Claim: Tickle 2012 (Acta D68:454-467) states "for RSR and RSCC no sensible criterion for
   significance which is independent of B factor can be specified"; the map limiting-radius convention
   alone gives a large swing (MAPMAN fixed ~1.5 Å vs SFALL B-dependent ~2.67 Å at B=20); and the
   program-independent alternatives are RSZD (difference-density Z, ±3σ = accuracy) and RSZO
   (observed-density Z, ~1σ = precision). Confirm the quote, the radius numbers, and the RSZD/RSZO
   thresholds and their accuracy-vs-precision roles. Is demoting RSCC to matched-radius corroboration
   (and pointing accuracy at RSZD/RSZO) scientifically correct?

4. KEPT VALUES. Confirm these were correctly kept: clashscore = serious overlaps ≥ 0.4 Å per 1000
   atoms (Chen 2010; Williams 2018) with a ~0.5 hydrogen-build shift; Ramachandran 98%-favored /
   ~0.5%-outlier calibration (Williams 2018); FSC = 0.143 (half-maps) ↔ 0.5 (model/reference map)
   (Rosenthal & Henderson 2003; the 0.143↔0.5 pairing). Flag any that are misstated.

Report, per claim: CONFIRMED / WRONG / OVERSTATED / UNVERIFIABLE, with the corrected fact and a
primary-source citation for any WRONG/OVERSTATED verdict. Note especially any citation that is
mis-attributed, any magnitude that the literature does not support, and any place the registry states
a number more or less confidently than the source warrants.
</task>

<grounding_rules>
Ground every verdict in the primary literature or your tool outputs. Do not present an inference as a
fact. If you cannot verify a claim against a primary source, mark it UNVERIFIABLE rather than guessing.
Prefer IUCr journals (Acta Cryst D/A, J Appl Cryst), the named method papers, and wwPDB validation
papers over secondary summaries.
</grounding_rules>

<citation_rules>
For every WRONG or OVERSTATED verdict, cite the primary source (author, year, journal, volume/pages or
DOI) that establishes the correct fact. Quote the specific sentence or number where possible.
</citation_rules>

<dig_deeper_nudge>
After the first questionable claim, keep going: check whether the driver rubrics (T05/T10/T11/T13) now
match the corrected registry values, and whether any number in ref/research/template_tolerance_review.md
contradicts the value actually written into ref/thresholds_and_standards.md.
</dig_deeper_nudge>

<structured_output_contract>
Return one section per claim (1-4), each with a verdict (CONFIRMED / WRONG / OVERSTATED / UNVERIFIABLE),
the corrected fact + citation where applicable, and the exact registry line affected. End with a
one-line overall verdict: are PR #16's scientific criteria trustworthy as merged, or do specific
numbers/citations need correction? Compact — no restating the diff.
</structured_output_contract>

<action_safety>
Read-only review. Do not modify files, push, or comment on the PR. If you check out anything, leave the
working tree as you found it.
</action_safety>
