# 6XVM round-5 recovery — verbatim shell transcript

Every shell command executed, in order. Commands were issued from an agent harness that resets
the working directory between calls, so absolute paths and `sh -c 'cd ... && ...'` wrappers are
used throughout. Heredocs that create helper scripts are reproduced in full.

Refinement invocations are marked **[REFINE n/6]**. The one launch that failed during PHIL
parsing, before refinement, is marked **[NOT COUNTED]**.

---

### 1. Inspect inputs (cache MTZ found missing)

```bash
mkdir -p /tmp/agent_r5_6xvm && cd /tmp/agent_r5_6xvm && ls -la /tmp/nc_round1_work/r4p_6xvm.pdb /tmp/nc_round1_cache/6xvm.mtz
```

```bash
/opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/6xvm.mtz 2>&1 | head -50
```

```bash
ls -la /tmp/nc_round1_cache/ 2>&1 | head -40; echo "---WORK---"; ls -la /tmp/nc_round1_work/ 2>&1 | head -40
```

```bash
find /tmp -maxdepth 3 -iname "*6xvm*" 2>/dev/null | head -50
```

```bash
ls -la /private/tmp/nc_round1_work/ | grep -i 6xvm
```

```bash
ls -la /private/tmp/nc_round1_cache/ | grep -i 6xvm; echo "===other tmp==="; ls -d /private/tmp/agent_r* /private/tmp/*6xvm* /private/tmp/*6XVM* 2>/dev/null
```

```bash
find /private/tmp -maxdepth 2 -iname "*6xvm*mtz" 2>/dev/null | grep -v nc_round1 | head -20; echo "=== agent dir ==="; ls -la /private/tmp/agent_r5_6xvm/
```

### 2. Identify a faithful copy of the observations

```bash
/opt/homebrew/bin/gemmi mtz -H /private/tmp/nc_round1_work/r4r_r4p_6xvm_001.mtz 2>&1 | head -60
```

```bash
grep -n -i -E "labels|file_name|r_free_flags|test_flag_value" /private/tmp/nc_round1_work/r4r_r4p_6xvm_001.eff 2>&1 | head -40
```

```bash
grep -n -i -E "R-free|test set|Free-R|flag|resolution range|Number of|completeness" /private/tmp/nc_round1_work/refine_r4r_r4p_6xvm.log 2>&1 | head -40
```

```bash
cat > /tmp/agent_r5_6xvm/list_arrays.py <<'EOF'
from iotbx.reflection_file_reader import any_reflection_file
f = any_reflection_file("/private/tmp/nc_round1_work/r4r_r4p_6xvm_001.mtz")
for ma in f.as_miller_arrays():
    print(ma.info().label_string(), "|", ma.size(), "| anom:", ma.anomalous_flag(),
          "| type:", type(ma.data()).__name__, "| d_range:", ma.d_max_min())
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python /tmp/agent_r5_6xvm/list_arrays.py 2>&1 | head -30
```

### 3. Profile the perturbed model

```bash
grep -c "^ANISOU" /private/tmp/nc_round1_work/r4p_6xvm.pdb; echo "--- atom counts ---"; grep -c "^ATOM\|^HETATM" /private/tmp/nc_round1_work/r4p_6xvm.pdb; echo "--- waters ---"; grep "HOH" /private/tmp/nc_round1_work/r4p_6xvm.pdb | grep -c "^ATOM\|^HETATM"; echo "--- header ---"; grep -E "^CRYST1|^REMARK   3   RESOLUTION|^HEADER|^TITLE|^EXPDTA" /private/tmp/nc_round1_work/r4p_6xvm.pdb | head; echo "--- altlocs ---"; awk '/^ATOM|^HETATM/ {print substr($0,17,1)}' /private/tmp/nc_round1_work/r4p_6xvm.pdb | sort | uniq -c
```

```bash
cd /tmp/agent_r5_6xvm && awk '/^ATOM|^HETATM/ {ser=substr($0,7,5); name=substr($0,13,4); res=substr($0,18,3); ch=substr($0,22,1); key=ch" "res; iso[key]++; last=key} /^ANISOU/ {ser=substr($0,7,5); res=substr($0,18,3); ch=substr($0,22,1); key=ch" "res; ani[key]++} END {for (k in iso) printf "%-10s atoms=%d aniso=%d\n", k, iso[k], ani[k]}' /private/tmp/nc_round1_work/r4p_6xvm.pdb | sort | head -40
```

