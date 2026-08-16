# 9TXE blinded agentic recovery — verbatim shell transcript

Every shell command executed, in execution order. Commands were issued from the session's
working directory; each refinement/analysis command sets its own `cd` explicitly.
Refinement-program invocations are marked **[REFINE n/6]**. There were no failed or
aborted refinement launches — all six ran to completion.

No network command (curl, wget, phenix.fetch_pdb, git fetch, …) appears anywhere below.
No command reads this repository's `ref/` or `data/` trees, any `*_mask.json`, any
`*_validation.xml`, or any file under `/tmp/nc_round1_cache/`.

---

### 1 — attempt to open the named inputs (MTZ already reaped)

```bash
mkdir -p /tmp/agent_r5_9txe && cd /tmp/agent_r5_9txe && ls -la /tmp/nc_round1_work/r4p_9txe.pdb /tmp/nc_round1_cache/9txe.mtz && /opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/9txe.mtz 2>&1 | head -60
```
→ exit 1: `ls: /tmp/nc_round1_cache/9txe.mtz: No such file or directory`. The `gemmi mtz
--dump` never executed (shell `&&` short-circuit), so no cache file was ever opened.

### 2 — establish what survives (directory listings only, no file contents read)

```bash
ls -la /tmp/nc_round1_cache/ 2>&1 | head -40; echo "=== work ==="; ls -la /tmp/nc_round1_work/ 2>&1 | head -60
```

### 3 — locate 9txe-related artifacts

```bash
ls -la /tmp/nc_round1_cache/ | grep -i 9txe; echo "=== work 9txe ==="; ls -la /tmp/nc_round1_work/ | grep -i 9txe
```

### 4 — inspect the recovery-source MTZ header (column labels + provenance)

```bash
cd /tmp/agent_r5_9txe && /opt/homebrew/bin/gemmi mtz -d --headers /tmp/nc_round1_work/r4r_r4p_9txe_001.mtz 2>&1 | head -70
```

### 5 — inspect the perturbed model's composition

```bash
cd /tmp/agent_r5_9txe && grep -c ATOM /tmp/nc_round1_work/r4p_9txe.pdb; echo "--- HETATM/water counts ---"; grep '^HETATM' /tmp/nc_round1_work/r4p_9txe.pdb | awk '{print $4}' | sort | uniq -c | sort -rn | head -20; echo "--- header ---"; grep -E '^(CRYST1|REMARK   2|REMARK   3   RESOL|SCALE|EXPDTA|TITLE)' /tmp/nc_round1_work/r4p_9txe.pdb | head -20; echo "--- chains/altloc ---"; grep '^ATOM' /tmp/nc_round1_work/r4p_9txe.pdb | cut -c22 | sort | uniq -c; grep '^ATOM' /tmp/nc_round1_work/r4p_9txe.pdb | cut -c17 | sort | uniq -c
```

### 6 — strip the recovered MTZ to observations + free flags only

```bash
cd /tmp/agent_r5_9txe && cat > strip.py <<'EOF'
from iotbx.reflection_file_reader import any_reflection_file
from iotbx import mtz
rf = any_reflection_file("/tmp/nc_round1_work/r4r_r4p_9txe_001.mtz")
fobs = None; free = None
for ma in rf.as_miller_arrays(merge_equivalents=False):
    lab = ma.info().labels
    if lab[:2] == ["F-obs","SIGF-obs"]:
        fobs = ma
    if lab == ["R-free-flags"]:
        free = ma
print("FOBS:", fobs.info().labels, fobs.size(), fobs.d_max_min())
print("FREE:", free.info().labels, free.size(), "n_free=", (free.data()==1).count(True))
print("space group:", fobs.space_group_info(), "cell:", fobs.unit_cell())
print("anomalous:", fobs.anomalous_flag())
mo = fobs.as_mtz_dataset(column_root_label="FOBS", column_types="FQ")
mo.add_miller_array(free, column_root_label="FreeR_flag")
mo.mtz_object().write("/tmp/agent_r5_9txe/9txe_obs.mtz")
print("wrote stripped mtz")
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python strip.py 2>&1 | tail -20
```

### 7 — verify the free-flag convention (which value is the test set?)

