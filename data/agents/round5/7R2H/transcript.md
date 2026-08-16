# 7R2H blinded agentic recovery — verbatim shell transcript

Every shell command executed for this task, in execution order. Commands are
reproduced exactly as run. Working directory for all `cd`-prefixed commands is
`/tmp/agent_r5_7r2h/`.

Refinement-program invocations are flagged **[REFINE n/6]**. Six were consumed
(run 4 was killed mid-run and produced no model; it is still counted). The
`setsid` attempt at #53 is explicitly flagged as having started no process.

---

### 1
```bash
mkdir -p /tmp/agent_r5_7r2h && cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi mtzinfo /tmp/nc_round1_cache/7r2h.mtz
```
(failed: `'mtzinfo' is not a gemmi command`)

### 2
```bash
/opt/homebrew/bin/gemmi info /tmp/nc_round1_work/r4p_7r2h.pdb
```
(failed: `'info' is not a gemmi command`)

### 3
```bash
/opt/homebrew/bin/gemmi --help 2>&1 | head -50
```

### 4
```bash
/opt/homebrew/bin/gemmi mtz /tmp/nc_round1_cache/7r2h.mtz
```

### 5
```bash
/opt/homebrew/bin/gemmi contents /tmp/nc_round1_work/r4p_7r2h.pdb
```

### 6
```bash
head -30 /tmp/nc_round1_work/r4p_7r2h.pdb; echo "---- ANISOU/altloc check ----"; grep -c "^ANISOU" /tmp/nc_round1_work/r4p_7r2h.pdb; echo "atoms:"; grep -c "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_7r2h.pdb; echo "altlocs:"; awk '/^ATOM|^HETATM/{print substr($0,17,1)}' /tmp/nc_round1_work/r4p_7r2h.pdb | sort | uniq -c
```

### 7
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_7r2h.pdb /tmp/nc_round1_cache/7r2h.mtz labels=FOBS,SIGFOBS 2>&1 | tail -60
```
(failed: `Unknown command line parameter definition: labels = FOBS,SIGFOBS`)

### 8
```bash
cd /tmp/agent_r5_7r2h && awk '/^ATOM|^HETATM/{el=substr($0,77,2); occ=substr($0,55,6)+0; if(el~/H/) print "H",occ; else print "nonH",occ}' /tmp/nc_round1_work/r4p_7r2h.pdb | sort | uniq -c | sort -k2,2 -k3,3n | head -40
```

### 9
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data --help 2>&1 | head -60
```

### 10
```bash
cd /tmp/agent_r5_7r2h && awk '/^ATOM|^HETATM/{el=substr($0,77,2); occ=substr($0,55,6)+0; if(el!~/H/) print occ}' /tmp/nc_round1_work/r4p_7r2h.pdb | sort -n | uniq -c | head -30; echo "=== B factor stats nonH ==="; awk '/^ATOM|^HETATM/{el=substr($0,77,2); b=substr($0,61,6)+0; if(el!~/H/) print b}' /tmp/nc_round1_work/r4p_7r2h.pdb | sort -n | awk '{a[NR]=$1} END{print "min",a[1],"med",a[int(NR/2)],"max",a[NR],"n",NR}'
```

### 11 — baseline R
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_7r2h.pdb /tmp/nc_round1_cache/7r2h.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | tail -50
```

### 12
```bash
grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_7r2h.pdb | awk 'substr($0,77,2)!~/H/ && substr($0,55,6)+0 < 1' | head -40
```

### 13
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi rmsz /tmp/nc_round1_work/r4p_7r2h.pdb 2>&1 | tail -20
```
(failed: `Set $CLIBD_MON or use option --monomers.`)

### 14 — verify free-flag convention
```bash
cd /tmp/agent_r5_7r2h && python3 -c "
import gemmi
mtz=gemmi.read_mtz_file('/tmp/nc_round1_cache/7r2h.mtz')
import numpy as np
d=mtz.column_with_label('R-free-flags').array
print('flag 0:',int((d==0).sum()),' flag 1:',int((d==1).sum()),' total',d.size)
d1=mtz.column_with_label('R-free-flags-1').array
import collections
print('R-free-flags-1 hist:',sorted(collections.Counter(d1.astype(int)).items())[:5])
"
```