### 4. Recover the observation columns

```bash
cat > /tmp/agent_r5_6xvm/recover_data.py <<'EOF'
"""Recover the original FOBS/SIGFOBS/R-free-flags columns from a prior
phenix.refine output MTZ (the cache copy of 6xvm.mtz was deleted by the
/tmp reaper).  We copy ONLY experimental-observation columns; every
model-derived column (F-model, 2FOFCWT, FOFCWT, ANOM, F-obs-filtered)
is discarded so that no prior model can leak into this run."""
import iotbx.mtz
from cctbx.array_family import flex

SRC = "/private/tmp/nc_round1_work/r4r_r4p_6xvm_001.mtz"
DST = "/tmp/agent_r5_6xvm/6xvm_recovered.mtz"

m = iotbx.mtz.object(file_name=SRC)
print("source title:", m.title())
print("space group:", m.space_group_name(), "| n_refl:", m.n_reflections())

cols = {c.label(): c for c in m.columns()}
print("columns:", sorted(cols.keys()))

# Raw column extraction: these are byte-for-byte the values phenix read from
# the original 6xvm.mtz (F-obs / SIGF-obs are the unmodified input, as opposed
# to F-obs-filtered which phenix derived).
sel_f    = cols["F-obs"].selection_valid()
sel_s    = cols["SIGF-obs"].selection_valid()
fp_plus  = cols["R-free-flags(+)"]
fp_minus = cols["R-free-flags(-)"]

# Verify the (+)/(-) free flags agree wherever both are present: they must,
# because phenix expanded ONE original R-free-flags column into a Friedel pair.
vp, vm = fp_plus.selection_valid(), fp_minus.selection_valid()
both = vp & vm
ap = fp_plus.extract_values().as_double()
am = fp_minus.extract_values().as_double()
disagree = (ap.select(both) != am.select(both)).count(True)
print("free-flag rows with both mates: %d | disagreements: %d" % (both.count(True), disagree))
assert disagree == 0, "R-free-flags(+)/(-) disagree -- recovery unsafe"

mi   = m.extract_miller_indices()
fobs = cols["F-obs"].extract_values().as_double()
sigf = cols["SIGF-obs"].extract_values().as_double()
free = ap.set_selected(~vp, am.select(~vp) if (~vp).count(True) else ap.select(~vp))

keep = sel_f & sel_s & (vp | vm)
print("rows kept: %d of %d" % (keep.count(True), m.n_reflections()))

import cctbx.miller, cctbx.crystal
xs = cctbx.crystal.symmetry(
    unit_cell=m.crystals()[0].unit_cell(),
    space_group=m.space_group())
ms = cctbx.miller.set(xs, mi.select(keep), anomalous_flag=False)
famp = ms.array(data=fobs.select(keep), sigmas=sigf.select(keep))
fflg = ms.array(data=free.select(keep).iround())

print("d_max_min:", famp.d_max_min())
print("free flag values:", sorted(set(fflg.data())))
n0 = (fflg.data() == 0).count(True)
print("test set (flag==0): %d  (%.2f%%)" % (n0, 100.0 * n0 / fflg.size()))

mo = famp.as_mtz_dataset(column_root_label="FOBS", column_types="FQ")
mo.add_miller_array(fflg, column_root_label="R-free-flags", column_types="I")
mo.mtz_object().write(DST)
print("wrote", DST)
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python /tmp/agent_r5_6xvm/recover_data.py 2>&1 | tail -25
```

### 5. Validate the recovery by scoring the perturbed model

```bash
cd /tmp/agent_r5_6xvm && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /private/tmp/nc_round1_work/r4p_6xvm.pdb /tmp/agent_r5_6xvm/6xvm_recovered.mtz > /tmp/agent_r5_6xvm/mvd_start.log 2>&1; cat /tmp/agent_r5_6xvm/mvd_start.log
```

### 6. Baseline geometry and ADP state

```bash
cd /tmp/agent_r5_6xvm && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /private/tmp/nc_round1_work/r4p_6xvm.pdb > cs_start.log 2>&1; tail -5 cs_start.log; echo "=== RAMA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /private/tmp/nc_round1_work/r4p_6xvm.pdb 2>&1 | tail -6; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /private/tmp/nc_round1_work/r4p_6xvm.pdb 2>&1 | tail -5
```

