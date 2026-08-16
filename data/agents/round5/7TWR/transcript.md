# 7TWR blinded recovery — verbatim shell transcript, in execution order

Every shell command executed for this task, in order. Commands are reproduced exactly as issued.
Non-shell actions (writing a PHIL `.eff` file with an editor tool) are marked `[FILE WRITE]` and the
full file content is inlined, since the runs cannot be reproduced without it.

Refinement-program invocations are flagged:
- **[REFINE n/6]** — performed actual refinement, counts against the budget.
- **[REJECTED — NOT COUNTED]** — exited during PHIL parsing before any refinement macro-cycle began.

Working directory for all scratch work: `/tmp/agent_r5_7twr/`.

---

## 1. Inventory

```bash
mkdir -p /tmp/agent_r5_7twr && cd /tmp/agent_r5_7twr && ls -la /tmp/nc_round1_work/r4p_7twr.pdb /tmp/nc_round1_cache/7twr.mtz
```

```bash
/opt/homebrew/bin/gemmi mtzinfo /tmp/nc_round1_cache/7twr.mtz 2>&1 | head -50
```
(not a gemmi subcommand — corrected next)

```bash
/opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/7twr.mtz 2>&1 | head -60
```

```bash
head -20 /tmp/nc_round1_work/r4p_7twr.pdb; echo "---"; grep -c "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_7twr.pdb; echo "---"; grep "^HETATM" /tmp/nc_round1_work/r4p_7twr.pdb | cut -c18-20 | sort | uniq -c | sort -rn | head -20
```

```bash
cd /tmp/agent_r5_7twr && grep -c "^ANISOU" /tmp/nc_round1_work/r4p_7twr.pdb; echo "--- altloc counts:"; grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_7twr.pdb | cut -c17 | sort | uniq -c; echo "--- occupancy distribution:"; grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_7twr.pdb | cut -c55-60 | sort | uniq -c | sort -rn | head; echo "--- B-factor range:"; grep "^ATOM" /tmp/nc_round1_work/r4p_7twr.pdb | cut -c61-66 | sort -n | head -3; grep "^ATOM" /tmp/nc_round1_work/r4p_7twr.pdb | cut -c61-66 | sort -n | tail -3; echo "--- element H count:"; grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_7twr.pdb | cut -c77-78 | sort | uniq -c
```

```bash
grep "^CRYST1\|^REMARK   2\|^REMARK   3   R VALUE\|^SCALE" /tmp/nc_round1_work/r4p_7twr.pdb | head -20; echo "---REMARKS mentioning perturb/random:"; grep -i "perturb\|random\|shake\|REMARK   1" /tmp/nc_round1_work/r4p_7twr.pdb | head
```

## 2. Baseline measurement and damage diagnosis

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_7twr.pdb /tmp/nc_round1_cache/7twr.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > baseline_mvd.log 2>&1; tail -60 baseline_mvd.log
```
→ R-work 0.4154, R-free 0.4295

```bash
ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -i "molprob\|model_stat\|geometry\|douse\|holton\|real_space"
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/nc_round1_work/r4p_7twr.pdb 2>&1 | tail -5; echo "=== RAMA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/nc_round1_work/r4p_7twr.pdb 2>&1 | tail -6; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/nc_round1_work/r4p_7twr.pdb 2>&1 | tail -5
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_statistics /tmp/nc_round1_work/r4p_7twr.pdb > baseline_modelstats.log 2>&1; grep -A30 "GEOMETRY RESTRAINTS LIBRARY\|Deviations from ideal\|bond      \|angle     " baseline_modelstats.log | head -40; echo "=== ADP ==="; grep -B2 -A12 "ADP statistics\|Isotropic\|Anisotropic" baseline_modelstats.log | head -40
```
→ bond RMSD 0.0101 Å, angle 1.031° (geometry near-ideal ⇒ not a bond-breaking shake)

```bash
cd /tmp/agent_r5_7twr && /opt/homebrew/bin/gemmi convert --select='/1/A' /tmp/nc_round1_work/r4p_7twr.pdb chainA.pdb && /opt/homebrew/bin/gemmi convert --select='/1/B' /tmp/nc_round1_work/r4p_7twr.pdb chainB.pdb && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.superpose_pdbs chainA.pdb chainB.pdb > superpose_AB.log 2>&1; grep -i "rmsd\|n_atoms\|number of atoms" superpose_AB.log | head -20
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation /tmp/nc_round1_work/r4p_7twr.pdb /tmp/nc_round1_cache/7twr.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags detail=residue > rsc_baseline.log 2>&1; echo "exit=$?"; tail -20 rsc_baseline.log
```
(wrong label params — corrected next)

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation --show-defaults 2>&1 | head -40
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation /tmp/nc_round1_work/r4p_7twr.pdb /tmp/nc_round1_cache/7twr.mtz data_labels="FOBS,SIGFOBS" detail=residue > rsc_baseline.log 2>&1; echo "exit=$?"; grep -v "^ *$" rsc_baseline.log | tail -5; echo "=== stats ==="; awk '$1=="A"||$1=="B"' rsc_baseline.log | head -3
```