### 15 — reset hydrogen occupancies to parent occupancy
```bash
cd /tmp/agent_r5_7r2h && python3 << 'EOF'
import gemmi
st = gemmi.read_structure('/tmp/nc_round1_work/r4p_7r2h.pdb')
st.setup_entities()
changed = 0
for model in st:
    for chain in model:
        for res in chain:
            # group by altloc
            groups = {}
            for atom in res:
                if atom.element != gemmi.Element('H') and atom.element != gemmi.Element('D'):
                    groups.setdefault(atom.altloc, []).append(atom.occ)
            for atom in res:
                if atom.element == gemmi.Element('H') or atom.element == gemmi.Element('D'):
                    cand = groups.get(atom.altloc) or groups.get('') or [o for v in groups.values() for o in v]
                    if cand:
                        newocc = max(cand)
                        if abs(newocc - atom.occ) > 1e-6:
                            atom.occ = newocc
                            changed += 1
print('H occupancies reset:', changed)
st.setup_entities()
st.write_pdb('/tmp/agent_r5_7r2h/start.pdb')
EOF
grep -c "^ATOM\|^HETATM" /tmp/agent_r5_7r2h/start.pdb
```

### 16
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data start.pdb /tmp/nc_round1_cache/7r2h.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "r_work|r_free"
```

### 17
```bash
cd /tmp/agent_r5_7r2h && (/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_statistics start.pdb 2>&1 || /Users/marcin/phenix-2.0-5936/phenix_bin/mmtbx.model_statistics start.pdb 2>&1) | grep -iE "bond|angle|dihedral|chirality|planarity|rmsd|deviation" | head -25
```

### 18
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | grep -n "labels\|test_flag_value\|anisotropic\|strategy\|number_of_macro" | head -30
```

### 19
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | sed -n '1,70p'
```

### 20
```bash
sysctl -n hw.ncpu
```

### 21
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | sed -n '120,220p'
```

### 22
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | grep -nE "^  nproc|nproc =|random_seed" | head
```

### 23 — **[REFINE 1/6]** recovery refinement
```bash
cd /tmp/agent_r5_7r2h && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start.pdb /tmp/nc_round1_cache/7r2h.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" xray_data.r_free_flags.test_flag_value=0 main.number_of_macro_cycles=8 output.prefix=r1 --overwrite > r1.log 2>&1; echo "EXIT=$?"; tail -40 r1.log
```
Result: R-work 0.4332 → 0.1473, R-free 0.4410 → 0.1585.

### 24
```bash
cd /tmp/agent_r5_7r2h && ls; echo "=== macrocycle ends ==="; grep -E "^ +[0-9]+_?start:|^ +end:|^ +[0-9]+_occ:" r1.log | head -30
```

### 25
```bash
cd /tmp/agent_r5_7r2h && echo "=== CLASH ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r1_001.pdb 2>&1 | tail -2; echo "=== RAMA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r1_001.pdb 2>&1 | tail -3; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r1_001.pdb 2>&1 | tail -2; echo "=== waters aniso? ==="; grep " HOH " r1_001.pdb | grep -c "^ANISOU"; echo "total HOH O atoms:"; grep "^HETATM" r1_001.pdb | grep -c " HOH "
```

### 26
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi blobs --help 2>&1 | head -20
```

### 27
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi mtz r1_001.mtz | grep -A25 "Column  "
```

### 28
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi blobs --mask-water --sigma=3.0 -f FOFCWT -p PHFOFCWT r1_001.mtz r1_001.pdb 2>&1 | tail -25
```
(failed: usage dump)

### 29
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi blobs -d --mask-water r1_001.mtz r1_001.pdb 2>&1 | head -25
```
(failed: `Invalid option.`)

### 30
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi blobs r1_001.mtz r1_001.pdb 2>&1 | head -20; echo "=== now with sigma ==="; /opt/homebrew/bin/gemmi blobs --sigma=3.5 r1_001.mtz r1_001.pdb 2>&1 | head -20
```