```bash
cd /tmp/agent_r5_9txe && cat > checkfree.py <<'EOF'
from iotbx.reflection_file_reader import any_reflection_file
from cctbx.array_family import flex
rf = any_reflection_file("/tmp/agent_r5_9txe/9txe_obs.mtz")
arrs = {tuple(a.info().labels): a for a in rf.as_miller_arrays()}
for k in arrs: print("label:", k)
fobs = [a for a in rf.as_miller_arrays() if a.info().labels[0]=="FOBS"][0]
free = [a for a in rf.as_miller_arrays() if "FreeR_flag" in a.info().labels[0]][0]
f, fr = fobs.common_sets(free)
d = fr.data()
vals = sorted(set(d))
print("common refl:", f.size())
for v in vals:
    n = (d==v).count(True)
    print("  value %d : %d  (%.2f%%)" % (v, n, 100.0*n/f.size()))
print("d_max_min:", f.d_max_min())
print("completeness:", f.completeness())
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python checkfree.py 2>&1 | tail -20
```

### 8 — check hydrogens, elements, B-factors, ANISOU in the perturbed model

```bash
cd /tmp/agent_r5_9txe && grep -c ' H ' /tmp/nc_round1_work/r4p_9txe.pdb; echo "--- element col ---"; grep -E '^(ATOM|HETATM)' /tmp/nc_round1_work/r4p_9txe.pdb | cut -c77-78 | sort | uniq -c; echo "--- residue range ---"; grep '^ATOM' /tmp/nc_round1_work/r4p_9txe.pdb | cut -c23-26 | sort -n | uniq | head -3; grep '^ATOM' /tmp/nc_round1_work/r4p_9txe.pdb | cut -c23-26 | sort -n | uniq | tail -3; echo "--- B factor stats ---"; grep -E '^(ATOM|HETATM)' /tmp/nc_round1_work/r4p_9txe.pdb | cut -c61-66 | awk '{s+=$1; if($1<mn||NR==1)mn=$1; if($1>mx)mx=$1; n++} END{printf "mean %.2f min %.2f max %.2f n %d\n", s/n, mn, mx, n}'; echo "--- ANISOU? ---"; grep -c '^ANISOU' /tmp/nc_round1_work/r4p_9txe.pdb
```

### 9 — baseline fit of the perturbed model

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_9txe.pdb /tmp/agent_r5_9txe/9txe_obs.mtz f_obs_label=FOBS r_free_flags_label=FreeR_flag > mvd_start.log 2>&1; tail -40 mvd_start.log
```

### 10 — baseline geometry of the perturbed model

```bash
cd /tmp/agent_r5_9txe && cat > geostat.py <<'EOF'
import mmtbx.model, iotbx.pdb
from libtbx.utils import null_out
pdb_inp = iotbx.pdb.input("/tmp/nc_round1_work/r4p_9txe.pdb")
m = mmtbx.model.manager(model_input=pdb_inp, log=null_out())
m.process(make_restraints=True)
gs = m.geometry_statistics()
gs.show()
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | tail -30
```

### 11 — top of the same geometry report

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -35
```

### 12 — add riding hydrogens and metal links

```bash
cd /tmp/agent_r5_9txe && cp /tmp/nc_round1_work/r4p_9txe.pdb ./start.pdb && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ready_set start.pdb > readyset.log 2>&1; echo "exit=$?"; tail -25 readyset.log; ls -la /tmp/agent_r5_9txe/
```

### 13 — verify H addition, ANISOU retention, Fe–Cys links

```bash
cd /tmp/agent_r5_9txe && grep -cE '^(ATOM|HETATM)' start.updated.pdb; grep -E '^(ATOM|HETATM)' start.updated.pdb | cut -c77-78 | sort | uniq -c; echo "ANISOU: $(grep -c '^ANISOU' start.updated.pdb)"; echo "LINK/edits:"; grep -E '^LINK' start.updated.pdb | head
```

### 14 — **[REFINE 1/6]** coordinates + anisotropic ADPs, no solvent changes

```bash
cd /tmp/agent_r5_9txe && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start.updated.pdb 9txe_obs.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=FreeR_flag" xray_data.r_free_flags.test_flag_value=0 refinement.main.target=ml main.use_experimental_phases=False strategy=individual_sites+individual_adp+occupancies main.number_of_macro_cycles=8 adp.individual.anisotropic="not element H" hydrogens.refine=riding ordered_solvent=False main.nproc=4 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1 &
echo "PID=$!"; sleep 60; tail -5 /tmp/agent_r5_9txe/r1.log
```