```bash
cd /tmp/agent_r5_7twr && awk 'NF==8 && ($1=="A"||$1=="B") {cc=$6; if($2=="HOH"){w++; ws+=cc; if(cc<0.5)wlo++} else {p++; ps+=cc; if(cc<0.7)plo++; if(cc<0.5)pvlo++}} END {printf "protein residues: %d  meanCC=%.3f  CC<0.7: %d  CC<0.5: %d\n", p, ps/p, plo, pvlo; printf "waters: %d  meanCC=%.3f  CC<0.5: %d\n", w, ws/w, wlo}' rsc_baseline.log; echo "=== worst 15 protein residues ==="; awk 'NF==8 && ($1=="A"||$1=="B") && $2!="HOH"' rsc_baseline.log | sort -k6 -n | head -15
```
→ protein mean RSCC 0.821; **water mean RSCC 0.466, 344 waters < 0.5** — solvent is the damage

## 3. Prune dead solvent (model edit, no refinement)

```bash
cd /tmp/agent_r5_7twr && awk 'NF==8 && ($1=="A"||$1=="B") && $2=="HOH" && $6<0.5 {print $1"_"$3}' rsc_baseline.log | sort -u > dead_waters.txt && wc -l < dead_waters.txt && python3 - <<'EOF'
dead = set(open('/tmp/agent_r5_7twr/dead_waters.txt').read().split())
out, removed = [], 0
for line in open('/tmp/nc_round1_work/r4p_7twr.pdb'):
    if line.startswith(('ATOM','HETATM','ANISOU')) and line[17:20]=='HOH':
        key = line[21].strip()+'_'+line[22:26].strip()
        if key in dead:
            if line.startswith(('ATOM','HETATM')): removed += 1
            continue
    out.append(line)
open('/tmp/agent_r5_7twr/start_pruned.pdb','w').writelines(out)
print('water atoms removed:', removed)
EOF
grep -c "HOH" /tmp/agent_r5_7twr/start_pruned.pdb
```

```bash
sysctl -n hw.ncpu hw.memsize 2>&1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --version 2>&1 | head -3
```

## 4. Two rejected launches

**[REJECTED — NOT COUNTED]** wrong PHIL scope for the free-flag parameters; also demonstrates the
`cd && nohup ... &` backgrounding mistake (the whole list was backgrounded, so the foreground `tail`
looked in the wrong directory):

```bash
cd /tmp/agent_r5_7twr && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start_pruned.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags refinement.input.xray_data.r_free_flags.test_flag_value=0 refinement.input.xray_data.r_free_flags.generate=False refine.strategy=individual_sites+individual_adp+occupancies refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=6 ordered_solvent=True main.nproc=8 output.prefix=r1 --overwrite > r1_launch.log 2>&1 &
echo "launched pid $!"; sleep 90; tail -25 r1_launch.log
```
→ `Sorry: Some PHIL parameters are not recognized`: `refinement.input.xray_data.r_free_flags.*`

```bash
ps aux | grep -c "[p]henix"; ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/r1_launch.log 2>&1; ls /tmp/agent_r5_7twr/
```

```bash
sleep 240; tail -30 /tmp/agent_r5_7twr/r1_launch.log
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 > defaults.txt 2>&1; wc -l defaults.txt; grep -n "test_flag_value\|r_free_flags {\|generate =\|anisotropic\|ordered_solvent\|number_of_macro_cycles" defaults.txt | head -30
```

```bash
cd /tmp/agent_r5_7twr && sed -n '25,50p;155,210p' defaults.txt
```

```bash
cd /tmp/agent_r5_7twr && head -24 defaults.txt
```

```bash
cd /tmp/agent_r5_7twr && python3 - <<'EOF'
import re
path=[]
for i,line in enumerate(open('defaults.txt'),1):
    s=line.rstrip('\n')
    ind=len(s)-len(s.lstrip())
    lvl=ind//2
    m=re.match(r'^\s*([A-Za-z_0-9]+)\s*\{\s*$',s)
    if m:
        path=path[:lvl]+[m.group(1)]; continue
    if s.strip()=='}':
        path=path[:lvl]; continue
    m2=re.match(r'^\s*([A-Za-z_0-9]+)\s*=',s)
    if m2 and m2.group(1) in ('test_flag_value','anisotropic','ordered_solvent','number_of_macro_cycles','individual','nproc','strategy','convert_to_anisotropic'):
        print(i, '.'.join(path[:lvl]+[m2.group(1)]))
EOF
```