```bash
cd /tmp/agent_r5_6xvm && cat > adpstat.py <<'EOF'
import iotbx.pdb
h = iotbx.pdb.input(file_name="/private/tmp/nc_round1_work/r4p_6xvm.pdb").construct_hierarchy()
n_aniso=n_iso=0; bs=[]
from collections import Counter
c=Counter()
for a in h.atoms():
    bs.append(a.b)
    if a.uij_is_defined(): n_aniso+=1; c[a.parent().parent().parent().id+"_aniso"]+=1
    else: n_iso+=1; c[a.parent().parent().parent().id+"_iso"]+=1
import numpy as np
bs=np.array(bs)
print("aniso:",n_aniso,"iso:",n_iso)
print("B: min %.2f max %.2f mean %.2f median %.2f"%(bs.min(),bs.max(),bs.mean(),np.median(bs)))
for k in sorted(c): print("  ",k,c[k])
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python adpstat.py 2>&1 | tail -30
```

### 7. Parameter reconnaissance

```bash
ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -i -E "ready_set|reduce|hydrogen|add_h"
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | grep -n -i -E "hydrogens|ordered_solvent|optimize_.*weight|anisotropic|number_of_macro" | head -30
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | sed -n '125,145p;160,180p;200,220p;370,382p'
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 2>&1 | grep -n -E "^\s*(modify_start_model|hydrogens|ordered_solvent|main) \{|convert_to_anisotropic|switch_to_isotropic_high_res_limit|^\s*refine = |real_space_refine|riding" | head -30
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --attributes-level=2 --show-defaults=1 2>&1 | grep -n -B2 -A6 "switch_to_isotropic_high_res_limit" | head -30
```

### 8. Hydrogen-adding attempts (both outputs verified bad and discarded)

```bash
cd /tmp/agent_r5_6xvm && cp /private/tmp/nc_round1_work/r4p_6xvm.pdb ./start.pdb && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ready_set start.pdb add_h_to_water=False optimise_final_geometry_of_hydrogens=False > ready_set.log 2>&1; echo "exit=$?"; tail -20 ready_set.log; ls -la /tmp/agent_r5_6xvm/
```

```bash
cd /tmp/agent_r5_6xvm && echo "start atoms: $(grep -c '^ATOM\|^HETATM' start.pdb)  aniso: $(grep -c '^ANISOU' start.pdb)"; echo "updated atoms: $(grep -c '^ATOM\|^HETATM' start.updated.pdb)  aniso: $(grep -c '^ANISOU' start.updated.pdb)"; echo "updated H: $(awk '/^ATOM|^HETATM/ {e=substr($0,77,2); gsub(/ /,"",e); if(e=="H") n++} END {print n+0}' start.updated.pdb)"
```

```bash
cd /tmp/agent_r5_6xvm && grep '^ATOM\|^HETATM' start.updated.pdb | head -3 | cat -A | cut -c1-200 | head -5; echo "=== element col tally ==="; awk '/^ATOM|^HETATM/ {print "["substr($0,77,2)"]"}' start.updated.pdb | sort | uniq -c | sort -rn | head
```

```bash
cd /tmp/agent_r5_6xvm && awk '/^ATOM|^HETATM/ {print substr($0,22,1)}' start.updated.pdb | sort | uniq -c; echo "=== orig ==="; awk '/^ATOM|^HETATM/ {print substr($0,22,1)}' start.pdb | sort | uniq -c
```

```bash
cd /tmp/agent_r5_6xvm && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.reduce -BUILD -Quiet start.pdb > reduce_h.pdb 2> reduce.log; echo "exit=$?"; echo "heavy: $(awk '/^ATOM|^HETATM/ {e=substr($0,77,2); gsub(/ /,"",e); if(e!="H" && e!="D") n++} END {print n+0}' reduce_h.pdb)"; echo "H: $(awk '/^ATOM|^HETATM/ {e=substr($0,77,2); gsub(/ /,"",e); if(e=="H") n++} END {print n+0}' reduce_h.pdb)"; echo "aniso: $(grep -c '^ANISOU' reduce_h.pdb)"; tail -3 reduce.log
```