### 31 — isolate which gemmi option is unsupported
```bash
cd /tmp/agent_r5_7r2h && for opt in "--mask-water" "-f FOFCWT -p PHFOFCWT" "--min-volume=2" "--min-score=2"; do printf "%-30s -> " "$opt"; /opt/homebrew/bin/gemmi blobs $opt --sigma=3.0 r1_001.mtz r1_001.pdb 2>&1 | head -1; done
```
(`--mask-water` is advertised in help but not implemented in this build)

### 32
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi blobs -f FOFCWT -p PHFOFCWT --sigma=3.0 --min-volume=2 --min-score=2 r1_001.mtz r1_001.pdb 2>&1 | tail -40; echo "=== count ==="; /opt/homebrew/bin/gemmi blobs -f FOFCWT -p PHFOFCWT --sigma=3.0 --min-volume=2 --min-score=2 r1_001.mtz r1_001.pdb 2>&1 | grep -c "^#"
```
9 unmodelled blobs, strongest 5.1 e⁻ / 27.9σ near ASN 108.

### 33
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 2>&1 | sed -n '/^  ordered_solvent {/,/^  }/p' | head -45
```

### 34
```bash
cd /tmp/agent_r5_7r2h && grep -c "^ANISOU" r1_001.pdb; grep -c "^ATOM\|^HETATM" r1_001.pdb
```

### 35 — **[REFINE 2/6]** ordered-solvent rebuild
```bash
cd /tmp/agent_r5_7r2h && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/7r2h.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" xray_data.r_free_flags.test_flag_value=0 main.number_of_macro_cycles=6 main.ordered_solvent=True output.prefix=r2 --overwrite > r2.log 2>&1; echo "EXIT=$?"; grep -E "^ +[0-9]+_occ:|^ +end:" r2.log; tail -6 r2.log
```
Result: R-work 0.1409, R-free 0.1513; waters 335 → 460 → 376 after final filter.

### 36
```bash
cd /tmp/agent_r5_7r2h && echo "=== waters ==="; grep "^HETATM" r2_001.pdb | grep -c " HOH "; echo "=== CLASH ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r2_001.pdb 2>&1 | tail -1; echo "=== RAMA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r2_001.pdb 2>&1 | tail -3; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r2_001.pdb 2>&1 | tail -2
```

### 37
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi blobs -f FOFCWT -p PHFOFCWT --sigma=3.0 --min-volume=2 --min-score=2 r2_001.mtz r2_001.pdb 2>&1 | head -30
```
Residual blobs down to 3 (max 2.4 e⁻).

### 38 — **[REFINE 3/6]** anisotropic ADPs for all non-H (test)
```bash
cd /tmp/agent_r5_7r2h && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb /tmp/nc_round1_cache/7r2h.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" xray_data.r_free_flags.test_flag_value=0 main.number_of_macro_cycles=6 refine.adp.individual.anisotropic="not (element H or element D)" output.prefix=r3 --overwrite > r3.log 2>&1; echo "EXIT=$?"; grep -E "^ +[0-9]+_occ:|^ +end:" r3.log; tail -5 r3.log
```
Result: R-work 0.1403, R-free 0.1516 — rejected (no cross-validated gain).

### 39
```bash
cd /tmp/agent_r5_7r2h && echo "r2 ANISOU: $(grep -c '^ANISOU' r2_001.pdb)"; echo "r3 ANISOU: $(grep -c '^ANISOU' r3_001.pdb)"; echo "r3 HOH ANISOU: $(grep '^ANISOU' r3_001.pdb | grep -c ' HOH ')"; echo "r2 HOH ANISOU: $(grep '^ANISOU' r2_001.pdb | grep -c ' HOH ')"
```

### 40
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 2>&1 | grep -nE "optimize_|wxc_scale|wxu_scale|^ *wxc |^ *wxu " | head -20
```

### 41
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>&1 | grep -nE "optimize_xyz_weight|optimize_adp_weight|wxc_scale|wxu_scale|weight_selection" | head -20
```

### 42
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>&1 | sed -n '1015,1060p'
```