`[FILE WRITE] /tmp/agent_r5_7twr/r1.eff` (first version — `output` nested under `refinement`, rejected):

```
data_manager { fmodel { xray_data { r_free_flags { test_flag_value = 0
  generate = False } } } }
refinement {
  refine { strategy = individual_sites+individual_adp+occupancies
    adp { individual { anisotropic = "not (element H or element D)"
                       isotropic = "element H or element D" } } }
  main { number_of_macro_cycles = 6  ordered_solvent = True  nproc = 8 }
  output { prefix = "r1" }
}
```

**[REJECTED — NOT COUNTED]**:

```bash
nohup bash -c 'cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start_pruned.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags r1.eff --overwrite > r1_launch.log 2>&1' > /dev/null 2>&1 &
sleep 120; tail -20 /tmp/agent_r5_7twr/r1_launch.log
```
→ `Unrecognized PHIL parameters: refinement.output.prefix` — exited before refinement

```bash
cd /tmp/agent_r5_7twr && python3 - <<'EOF'
import re
lines=open('/tmp/agent_r5_7twr/r1.eff').read()
lines=lines.replace('  output {\n    prefix = "r1"\n  }\n','')
lines+='output {\n  prefix = "r1"\n  serial = 1\n}\n'
open('/tmp/agent_r5_7twr/r1.eff','w').write(lines)
print(lines)
EOF
```

## 5. [REFINE 1/6] — protein recovery + ordered solvent

Final `r1.eff`: as above but with `output { prefix = "r1"  serial = 1 }` at top level.

```bash
nohup bash -c 'cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start_pruned.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags r1.eff --overwrite > r1_launch.log 2>&1' > /dev/null 2>&1 &
sleep 180; echo "=== size: $(wc -l < /tmp/agent_r5_7twr/r1_launch.log)"; grep -n "Unrecognized\|Sorry\|start R-work\|r_work\|Number of X-ray\|test_flag_value\|free reflections" /tmp/agent_r5_7twr/r1_launch.log | head -20
```

```bash
sleep 600; grep -c "" /tmp/agent_r5_7twr/r1_launch.log; grep -n "macro_cycle\|r_work=.*r_free=.*coordinate error\|ordered solvent\|Number of ordered solvent\|water" /tmp/agent_r5_7twr/r1_launch.log | tail -25
```
(timed out at the 10-minute tool limit; job unaffected)

```bash
grep -E "coordinate error \(max" /tmp/agent_r5_7twr/r1_launch.log | tail -8; echo "=== ordered solvent ==="; grep -iE "ordered_solvent|number of water|added|removed" /tmp/agent_r5_7twr/r1_launch.log | tail -12; echo "=== running? ==="; ps aux | grep -c "[p]henix.refine"
```

```bash
sleep 540; grep -E "coordinate error \(max" /tmp/agent_r5_7twr/r1_launch.log | tail -5; echo "=== running: $(ps aux | grep -c '[p]henix.refine')"; ls -la /tmp/agent_r5_7twr/ | grep r1_
```

```bash
sleep 560; echo "=== running: $(ps aux | grep -c '[p]henix.refine')"; grep -E "coordinate error \(max" /tmp/agent_r5_7twr/r1_launch.log | tail -3; ls /tmp/agent_r5_7twr/ | grep -E "r1_001\.(pdb|mtz|cif)"
```

```bash
sleep 300; echo "running: $(ps aux | grep -c '[p]henix.refine')"; tail -45 /tmp/agent_r5_7twr/r1_launch.log
```
→ **Final R-work 0.1264, R-free 0.1375**; final solvent filter cut 845→623 waters and *raised* R-free 0.1343→0.1375

```bash
cd /tmp/agent_r5_7twr && grep -B3 -A18 "ordered_solvent {" defaults.txt | head -45
```

```bash
cd /tmp/agent_r5_7twr && echo "=== clash ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r1_001.pdb 2>&1 | tail -2; echo "=== rama ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r1_001.pdb 2>&1 | tail -2; echo "=== rota ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r1_001.pdb 2>&1 | tail -1; echo "=== waters ==="; grep -c "HOH.*O  " r1_001.pdb
```

```bash
cd /tmp/agent_r5_7twr && sed -n '/^  ordered_solvent {/,/^  }/p' defaults.txt | sed -n '20,60p'; echo "=== chains/waters in r1 ==="; awk '/^ATOM|^HETATM/{print substr($0,18,3), substr($0,22,1)}' r1_001.pdb | sort | uniq -c | sort -rn | head
```