```bash
cd /tmp/agent_r5_6xvm && echo "=== start.pdb element tally ==="; awk '/^ATOM|^HETATM/ {print "["substr($0,77,2)"]"}' start.pdb | sort | uniq -c | sort -rn; echo "=== heavy atoms with ANISOU? ==="; awk '/^ATOM|^HETATM/ {e=substr($0,77,2); gsub(/ /,"",e); if(e!="H"){h++}} /^ANISOU/ {a++} END {print "heavy="h, "anisou="a}' start.pdb
```

```bash
head -25 /private/tmp/nc_round1_work/refine_r4r_r4p_6xvm.log
```

```bash
sysctl -n hw.ncpu; rm -f /tmp/agent_r5_6xvm/start.updated.pdb /tmp/agent_r5_6xvm/reduce_h.pdb /tmp/agent_r5_6xvm/start.eff
```

### 9. Refinement run 1 — first launch rejected **[NOT COUNTED]**

Rejected during PHIL parsing (`Ambiguous parameter definition: nproc = 8`); no refinement ran,
no output written.

```bash
cd /tmp/agent_r5_6xvm && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start.pdb 6xvm_recovered.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" main.number_of_macro_cycles=8 hydrogens.refine=riding nproc=8 output.prefix=r1 --overwrite > r1.log 2>&1 &
echo "launched pid=$!"; sleep 90; grep -n -E "test_flag_value|Test \(free\)|r_work|r_free|Number of test" r1.log | head -20; echo "--- tail ---"; tail -5 r1.log
```

```bash
ls -la /tmp/agent_r5_6xvm/*.log /tmp/agent_r5_6xvm/r1* 2>&1 | head; echo "=== running? ==="; ps aux | grep -c "[p]henix.refine"
```

```bash
cat /tmp/agent_r5_6xvm/r1.log
```

### 10. Refinement run 1 **[REFINE 1/6]** — restore coordinates

```bash
nohup sh -c 'cd /tmp/agent_r5_6xvm && exec /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start.pdb 6xvm_recovered.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" main.number_of_macro_cycles=8 hydrogens.refine=riding main.nproc=4 output.prefix=r1 --overwrite' > /tmp/agent_r5_6xvm/r1.log 2>&1 &
echo "launched pid=$!"; sleep 120; echo "=== size: $(wc -c < /tmp/agent_r5_6xvm/r1.log) ==="; grep -n -E "Test \(free\)|test_flag_value|r_work = |r_free = |start:|Number of Miller" /tmp/agent_r5_6xvm/r1.log | head -20; tail -4 /tmp/agent_r5_6xvm/r1.log
```

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6XVM && echo ok; sleep 240; grep -c "r_work = " /tmp/agent_r5_6xvm/r1.log; tail -3 /tmp/agent_r5_6xvm/r1.log; ls -la /tmp/agent_r5_6xvm/r1* 2>/dev/null
```

```bash
sleep 420; grep -E "^\s*\|?\s*r_work = " /tmp/agent_r5_6xvm/r1.log | tail -8; echo "--- tail ---"; tail -3 /tmp/agent_r5_6xvm/r1.log; ls /tmp/agent_r5_6xvm/r1_001.pdb 2>/dev/null && echo "PDB WRITTEN"
```

```bash
sleep 60; tail -40 /tmp/agent_r5_6xvm/r1.log; echo "=== DONE? ==="; ls -la /tmp/agent_r5_6xvm/r1_001.pdb /tmp/agent_r5_6xvm/r1_001.mtz 2>/dev/null
```

```bash
grep -B2 "^\s*start:" /tmp/agent_r5_6xvm/r1.log | head -6; echo "=== VALIDATION r1 ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/agent_r5_6xvm/r1_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/agent_r5_6xvm/r1_001.pdb 2>&1 | tail -3; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/agent_r5_6xvm/r1_001.pdb 2>&1 | tail -2
```

### 11. Refinement run 2 **[REFINE 2/6]** — crashed mid-refinement

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 2>&1 | sed -n '/^  ordered_solvent {/,/^  }/p' | head -45
```