### 15 — wait for run 1

```bash
cd /tmp/agent_r5_9txe && for i in $(seq 1 30); do if ! kill -0 8662 2>/dev/null; then echo "DONE after ~$((i*30))s"; break; fi; sleep 30; done; grep -E '^ *(Start|Final) R-|r_work=' r1.log | tail -6; echo "---"; ls -la r1_001*
```

### 16 — geometry after run 1

```bash
cd /tmp/agent_r5_9txe && sed -i '' 's|/tmp/nc_round1_work/r4p_9txe.pdb|/tmp/agent_r5_9txe/r1_001.pdb|' geostat.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -22; echo "=== waters ==="; grep 'HOH' r1_001.pdb | grep -c '^HETATM'
```

### 17 — **[REFINE 2/6]** add ordered-solvent rebuilding

```bash
cd /tmp/agent_r5_9txe && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb 9txe_obs.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=FreeR_flag" xray_data.r_free_flags.test_flag_value=0 refinement.main.target=ml main.use_experimental_phases=False strategy=individual_sites+individual_adp+occupancies main.number_of_macro_cycles=8 adp.individual.anisotropic="not element H" hydrogens.refine=riding main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle main.nproc=4 output.prefix=r2 output.serial=1 --overwrite > r2.log 2>&1 &
echo "PID=$!"
```

### 18 — wait for run 2

```bash
cd /tmp/agent_r5_9txe && for i in $(seq 1 40); do if ! kill -0 12822 2>/dev/null; then echo "DONE"; break; fi; sleep 30; done; grep -E 'Start R-work|Final R-work' r2.log; echo "waters: $(grep 'HOH' r2_001.pdb | grep -c '^HETATM')"
```

### 19 — geometry after run 2

```bash
cd /tmp/agent_r5_9txe && sed -i '' 's|r1_001.pdb|r2_001.pdb|' geostat.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -20; echo "=== water O count ==="; awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r2_001.pdb | wc -l
```

### 20 — **[REFINE 3/6]** weight optimisation

```bash
cd /tmp/agent_r5_9txe && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb 9txe_obs.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=FreeR_flag" xray_data.r_free_flags.test_flag_value=0 refinement.main.target=ml main.use_experimental_phases=False strategy=individual_sites+individual_adp+occupancies main.number_of_macro_cycles=8 adp.individual.anisotropic="not element H" hydrogens.refine=riding main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True main.nproc=4 output.prefix=r3 output.serial=1 --overwrite > r3.log 2>&1 &
echo "PID=$!"
```

### 21 — wait for run 3 (this poll hit the 600 s tool timeout and was backgrounded)

```bash
cd /tmp/agent_r5_9txe && for i in $(seq 1 90); do if ! kill -0 23000 2>/dev/null; then echo "DONE"; break; fi; sleep 30; done; grep -E 'Start R-work|Final R-work' r3.log; echo "waters: $(awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r3_001.pdb | wc -l)"
```

### 22 — re-poll run 3

```bash
sleep 420; cd /tmp/agent_r5_9txe && grep -E 'Start R-work|Final R-work' r3.log; grep -cE 'macro_cycle' r3.log; tail -3 r3.log; kill -0 23000 2>/dev/null && echo "STILL RUNNING" || echo "FINISHED"
```

### 23 — geometry, waters and chosen weights after run 3

```bash
cd /tmp/agent_r5_9txe && sed -i '' 's|r2_001.pdb|r3_001.pdb|' geostat.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -20; echo "=== waters ==="; awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r3_001.pdb | wc -l; echo "=== optimized weights ==="; grep -E 'wxc |wxu |Best.*weight|optimal' r3.log | tail -8
```