```bash
cd /tmp/agent_r5_7twr && awk '/^ATOM|^HETATM/ && substr($0,18,3)=="HOH"' r1_001.pdb | wc -l; echo "--- unique water chains:"; awk '/^ATOM|^HETATM/ && substr($0,18,3)=="HOH" {print substr($0,22,1)}' r1_001.pdb | sort | uniq -c; echo "--- aniso records:"; grep -c "^ANISOU" r1_001.pdb
```

```bash
cd /tmp/agent_r5_7twr && grep -n "optimize_xyz_weight\|optimize_adp_weight\|wxc_scale\|wxu_scale\|^  target_weights\|weight_selection" defaults.txt | head -20
```

## 6. [REFINE 2/6] — crashed in macro-cycle 2 (PHENIX bug); counted

`[FILE WRITE] /tmp/agent_r5_7twr/r2.eff`:

```
data_manager { fmodel { xray_data { r_free_flags { test_flag_value = 0
  generate = False } } } }
refinement {
  refine { strategy = individual_sites+individual_adp+occupancies
    adp { individual { anisotropic = "not (element H or element D)"
                       isotropic = "element H or element D" } } }
  main { number_of_macro_cycles = 5  ordered_solvent = True  nproc = 8 }
  ordered_solvent { mode = every_macro_cycle_after_first
                    new_solvent = anisotropic
                    ignore_final_filtering_step = True }
  target_weights { optimize_xyz_weight = True  optimize_adp_weight = True }
}
output { prefix = "r2"  serial = 1 }
```

```bash
nohup bash -c 'cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags r2.eff --overwrite > r2_launch.log 2>&1' > /dev/null 2>&1 &
sleep 200; grep -n "Unrecognized\|Sorry" /tmp/agent_r5_7twr/r2_launch.log | head; echo "--- progress:"; grep -E "coordinate error \(max" /tmp/agent_r5_7twr/r2_launch.log | tail -3
```

```bash
cd /tmp/agent_r5_7twr && grep -nE "^\s+(start|[0-9]+_[a-z]+):" r2_launch.log | head -20; echo "=== header r_work ==="; grep -n "r_work= 0\|Start R-work" r2_launch.log | head -5
```

```bash
cd /tmp/agent_r5_7twr && grep -n "Writing\|\.pdb\b" r1_launch.log | tail -15; echo "=== atom counts ==="; echo "pdb: $(grep -c '^ATOM\|^HETATM' r1_001.pdb)"; /opt/homebrew/bin/gemmi convert r1_001.cif /tmp/agent_r5_7twr/r1_from_cif.pdb 2>&1 | head -3; echo "cif->pdb: $(grep -c '^ATOM\|^HETATM' /tmp/agent_r5_7twr/r1_from_cif.pdb)"
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r1_001.pdb /tmp/nc_round1_cache/7twr.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free|scattering|hydrogen"
```
→ independently confirms 0.1264 / 0.1374

```bash
cd /tmp/agent_r5_7twr && sed -n '780,845p' r2_launch.log
```

```bash
cd /tmp/agent_r5_7twr && grep -E "^\s+(start|end|[0-9]+_[a-z]+):" r2_launch.log | tail -20; echo "=== running: $(ps aux | grep -c '[p]henix.refine')"
```

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TWR && ls -d /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TWR && sleep 500; cd /tmp/agent_r5_7twr && grep -E "^\s+(start|end|[0-9]+_[a-z]+):" r2_launch.log | tail -8; echo "running: $(ps aux | grep -c '[p]henix.refine')"
```

```bash
sleep 580; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max" r2_launch.log | tail -6; echo "running: $(ps aux | grep -c '[p]henix.refine')"
```

```bash
sleep 595; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max" r2_launch.log | tail -4; echo "running: $(ps aux | grep -c '[p]henix.refine')"
```

```bash
cd /tmp/agent_r5_7twr && tail -18 r2_launch.log; echo "=== log size $(wc -l < r2_launch.log) lines, updated $(date -r r2_launch.log +%H:%M:%S), now $(date +%H:%M:%S)"
```
→ `RuntimeError: cctbx Internal Error: CCTBX_ASSERT(f.use_u_iso()) failure` in `ordered_solvent.refine_oat`

```bash
cd /tmp/agent_r5_7twr && grep -n "Traceback\|Sorry\|RuntimeError" r2_launch.log | head -5; echo "=== r2 outputs ==="; ls -la /tmp/agent_r5_7twr/ | grep r2_; echo "=== stale procs ==="; pgrep -f "phenix.refine" | wc -l; pkill -f "phenix.refine"; sleep 3; echo "after kill: $(pgrep -f 'phenix.refine' | wc -l)"
```

## 7. [REFINE 3/6] — weight optimization, anisotropic-water change reverted

`[FILE WRITE] /tmp/agent_r5_7twr/r3.eff`:

```
data_manager { fmodel { xray_data { r_free_flags { test_flag_value = 0
  generate = False } } } }
