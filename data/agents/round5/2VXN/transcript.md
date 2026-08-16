# 2VXN blinded recovery — verbatim shell transcript

Every shell command executed, in execution order. Commands are reproduced exactly as run.
Independent commands issued in the same turn are grouped and marked; they were executed in
parallel within that turn, in the order listed.

Legend: `[R#]` marks an invocation of a refinement program (`phenix.refine`). Six such
invocations occur: `[R1]` (aborted on a parameter error, 4 s, no refinement performed) through
`[R6]`.

---

### Turn 1 — inspect inputs (parallel pair)

```bash
mkdir -p /tmp/agent_r5_2vxn && cd /tmp/agent_r5_2vxn && gemmi mtz --dump /tmp/nc_round1_cache/2vxn.mtz 2>&1 | head -60
```

```bash
head -30 /tmp/nc_round1_work/r4p_2vxn.pdb; echo "---GREP---"; grep -c "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_2vxn.pdb; echo "---HETATM types---"; grep "^HETATM" /tmp/nc_round1_work/r4p_2vxn.pdb | cut -c18-20 | sort | uniq -c
```

### Turn 2 — baseline R-factors and model composition (parallel pair)

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_2vxn.pdb /tmp/nc_round1_cache/2vxn.mtz > baseline_mvd.log 2>&1; cat baseline_mvd.log
```

```bash
grep -c "^ATOM" /tmp/nc_round1_work/r4p_2vxn.pdb; echo "--- anisou count:"; grep -c "^ANISOU" /tmp/nc_round1_work/r4p_2vxn.pdb; echo "--- altlocs:"; grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_2vxn.pdb | cut -c17 | sort | uniq -c; echo "--- chains:"; grep "^ATOM" /tmp/nc_round1_work/r4p_2vxn.pdb | cut -c22 | sort | uniq -c; echo "--- REMARKs:"; grep "^REMARK" /tmp/nc_round1_work/r4p_2vxn.pdb | head -20
```

### Turn 3 — baseline geometry (MolProbity)

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity /tmp/nc_round1_work/r4p_2vxn.pdb output.prefix=base_mp > base_mp.log 2>&1; sed -n '/Summary/,/^$/p' base_mp.log | head -40; echo "=== geometry ==="; grep -A6 "Bond ..*:" base_mp.log | head -40
```

### Turn 4 — Rama/rota/clash, and the ANISOU-stripped control (parallel pair)

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/nc_round1_work/r4p_2vxn.pdb 2>&1 | tail -5; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/nc_round1_work/r4p_2vxn.pdb 2>&1 | tail -5; echo "=== CLASH ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/nc_round1_work/r4p_2vxn.pdb 2>&1 | tail -4
```

```bash
cd /tmp/agent_r5_2vxn && grep -v "^ANISOU" /tmp/nc_round1_work/r4p_2vxn.pdb > test_noaniso.pdb && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data test_noaniso.pdb /tmp/nc_round1_cache/2vxn.mtz 2>&1 | grep -E "^  r_work|^  r_free"
```

### Turn 5 — per-residue real-space CC, occupancy/B stats (parallel pair)

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation /tmp/nc_round1_work/r4p_2vxn.pdb /tmp/nc_round1_cache/2vxn.mtz detail=residue > rscc.log 2>&1; tail -30 rscc.log; echo "=== CC distribution (protein) ==="; awk '/^ /{print}' rscc.log | head -3
```

```bash
cd /tmp/agent_r5_2vxn && echo "=== occupancy values ==="; grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_2vxn.pdb | cut -c55-60 | sort | uniq -c | sort -rn | head -15; echo "=== B-factor stats ==="; grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_2vxn.pdb | cut -c61-66 | awk '{s+=$1; n++; if($1>mx)mx=$1; if(n==1||$1<mn)mn=$1} END{print "n="n, "mean="s/n, "min="mn, "max="mx}'
```

### Turn 6 — determine RSCC column layout

```bash
cd /tmp/agent_r5_2vxn && grep -E "^ A " rscc.log | grep -v HOH | awk '{cc=$5; if(NF==7) cc=$5; print}' | head -5; echo "=== header line ==="; grep -B2 "^ A " rscc.log | head -6
```

### Turn 7 — RSCC distribution summary