### 24 — enumerate the clashes introduced in run 3

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r3_001.pdb keep_hydrogens=True verbose=True > clash_r3.log 2>&1; head -30 clash_r3.log; echo "=== HOH-HOH clash fraction ==="; grep -c 'HOH' clash_r3.log; grep -E '^ *:' clash_r3.log | wc -l
```

### 25 — the clash list itself

```bash
cd /tmp/agent_r5_9txe && grep -A40 'Bad Clashes' clash_r3.log | head -45; echo "=== score line ==="; grep -i 'clashscore' clash_r3.log | tail -3
```

### 26–28 — look up the relevant phenix.refine parameter names

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | grep -E 'min_solv_solv_dist|min_model_peak_dist|max_model_peak_dist|primary_map_cutoff|secondary_map_cutoff|bond_rmsd|weight_selection_criteria|max_deviation' | head -20
```

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | grep -A8 'weight_selection_criteria {'; echo "=== solvent block ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | grep -B3 -A24 '^  ordered_solvent {' | head -40
```

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | sed -n '/^  ordered_solvent {/,/^  }/p' | tail -30
```

### 29 — remove the four clashing waters

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools r3_001.pdb remove="resname HOH and ((chain S and resseq 1070) or (chain S and resseq 824) or (chain S and resseq 1066) or (chain A and resseq 215))" output.file_name=r3_trim.pdb > pdbtools.log 2>&1; echo "exit=$?"; echo "waters before: $(awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r3_001.pdb | wc -l)  after: $(awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r3_trim.pdb | wc -l)"
```

### 30 — **[REFINE 4/6]** stricter solvent distance + bond-RMSD ceiling on weight selection

```bash
cd /tmp/agent_r5_9txe && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_trim.pdb 9txe_obs.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=FreeR_flag" xray_data.r_free_flags.test_flag_value=0 refinement.main.target=ml main.use_experimental_phases=False strategy=individual_sites+individual_adp+occupancies main.number_of_macro_cycles=8 adp.individual.anisotropic="not element H" hydrogens.refine=riding main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle ordered_solvent.dist_min=2.4 target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True target_weights.weight_selection_criteria.bonds_rmsd=0.013 main.nproc=4 output.prefix=r4 output.serial=1 --overwrite > r4.log 2>&1 &
echo "PID=$!"
```

### 31–32 — poll run 4

```bash
sleep 540; cd /tmp/agent_r5_9txe && kill -0 44364 2>/dev/null && echo "STILL RUNNING" || echo "FINISHED"; grep -E 'Start R-work|Final R-work' r4.log
```

```bash
sleep 480; cd /tmp/agent_r5_9txe && kill -0 44364 2>/dev/null && echo "STILL RUNNING" || echo "FINISHED"; grep -E 'Start R-work|Final R-work' r4.log; tail -2 r4.log
```

### 33 — geometry after run 4

```bash
cd /tmp/agent_r5_9txe && sed -i '' 's|r3_001.pdb|r4_001.pdb|' geostat.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -20; echo "=== waters ==="; awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r4_001.pdb | wc -l
```

### 34 — clashes after run 4, and confirm the bond-RMSD criterion was passed through

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r4_001.pdb keep_hydrogens=True verbose=True > clash_r4.log 2>&1; grep -A30 'Bad Clashes' clash_r4.log | head -20; grep -i '^clashscore' clash_r4.log; echo "=== was bond_rmsd criterion used? ==="; grep -iE 'bonds_rmsd|weight_selection|rejected' r4.log | head -5
```