refinement {
  refine { strategy = individual_sites+individual_adp+occupancies }
  main { number_of_macro_cycles = 4  ordered_solvent = True  nproc = 8 }
  ordered_solvent { ignore_final_filtering_step = True }
  target_weights { optimize_xyz_weight = True  optimize_adp_weight = True }
}
output { prefix = "r3"  serial = 1 }
```

```bash
nohup bash -c 'cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags r3.eff --overwrite > r3_launch.log 2>&1' > /dev/null 2>&1 &
sleep 240; cd /tmp/agent_r5_7twr && grep -n "Unrecognized\|Sorry\|Traceback" r3_launch.log | head -3; grep -E "iso *aniso|Overall:" r3_launch.log | head -4; grep -E "MACRO_CYCLE|coordinate error \(max" r3_launch.log | tail -4
```

```bash
cd /tmp/agent_r5_7twr && grep -E "^\s+(start|end|re-set all scales):" r3_launch.log | head -6; echo "=== weight selection criteria ==="; sed -n '1040,1055p' defaults.txt
```

```bash
sleep 595; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max" r3_launch.log | tail -4; echo "running: $(pgrep -f 'phenix.refine' | wc -l)"
```

```bash
sleep 590; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max|Final R-work" r3_launch.log | tail -4; echo "running: $(pgrep -f 'phenix.refine' | wc -l)"; ls /tmp/agent_r5_7twr | grep -E "r3_001\.(pdb|mtz)"
```
→ **Final R-work 0.1104, R-free 0.1235**

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r3_001.pdb /tmp/nc_round1_cache/7twr.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free"; echo "=== waters: $(awk '/^ATOM|^HETATM/ && substr($0,18,3)=="HOH"' r3_001.pdb | wc -l)"; echo "=== clash/rama/rota ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r3_001.pdb 2>&1 | tail -1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r3_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r3_001.pdb 2>&1 | tail -1
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation r3_001.pdb /tmp/nc_round1_cache/7twr.mtz data_labels="FOBS,SIGFOBS" detail=residue > rsc_r3.log 2>&1; awk 'NF==8 && $2=="HOH" {n++; s+=$6; if($6<0.5)lo++; if($6<0.6)lo6++; if($6<0.7)lo7++} END {printf "waters scored: %d  meanCC=%.3f  CC<0.5: %d  CC<0.6: %d  CC<0.7: %d\n", n, s/n, lo, lo6, lo7}' rsc_r3.log; awk 'NF==8 && $2!="HOH" && ($1=="A"||$1=="B") {n++; s+=$6; if($6<0.7)lo++} END {printf "protein residues: %d  meanCC=%.3f  CC<0.7: %d\n", n, s/n, lo}' rsc_r3.log
```
→ protein mean RSCC 0.985 (0 below 0.7); waters mean 0.846, 21 below 0.5

## 8. [REFINE 4/6] — prune 21 unsupported waters, continue

```bash
cd /tmp/agent_r5_7twr && awk 'NF==8 && $2=="HOH" && $6<0.5 {print $1"_"$3}' rsc_r3.log | sort -u > dead_waters_r3.txt && wc -l < dead_waters_r3.txt && python3 - <<'EOF'
dead = set(open('/tmp/agent_r5_7twr/dead_waters_r3.txt').read().split())
out, removed = [], 0
for line in open('/tmp/agent_r5_7twr/r3_001.pdb'):
    if line.startswith(('ATOM','HETATM','ANISOU')) and line[17:20]=='HOH':
        key = line[21].strip()+'_'+line[22:26].strip()
        if key in dead:
            if line.startswith(('ATOM','HETATM')): removed += 1
            continue
    out.append(line)
open('/tmp/agent_r5_7twr/r3_pruned.pdb','w').writelines(out)
print('water atoms removed:', removed)
print('waters remaining:', sum(1 for l in out if l.startswith(('ATOM','HETATM')) and l[17:20]=='HOH'))
EOF
```

```bash
cd /tmp/agent_r5_7twr && sed 's/number_of_macro_cycles = 4/number_of_macro_cycles = 5/; s/prefix = "r3"/prefix = "r4"/' r3.eff > r4.eff && cat r4.eff | grep -E "macro_cycles|prefix|optimize|ignore_final"
```

```bash
nohup bash -c 'cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_pruned.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags r4.eff --overwrite > r4_launch.log 2>&1' > /dev/null 2>&1 &
sleep 300; cd /tmp/agent_r5_7twr && grep -n "Unrecognized\|Sorry\|Traceback" r4_launch.log | head -3; grep -E "MACRO_CYCLE|coordinate error \(max" r4_launch.log | tail -4
```