```bash
cd /tmp/agent_r5_2vxn && echo "=== PROTEIN CC stats ==="; grep -E "^ A " rscc.log | grep -vE "HOH|GOL|ACT|PGA|PGH" | awk '{cc=$6; s+=cc; n++; if(cc<0.7)lo++; if(cc>0.9)hi++} END{printf "n=%d mean=%.3f  <0.70:%d  >0.90:%d\n", n, s/n, lo+0, hi+0}'; echo "=== WATER CC stats ==="; grep -E "^ A " rscc.log | grep HOH | awk '{cc=$6; s+=cc; n++; if(cc<0.5)lo++} END{printf "n=%d mean=%.3f  <0.50:%d\n", n, s/n, lo+0}'; echo "=== worst 12 protein residues ==="; grep -E "^ A " rscc.log | grep -vE "HOH|GOL|ACT|PGA|PGH" | sort -k6 -g | head -12
```

### Turn 8 — locate PHENIX docs; add hydrogens (parallel pair)

```bash
ls /Users/marcin/phenix-2.0-5936/doc/ 2>/dev/null | head -20; echo "=== refine doc ==="; find /Users/marcin/phenix-2.0-5936/doc -iname "*refine*" 2>/dev/null | head -20
```

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ready_set /tmp/nc_round1_work/r4p_2vxn.pdb output_file_name=start_h.pdb > ready_set.log 2>&1; tail -25 ready_set.log; ls -la /tmp/agent_r5_2vxn/
```

### Turn 9 — verify H addition; find refine phil (parallel pair)

```bash
grep -c "^ATOM\|^HETATM" /tmp/agent_r5_2vxn/start_h.pdb.pdb; echo "--- H count:"; awk '/^ATOM|^HETATM/{if(substr($0,77,2)==" H")n++}END{print n+0}' /tmp/agent_r5_2vxn/start_h.pdb.pdb; echo "--- anisou preserved:"; grep -c "^ANISOU" /tmp/agent_r5_2vxn/start_h.pdb.pdb
```

```bash
P=/Users/marcin/phenix-2.0-5936; grep -rn "optimize_xyz_weight\|optimize_adp_weight" $P/modules/phenix/phenix/refinement/*.py 2>/dev/null | head -5; echo "=== find refine phil ==="; ls $P/modules/phenix/phenix/refinement/ 2>/dev/null | head -30
```

### Turn 10 — inspect PHENIX install layout

```bash
ls /Users/marcin/phenix-2.0-5936/; echo "=== ==="; ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -i "refine\|dynam\|ready"
```

### Turn 11 — find refine phil in conda libs

```bash
P=/Users/marcin/phenix-2.0-5936; F=$(find $P/lib $P/_conda -name "refine.py" -path "*phenix*" 2>/dev/null | head -5); echo "$F"; echo "=== grep ==="; grep -rl "optimize_xyz_weight" $P/lib $P/_conda 2>/dev/null | head -5
```

### Turn 12 — grep refinement phil scope

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement; grep -n "optimize_xyz_weight\|optimize_adp_weight\|ordered_solvent\|nqh_flips\|simulated_annealing\|number_of_macro_cycles\|fix_rotamers\|silent" $P/command_line/refine.py 2>/dev/null | head -30; echo "=== files ==="; ls $P/ | head -40
```

### Turn 13 — extract key refine parameters

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; grep -n "optimize_xyz_weight\|optimize_adp_weight\|ordered_solvent\|nqh_flips\|simulated_annealing\|number_of_macro_cycles\|fix_rotamers\|strategy\|main *{\|scattering_table\|adp *{" $P | head -40
```

### Turn 14 — read strategy options and optimize flags

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; sed -n '105,140p' $P; echo "=== weights/optimize ==="; grep -n "optimize" $P | head -20
```

### Turn 15 — find weight/resolution parameters

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; grep -n "wxc_scale\|wxu_scale\|weight_selection\|optimize_weight\|^  target_weights\|automatic\|adp *{" $P | head -25; echo "=== target_weights scope ==="; sed -n '/target_weights/,/^  }/p' $P | head -50
```

### Turn 16 — determine scope containing `stir`

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; grep -n "stir\|^  [a-z_]* *$\|^  [a-z_]*$\|^  main\|^  }" $P | sed -n '1,60p'
```

### Turn 17 — read stir and anisotropic ADP params

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; sed -n '455,500p' $P; echo "=== adp scope 470-495 ==="; sed -n '470,495p' $P
```

### Turn 18 — read `refine.adp` selection parameters

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; sed -n '/^    adp$/,/^    occupancies/p' $P | head -60
```

### Turn 19 — `[R1]` refinement invocation 1 — ABORTED on PHIL parameter error (4 s, no refinement performed)

```bash
cd /tmp/agent_r5_2vxn && mkdir -p r1 && cd r1 && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine \
  /tmp/agent_r5_2vxn/start_h.pdb.pdb \
  /tmp/nc_round1_cache/2vxn.mtz \
  /tmp/agent_r5_2vxn/start_h.cif.cif \
  "miller_array.labels.name=FOBS,SIGFOBS" \
  "miller_array.labels.name=R-free-flags" \
  refinement.input.xray_data.high_resolution=2.5 \
  refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp \
  refinement.main.number_of_macro_cycles=3 \
  refinement.main.nqh_flips=True \
  refinement.main.ordered_solvent=False \
  output.prefix=r1 output.serial=1 \
  --overwrite > /tmp/agent_r5_2vxn/r1/r1.log 2>&1; echo "EXIT=$?"; tail -5 /tmp/agent_r5_2vxn/r1/r1.log
```

### Turn 20 — read the parameter error

```bash
grep -B15 "Please run this program" /tmp/agent_r5_2vxn/r1/r1.log | head -30
```

### Turn 21 — find the correct resolution parameter

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; grep -n "high_resolution\|low_resolution" $P | head; echo "=== input scope ==="; sed -n '24,31p' $P; echo "=== output scope 32-94 ==="; sed -n '32,60p' $P
```

### Turn 22 — read parsed DataManager scope

```bash
grep -B45 "Unrecognized PHIL" /tmp/agent_r5_2vxn/r1/r1.log | head -50
```

### Turn 23 — inspect ready_set CIF; look for DataManager resolution param (parallel pair)

```bash
head -20 /tmp/agent_r5_2vxn/start_h.cif.cif; echo "=== data blocks ==="; grep -c "^data_" /tmp/agent_r5_2vxn/start_h.cif.cif; grep "^data_" /tmp/agent_r5_2vxn/start_h.cif.cif | head
```

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages; grep -rn "high_resolution" $P/iotbx/data_manager/miller_array.py 2>/dev/null | head -10; echo "=== d_min in refinement main ==="; grep -n "d_min\b" $P/phenix/refinement/__init__.params | head -10
```

### Turn 24 — split restraints-only CIF; locate `xray_data` scope (parallel pair)

```bash
grep -c "_atom_site" /tmp/agent_r5_2vxn/start_h.cif.cif; echo "=== split restraints only ==="; python3 - <<'EOF'
import re
src=open('/tmp/agent_r5_2vxn/start_h.cif.cif').read()
blocks=re.split(r'(?m)^(?=data_)', src)
keep=[b for b in blocks if b.startswith('data_comp_')]
open('/tmp/agent_r5_2vxn/ligands.cif','w').write(''.join(keep))
print("kept blocks:", [b.split('\n')[0] for b in keep])
EOF
wc -l /tmp/agent_r5_2vxn/ligands.cif
```

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages; grep -rn "xray_data" $P/phenix/refinement/__init__.params | head; echo "=== mmtbx utils data scope ==="; grep -rn "high_resolution" $P/mmtbx/utils/__init__.py | head -8
```

### Turn 25 — confirm `xray_data` lives under the GUI-only scope

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix/refinement/__init__.params; sed -n '1040,1075p' $P; echo "=== parent scopes: lines with 2-space indent names before 1059 ==="; awk 'NR<1060 && /^  [a-z_]+$/{print NR": "$0}' $P | tail -5
```

### Turn 26 — check `stir` implementation; gemmi mtz options (parallel pair)

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix; grep -rn "stir" $P/refinement/driver.py $P/refinement/macro_cycle.py $P/refinement/runtime.py 2>/dev/null | head -20
```

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages; grep -n "high_resolution\|low_resolution\|labels\|type = \|\.type=" $P/iotbx/data_manager/miller_array.py 2>/dev/null | head -25
```

### Turn 27 — truncate MTZ to 1.6 Å

```bash
cd /tmp/agent_r5_2vxn && cat > cut.py <<'EOF'
from iotbx import mtz
import sys
inp, out, dmin = sys.argv[1], sys.argv[2], float(sys.argv[3])
m = mtz.object(inp)
mas = m.as_miller_arrays()
sel = [a for a in mas]
out_obj = None
for a in sel:
    a2 = a.resolution_filter(d_min=dmin)
    lab = a.info().labels
    print("array", lab, "n_in", a.size(), "n_out", a2.size())
    if out_obj is None:
        out_obj = a2.as_mtz_dataset(column_root_label=lab[0])
    else:
        out_obj.add_miller_array(a2, column_root_label=lab[0])
out_obj.mtz_object().write(out)
print("wrote", out)
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python cut.py /tmp/nc_round1_cache/2vxn.mtz /tmp/agent_r5_2vxn/2vxn_1p6.mtz 1.6 2>&1 | tail -10; echo "=== verify ==="; gemmi mtz --dump /tmp/agent_r5_2vxn/2vxn_1p6.mtz 2>&1 | grep -A8 "Column "
```

### Turn 28 — verify free-flag value distribution

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
from iotbx import mtz
m=mtz.object('/tmp/nc_round1_cache/2vxn.mtz')
for a in m.as_miller_arrays():
    if 'R-free-flags' in a.info().labels:
        d=a.data()
        import collections
        print(collections.Counter(d))
"
```

### Turn 29 — `[R2]` refinement invocation 2 — 1.6 Å convergence stage

```bash
mkdir -p /tmp/agent_r5_2vxn/r2 && cd /tmp/agent_r5_2vxn/r2 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine \
  /tmp/agent_r5_2vxn/start_h.pdb.pdb \
  /tmp/agent_r5_2vxn/2vxn_1p6.mtz \
  /tmp/agent_r5_2vxn/ligands.cif \
  "miller_array.labels.name=FOBS,SIGFOBS" \
  "miller_array.labels.name=R-free-flags" \
  refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies \
  refinement.main.number_of_macro_cycles=5 \
  refinement.main.nqh_flips=True \
  refinement.main.ordered_solvent=True \
  output.prefix=r2 output.serial=1 \
  --overwrite > /tmp/agent_r5_2vxn/r2/r2.log 2>&1 &
echo "launched pid $!"; sleep 90; tail -20 /tmp/agent_r5_2vxn/r2/r2.log
```

### Turn 30 — wait for R2 and report

```bash
while kill -0 76515 2>/dev/null; do sleep 30; done; echo "DONE"; grep -E "Final R-work|Final R-free|^  r_work|^  r_free" /tmp/agent_r5_2vxn/r2/r2.log | tail -10; echo "=== files ==="; ls /tmp/agent_r5_2vxn/r2/ | grep -E "pdb|mtz"
```

### Turn 31 — evaluate the 1.6 Å model against full 0.82 Å data

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r2/r2_001.pdb /tmp/nc_round1_cache/2vxn.mtz > r2_fullres_mvd.log 2>&1; grep -E "^  r_work|^  r_free" r2_fullres_mvd.log; echo "=== shells ==="; sed -n '/Resolution    Compl/,/r_work:/p' r2_fullres_mvd.log | tail -18; echo "=== aniso present? ==="; grep -c "^ANISOU" r2/r2_001.pdb
```

### Turn 32 — `[R3]` refinement invocation 3 — full 0.82 Å, anisotropic ADPs

```bash
mkdir -p /tmp/agent_r5_2vxn/r3 && cd /tmp/agent_r5_2vxn/r3 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine \
  /tmp/agent_r5_2vxn/r2/r2_001.pdb \
  /tmp/nc_round1_cache/2vxn.mtz \
  /tmp/agent_r5_2vxn/ligands.cif \
  "miller_array.labels.name=FOBS,SIGFOBS" \
  "miller_array.labels.name=R-free-flags" \
  refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies \
  "refinement.refine.adp.individual.anisotropic=not element H" \
  refinement.main.number_of_macro_cycles=4 \
  refinement.main.nqh_flips=True \
  refinement.main.ordered_solvent=True \
  output.prefix=r3 output.serial=1 \
  --overwrite > /tmp/agent_r5_2vxn/r3/r3.log 2>&1 &
echo "launched pid $!"; sleep 120; grep -E "r_work=|Unrecognized|Sorry" /tmp/agent_r5_2vxn/r3/r3.log | tail -5
```

### Turn 33 — poll R3 progress

```bash
sleep 900; echo "=== running? ==="; kill -0 16926 2>/dev/null && echo YES || echo NO; grep -E "MACRO_CYCLE|r_work=.*r_free=.*n_water" /tmp/agent_r5_2vxn/r3/r3.log | tail -6
```

### Turn 34 — wait for R3

```bash
while kill -0 16926 2>/dev/null; do sleep 60; done; echo "DONE"; grep -E "Final R-work" /tmp/agent_r5_2vxn/r3/r3.log; grep -E "MACRO_CYCLE" /tmp/agent_r5_2vxn/r3/r3.log | tail -3; ls /tmp/agent_r5_2vxn/r3/ | grep -E "\.pdb|\.mtz"
```

### Turn 35 — R trajectory and MolProbity on R3 (parallel pair)

```bash
cd /tmp/agent_r5_2vxn && grep -E "^ *r_work= *0\.|Final R-work" r3/r3.log | grep -v "n_water" | tail -20; echo "=== per-macrocycle summary lines ==="; grep -B2 -A8 "MACRO_CYCLE" r3/r3.log | grep -E "r_work=|MACRO_CYCLE" | tail -20
```

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r3/r3_001.pdb output.prefix=r3_mp > r3_mp.log 2>&1; grep -E "Ramachandran outliers|favored|Rotamer outliers|C-beta|Clashscore|RMS\(bonds\)|RMS\(angles\)|MolProbity score" r3_mp.log | head -20
```

### Turn 36 — locate weight-optimization parameter path

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/phenix; grep -n "optimize_xyz_weight\|optimize_adp_weight" $P/refinement/xyz_reciprocal_space.py $P/refinement/weights.py 2>/dev/null | head -10; echo "=== weights params scope ==="; grep -rn "optimize_xyz_weight" $P/refinement/customizations/ref_joint.params | head -3; echo "=== main scope check ==="; grep -n "optimize_xyz_weight\|optimize_adp_weight\|wxc_scale\|wxu_scale" /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/targets.py 2>/dev/null | head
```

### Turn 37 — confirm `target_weights` phil path and skip-guard logic

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages; sed -n '757,764p' $P/phenix/refinement/__init__.params; echo "=== included scope defaults ==="; grep -n "optimize_xyz_weight\|optimize_adp_weight" $P/mmtbx/refinement/targets.py $P/mmtbx/refinement/weight_xray_chem.py 2>/dev/null | head; echo "=== logic ==="; sed -n '450,470p' $P/phenix/refinement/xyz_reciprocal_space.py
```

### Turn 38 — confirm weight parameter names

```bash
P=/Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement; grep -n "optimize_xyz_weight\|optimize_adp_weight\|force_optimize_weights\|wxc_scale\|wxu_scale" $P/weights.py | head -15
```

### Turn 39 — `[R4]` refinement invocation 4 — weight-optimized polish (later killed; produced no output model)

```bash
mkdir -p /tmp/agent_r5_2vxn/r4 && cd /tmp/agent_r5_2vxn/r4 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine \
  /tmp/agent_r5_2vxn/r3/r3_001.pdb \
  /tmp/nc_round1_cache/2vxn.mtz \
  /tmp/agent_r5_2vxn/ligands.cif \
  "miller_array.labels.name=FOBS,SIGFOBS" \
  "miller_array.labels.name=R-free-flags" \
  refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies \
  "refinement.refine.adp.individual.anisotropic=not element H" \
  refinement.main.number_of_macro_cycles=4 \
  refinement.main.nqh_flips=True \
  refinement.main.ordered_solvent=True \
  refinement.target_weights.optimize_xyz_weight=True \
  refinement.target_weights.optimize_adp_weight=True \
  output.prefix=r4 output.serial=1 \
  --overwrite > /tmp/agent_r5_2vxn/r4/r4.log 2>&1 &
echo "launched pid $!"; sleep 120; grep -E "Unrecognized|Sorry|r_work=" /tmp/agent_r5_2vxn/r4/r4.log | tail -4
```

### Turn 40 — create deliverables directory

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/2VXN/ && echo created; ls -d /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/2VXN/
```

### Turn 41 — poll R4

```bash
sleep 1200; kill -0 70114 2>/dev/null && echo "RUNNING" || echo "DONE"; grep -E "MACRO_CYCLE|Final R-work" /tmp/agent_r5_2vxn/r4/r4.log | tail -5; grep -E "r_work=.*r_free=" /tmp/agent_r5_2vxn/r4/r4.log | tail -3
```

### Turn 42 — wait for R4

```bash
while kill -0 70114 2>/dev/null; do sleep 60; done; echo "DONE"; grep -E "Final R-work" /tmp/agent_r5_2vxn/r4/r4.log; echo "=== weight info ==="; grep -E "wxc = |wxu = " /tmp/agent_r5_2vxn/r4/r4.log | tail -4
```

### Turn 43 — check R4 completion status (no output file found)

```bash
tail -30 /tmp/agent_r5_2vxn/r4/r4.log; echo "=== files ==="; ls -la /tmp/agent_r5_2vxn/r4/ | grep -E "\.pdb|\.mtz"
```

### Turn 44 — diagnose R4 termination

```bash
ps aux | grep -i "phenix.refine\|python.*refine" | grep -v grep | head; echo "=== exit clue ==="; grep -iE "error|traceback|killed|memory|sorry" /tmp/agent_r5_2vxn/r4/r4.log | tail -10; echo "=== log size/mtime ==="; ls -la /tmp/agent_r5_2vxn/r4/
```

### Turn 45 — check memory pressure and OOM kills

```bash
memory_pressure 2>/dev/null | tail -5; echo "=== vm_stat ==="; vm_stat | head -6; echo "=== recent kills ==="; log show --last 45m --predicate 'eventMessage CONTAINS "memorystatus" OR eventMessage CONTAINS "jetsam"' 2>/dev/null | tail -8
```

### Turn 46 — `[R5]` refinement invocation 5 — weight-optimized polish, foreground

```bash
mkdir -p /tmp/agent_r5_2vxn/r5 && cd /tmp/agent_r5_2vxn/r5 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine \
  /tmp/agent_r5_2vxn/r3/r3_001.pdb \
  /tmp/nc_round1_cache/2vxn.mtz \
  /tmp/agent_r5_2vxn/ligands.cif \
  "miller_array.labels.name=FOBS,SIGFOBS" \
  "miller_array.labels.name=R-free-flags" \
  refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies \
  "refinement.refine.adp.individual.anisotropic=not element H" \
  refinement.main.number_of_macro_cycles=3 \
  refinement.main.nqh_flips=True \
  refinement.main.ordered_solvent=True \
  refinement.target_weights.optimize_xyz_weight=True \
  refinement.target_weights.optimize_adp_weight=True \
  output.write_geo_file=False \
  output.prefix=r5 output.serial=1 \
  --overwrite > /tmp/agent_r5_2vxn/r5/r5.log 2>&1; echo "EXIT=$?"; grep -E "Final R-work" /tmp/agent_r5_2vxn/r5/r5.log; ls /tmp/agent_r5_2vxn/r5/ | grep -E "\.pdb|\.mtz"
```

### Turn 47 — validate R5 (parallel pair)

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r5/r5_001.pdb output.prefix=r5_mp > r5_mp.log 2>&1; grep -E "Ramachandran outliers|favored =|Rotamer outliers|C-beta deviations|Clashscore|RMS\(bonds\)|RMS\(angles\)|MolProbity score" r5_mp.log | head -10; echo "=== waters/atoms ==="; grep -c "^ATOM\|^HETATM" r5/r5_001.pdb; grep "^HETATM" r5/r5_001.pdb | grep -c HOH
```

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r5/r5_001.pdb /tmp/nc_round1_cache/2vxn.mtz > r5_mvd.log 2>&1; grep -E "^  r_work|^  r_free" r5_mvd.log | head -2; echo "=== outer shells ==="; sed -n '/Resolution    Compl/,/^$/p' r5_mvd.log | tail -6
```

### Turn 48 — `[R6]` refinement invocation 6 — final continuation polish

```bash
mkdir -p /tmp/agent_r5_2vxn/r6 && cd /tmp/agent_r5_2vxn/r6 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine \
  /tmp/agent_r5_2vxn/r5/r5_001.pdb \
  /tmp/nc_round1_cache/2vxn.mtz \
  /tmp/agent_r5_2vxn/ligands.cif \
  "miller_array.labels.name=FOBS,SIGFOBS" \
  "miller_array.labels.name=R-free-flags" \
  refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies \
  "refinement.refine.adp.individual.anisotropic=not element H" \
  refinement.main.number_of_macro_cycles=3 \
  refinement.main.nqh_flips=True \
  refinement.main.ordered_solvent=True \
  refinement.target_weights.optimize_xyz_weight=True \
  refinement.target_weights.optimize_adp_weight=True \
  output.write_geo_file=False \
  output.prefix=r6 output.serial=1 \
  --overwrite > /tmp/agent_r5_2vxn/r6/r6.log 2>&1; echo "EXIT=$?"; grep -E "Final R-work" /tmp/agent_r5_2vxn/r6/r6.log; ls /tmp/agent_r5_2vxn/r6/ | grep -E "\.pdb"
```

### Turn 49 — validate R6 (parallel pair)

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r6/r6_001.pdb output.prefix=r6_mp > r6_mp.log 2>&1; grep -E "Ramachandran outliers|favored =|Rotamer outliers|C-beta deviations|Clashscore|RMS\(bonds\)|RMS\(angles\)|MolProbity score" r6_mp.log | head -10
```

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r6/r6_001.pdb /tmp/nc_round1_cache/2vxn.mtz > r6_mvd.log 2>&1; grep -E "^  r_work|^  r_free" r6_mvd.log | head -2; echo "=== waters ==="; grep "^HETATM" r6/r6_001.pdb | grep -c HOH; echo "=== atoms ==="; grep -c "^ATOM\|^HETATM" r6/r6_001.pdb; echo "=== anisou ==="; grep -c "^ANISOU" r6/r6_001.pdb
```

### Turn 50 — final real-space CC and independent gemmi validation (parallel pair)

```bash
cd /tmp/agent_r5_2vxn && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation r6/r6_001.pdb /tmp/nc_round1_cache/2vxn.mtz detail=residue > r6_rscc.log 2>&1; echo "=== PROTEIN CC ==="; grep -E "^ A " r6_rscc.log | grep -vE "HOH|GOL|ACT|PGA|PGH" | awk 'NF==8{cc=$6; s+=cc; n++; if(cc<0.8)lo++} END{printf "n=%d mean=%.3f  <0.80:%d\n", n, s/n, lo+0}'; echo "=== WATER CC ==="; grep -E "^ A " r6_rscc.log | grep HOH | awk 'NF==8{cc=$6; s+=cc; n++; if(cc<0.5)lo++} END{printf "n=%d mean=%.3f  <0.50:%d\n", n, s/n, lo+0}'
```

```bash
cd /tmp/agent_r5_2vxn && gemmi validate r6/r6_001.pdb 2>&1 | head -10; echo "EXIT=$?"; echo "=== gemmi content summary ==="; gemmi content r6/r6_001.pdb 2>&1 | head -20
```

### Turn 51 — confirm final model parses cleanly in gemmi

```bash
cd /tmp/agent_r5_2vxn && gemmi convert r6/r6_001.pdb /tmp/agent_r5_2vxn/final_check.cif && echo "gemmi parse OK" && gemmi validate /tmp/agent_r5_2vxn/final_check.cif 2>&1 | head -5; echo "--- exit=$?"; echo "=== gemmi model stats ==="; gemmi mask --help >/dev/null 2>&1; python3 -c "
import subprocess
out=subprocess.run(['gemmi','convert','--to','pdb','/tmp/agent_r5_2vxn/final_check.cif','/dev/null'],capture_output=True,text=True)
print('roundtrip rc=',out.returncode, out.stderr[:200])
"
```

### Turn 52 — copy final model to deliverables

```bash
D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/2VXN; cp /tmp/agent_r5_2vxn/r6/r6_001.pdb $D/final.pdb && echo copied; head -2 $D/final.pdb | cut -c1-70; grep -c "^ATOM\|^HETATM" $D/final.pdb; grep "^CRYST1" $D/final.pdb; ls -la $D/
```

### Turn 53 — final verification of deliverables

```bash
D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/2VXN; ls -la $D/; echo "=== final.pdb sanity ==="; grep -c "^ATOM\|^HETATM" $D/final.pdb; grep -c "^ANISOU" $D/final.pdb; grep "^CRYST1" $D/final.pdb
```