```bash
nohup sh -c 'cd /tmp/agent_r5_6xvm && exec /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb 6xvm_recovered.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" main.number_of_macro_cycles=8 main.ordered_solvent=True ordered_solvent.new_solvent=anisotropic hydrogens.refine=riding main.nproc=4 output.prefix=r2 --overwrite' > /tmp/agent_r5_6xvm/r2.log 2>&1 &
echo "launched pid=$!"; sleep 300; grep -E "^\s*\|?\s*r_work = " /tmp/agent_r5_6xvm/r2.log | tail -3; tail -3 /tmp/agent_r5_6xvm/r2.log
```

```bash
sleep 600; grep -E "^\s*\|?\s*r_work = " /tmp/agent_r5_6xvm/r2.log | tail -3; echo "--- solvent ---"; grep -E "ordered solvent|number of ordered solvent|Total number of water" /tmp/agent_r5_6xvm/r2.log | tail -5; echo "--- tail ---"; tail -3 /tmp/agent_r5_6xvm/r2.log
```
*(harness timeout at 10 min; job already dead)*

```bash
grep -E "^\s*\|?\s*r_work = " /tmp/agent_r5_6xvm/r2.log | tail -3; echo "--- tail ---"; tail -4 /tmp/agent_r5_6xvm/r2.log; echo "--- running? ---"; ps aux | grep "[r]2.log\|prefix=r2" | wc -l
```

```bash
ls -la /tmp/agent_r5_6xvm/r2* 2>/dev/null; echo "=== crash context ==="; grep -n -B8 "CCTBX_ASSERT" /tmp/agent_r5_6xvm/r2.log | head -20; echo "=== alive? ==="; pgrep -fl "prefix=r2" | head
```

### 12. Refinement run 3 **[REFINE 3/6]** — ordered solvent, isotropic new waters

```bash
nohup sh -c 'cd /tmp/agent_r5_6xvm && exec /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb 6xvm_recovered.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" main.number_of_macro_cycles=8 main.ordered_solvent=True hydrogens.refine=riding main.nproc=4 output.prefix=r3 --overwrite' > /tmp/agent_r5_6xvm/r3.log 2>&1 &
echo "launched pid=$!"; sleep 540; grep -E "^\s*\|?\s*r_work = " /tmp/agent_r5_6xvm/r3.log | tail -2; tail -3 /tmp/agent_r5_6xvm/r3.log
```

```bash
sleep 540; grep -E "^\s*\|?\s*r_work = " /tmp/agent_r5_6xvm/r3.log | tail -2; echo "--- solvent ---"; grep -E "Number of.*water|ordered solvent|solvent: " /tmp/agent_r5_6xvm/r3.log | tail -4; tail -3 /tmp/agent_r5_6xvm/r3.log
```

```bash
sleep 45; grep -E "^Start R-work|^Final R-work" /tmp/agent_r5_6xvm/r3.log; echo "=== waters ==="; for f in start.pdb r1_001.pdb r3_001.pdb; do printf "%-14s waters=%s atoms=%s\n" "$f" "$(grep 'HOH' /tmp/agent_r5_6xvm/$f | grep -c '^ATOM\|^HETATM')" "$(grep -c '^ATOM\|^HETATM' /tmp/agent_r5_6xvm/$f)"; done; echo "=== validation r3 ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/agent_r5_6xvm/r3_001.pdb 2>&1 | tail -1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/agent_r5_6xvm/r3_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/agent_r5_6xvm/r3_001.pdb 2>&1 | tail -1
```

```bash
grep -E "^\s+(start|end):" /tmp/agent_r5_6xvm/r3.log | tail -2; echo "=== header ==="; grep -E "R-work R-free|Rwork Rfree|bonds angles" /tmp/agent_r5_6xvm/r3.log | tail -3; echo "=== final rmsd block ==="; grep -n -A12 "Final model vs data\|FINAL:" /tmp/agent_r5_6xvm/r3.log | tail -25
```

