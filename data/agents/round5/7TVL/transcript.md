# transcript.md — 7TVL blinded agentic recovery (round 5)

Every shell command in execution order, verbatim. `P=/Users/marcin/phenix-2.0-5936/phenix_bin`.
Refinement-program invocations that actually performed refinement are tagged **[REFINE n/6]**.

## Phase 0 — inspect inputs (no refinement)

```bash
mkdir -p /tmp/agent_r5_7tvl && cd /tmp/agent_r5_7tvl && ls -la /tmp/nc_round1_work/r4p_7tvl.pdb /tmp/nc_round1_cache/7tvl.mtz
```

```bash
/opt/homebrew/bin/gemmi mtzinfo /tmp/nc_round1_cache/7tvl.mtz 2>&1 | head -50
```
(failed: not a gemmi subcommand)

```bash
/opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/7tvl.mtz 2>&1 | head -60
```

```bash
head -20 /tmp/nc_round1_work/r4p_7tvl.pdb; echo ---; grep -c ATOM /tmp/nc_round1_work/r4p_7tvl.pdb; echo ---; grep HOH /tmp/nc_round1_work/r4p_7tvl.pdb | wc -l
```

```bash
cd /tmp/nc_round1_work && echo "ANISOU: $(grep -c '^ANISOU' r4p_7tvl.pdb)"; echo "ATOM: $(grep -c '^ATOM' r4p_7tvl.pdb)"; echo "HETATM: $(grep -c '^HETATM' r4p_7tvl.pdb)"; echo "--- het residue types:"; grep '^HETATM' r4p_7tvl.pdb | cut -c18-20 | sort | uniq -c; echo "--- altloc:"; grep '^ATOM\|^HETATM' r4p_7tvl.pdb | cut -c17 | sort | uniq -c; echo "--- elements:"; grep '^ATOM\|^HETATM' r4p_7tvl.pdb | cut -c77-78 | sort | uniq -c; echo "--- chains:"; grep '^ATOM' r4p_7tvl.pdb | cut -c22 | sort | uniq -c
```

```bash
grep -E '^REMARK|^CRYST|^EXPDTA|^SEQRES' /tmp/nc_round1_work/r4p_7tvl.pdb | head -40
```

```bash
cd /tmp/agent_r5_7tvl && /opt/homebrew/bin/gemmi mtz2cif /tmp/nc_round1_cache/7tvl.mtz - 2>/dev/null | head -5 >/dev/null; python3 -c "
import gemmi
m = gemmi.read_mtz_file('/tmp/nc_round1_cache/7tvl.mtz')
print('cell',m.cell,'sg',m.spacegroup.hm,'nref',m.nreflections)
print('dmin', m.resolution_high(), 'dmax', m.resolution_low())
import numpy as np
d = m.array
labs = [c.label for c in m.columns]
print(labs)
i_f = labs.index('R-free-flags'); i_f1 = labs.index('R-free-flags-1')
c0 = d[:,i_f]; c1 = d[:,i_f1]
import collections
print('R-free-flags counts', collections.Counter(c0[~np.isnan(c0)]).most_common())
print('R-free-flags-1 counts', sorted(collections.Counter(c1[~np.isnan(c1)]).most_common()))
fo = d[:, labs.index('FOBS')]
print('FOBS nonnan', np.sum(~np.isnan(fo)), 'of', len(fo))
"
```

```bash
cd /tmp/agent_r5_7tvl && cp /tmp/nc_round1_work/r4p_7tvl.pdb start.pdb && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.model_vs_data start.pdb /tmp/nc_round1_cache/7tvl.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > mvd_start.log 2>&1; tail -60 mvd_start.log
```

```bash
P=/Users/marcin/phenix-2.0-5936/phenix_bin; ls $P | grep -iE 'molprob|geometry|validat|ready_set|reduce|elbow|maps|real_space|dynamics|xtriage'
```