### 35 — remove re-picked spurious waters, then **[REFINE 5/6]** filter-only solvent

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools r4_001.pdb remove="resname HOH and chain S and (resseq 1335 or resseq 1278 or resseq 1104)" output.file_name=r4_trim.pdb > pdbtools2.log 2>&1; echo "exit=$?"; awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r4_trim.pdb | wc -l
nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_trim.pdb 9txe_obs.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=FreeR_flag" xray_data.r_free_flags.test_flag_value=0 refinement.main.target=ml main.use_experimental_phases=False strategy=individual_sites+individual_adp+occupancies main.number_of_macro_cycles=8 adp.individual.anisotropic="not element H" hydrogens.refine=riding main.ordered_solvent=True ordered_solvent.mode=filter_only target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True main.nproc=4 output.prefix=r5 output.serial=1 --overwrite > r5.log 2>&1 &
echo "PID=$!"
```

### 36–37 — poll run 5

```bash
sleep 560; cd /tmp/agent_r5_9txe && kill -0 71110 2>/dev/null && echo "STILL RUNNING" || echo "FINISHED"; grep -E 'Start R-work|Final R-work' r5.log
```

```bash
sleep 420; cd /tmp/agent_r5_9txe && kill -0 71110 2>/dev/null && echo "STILL RUNNING" || echo "FINISHED"; grep -E 'Start R-work|Final R-work' r5.log; tail -2 r5.log
```

### 38 — geometry, waters and clashes after run 5

```bash
cd /tmp/agent_r5_9txe && sed -i '' 's|r4_001.pdb|r5_001.pdb|' geostat.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -20; echo "=== waters ==="; awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r5_001.pdb | wc -l; echo "=== clashes ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r5_001.pdb keep_hydrogens=True verbose=True 2>/dev/null | grep -A15 'Bad Clashes' | head -12
```

### 39–41 — residual difference density

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r5_001.pdb r5_001.mtz map_type="mFo-DFc" peak_search.min_cross_distance=1.5 > peaks.log 2>&1; echo "exit=$?"; grep -E 'peaks|holes' peaks.log | head -8; echo "=== top peaks ==="; sed -n '/Peaks:/,/Holes:/p' peaks.log | head -18; echo "=== top holes ==="; sed -n '/Holes:/,$p' peaks.log | head -10
```

```bash
cd /tmp/agent_r5_9txe && grep -B2 -A25 'Water molecules with mFo-DFc peaks' peaks.log | head -35; echo "=== strongest peaks (sigma) ==="; awk '$NF+0>5.0' peaks_holes.pdb 2>/dev/null | head; grep -E 'peak.*sigma|Maximum|max ' peaks.log | head -10
```

```bash
cd /tmp/agent_r5_9txe && head -3 peaks_holes.pdb; grep -E '^(ATOM|HETATM)' peaks_holes.pdb | sort -k11 -rn 2>/dev/null | head -5; echo "=== by occupancy/B col ==="; awk '/^HETATM|^ATOM/{print substr($0,55,12), substr($0,18,10)}' peaks_holes.pdb | sort -k2 -rn | head -6
```

### 42 — identify what sits next to the strongest peaks

```bash
cd /tmp/agent_r5_9txe && cat > nearpeak.py <<'EOF'
import iotbx.pdb
from scitbx.array_family import flex
m = iotbx.pdb.input("r5_001.pdb").construct_hierarchy()
xrs = iotbx.pdb.input("r5_001.pdb").xray_structure_simple()
sites = xrs.sites_cart(); atoms = list(m.atoms())
pk = iotbx.pdb.input("peaks_holes.pdb").construct_hierarchy()
uc = xrs.unit_cell(); sg = xrs.space_group()
import cctbx.crystal
sst = xrs.special_position_settings()
asu = sst.asu_mappings(buffer_thickness=5.0)
for i, a in enumerate(pk.atoms()):
    if i >= 6: break
    p = a.xyz; sig = a.b
    best = None
    for j, s in enumerate(sites):
        d = uc.min_distance_sym_equiv(uc.fractionalize(p), uc.fractionalize(s)) if False else None
    # simple: use direct + symmetry via min_mod_short
    import math
    dists = []
    fp = uc.fractionalize(p)
    for j, s in enumerate(sites):
        fs = uc.fractionalize(s)
        dmin = 1e9
        for op in sg.all_ops():
            fsym = op * fs
            dd = [fp[k]-fsym[k] for k in range(3)]
            dd = [x - round(x) for x in dd]
            dist = uc.length(dd)
            if dist < dmin: dmin = dist
        dists.append((dmin, j))
    dists.sort()
    lab = []
    for dmin, j in dists[:3]:
        at = atoms[j]
        lab.append("%s %s%s %s (%.2fA)" % (at.parent().parent().parent().id.strip(), at.parent().resname.strip(), at.parent().parent().resseq.strip(), at.name.strip(), dmin))
    print("peak %d  %.2f sigma -> %s" % (i+1, sig, "; ".join(lab)))
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python nearpeak.py 2>&1 | tail -10
```

### 43 — confirm the C-terminal OXT is missing