### 13. Refinement run 4 **[REFINE 4/6]** — weight optimization

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 2>&1 | grep -n -E "optimize_xyz_weight|optimize_adp_weight|^  target_weights \{" | head
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>&1 | grep -n -E "optimize_.*weight|weight_selection_criteria|^\s*target_weights \{" | head -20
```

```bash
nohup sh -c 'cd /tmp/agent_r5_6xvm && exec /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_001.pdb 6xvm_recovered.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" main.number_of_macro_cycles=6 main.ordered_solvent=True target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True hydrogens.refine=riding main.nproc=4 output.prefix=r4 --overwrite' > /tmp/agent_r5_6xvm/r4.log 2>&1 &
echo "launched pid=$!"; sleep 480; grep -E "^\s+(start|end|[0-9]+_[a-z]+):" /tmp/agent_r5_6xvm/r4.log | tail -3; tail -3 /tmp/agent_r5_6xvm/r4.log
```

```bash
sleep 570; grep -E "^\s+end:" /tmp/agent_r5_6xvm/r4.log | tail -2; echo "--- last stages ---"; grep -E "^\s+[0-9]+_[a-z0-9]+:" /tmp/agent_r5_6xvm/r4.log | tail -4; echo "--- tail ---"; tail -3 /tmp/agent_r5_6xvm/r4.log
```

```bash
sleep 570; grep -E "^\s+end:" /tmp/agent_r5_6xvm/r4.log | tail -2; grep -E "^\s+[0-9]+_[a-z0-9]+:" /tmp/agent_r5_6xvm/r4.log | tail -3; echo "--- tail ---"; tail -3 /tmp/agent_r5_6xvm/r4.log; pgrep -fl "prefix=r4" | wc -l
```

```bash
grep -E "^Final R-work" /tmp/agent_r5_6xvm/r4.log; echo "=== validation r4 ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/agent_r5_6xvm/r4_001.pdb 2>&1 | tail -1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/agent_r5_6xvm/r4_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/agent_r5_6xvm/r4_001.pdb 2>&1 | tail -1
```

```bash
cd /tmp/agent_r5_6xvm && awk '/^ATOM|^HETATM/ {e=substr($0,77,2); gsub(/ /,"",e); ser=substr($0,7,5); if(e!="H"){heavy++; key=ser; seen[key]=1}} /^ANISOU/ {a++} END {print "heavy="heavy, "anisou="a, "iso_heavy="heavy-a}' r4_001.pdb; echo "waters: $(grep 'HOH' r4_001.pdb | grep -c '^ATOM\|^HETATM')"; echo "total atoms: $(grep -c '^ATOM\|^HETATM' r4_001.pdb)"
```

```bash
cd /tmp/agent_r5_6xvm && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r4_001.pdb > cs_r4_full.log 2>&1; head -30 cs_r4_full.log; echo "=== clash partner tally ==="; grep -E ":[0-9]" cs_r4_full.log | grep -c "HOH"; echo "total clash lines: $(grep -cE ':-?[0-9]+\.[0-9]+$' cs_r4_full.log)"
```

```bash
cd /tmp/agent_r5_6xvm && grep -E ':-?[0-9]+\.[0-9]+$' cs_r4_full.log | sort -t: -k2 -rn | head -30
```

### 14. Refinement run 5 **[REFINE 5/6]** — stricter solvent distance

```bash
nohup sh -c 'cd /tmp/agent_r5_6xvm && exec /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_001.pdb 6xvm_recovered.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" main.number_of_macro_cycles=6 main.ordered_solvent=True ordered_solvent.dist_min=2.3 ordered_solvent.mode=every_macro_cycle_after_first target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True hydrogens.refine=riding main.nproc=4 output.prefix=r5 --overwrite' > /tmp/agent_r5_6xvm/r5.log 2>&1 &
echo "launched pid=$!"; sleep 500; grep -E "^\s+(start|end):" /tmp/agent_r5_6xvm/r5.log | tail -2; grep -E "^\s+[0-9]+_[a-z0-9]+:" /tmp/agent_r5_6xvm/r5.log | tail -3; tail -2 /tmp/agent_r5_6xvm/r5.log
```

```bash
sleep 570; grep -E "^\s+end:" /tmp/agent_r5_6xvm/r5.log | tail -1; grep -E "^\s+[0-9]+_[a-z0-9]+:" /tmp/agent_r5_6xvm/r5.log | tail -3; echo "--- tail ---"; tail -2 /tmp/agent_r5_6xvm/r5.log
```

```bash
sleep 570; grep -E "^\s+end:" /tmp/agent_r5_6xvm/r5.log | tail -1; grep -E "^\s+[0-9]+_[a-z0-9]+:" /tmp/agent_r5_6xvm/r5.log | tail -3; tail -2 /tmp/agent_r5_6xvm/r5.log; pgrep -fl "prefix=r5" | wc -l
```

```bash
cd /tmp/agent_r5_6xvm && grep -E "^Final R-work" r5.log; echo "=== r5 validation ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r5_001.pdb 2>&1 | grep clashscore; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r5_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r5_001.pdb 2>&1 | tail -1; echo "waters: $(grep HOH r5_001.pdb | grep -c '^ATOM\|^HETATM')"
```

```bash
cd /tmp/agent_r5_6xvm && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r5_001.pdb 2>&1 | grep -E ':-?[0-9]+\.[0-9]+$' | sort -t: -k2 -rn > cs_r5_list.txt; wc -l < cs_r5_list.txt; head -14 cs_r5_list.txt; echo "=== HOH-involving: $(grep -c HOH cs_r5_list.txt) ==="; echo "=== min water-protein dist check ==="; /opt/homebrew/bin/gemmi contact --maxdist=2.3 --ignore=same-asu r5_001.pdb 2>&1 | head -5
```

### 15. Targeted water removal (no refinement invocation)

```bash
cd /tmp/agent_r5_6xvm && cat > pick_bad_waters.py <<'EOF'
import re
# Clash lines look like:  " C 112  ASN  HB2  S 397  HOH  O   :0.795"
# Two atom records of 15 chars each, then ":overlap".
bad = set()
rows = []
for line in open("cs_r5_list.txt"):
    line = line.rstrip("\n")
    m = re.match(r"^(.{15})(.{15}):(-?[\d.]+)$", line)
    if not m:
        continue
    a1, a2, ov = m.group(1), m.group(2), float(m.group(3))
    for a, other in ((a1, a2), (a2, a1)):
        if a[10:13].strip() == "HOH" and other[10:13].strip() != "HOH":
            ch = a[0:2].strip(); num = a[2:7].strip()
            bad.add((ch, num))
            rows.append((ov, ch, num, other.strip()))