```bash
cd /tmp/agent_r5_7tvl && python3 -c "
import gemmi, numpy as np
st = gemmi.read_structure('start.pdb')
st.setup_entities()
bs=[]; occ=[]
for m in st:
    for ch in m:
        for r in ch:
            for a in r:
                bs.append(a.b_iso); occ.append(a.occ)
    break
bs=np.array(bs); occ=np.array(occ)
print('B: min %.2f max %.2f mean %.2f median %.2f'%(bs.min(),bs.max(),bs.mean(),np.median(bs)))
print('occ: min %.2f max %.2f mean %.3f'%(occ.min(),occ.max(),occ.mean()))
print('n occ<1:', np.sum(occ<0.999))
"
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.molprobity start.pdb output.prefix=mp_start > mp_start_run.log 2>&1; sed -n '/Summary/,/=====/p' mp_start.out 2>/dev/null | head -40; echo "=== tail of run log ==="; tail -30 mp_start_run.log
```

## Phase 1 — hydrogens + refinement run 1

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && time $P/phenix.ready_set start.pdb add_h_to_water=False optimise_final_geometry_of_hydrogens=False > readyset.log 2>&1; echo "exit=$?"; tail -25 readyset.log; ls -la *.pdb *.cif 2>/dev/null
```

```bash
cd /tmp/agent_r5_7tvl && echo "H atoms: $(awk '/^ATOM|^HETATM/ && substr($0,77,2)==" H"' start.updated.pdb | wc -l)"; echo "D atoms: $(awk '/^ATOM|^HETATM/ && substr($0,77,2)==" D"' start.updated.pdb | wc -l)"; echo "total atoms: $(grep -cE '^(ATOM|HETATM)' start.updated.pdb)"; echo "ANISOU: $(grep -c '^ANISOU' start.updated.pdb)"; grep -iE 'flip|LINK' readyset.log | head
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.refine --show-defaults=2 > defaults.txt 2>&1; echo lines=$(wc -l < defaults.txt); grep -nE 'anisotropic|^ *ordered_solvent|simulated_annealing|optimize_xyz_weight|optimize_adp_weight|nqh_flips|number_of_macro_cycles|refine_riding|^ *riding|strategy' defaults.txt | head -40
```

```bash
cd /tmp/agent_r5_7tvl && sed -n '140,200p' defaults.txt
```

```bash
cd /tmp/agent_r5_7tvl && sed -n '815,900p' defaults.txt; echo ===; sed -n '975,1000p' defaults.txt
```

```bash
cd /tmp/agent_r5_7tvl && grep -nE '^ *hydrogens|^ *refine = |nproc|real_space_refine_overall|^ *build = ' defaults.txt | head -20; echo ===; sed -n '/^  hydrogens {/,/^  }/p' defaults.txt | head -30
```

**[REFINE 1/6]**
```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && nohup $P/phenix.refine start.updated.pdb /tmp/nc_round1_cache/7tvl.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=3 refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.hydrogens.refine=riding refinement.main.nproc=8 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1 &
echo "launched pid $!"; sleep 60; tail -20 r1.log
```

```bash
ls -la /tmp/agent_r5_7tvl/ | head -30; echo "=== pgrep:"; pgrep -fl phenix | head
```

```bash
cd /tmp/agent_r5_7tvl && grep -nE 'MACRO_CYCLE|r_work|r_free|Sorry|Traceback|anisotropic:|isotropic:' r1.log | tail -30
```

```bash
cd /tmp/agent_r5_7tvl && grep -nE 'Number of.*anisotropic|Anisotropic|aniso|Number of atoms|riding|Number of scatterers' r1.log | head -20
```

```bash
sleep 240; cd /tmp/agent_r5_7tvl && grep -nE 'MACRO_CYCLE|^ *r_work=|Sorry|Traceback|Final ' r1.log | tail -25; echo "=== done? ==="; pgrep -f 'output.prefix=r1' >/dev/null && echo RUNNING || echo FINISHED
```

```bash
sleep 90; cd /tmp/agent_r5_7tvl && pgrep -f 'output.prefix=r1' >/dev/null && echo RUNNING || echo FINISHED; sed -n '/==== Final ====/,$p' r1.log | head -60
```

```bash
cd /tmp/agent_r5_7tvl && sed -n '/REFINEMENT STATISTICS STEP BY STEP/,$p' r1.log | sed -n '40,70p'; echo "=== final geometry ==="; grep -A25 'Final: r_work' r1.log | head -35; ls -la r1_001.pdb r1_001.mtz
```

## Phase 2 — run 2 (aborted launch: PHENIX bug, then fixed and relaunched)

**[NOT COUNTED — crashed in `Extract refinement strategy and selections`, before any refinement step ran]**
```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && nohup $P/phenix.refine r1_001.pdb /tmp/nc_round1_cache/7tvl.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.ordered_solvent.new_solvent=anisotropic refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.hydrogens.refine=riding refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=4 output.prefix=r2 output.serial=1 --overwrite > r2.log 2>&1 &
echo "launched pid $!"; sleep 45; grep -nE 'Sorry|Traceback|MACRO_CYCLE' /tmp/agent_r5_7tvl/r2.log | head
```

```bash
cd /tmp/agent_r5_7tvl && sed -n '480,540p' r2.log
```

```bash
sed -n '430,490p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/occupancies.py
```

```bash
cd /tmp/agent_r5_7tvl && echo "waters with altloc in r1_001.pdb:"; awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH"' r1_001.pdb | cut -c17 | sort | uniq -c; echo "--- water chains:"; awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH"' r1_001.pdb | cut -c22 | sort | uniq -c; echo "--- water occupancies not 1:"; awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH" && substr($0,55,6)+0 < 0.999' r1_001.pdb | wc -l; echo "--- GOL/SO4 altloc:"; awk '/^(ATOM|HETATM)/ && (substr($0,18,3)=="GOL"||substr($0,18,3)=="SO4")' r1_001.pdb | cut -c17,18-20,22-26 | sort | uniq -c
```

```bash
cd /tmp/agent_r5_7tvl && awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH"{o=substr($0,55,6)+0; print o}' r1_001.pdb | sort -n | head -20; echo "..."; echo "count occ<0.2: $(awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH" && substr($0,55,6)+0<0.2' r1_001.pdb | wc -l)"; echo "count occ<1e-6: $(awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH" && substr($0,55,6)+0<0.000001' r1_001.pdb | wc -l)"; echo "--- altloc waters detail:"; awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH" && substr($0,17,1)!=" "' r1_001.pdb | cut -c1-60
```

```bash
cd /tmp/agent_r5_7tvl && python3 -c "<alt-conf water A-B distance + orphan-water scan, first version; NeighborSearch signature error>"
```

```bash
cd /tmp/agent_r5_7tvl && python3 -c "<alt-conf water A-B distance + orphan-water scan, corrected NeighborSearch(model, cell, radius)>"
```

```bash
cd /tmp/agent_r5_7tvl && python3 - <<'PY'
targets_del = {('B','HOH',564),('B','HOH',613)}   # alt conformers refined to occ 0.00 / 0.06
targets_keep = {('A','HOH',564),('A','HOH',613)}  # promote to full occupancy, no altloc
out=[]; ndel=0; nfix=0
for line in open('r1_001.pdb'):
    if line[:6] in ('ATOM  ','HETATM','ANISOU'):
        alt=line[16]; res=line[17:20].strip(); num=int(line[22:26])
        key=(alt,res,num)
        if key in targets_del:
            ndel+=1; continue
        if key in targets_keep:
            line = line[:16]+' '+line[17:]
            if line[:6]!='ANISOU':
                line = line[:54]+'  1.00'+line[60:]
            nfix+=1
    out.append(line)
open('r1_fix.pdb','w').writelines(out)
print('deleted lines:',ndel,'  relabelled lines:',nfix)
PY
echo "--- verify:"; grep -E 'HOH A (564|613)' r1_fix.pdb; echo "atoms: $(grep -cE '^(ATOM|HETATM)' r1_fix.pdb)  anisou: $(grep -c '^ANISOU' r1_fix.pdb)"; echo "zero-occ waters left: $(awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH" && substr($0,55,6)+0<0.000001' r1_fix.pdb | wc -l)"
```

**[REFINE 2/6]**
```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && nohup $P/phenix.refine r1_fix.pdb /tmp/nc_round1_cache/7tvl.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.ordered_solvent.new_solvent=anisotropic refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.hydrogens.refine=riding refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=4 output.prefix=r2 output.serial=1 --overwrite > r2.log 2>&1 &
echo "launched pid $!"; sleep 120; grep -nE 'Sorry|Traceback|MACRO_CYCLE|^ *r_work=' /tmp/agent_r5_7tvl/r2.log | tail -12
```

## Phase 3 — diagnosing the run-2 crash, then runs 3 and 4

```bash
cd /tmp/agent_r5_7tvl && sed -n '960,1040p' r2.log
```

```bash
cd /tmp/agent_r5_7tvl && sed -n '1040,1070p' r2.log; echo "=== calculators.py:80-100 ==="; sed -n '80,100p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/calculators.py; echo "=== ordered_solvent.py:575-600,700-720 ==="; sed -n '575,600p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/solvent/ordered_solvent.py; sed -n '700,720p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/solvent/ordered_solvent.py
```

```bash
cd /tmp/agent_r5_7tvl && ls -la r2* 2>/dev/null; echo "=== weight optimization choices ==="; grep -nE 'optimal|wxc|wxu|Optimiz|weight' r2.log | grep -viE 'target_weights\.|^ *#' | head -30
```

```bash
cd /tmp/agent_r5_7tvl && grep -nE 'wxc = |wxu = |Optimizing|optimization|trial|best weight' r2.log | head -20; echo "=== run1 weights ==="; grep -nE 'wxc = |wxu = ' r1.log | head; echo "=== r2 macrocycle1 step table ==="; sed -n '761,930p' r2.log | grep -nE '^ *[0-9a-z_]+: *r_work|r_work=' | head -20
```

```bash
cd /tmp/agent_r5_7tvl && grep -nE 'occupancy_min|occupancy_max|^ *min_occupancy' defaults.txt
```

**[REFINE 3/6]**
```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && nohup $P/phenix.refine r1_fix.pdb /tmp/nc_round1_cache/7tvl.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=8 refinement.main.ordered_solvent=True refinement.main.occupancy_min=0.02 refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.hydrogens.refine=riding refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=4 output.prefix=r3 output.serial=1 --overwrite > r3.log 2>&1 &
echo "launched pid $!"; sleep 300; grep -nE 'MACRO_CYCLE|Sorry|Traceback' r3.log | tail -6; grep -E 'n_water=|^ *end:' r3.log | tail -12
```

```bash
ls -la /tmp/agent_r5_7tvl/r3* 2>&1; grep -nE 'MACRO_CYCLE|Sorry|Traceback' /tmp/agent_r5_7tvl/r3.log 2>&1 | tail -6
```

```bash
grep -E 'n_water=|Add new water|Filter \(map\)|ADP\+occupancy|^ *end:' /tmp/agent_r5_7tvl/r3.log | tail -25
```

```bash
sleep 600; grep -nE 'MACRO_CYCLE|Sorry|Traceback|Job complete' /tmp/agent_r5_7tvl/r3.log | tail -6; grep -E '^ *[0-9]+_(bss|xyzrec|adp|occ)|^ *end:' /tmp/agent_r5_7tvl/r3.log | tail -12; pgrep -f 'output.prefix=r3' >/dev/null && echo RUNNING || echo FINISHED
```
(timed out at 10 min; run still going)

```bash
grep -nE 'MACRO_CYCLE|Sorry|Traceback|Job complete' /tmp/agent_r5_7tvl/r3.log | tail -6; echo "=== step table ==="; grep -E '^ *[0-9]+_(bss|xyzrec|adp|occ|updatesol)|^ *end:' /tmp/agent_r5_7tvl/r3.log | tail -14; pgrep -f 'output.prefix=r3' >/dev/null && echo RUNNING || echo FINISHED
```

```bash
grep -E 'n_water=|final r_work' /tmp/agent_r5_7tvl/r3.log | tail -8; echo "=== r_work trace ==="; grep -E '^r_work=' /tmp/agent_r5_7tvl/r3.log | tail -10
```

```bash
sleep 540; pgrep -f 'output.prefix=r3' >/dev/null && echo RUNNING || echo FINISHED; grep -nE 'Job complete|Traceback' /tmp/agent_r5_7tvl/r3.log | tail -3; echo "=== final ==="; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r3.log; sed -n '/REFINEMENT STATISTICS STEP BY STEP/,$p' /tmp/agent_r5_7tvl/r3.log | tail -18
```

```bash
grep -nE 'MACRO_CYCLE' /tmp/agent_r5_7tvl/r3.log | tail -3; grep -E '^r_work=' /tmp/agent_r5_7tvl/r3.log | tail -4; grep -E 'n_water=' /tmp/agent_r5_7tvl/r3.log | tail -3
```

```bash
sleep 480; pgrep -f 'output.prefix=r3' >/dev/null && echo RUNNING || echo FINISHED; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r3.log; sed -n '/REFINEMENT STATISTICS STEP BY STEP/,$p' /tmp/agent_r5_7tvl/r3.log | tail -16; ls -la /tmp/agent_r5_7tvl/r3_001.pdb 2>&1
```

```bash
sed -n '/REFINEMENT STATISTICS STEP BY STEP/,/^---/p' /tmp/agent_r5_7tvl/r3.log | tail -20; echo "=== resolution bins ==="; sed -n '/Statistics in resolution bins/,/Approximation/p' /tmp/agent_r5_7tvl/r3.log | tail -16
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.molprobity r3_001.pdb output.prefix=mp_r3 > mp_r3_run.log 2>&1; sed -n '/=== Summary ===/,$p' mp_r3.out | head -20; echo "=== waters ==="; awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH"' r3_001.pdb | wc -l
```

```bash
grep -nE 'Filter|n_water=|ignore_final' /tmp/agent_r5_7tvl/r3.log | tail -20; echo "=== tools ==="; ls /Users/marcin/phenix-2.0-5936/phenix_bin | grep -iE 'find_peaks|holes'
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.find_peaks_holes r3_001.pdb r3_001.mtz map_type="mFo-DFc" peak_search.min_cross_distance=1.5 > fph_r3.log 2>&1; echo exit=$?; grep -nE 'peaks|holes|sigma' fph_r3.log | head -20; echo "=== strongest ==="; sed -n '/Found .* peaks/,$p' fph_r3.log | head -40
```

```bash
cd /tmp/agent_r5_7tvl && sed -n '45,80p' fph_r3.log; echo "=== HOLES ==="; sed -n '219,250p' fph_r3.log; echo "=== water peaks ==="; sed -n '280,304p' fph_r3.log
```

**[REFINE 4/6]**
```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && nohup $P/phenix.refine r3_001.pdb /tmp/nc_round1_cache/7tvl.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=5 refinement.main.ordered_solvent=True refinement.main.occupancy_min=0.02 refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.ordered_solvent.primary_map_cutoff=2.8 refinement.ordered_solvent.secondary_map_and_map_cc_filter.poor_cc_threshold=0.5 refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.hydrogens.refine=riding refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=4 output.prefix=r4 output.serial=1 --overwrite > r4.log 2>&1 &
echo "launched pid $!"; sleep 240; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r4.log | tail -4; grep -E 'n_water=' /tmp/agent_r5_7tvl/r4.log | tail -6
```

```bash
grep -nE 'r_work=|n_water=|Filter|Add new|start:' /tmp/agent_r5_7tvl/r4.log | sed -n '1,45p'
```

```bash
echo "=== run3 wxc/wxu ==="; grep -E 'wxc = |wxu = ' /tmp/agent_r5_7tvl/r3.log; echo "=== run4 wxc/wxu ==="; grep -E 'wxc = |wxu = ' /tmp/agent_r5_7tvl/r4.log
```

## Phase 4 — runs 5 and 6, validation

```bash
sleep 300; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r4.log | tail -3; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r4.log | tail -8
```

```bash
sleep 600; pgrep -f 'output.prefix=r4' >/dev/null && echo RUNNING || echo FINISHED; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r4.log; grep -nE 'Traceback' /tmp/agent_r5_7tvl/r4.log | tail -2; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r4.log | tail -6
```
(timed out at 10 min)

```bash
pgrep -f 'output.prefix=r4' >/dev/null && echo RUNNING || echo FINISHED; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r4.log; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r4.log | tail -3; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r4.log | tail -6; ls -la /tmp/agent_r5_7tvl/r4_001.pdb 2>&1
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.molprobity r4_001.pdb output.prefix=mp_r4 > mp_r4_run.log 2>&1; sed -n '/=== Summary ===/,$p' mp_r4.out | head -20
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.find_peaks_holes r4_001.pdb r4_001.mtz map_type="mFo-DFc" > fph_r4.log 2>&1; sed -n '/SUMMARY OF MAP PEAKS/,$p' fph_r4.log
```

```bash
cd /tmp/agent_r5_7tvl && sed -n '/Positive difference map peaks/,/Negative difference/p' fph_r4.log | head -30; echo "=== suspicious waters ==="; sed -n '/Water molecules with mFo-DFc peaks/,/SUMMARY/p' fph_r4.log
```

```bash
cd /tmp/agent_r5_7tvl && python3 -c "<peak-environment analysis: for each of the 6 strongest mFo-DFc peaks in peaks_holes.pdb, list all r4_001.pdb atoms within 4 A using symmetry-aware gemmi.NeighborSearch>"
```

```bash
cd /tmp/agent_r5_7tvl && python3 -c "<water occupancy/B histogram over r4_001.pdb>"
```

**[REFINE 5/6]**
```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && nohup $P/phenix.refine r4_001.pdb /tmp/nc_round1_cache/7tvl.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True refinement.main.occupancy_min=0.02 refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.ordered_solvent.primary_map_cutoff=2.8 refinement.ordered_solvent.secondary_map_and_map_cc_filter.poor_cc_threshold=0.5 refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.hydrogens.refine=riding refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=4 output.prefix=r5 output.serial=1 --overwrite > r5.log 2>&1 &
echo "launched pid $!"; sleep 420; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r5.log | tail -3; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r5.log | tail -6
```

```bash
sleep 600; pgrep -f 'output.prefix=r5' >/dev/null && echo RUNNING || echo FINISHED; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r5.log | tail -3; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r5.log | tail -5; grep -E 'Final R-work' /tmp/agent_r5_7tvl/r5.log
```
(timed out at 10 min)

```bash
pgrep -f 'output.prefix=r5' >/dev/null && echo RUNNING || echo FINISHED; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r5.log | tail -3; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r5.log | tail -5; grep -E 'Final R-work' /tmp/agent_r5_7tvl/r5.log
```

```bash
sleep 480; pgrep -f 'output.prefix=r5' >/dev/null && echo RUNNING || echo FINISHED; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r5.log; grep -nE 'Traceback' /tmp/agent_r5_7tvl/r5.log | tail -2; ls -la /tmp/agent_r5_7tvl/r5_001.pdb 2>&1
```

```bash
sleep 400; pgrep -f 'output.prefix=r5' >/dev/null && echo RUNNING || echo FINISHED; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r5.log; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r5.log | tail -4; ls -la /tmp/agent_r5_7tvl/r5_001.pdb 2>&1
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.molprobity r5_001.pdb output.prefix=mp_r5 > mp_r5_run.log 2>&1; sed -n '/=== Summary ===/,$p' mp_r5.out | head -18
```

```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.find_peaks_holes r5_001.pdb r5_001.mtz map_type="mFo-DFc" > fph_r5.log 2>&1; sed -n '/SUMMARY OF MAP PEAKS/,$p' fph_r5.log
```

**[REFINE 6/6]**
```bash
cd /tmp/agent_r5_7tvl && P=/Users/marcin/phenix-2.0-5936/phenix_bin && nohup $P/phenix.refine r5_001.pdb /tmp/nc_round1_cache/7tvl.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=8 refinement.main.ordered_solvent=True refinement.main.occupancy_min=0.02 refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.ordered_solvent.primary_map_cutoff=2.8 refinement.ordered_solvent.secondary_map_and_map_cc_filter.poor_cc_threshold=0.5 refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.hydrogens.refine=riding refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=4 output.prefix=r6 output.serial=1 --overwrite > r6.log 2>&1 &
echo "launched pid $!"; mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TVL && echo "deliverables dir ready"
```

## Phase 5 — run 6 outcome, final selection and verification

```bash
sleep 900; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r6.log | tail -3; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r6.log | tail -4
```
(timed out at 10 min)

```bash
grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r6.log | tail -3; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r6.log | tail -4; pgrep -f 'output.prefix=r6' >/dev/null && echo RUNNING || echo FINISHED
```

```bash
sleep 700; grep -nE 'MACRO_CYCLE|Traceback' /tmp/agent_r5_7tvl/r6.log | tail -2; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r6.log; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r6.log | tail -4; pgrep -f 'output.prefix=r6' >/dev/null && echo RUNNING || echo FINISHED
```
(timed out at 10 min)

```bash
grep -nE 'MACRO_CYCLE' /tmp/agent_r5_7tvl/r6.log | tail -2; grep -E 'Start R-work|Final R-work' /tmp/agent_r5_7tvl/r6.log; grep -E 'n_water=|^r_work=' /tmp/agent_r5_7tvl/r6.log | tail -4; pgrep -f 'output.prefix=r6' >/dev/null && echo RUNNING || echo FINISHED
```

```bash
tail -30 /tmp/agent_r5_7tvl/r6.log; echo "=== exit indicators ==="; grep -nE 'Traceback|Sorry|Error|Killed|MemoryError' /tmp/agent_r5_7tvl/r6.log | tail -10; echo "=== outputs ==="; ls -la /tmp/agent_r5_7tvl/r6_00*.pdb 2>&1
```
(run 6 killed mid macro-cycle 5 with no traceback and no output model; 15 concurrent
phenix_refine processes from other agents were running on the shared machine)

```bash
ls -la /tmp/agent_r5_7tvl/r6* 2>&1 | head; echo "=== memory pressure ==="; vm_stat | head -5; echo "=== other phenix jobs ==="; pgrep -fl phenix_refine | wc -l
```

```bash
cd /tmp/agent_r5_7tvl && echo "atoms: $(grep -cE '^(ATOM|HETATM)' r5_001.pdb)"; echo "anisou: $(grep -c '^ANISOU' r5_001.pdb)"; echo "H: $(awk '/^(ATOM|HETATM)/ && substr($0,77,2)==" H"' r5_001.pdb | wc -l)"; echo "HOH: $(awk '/^(ATOM|HETATM)/ && substr($0,18,3)=="HOH"' r5_001.pdb | wc -l)"; echo "chains: $(awk '/^(ATOM|HETATM)/' r5_001.pdb | cut -c22 | sort -u | tr -d '\n')"; tail -3 r5_001.pdb; echo "=== END record present? ==="; grep -c '^END' r5_001.pdb
```

```bash
cd /tmp/agent_r5_7tvl && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TVL && cp r5_001.pdb $D/final.pdb && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.model_vs_data $D/final.pdb /tmp/nc_round1_cache/7tvl.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > mvd_final.log 2>&1; grep -E 'r_work|r_free|flag value|Number of F-obs' mvd_final.log | head
```

```bash
cd /tmp/agent_r5_7tvl && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TVL && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.molprobity $D/final.pdb output.prefix=mp_final > mp_final_run.log 2>&1; sed -n '/=== Summary ===/,$p' mp_final.out | head -18; echo "=== delivered file ==="; ls -la $D/
```

---

## Refinement-invocation ledger

| # | prefix | counted | outcome |
|---|---|---|---|
| — | `r2` (1st launch) | **no** | `ValueError` in `occupancy_selections`, during *Extract refinement strategy and selections* — before any refinement step executed |
| 1 | `r1` | yes | completed, 3 macro-cycles, 0.1223 / 0.1311 |
| 2 | `r2` (2nd launch) | yes | `CCTBX_ASSERT(f.use_u_iso())` in ordered-solvent new-water ADP refinement, during macro-cycle 2; macro-cycle 1 had completed, so it refined. No output model |
| 3 | `r3` | yes | completed, 8 macro-cycles, 0.1054 / 0.1138 |
| 4 | `r4` | yes | completed, 5 macro-cycles, 0.1001 / 0.1100 |
| 5 | `r5` | yes | completed, 6 macro-cycles, **0.0978 / 0.1083 → final.pdb** |
| 6 | `r6` | yes | killed externally during macro-cycle 5 occupancy refinement; no traceback, no output model |

Six counted `phenix.refine` invocations — exactly the budget.

Non-refinement tools used (no refinement performed, not counted): `gemmi mtz --dump`,
`phenix.model_vs_data`, `phenix.molprobity`, `phenix.find_peaks_holes`,
`phenix.ready_set`, `phenix.refine --show-defaults`, and `python3` with `gemmi` for
inspection only.

## Compliance note

No network access of any kind was attempted (no `curl`, `wget`, or `phenix.fetch_pdb`).
No file under this repository's `ref/` or `data/` trees was read. No `*_mask.json` or
`*_validation.xml` was read. The only file read from `/tmp/nc_round1_cache/` was
`7tvl.mtz`; it remained present for the whole session, so no recovery from a refinement
output MTZ was needed.