```bash
cd /tmp/agent_r5_9txe && grep -E 'LEU A  95' r5_001.pdb | grep '^ATOM' | cut -c13-27 | tr '\n' ' '; echo; echo "OXT present: $(grep -c ' OXT ' r5_001.pdb)"
```

### 44 — add OXT at sp2 carboxylate geometry

```bash
cd /tmp/agent_r5_9txe && cat > addoxt.py <<'EOF'
import iotbx.pdb
from scitbx import matrix
pdb_in = iotbx.pdb.input("r5_001.pdb")
h = pdb_in.construct_hierarchy()
h.atoms().reset_serial()
for rg in h.residue_groups():
    for ag in rg.atom_groups():
        if ag.resname.strip()=="LEU" and rg.resseq.strip()=="95":
            d = {a.name.strip(): matrix.col(a.xyz) for a in ag.atoms()}
            if "OXT" in d: print("already present"); raise SystemExit
            C, O, CA = d["C"], d["O"], d["CA"]
            v1 = (O - C).normalize(); v2 = (CA - C).normalize()
            direction = -(v1 + v2).normalize()
            oxt_xyz = C + direction * 1.251
            proto = [a for a in ag.atoms() if a.name.strip()=="O"][0]
            new = proto.detached_copy()
            new.name = " OXT"; new.xyz = tuple(oxt_xyz); new.element = " O"
            new.uij = (-1,-1,-1,-1,-1,-1); new.set_b(proto.b); new.occ = 1.0
            ag.append_atom(new)
            print("added OXT at %.3f %.3f %.3f  (C-OXT %.3f A)" % (oxt_xyz[0],oxt_xyz[1],oxt_xyz[2],(oxt_xyz-C).length()))
h.atoms().reset_serial()
h.write_pdb_file("r5_oxt.pdb", crystal_symmetry=pdb_in.crystal_symmetry())
print("wrote r5_oxt.pdb")
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python addoxt.py 2>&1 | tail -5
```

### 45 — **[REFINE 6/6]** final refinement, water picking re-enabled

```bash
cd /tmp/agent_r5_9txe && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r5_oxt.pdb 9txe_obs.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=FreeR_flag" xray_data.r_free_flags.test_flag_value=0 refinement.main.target=ml main.use_experimental_phases=False strategy=individual_sites+individual_adp+occupancies main.number_of_macro_cycles=8 adp.individual.anisotropic="not element H" hydrogens.refine=riding main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle ordered_solvent.dist_min=2.2 target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True main.nproc=4 output.prefix=r6 output.serial=1 --overwrite > r6.log 2>&1 &
echo "PID=$!"
```

### 46–47 — poll run 6

```bash
sleep 570; cd /tmp/agent_r5_9txe && kill -0 93318 2>/dev/null && echo "STILL RUNNING" || echo "FINISHED"; grep -E 'Start R-work|Final R-work' r6.log
```

```bash
sleep 540; cd /tmp/agent_r5_9txe && kill -0 93318 2>/dev/null && echo "STILL RUNNING" || echo "FINISHED"; grep -E 'Start R-work|Final R-work' r6.log; tail -2 r6.log
```

### 48 — geometry, waters and clashes after run 6

```bash
cd /tmp/agent_r5_9txe && sed -i '' 's|r5_001.pdb|r6_001.pdb|' geostat.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -20; echo "=== waters ==="; awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r6_001.pdb | wc -l; echo "=== clashes ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r6_001.pdb keep_hydrogens=True verbose=True 2>/dev/null | grep -A15 'Bad Clashes' | head -14
```