for ov, ch, num, other in sorted(rows, reverse=True):
    print("  %.3f  HOH %s %s  vs  %s" % (ov, ch, num, other))
print("\nunique clashing waters: %d" % len(bad))
open("bad_waters.txt","w").write("\n".join("%s %s" % (c,n) for c,n in sorted(bad)))
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python pick_bad_waters.py 2>&1 | tail -25
```
*(matched nothing — field widths were wrong; corrected below)*

```bash
cd /tmp/agent_r5_6xvm && head -3 cs_r5_list.txt | /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import sys
for l in sys.stdin: print(repr(l))"
```

```bash
cd /tmp/agent_r5_6xvm && cat > pick_bad_waters.py <<'EOF'
# clashscore lines: two 17-char atom records, then ":overlap"
# record layout: [0:2]=chain [2:7]=resnum [7]=altloc [8:11]=resname [11:]=atom
def parse(r):
    return dict(ch=r[0:2].strip(), num=r[2:7].strip(), alt=r[7].strip(),
                res=r[8:11].strip(), atom=r[11:].strip())

bad, rows = set(), []
for line in open("cs_r5_list.txt"):
    line = line.rstrip("\n")
    i = line.rfind(":")
    if i < 0: continue
    ov = float(line[i+1:]); part = line[:i]
    a1, a2 = parse(part[0:17]), parse(part[17:34])
    for a, other in ((a1, a2), (a2, a1)):
        if a["res"] == "HOH" and other["res"] != "HOH":
            bad.add((a["ch"], a["num"]))
            rows.append((ov, a["ch"], a["num"], other))

for ov, ch, num, o in sorted(rows, reverse=True):
    print("  %.3f  HOH %s/%s   vs  %s %s%s %s %s" %
          (ov, ch, num, o["ch"], o["alt"], o["res"], o["num"], o["atom"]))