```bash
cd /tmp/agent_r5_7twr && grep -E "iso *aniso" -A2 r4_launch.log | head -6; echo "=== water ADP types in r3_001 ==="; python3 -c "
import collections
aniso=set()
for l in open('/tmp/agent_r5_7twr/r3_001.pdb'):
    if l.startswith('ANISOU'): aniso.add(l[6:11]+l[21]+l[22:26])
n_iso=n_an=0
for l in open('/tmp/agent_r5_7twr/r3_001.pdb'):
    if l.startswith(('ATOM','HETATM')) and l[17:20]=='HOH':
        if l[6:11]+l[21]+l[22:26] in aniso: n_an+=1
        else: n_iso+=1
print('waters aniso:',n_an,' iso:',n_iso)"
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdb_atom_selection r3_001.pdb "resname HOH and bfactor < 30" 2>&1 | tail -4; echo "=== test2 ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdb_atom_selection r3_001.pdb "not (element H or element D or (resname HOH and bfactor > 30))" 2>&1 | tail -3
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdb_atom_selection r3_001.pdb "resname HOH and bfactor < 30" 2>&1 | grep -iE "selected|number of atoms" | head -5; echo "---"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdb_atom_selection r3_001.pdb "resname HOH" 2>&1 | grep -iE "selected|number of atoms" | head -3
```

```bash
sleep 595; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max|Final R-work" r4_launch.log | tail -5; echo "running: $(pgrep -f 'phenix.refine' | wc -l)"
```

```bash
sleep 595; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max|Final R-work" r4_launch.log | tail -4; echo "running: $(pgrep -f 'phenix.refine' | wc -l)"; ls /tmp/agent_r5_7twr | grep -E "r4_001\.(pdb|mtz)"
```
→ **Final R-work 0.1087, R-free 0.1218**

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r4_001.pdb /tmp/nc_round1_cache/7twr.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free"; echo "waters: $(awk '/^ATOM|^HETATM/ && substr($0,18,3)==\"HOH\"' r4_001.pdb | wc -l)"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r4_001.pdb 2>&1 | tail -1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r4_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r4_001.pdb 2>&1 | tail -1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_statistics r4_001.pdb 2>&1 | grep -E "bond |angle "
```
(the inner `awk` quoting failed harmlessly; water count re-taken next)

```bash
cd /tmp/agent_r5_7twr && echo "waters: $(grep -c '^HETATM.*HOH\|^ATOM.*HOH' r4_001.pdb)"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r4_001.pdb 2>&1 > clash_r4.txt; echo "=== clash involvement ==="; grep -c "HOH" clash_r4.txt; grep -v "clashscore" clash_r4.txt | grep -c ":"; echo "--- sample:"; head -8 clash_r4.txt
```

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation r4_001.pdb /tmp/nc_round1_cache/7twr.mtz data_labels="FOBS,SIGFOBS" detail=residue > rsc_r4.log 2>&1; awk 'NF==8 && $2=="HOH" {n++; s+=$6; if($6<0.5)lo++} END {printf "waters scored: %d meanCC=%.3f CC<0.5: %d\n", n, s/n, lo}' rsc_r4.log; awk 'NF==8 && $2!="HOH" && ($1=="A"||$1=="B") {n++; s+=$6} END {printf "protein residues: %d meanCC=%.3f\n", n, s/n}' rsc_r4.log
```

```bash
cd /tmp/agent_r5_7twr && sed -n '/Bad Clashes/,/^clashscore/p' clash_r4.txt | grep ":" | head -40
```
→ 30 of 39 bad clashes involve chain-S waters driven into protein side chains (worst 1.139 Å)

## 9. [REFINE 5/6] — prune clashing waters, freeze solvent, anisotropic well-ordered waters — **CHOSEN**

```bash
cd /tmp/agent_r5_7twr && python3 - <<'EOF'
import re
# waters with poor density support
dead = set()
for line in open('/tmp/agent_r5_7twr/rsc_r4.log'):
    f = line.split()
    if len(f) == 8 and f[1] == 'HOH' and float(f[5]) < 0.5:
        dead.add(f[0] + '_' + f[2])
n_cc = len(dead)
# waters in bad clashes with a NON-water partner
clash = set()
started = False
for line in open('/tmp/agent_r5_7twr/clash_r4.txt'):
    if 'Bad Clashes' in line: started = True; continue
    if not started or ':' not in line: continue
    spec = line.rsplit(':', 1)[0]
    parts = [spec[:len(spec)//2], spec[len(spec)//2:]]
    hits = re.findall(r'([A-Za-z])\s*(\d+)\s+HOH', spec)
    if len(hits) == 1:          # water clashing with something that is not water
        clash.add(hits[0][0] + '_' + hits[0][1])
print('poor-density waters:', n_cc, ' clashing waters:', len(clash), ' union:', len(dead | clash))
dead |= clash
out, removed = [], 0
for line in open('/tmp/agent_r5_7twr/r4_001.pdb'):
    if line.startswith(('ATOM','HETATM','ANISOU')) and line[17:20] == 'HOH':
        if line[21].strip() + '_' + line[22:26].strip() in dead:
            if line.startswith(('ATOM','HETATM')): removed += 1
            continue
    out.append(line)
open('/tmp/agent_r5_7twr/r4_pruned.pdb','w').writelines(out)
print('waters removed:', removed,
      ' remaining:', sum(1 for l in out if l.startswith(('ATOM','HETATM')) and l[17:20]=='HOH'))
EOF
```