### 49 — trim run 6's spurious waters and re-measure (model edit, not refinement)

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools r6_001.pdb remove="resname HOH and chain S and (resseq 1611 or resseq 1554 or resseq 1328 or resseq 1316 or resseq 1357)" output.file_name=r6_trim.pdb > pdbtools3.log 2>&1; echo "exit=$?"; awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' r6_trim.pdb | wc -l; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r6_trim.pdb 9txe_obs.mtz f_obs_label=FOBS r_free_flags_label=FreeR_flag > mvd_r6trim.log 2>&1; grep -E '^  r_work|^  r_free' mvd_r6trim.log; echo "=== clashscore ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r6_trim.pdb keep_hydrogens=True 2>/dev/null | grep -i '^clashscore'
```

### 50 — head-to-head comparison of the three candidates

```bash
cd /tmp/agent_r5_9txe && for f in r5_001 r5_oxt r6_trim; do /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $f.pdb 9txe_obs.mtz f_obs_label=FOBS r_free_flags_label=FreeR_flag > mvd_$f.log 2>&1; cs=$(/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore $f.pdb keep_hydrogens=True 2>/dev/null | grep -i '^clashscore' | awk '{print $3}'); rw=$(grep -E '^  r_work' mvd_$f.log | head -1 | awk '{print $2}'); rf=$(grep -E '^  r_free' mvd_$f.log | head -1 | awk '{print $2}'); nw=$(awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' $f.pdb | wc -l); echo "$f  R-work=$rw  R-free=$rf  clashscore=$cs  waters=$nw"; done
```

### 51 — compare my geometric OXT placement against the refined one

```bash
cd /tmp/agent_r5_9txe && echo "refined (r6):"; grep ' OXT ' r6_001.pdb | grep '^ATOM'; echo "my placement (r5_oxt):"; grep ' OXT ' r5_oxt.pdb | grep '^ATOM'
```

### 52 — build the final model (run 5 + refined OXT) and measure it

```bash
cd /tmp/agent_r5_9txe && cat > finalize.py <<'EOF'
import iotbx.pdb
from scitbx import matrix
pdb_in = iotbx.pdb.input("r5_001.pdb")
h = pdb_in.construct_hierarchy()
ref = iotbx.pdb.input("r6_001.pdb").construct_hierarchy()
oxt_ref = [a for a in ref.atoms() if a.name.strip()=="OXT"][0]
for rg in h.residue_groups():
    for ag in rg.atom_groups():
        if ag.resname.strip()=="LEU" and rg.resseq.strip()=="95":
            proto = [a for a in ag.atoms() if a.name.strip()=="O"][0]
            new = proto.detached_copy()
            new.name=" OXT"; new.xyz=oxt_ref.xyz; new.element=" O"
            new.uij=(-1,-1,-1,-1,-1,-1); new.set_b(oxt_ref.b); new.occ=1.0
            ag.append_atom(new)
            print("grafted refined OXT, B=%.2f" % oxt_ref.b)
h.atoms().reset_serial()
h.write_pdb_file("final_candidate.pdb", crystal_symmetry=pdb_in.crystal_symmetry())
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python finalize.py 2>&1 | tail -3
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data final_candidate.pdb 9txe_obs.mtz f_obs_label=FOBS r_free_flags_label=FreeR_flag > mvd_final.log 2>&1; grep -E '^  r_work|^  r_free' mvd_final.log | head -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore final_candidate.pdb keep_hydrogens=True 2>/dev/null | grep -i '^clashscore'
```

### 53 — full validation of the final model (independent oracles)

```bash
cd /tmp/agent_r5_9txe && sed -i '' 's|r6_001.pdb|final_candidate.pdb|' geostat.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | head -28; echo "=== independent tools ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze final_candidate.pdb 2>/dev/null | tail -3; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze final_candidate.pdb 2>/dev/null | tail -3
```

### 54 — Rama-Z and metal-coordination geometry of the final model

```bash
cd /tmp/agent_r5_9txe && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | sed -n '/RAMA-Z/,/MAX DEV/p' | head -8; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python geostat.py 2>&1 | grep -A4 'DETAILS OF BONDING'
```

### 55 — create the deliverable directory and copy the final model

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9TXE && cp /tmp/agent_r5_9txe/final_candidate.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9TXE/final.pdb && ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9TXE/ && grep -c '^ATOM\|^HETATM' /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9TXE/final.pdb && head -1 /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9TXE/final.pdb
```

### 56 — verify the delivered file's integrity

```bash
cd /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9TXE && echo "ANISOU: $(grep -c '^ANISOU' final.pdb)"; echo "FES: $(grep -c 'FES' final.pdb)"; echo "waters: $(awk '/^HETATM/ && substr($0,18,3)=="HOH" && substr($0,77,2)==" O"' final.pdb | wc -l)"; echo "H atoms: $(grep -E '^ATOM|^HETATM' final.pdb | cut -c77-78 | grep -c ' H')"; echo "OXT: $(grep -c ' OXT ' final.pdb)"
```