print("\nunique waters clashing with non-water: %d" % len(bad))
sel = " or ".join('(chain %s and resseq %s)' % (c, n) for c, n in sorted(bad, key=lambda x:(x[0], int(x[1]))))
open("bad_waters_sel.txt", "w").write("water and (" + sel + ")")
print("\nselection written to bad_waters_sel.txt")
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python pick_bad_waters.py 2>&1 | tail -28
```

```bash
cd /tmp/agent_r5_6xvm && SEL=$(cat bad_waters_sel.txt) && echo "SELECTION: $SEL" && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools r5_001.pdb remove="$SEL" output.file_name=r5_trimmed.pdb > pdbtools.log 2>&1; echo "exit=$?"; echo "waters before: $(grep HOH r5_001.pdb | grep -c '^ATOM\|^HETATM')  after: $(grep HOH r5_trimmed.pdb | grep -c '^ATOM\|^HETATM')"; echo "atoms before: $(grep -c '^ATOM\|^HETATM' r5_001.pdb)  after: $(grep -c '^ATOM\|^HETATM' r5_trimmed.pdb)"
```

```bash
cd /tmp/agent_r5_6xvm && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r5_trimmed.pdb 2>&1 | grep clashscore
```

### 16. Refinement run 6 **[REFINE 6/6]** — final polish

```bash
nohup sh -c 'cd /tmp/agent_r5_6xvm && exec /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r5_trimmed.pdb 6xvm_recovered.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" main.number_of_macro_cycles=6 main.ordered_solvent=False target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True hydrogens.refine=riding main.nproc=4 output.prefix=r6 --overwrite' > /tmp/agent_r5_6xvm/r6.log 2>&1 &
echo "launched pid=$!"; sleep 540; grep -E "^\s+(start|end):" /tmp/agent_r5_6xvm/r6.log | tail -2; grep -E "^\s+[0-9]+_[a-z0-9]+:" /tmp/agent_r5_6xvm/r6.log | tail -2; tail -2 /tmp/agent_r5_6xvm/r6.log
```

```bash
sleep 570; grep -E "^\s+end:" /tmp/agent_r5_6xvm/r6.log | tail -1; grep -E "^\s+[0-9]+_[a-z0-9]+:" /tmp/agent_r5_6xvm/r6.log | tail -2; tail -2 /tmp/agent_r5_6xvm/r6.log; pgrep -fl "prefix=r6" | wc -l
```

```bash
cd /tmp/agent_r5_6xvm && grep -E "^Final R-work" r6.log; echo "=== r6 validation ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r6_001.pdb 2>&1 | grep clashscore; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r6_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r6_001.pdb 2>&1 | tail -1; echo "waters: $(grep HOH r6_001.pdb | grep -c '^ATOM\|^HETATM')  atoms: $(grep -c '^ATOM\|^HETATM' r6_001.pdb)"
```

```bash
cd /tmp/agent_r5_6xvm && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r6_001.pdb 6xvm_recovered.mtz > mvd_r6.log 2>&1; grep -E "r_work|r_free|Completeness in resolution" mvd_r6.log | head -5
```

### 17. Deliverables

```bash
cd /tmp/agent_r5_6xvm && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6XVM && cp r6_001.pdb $D/final.pdb && cp 6xvm_recovered.mtz $D/6xvm_recovered.mtz && ls -la $D/ && echo "=== final.pdb sanity ===" && head -1 $D/final.pdb && grep -c "^ATOM\|^HETATM" $D/final.pdb && grep -c "^ANISOU" $D/final.pdb
```

```bash
cd /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6XVM && awk '/^ATOM|^HETATM/ {e=substr($0,77,2); gsub(/ /,"",e); c[e]++} END {for(k in c) print k, c[k]}' final.pdb; echo "waters: $(grep HOH final.pdb | grep -c '^ATOM\|^HETATM')"; echo "GOL: $(grep -c 'GOL' final.pdb)"
```

---

## Compliance notes

- **No network access of any kind** was used — no `curl`, `wget`, or `phenix.fetch_pdb`.
- **No deposited coordinates were read.** `/tmp/nc_round1_cache/6xvm.cif` was listed by `ls`
  but never opened. No `*_mask.json` or `*_validation.xml` was read. The only file read under
  `nc_round1_cache/` would have been `6xvm.mtz`, which no longer exists.
- Files read under `/tmp/nc_round1_work/` were the perturbed input model, and — for data
  recovery only — `r4r_r4p_6xvm_001.mtz` (observation columns only), plus its `.eff`/`.log` to
  confirm the original column labels and free-flag test value.
- **Refinement invocations: 6 of 6.** Run 2 crashed after performing refinement and is counted.
  The `nproc=8` launch failed during PHIL parsing before any refinement and is not counted.