### 43 — **[REFINE 4/6]** weight optimisation (later killed mid-run)
```bash
cd /tmp/agent_r5_7r2h && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb /tmp/nc_round1_cache/7r2h.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" xray_data.r_free_flags.test_flag_value=0 main.number_of_macro_cycles=3 main.ordered_solvent=True target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True output.prefix=r4 --overwrite > r4.log 2>&1 &
echo "started PID $!"
```
Killed during ADP refinement; no model written. Log preserved the weight scan.

### 44
```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7R2H && echo created
```

### 45
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r2_001.pdb /tmp/nc_round1_cache/7r2h.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | sed -n '/Resolution    Compl/,/Number of F-obs/p'
```

### 46
```bash
pgrep -fl "phenix.refine|phenix_env|libtbx" | head -5; echo "---"; ls -la /tmp/agent_r5_7r2h/r4* 2>/dev/null
```

### 47
```bash
cd /tmp/agent_r5_7r2h && for i in $(seq 1 120); do if [ -f r4_001.pdb ]; then echo "DONE after ~$((i/2)) min"; break; fi; sleep 30; done; grep -E "^ +[0-9]+_occ:|^ +end:|Final R" r4.log | tail -10
```
(timed out after 60 min)

### 48
```bash
cd /tmp/agent_r5_7r2h && grep -E "^ +[0-9]+_occ:|^ +end:|Final R" r4.log | tail; echo "=== progress ==="; grep -cE "r_work=" r4.log; tail -4 r4.log; echo "=== running? ==="; pgrep -f "prefix=r4" >/dev/null && echo YES || echo NO
```

### 49
```bash
ps aux | grep -i "phenix" | grep -v grep | awk '{print $2, $3, $11, $12, $13}' | head -10; echo "=== log mtime ==="; ls -la /tmp/agent_r5_7r2h/r4.log; date
```

### 50
```bash
cd /tmp/agent_r5_7r2h && tail -30 r4.log; echo "=== grep errors ==="; grep -inE "error|killed|memory|traceback|abort|exception" r4.log | tail -10
```

### 51
```bash
cd /tmp/agent_r5_7r2h && grep -n "XYZ refinement\|Best weight\|WEIGHT" r4.log | head; echo "=== weight table ==="; sed -n '/R-FACTORS             RMSD           CLASH  RAMA  ROTA CBET WEIGHT/,/Best weight/p' r4.log | head -40
```

### 52
```bash
cd /tmp/agent_r5_7r2h && sed -n '1005,1050p' r4.log
```
Weight scan: default 0.905 → 0.1407/0.1529; selected 1.628 → 0.1401/0.1528.

### 53
```bash
ps aux | grep phenix_refine | grep -v grep | awk '{print $2,$3"%cpu",$4"%mem",$NF}'; echo "=== memory ==="; vm_stat | head -6; echo "=== r4 water counts ==="; grep -iE "ordered solvent|number of water|Total number of water" /tmp/agent_r5_7r2h/r4.log | tail -8
```

### 54 — attempted detached launch; **no process started, not counted as an invocation**
```bash
cd /tmp/agent_r5_7r2h && setsid nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb /tmp/nc_round1_cache/7r2h.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" xray_data.r_free_flags.test_flag_value=0 main.number_of_macro_cycles=8 main.ordered_solvent=True target_weights.wxc_scale=0.9 output.prefix=r5 --overwrite > r5.log 2>&1 < /dev/null & disown; sleep 20; echo "launched"; ls -la r5.log
```
(failed: `setsid: command not found` — macOS has no `setsid`; the shell created
the empty redirect target but never executed phenix)

### 55
```bash
which setsid; ls /tmp/agent_r5_7r2h/ | grep r5; ps aux | grep phenix_refine | grep -v grep | wc -l
```

### 56 — confirm the two live phenix jobs belong to sibling agents, not me
```bash
ps aux | grep phenix_refine | grep -v grep | awk '{print $2, $(NF-3), $(NF-2), $(NF-1), $NF}'; echo "=== r5.log size ==="; ls -la /tmp/agent_r5_7r2h/r5.log; echo "=== cwd of procs ==="; for p in $(pgrep -f phenix_refine); do echo "PID $p: $(lsof -p $p 2>/dev/null | awk '$4=="cwd"{print $NF}')"; done
```
Working dirs `/private/tmp/agent_r5_2vxn/r6` and `/private/tmp/agent_r5_4m7g`.

### 57
```bash
cat /tmp/agent_r5_7r2h/r5.log
```

### 58 — **[REFINE 5/6]** second ordered-solvent pass
```bash
cd /tmp/agent_r5_7r2h && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb /tmp/nc_round1_cache/7r2h.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" xray_data.r_free_flags.test_flag_value=0 main.number_of_macro_cycles=8 main.ordered_solvent=True target_weights.wxc_scale=0.9 output.prefix=r5 --overwrite > r5.log 2>&1; echo "EXIT=$?"; grep -E "^ +[0-9]+_occ:|^ +end:|Final R" r5.log
```
Result: 0.1377/0.1501 at macro-cycle 7 with 470 waters; final filter → 388 waters,
0.1401/0.1513.

### 59 — **[REFINE 6/6]** final polish, solvent updating off
```bash
cd /tmp/agent_r5_7r2h && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r5_001.pdb /tmp/nc_round1_cache/7r2h.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" xray_data.r_free_flags.test_flag_value=0 main.number_of_macro_cycles=6 main.ordered_solvent=False target_weights.wxc_scale=0.9 output.prefix=r6 --overwrite > r6.log 2>&1; echo "EXIT=$?"; grep -E "^ +[0-9]+_occ:|^ +end:|Final R" r6.log
```
**Result: R-work 0.1393, R-free 0.1511, 388 waters. This is `final.pdb`.**

### 60 — independent re-measurement of the final model
```bash
cd /tmp/agent_r5_7r2h && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r6_001.pdb /tmp/nc_round1_cache/7r2h.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "r_work:|r_free:|outliers"
```
0.1394 / 0.1512 — agrees with `phenix.refine` to 0.0001.

### 61
```bash
cd /tmp/agent_r5_7r2h && echo "=== CLASH ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r6_001.pdb 2>&1 | tail -1; echo "=== RAMA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze r6_001.pdb 2>&1 | tail -3; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze r6_001.pdb 2>&1 | tail -2; echo "=== GEOM ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_statistics r6_001.pdb 2>&1 | grep -iE "Bond  |Angle |Chirality|Planarity|Nonbonded|Cbeta" | head
```

### 62
```bash
cd /tmp/agent_r5_7r2h && /opt/homebrew/bin/gemmi blobs -f FOFCWT -p PHFOFCWT --sigma=3.0 --min-volume=2 --min-score=2 r6_001.mtz r6_001.pdb 2>&1 | head -15; echo "=== waters ==="; grep "^HETATM" r6_001.pdb | grep -c " HOH "; echo "=== atoms ==="; grep -c "^ATOM\|^HETATM" r6_001.pdb
```
2 residual blobs (3.1 and 2.3 e⁻); 388 waters; 2903 atoms.

### 63 — deliver
```bash
cp /tmp/agent_r5_7r2h/r6_001.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7R2H/final.pdb && ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7R2H/
```

---

## Compliance notes

- **No network access of any kind** was made — no `curl`, `wget`, `phenix.fetch_pdb`,
  or any other retrieval. No deposited coordinates were obtained for 7R2H or any
  other entry.
- The **only** file read from `/tmp/nc_round1_cache/` was `7r2h.mtz`. No
  `*_mask.json`, `*_validation.xml`, or any other cache file was opened.
- Nothing in the repository's `ref/` or `data/` trees was read; the only repository
  path touched was the deliverables directory
  `data/agents/round5/7R2H/`, which was created and written to.
- Refinement-program invocations: **6** (transcript entries 23, 35, 38, 43, 58, 59).
  Entry 54 launched no process and is not counted. All other commands are
  validation, measurement, parameter inspection, or file handling.