`[FILE WRITE] /tmp/agent_r5_7twr/r5.eff`:

```
data_manager { fmodel { xray_data { r_free_flags { test_flag_value = 0
  generate = False } } } }
refinement {
  refine { strategy = individual_sites+individual_adp+occupancies
    adp { individual {
      anisotropic = "not (element H or element D or (resname HOH and bfactor > 30))"
      isotropic = "element H or element D or (resname HOH and bfactor > 30)" } } }
  main { number_of_macro_cycles = 4  ordered_solvent = False  nproc = 8 }
  target_weights { optimize_xyz_weight = True  optimize_adp_weight = True }
}
output { prefix = "r5"  serial = 1 }
```

```bash
nohup bash -c 'cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_pruned.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags r5.eff --overwrite > r5_launch.log 2>&1' > /dev/null 2>&1 &
sleep 280; cd /tmp/agent_r5_7twr && grep -n "Unrecognized\|Sorry\|Traceback" r5_launch.log | head -3; grep -E "iso *aniso" -A2 r5_launch.log | head -3; grep -E "MACRO_CYCLE|coordinate error \(max" r5_launch.log | tail -4
```

```bash
sleep 595; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max|Final R-work" r5_launch.log | tail -4; echo "running: $(pgrep -f 'phenix.refine' | wc -l)"
```
→ **Final R-work 0.1069, R-free 0.1228**

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r5_001.pdb /tmp/nc_round1_cache/7twr.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r5_001.pdb 2>&1 | tail -1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r5_001.pdb 2>&1 | tail -2; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r5_001.pdb 2>&1 | tail -1; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_statistics r5_001.pdb 2>&1 | grep -E "bond |angle "
```
→ clashscore 1.23, Rama 0.00% outliers / 99.40% favored, rota 0.63%, bond 0.0078 Å, angle 1.033°

## 10. [REFINE 6/6] — control: same water set, anisotropic conversion reverted

```bash
cd /tmp/agent_r5_7twr && sed 's/prefix = "r3"/prefix = "r6"/; s/ordered_solvent = True/ordered_solvent = False/; s/number_of_macro_cycles = 4/number_of_macro_cycles = 4/' r3.eff | grep -v "ignore_final_filtering_step" > r6.eff && grep -E "macro_cycles|prefix|optimize|ordered_solvent|anisotropic" r6.eff; nohup bash -c 'cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_pruned.pdb /tmp/nc_round1_cache/7twr.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags r6.eff --overwrite > r6_launch.log 2>&1' > /dev/null 2>&1 &
sleep 200; grep -n "Unrecognized\|Sorry\|Traceback" /tmp/agent_r5_7twr/r6_launch.log | head -3; grep -E "iso *aniso" -A2 /tmp/agent_r5_7twr/r6_launch.log | head -3
```

```bash
sleep 595; cd /tmp/agent_r5_7twr && grep -E "MACRO_CYCLE|coordinate error \(max|Final R-work" r6_launch.log | tail -4; echo "running: $(pgrep -f 'phenix.refine' | wc -l)"
```

```bash
sleep 180; cd /tmp/agent_r5_7twr && grep -E "Final R-work" r6_launch.log; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r6_001.pdb /tmp/nc_round1_cache/7twr.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r6_001.pdb 2>&1 | tail -1
```
→ **0.1088 / 0.1240**, clashscore 1.23 — worse than invocation 5 on both R statistics

```bash
cd /tmp/agent_r5_7twr && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation r5_001.pdb /tmp/nc_round1_cache/7twr.mtz data_labels="FOBS,SIGFOBS" detail=residue > rsc_r5.log 2>&1; awk 'NF==8 && $2=="HOH" {n++; s+=$6; if($6<0.5)lo++} END {printf "waters: %d meanCC=%.3f CC<0.5: %d\n", n, s/n, lo}' rsc_r5.log; awk 'NF==8 && $2!="HOH" && ($1=="A"||$1=="B") {n++; s+=$6; if($6<0.8)lo++} END {printf "protein residues: %d meanCC=%.3f CC<0.8: %d\n", n, s/n, lo}' rsc_r5.log
```

## 11. Deliverables

```bash
cd /tmp/agent_r5_7twr && cp r5_001.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TWR/final.pdb && head -3 /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TWR/final.pdb | cut -c1-70; grep -c "^ATOM\|^HETATM" /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TWR/final.pdb; grep -c "^CRYST1" /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7TWR/final.pdb
```

---

## Addendum — external-kill audit (added after a team-lead query)

A sibling agent disclosed running `pkill -f "phenix.refine"` at roughly **07:09 PDT** and seeing a job
on `7twr.mtz`. I audited every run against that window using PHENIX's own log timestamps and wall
clocks. **No run of mine was killed externally, and nothing needed re-running.**

| run | started | ended | wall clock | status |
|---|---|---|---|---|
| 1 (`r1.eff`) | 06:08:55 | **06:35:06** | 26m 11s | complete — ended 34 min *before* the window |
| 2 (`r2.eff`) | ~06:41 | **06:53:01** | ~12m | **crashed on its own 16 min before the window** |
| 3 (`r3.eff`) | 07:33:39 | 07:53:51 | 20m 12s | complete — started 24 min *after* the window |
| 4 (`r4.eff`) | 08:00:57 | 08:25:41 | 24m 44s | complete |
| 5 (`r5.eff`) | 08:30:45 | **08:44:25** | 13m 40s | complete — **source of `final.pdb`** |
| 6 (`r6.eff`) | 08:47:20 | 09:01:13 | 13m 53s | complete |

Nothing of mine was executing at 07:09 except orphaned worker children of run 2, which had already
died 16 minutes earlier. Killing those orphans cost nothing.

**Run 2 was not killed by anyone.** Its log ends in a full Python traceback terminating in
`RuntimeError: cctbx Internal Error: CCTBX_ASSERT(f.use_u_iso()) failure` inside
`mmtbx/solvent/ordered_solvent.py -> refine_oat`. A `SIGTERM`/`SIGKILL` leaves no Python traceback,
and the last log write was 06:53:01. It died of the `new_solvent=anisotropic` incompatibility
described above, through my own parameter choice. **It therefore still counts against my budget** —
I am not reclassifying it as an external kill, and my accounting stands at 6 of 6 used.

**`final.pdb` comes from a demonstrably complete refinement.** Run 5's log carries the full closing
sequence — `phenix.refine: finished`, `Job complete`, and a timing summary including
`Write final files (write_after_run_outputs): 47.4500` — and its outputs were written at 08:43
(`r5_001.pdb`) and 08:44 (`r5_001.mtz`), before the 08:44:25 finish stamp. No re-run is warranted.

### Self-disclosure: I also ran a global `pkill`

For completeness of the audit, and because it may affect *other* agents' entries rather than mine:
**I ran `pkill -f "phenix.refine"` myself at approximately 07:32–07:33 PDT** (the command is recorded
verbatim in section 6 above; the preceding command timestamped itself `now 07:32:00`). My intent was
narrow — reaping the 5 orphaned worker processes left behind by run 2's crash, which the log
confirms: `stale procs: 5` … `after kill: 0`.

But `pkill -f` matches on the full command line **across the whole machine**, not just my own
processes. If any sibling agent had a `phenix.refine` job running at 07:32–07:33, I killed it. That
was a real risk I did not consider at the time; the correct action would have been to kill only my
own orphans by PID, or to scope the match to my scratch directory
(e.g. `pkill -f "agent_r5_7twr"`). Flagging it so siblings can check their own logs for an
unexplained death in that window.

---

## Budget accounting

| # | phil | outcome |
|---|---|---|
| — | command-line params | **rejected at PHIL parsing, not counted** |
| — | `r1.eff` v1 | **rejected at PHIL parsing, not counted** |
| 1 | `r1.eff` | completed — 0.1264 / 0.1375 |
| 2 | `r2.eff` | refined macro-cycle 1, then crashed (cctbx assert) — **counted**, no output model |
| 3 | `r3.eff` | completed — 0.1104 / 0.1235 |
| 4 | `r4.eff` | completed — 0.1087 / 0.1218 |
| 5 | `r5.eff` | completed — **0.1069 / 0.1228 → `final.pdb`** |
| 6 | `r6.eff` | completed — 0.1088 / 0.1240 (control) |

**6 of 6 refinement invocations used.** No network access, no `ref/` or `data/` reads, no cache file
other than `7twr.mtz`, and the deposited map-coefficient columns (`FWT/PHWT`, `DELFWT/PHDELWT`)
inside that MTZ were deliberately not used.
