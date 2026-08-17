# 6F1O — verbatim shell transcript, in execution order

Every shell command issued during this task, in order. Annotations in *italics* mark
refinement-budget accounting and failures. Commands were issued from a harness that
resets the working directory between calls, hence the repeated `cd`.

Refinement-program invocations are numbered **[REFINE n/6]**. Launches that failed before
refinement began are marked **[NOT COUNTED]** with the reason.

---

**1.**
```bash
mkdir -p /tmp/agent_r5_6f1o && cd /tmp/agent_r5_6f1o && ls -la /tmp/nc_round1_work/r4p_6f1o.pdb /tmp/nc_round1_cache/6f1o.mtz
```

**2.** *(failed: not a gemmi subcommand)*
```bash
/opt/homebrew/bin/gemmi mtzinfo /tmp/nc_round1_cache/6f1o.mtz 2>&1 | head -50
```

**3.**
```bash
cd /tmp/agent_r5_6f1o && /opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/6f1o.mtz 2>&1 | head -60
```

**4.**
```bash
head -30 /tmp/nc_round1_work/r4p_6f1o.pdb; echo ---; grep -c ATOM /tmp/nc_round1_work/r4p_6f1o.pdb; echo ---; grep HOH /tmp/nc_round1_work/r4p_6f1o.pdb | wc -l; echo ---; tail -5 /tmp/nc_round1_work/r4p_6f1o.pdb
```

**5.**
```bash
cd /tmp/agent_r5_6f1o && /opt/homebrew/bin/gemmi mtz2cif /tmp/nc_round1_cache/6f1o.mtz - 2>/dev/null | awk '$0 !~ /^[#_ldh]/ && NF>5 {print $4}' | sort | uniq -c | head
```

**6.**
```bash
cd /tmp/nc_round1_work && grep -c "^ATOM" r4p_6f1o.pdb; grep -c "^HETATM" r4p_6f1o.pdb; grep "^HETATM" r4p_6f1o.pdb | cut -c18-20 | sort | uniq -c; echo "--- altlocs:"; grep "^ATOM\|^HETATM" r4p_6f1o.pdb | cut -c17 | sort | uniq -c
```

**7.**
```bash
cd /tmp/agent_r5_6f1o && python3 -c "
import gemmi
m=gemmi.read_mtz_file('/tmp/nc_round1_cache/6f1o.mtz')
import collections
d=m.column_with_label('R-free-flags')
print(collections.Counter(d.array.astype(int)))
f=m.column_with_label('FOBS').array
import math
print('FOBS nan:', sum(1 for x in f if math.isnan(x)))
print([c.label+':'+c.type for c in m.columns])
print('res', m.resolution_low(), m.resolution_high())
"
```

**8.** — baseline R-factors of the perturbed model
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_6f1o.pdb /tmp/nc_round1_cache/6f1o.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > mvd_start.log 2>&1; tail -60 mvd_start.log
```

**9.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/nc_round1_work/r4p_6f1o.pdb 2>&1 | tail -5; echo "=== RAMA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/nc_round1_work/r4p_6f1o.pdb 2>&1 | tail -8; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/nc_round1_work/r4p_6f1o.pdb 2>&1 | tail -6
```

**10.** *(failed: unrecognized argument)*
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools /tmp/nc_round1_work/r4p_6f1o.pdb --show-geometry-statistics 2>&1 | tail -40
```

**11.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity /tmp/nc_round1_work/r4p_6f1o.pdb > mp_start.log 2>&1; sed -n '/Geometry Restraints/,/^$/p;/Summary/,$p' mp_start.log | head -60
```

**12.** *(python error on `is_amino_acid`; the B-factor/occupancy output above the traceback was still produced and used)*
```bash
cd /tmp/agent_r5_6f1o && python3 -c "
import gemmi
st=gemmi.read_structure('/tmp/nc_round1_work/r4p_6f1o.pdb')
bs=[a.b_iso for m in st for ch in m for r in ch for a in r]
import statistics
print('n atoms',len(bs),'B min/mean/max %.2f %.2f %.2f'%(min(bs),statistics.mean(bs),max(bs)))
naniso=sum(1 for m in st for ch in m for r in ch for a in r if a.aniso.nonzero())
print('aniso set:',naniso)
occ=[a.occ for m in st for ch in m for r in ch for a in r]
print('occ min/max',min(occ),max(occ))
print('chains',[ (ch.name,len(ch)) for m in st for ch in m])
seq=gemmi.one_letter_code([r.name for r in st[0]['A'] if r.is_amino_acid()])
print(len(seq),seq)
"
```

**13.**
```bash
cd /tmp/agent_r5_6f1o && grep -c "^ANISOU" /tmp/nc_round1_work/r4p_6f1o.pdb; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools /tmp/nc_round1_work/r4p_6f1o.pdb convert_to_isotropic=True output.file_name=start_iso.pdb > pdbtools_iso.log 2>&1; grep -c "^ANISOU" start_iso.pdb; echo "iso conversion done"
```

**14.** — test whether anisotropic ADPs carry signal
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data start_iso.pdb /tmp/nc_round1_cache/6f1o.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "r_work|r_free"
```

**15.**
```bash
cd /tmp/agent_r5_6f1o && python3 -c "
import gemmi
st=gemmi.read_structure('/tmp/nc_round1_work/r4p_6f1o.pdb')
st.setup_entities()
n_an=0;n_no=0
from collections import Counter
c=Counter()
for ch in st[0]:
    for r in ch:
        for a in r:
            if a.aniso.nonzero(): n_an+=1
            else: c[r.name]+=1; n_no+=1
print('with ANISOU',n_an,'without',n_no)
print('residues lacking ANISOU (top):',c.most_common(12))
"
```

**16.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ready_set start_iso.pdb > readyset.log 2>&1; tail -25 readyset.log; ls -la *.pdb *.cif 2>/dev/null
```

**17.**
```bash
cd /tmp/agent_r5_6f1o && for f in start_iso.pdb start_iso.updated.pdb; do echo -n "$f  H atoms: "; grep -c "^ATOM.\{72\}.\{4\}H$\|^HETATM.\{70\}.\{4\}H$" $f 2>/dev/null || true; echo -n "   total: "; grep -c "^ATOM\|^HETATM" $f; done; echo "--- element col tally (updated):"; grep "^ATOM\|^HETATM" start_iso.updated.pdb | cut -c77-78 | sort | uniq -c
```

**18.**
```bash
cd /tmp/agent_r5_6f1o && echo "ORIGINAL element tally:"; grep "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_6f1o.pdb | cut -c77-78 | sort | uniq -c
```

**19.** *(traceback; `--version` unsupported — no refinement performed)* **[NOT COUNTED]**
```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --version 2>&1 | head -3; echo "---"; nproc 2>/dev/null || sysctl -n hw.ncpu
```

**20.** **[NOT COUNTED]** — *rejected at PHIL parsing before refinement started: "Unrecognized PHIL parameters: refinement.input.xray_data.r_free_flags.test_flag_value=0". The Phenix 2.0 path is `data_manager.fmodel.xray_data.r_free_flags.test_flag_value`.*
```bash
cd /tmp/agent_r5_6f1o && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start_iso.updated.pdb /tmp/nc_round1_cache/6f1o.mtz refinement.input.xray_data.labels=FOBS,SIGFOBS refinement.input.xray_data.r_free_flags.label=R-free-flags refinement.input.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_adp refinement.main.number_of_macro_cycles=3 refinement.main.simulated_annealing=True refinement.simulated_annealing.mode=first refinement.main.nproc=8 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1 &
echo "launched pid $!"; sleep 60; tail -20 /tmp/agent_r5_6f1o/r1.log
```

**21.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null > defaults.txt; grep -n "test_flag_value\|ignore_r_free_flags\|r_free_flags" defaults.txt | head -30; echo "=== labels ==="; grep -n "labels" defaults.txt | head -20
```

**22.**
```bash
cd /tmp/agent_r5_6f1o && sed -n '1,70p' defaults.txt
```

**23.**
```bash
cd /tmp/agent_r5_6f1o && sed -n '1270,1320p' defaults.txt; echo "=== ctx ==="; awk 'NR>=1200 && NR<=1275' defaults.txt | grep -n "^\s*[a-z_]* {" | head -20
```

**24.**
```bash
cd /tmp/agent_r5_6f1o && grep -n "simulated_annealing\|number_of_macro_cycles\|^\s*nproc\|strategy =\|ordered_solvent\b\|optimize_xyz_weight\|optimize_adp_weight" defaults.txt | head -30
```

**25.**
```bash
cd /tmp/agent_r5_6f1o && sed -n '145,160p;190,205p;1005,1030p' defaults.txt
```

**26.** **[REFINE 1/6]** — simulated annealing + sites + isotropic ADP
```bash
cd /tmp/agent_r5_6f1o && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start_iso.updated.pdb /tmp/nc_round1_cache/6f1o.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=5 refinement.main.simulated_annealing=True refinement.simulated_annealing.mode=first refinement.main.nproc=8 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1 &
echo "launched $!"; sleep 90; grep -E "^\s*(r_work|r_free)|start R-work|Simulated|macro_cycle|Sorry|Error" /tmp/agent_r5_6f1o/r1.log | tail -20; echo "...tail:"; tail -5 /tmp/agent_r5_6f1o/r1.log
```

**27.**
```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6F1O && echo created; sleep 180; grep -E "r_work=.*r_free=" /tmp/agent_r5_6f1o/r1.log | tail -8; echo "--- last:"; tail -3 /tmp/agent_r5_6f1o/r1.log
```

**28.**
```bash
sleep 300; grep -E "^\s*Start R-work|^\s*Final R-work|r_work= 0\.|Time" /tmp/agent_r5_6f1o/r1.log | tail -12; echo "--- last:"; tail -4 /tmp/agent_r5_6f1o/r1.log; ls /tmp/agent_r5_6f1o/r1_00*
```

**29.**
```bash
cd /tmp/agent_r5_6f1o && sed -n '/Final refinement statistics/,/^===/p' r1_001.log 2>/dev/null | head -50; echo "=== from r1.log ==="; grep -A30 "Final model summary\|^  Molprobity\|MolProbity score" r1.log | tail -40
```

**30.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r1_001.pdb > mp_r1.log 2>&1; sed -n '/=== Summary/,$p' mp_r1.log | head -20; echo "=== Rama-Z ==="; grep -A6 "Rama-Z values" mp_r1.log | head -8; echo "=== waters ==="; grep -c HOH r1_001.pdb
```

**31.**
```bash
cd /tmp/agent_r5_6f1o && sed -n '155,190p' defaults.txt; echo "=== ordered_solvent scope ==="; sed -n '842,880p' defaults.txt
```

**32.** **[REFINE 2/6]** — anisotropic ADPs
```bash
cd /tmp/agent_r5_6f1o && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/6f1o.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.adp.individual.anisotropic="not element H" refinement.main.number_of_macro_cycles=4 refinement.main.nproc=8 output.prefix=r2 output.serial=2 --overwrite > r2.log 2>&1 &
echo "launched $!"; sleep 240; grep -E "r_work= 0\.|Sorry|Error" /tmp/agent_r5_6f1o/r2.log | tail -8; echo "--- last:"; tail -3 /tmp/agent_r5_6f1o/r2.log
```

**33.**
```bash
sleep 240; grep -E "Start R-work|Final R-work" /tmp/agent_r5_6f1o/r2.log; grep -E "r_work= 0\." /tmp/agent_r5_6f1o/r2.log | tail -4; echo "--- last:"; tail -3 /tmp/agent_r5_6f1o/r2.log
```

**34.** **[REFINE 3/6]** — ordered solvent rebuilding. *(The trailing `phenix.molprobity` in this
same command did not produce its log — the harness returned once the background job
detached — so it was re-issued as command 36.)*
```bash
cd /tmp/agent_r5_6f1o && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_002.pdb /tmp/nc_round1_cache/6f1o.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.main.number_of_macro_cycles=5 refinement.main.nproc=8 output.prefix=r3 output.serial=3 --overwrite > r3.log 2>&1 &
echo "launched $!"; sleep 5; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r2_002.pdb > mp_r2.log 2>&1; sed -n '/=== Summary/,$p' mp_r2.log | head -14
```

**35.**
```bash
cd /tmp/agent_r5_6f1o && sed -n '/Summary/,$p' mp_r2.log | head -16; echo "=== r3 progress ==="; grep -E "r_work= 0\.|Number of waters|Sorry" r3.log | tail -6
```

**36.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r2_002.pdb > mp_r2.log 2>&1; sed -n '/Summary/,$p' mp_r2.log | head -14
```

**37.**
```bash
sleep 420; cd /tmp/agent_r5_6f1o && grep -E "r_work= 0\." r3.log | tail -6; echo "--- solvent:"; grep -iE "ordered solvent|number of.*water|added|removed" r3.log | tail -12; echo "--- last:"; tail -3 r3.log
```

**38.**
```bash
sleep 300; cd /tmp/agent_r5_6f1o && grep -E "Start R-work|Final R-work" r3.log; grep -E "r_work= 0\." r3.log | tail -3; echo "--- last:"; tail -3 r3.log; ls r3_003.pdb 2>/dev/null && grep -c HOH r3_003.pdb
```

**39.**
```bash
cd /tmp/agent_r5_6f1o && python3 -c "
import gemmi
st=gemmi.read_structure('r3_003.pdb')
nw=0; nw_an=0; nprot_an=0; nprot=0
for ch in st[0]:
    for r in ch:
        for a in r:
            if a.element==gemmi.Element('H'): continue
            if r.name=='HOH':
                nw+=1; nw_an+= 1 if a.aniso.nonzero() else 0
            else:
                nprot+=1; nprot_an+= 1 if a.aniso.nonzero() else 0
print('waters:',nw,' aniso:',nw_an)
print('non-water heavy:',nprot,' aniso:',nprot_an)
print('chains:',[(c.name,len(c)) for c in st[0]])
"
```

**40.** **[REFINE 4/6]** — *CRASHED after two completed macrocycles of genuine refinement
(reached r_work 0.1296 / r_free 0.1592) with `CCTBX_ASSERT(f.use_u_iso()) failure` inside
`ordered_solvent.refine_oat`. `new_solvent=anisotropic` is incompatible with solvent
updating in this build. No model written. **Counted against the budget** because
refinement did occur.*
```bash
cd /tmp/agent_r5_6f1o && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_003.pdb /tmp/nc_round1_cache/6f1o.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.adp.individual.anisotropic="not element H" refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.ordered_solvent.new_solvent=anisotropic refinement.main.number_of_macro_cycles=5 refinement.main.nproc=8 output.prefix=r4 output.serial=4 --overwrite > r4.log 2>&1 &
echo "launched $!"; sleep 400; grep -E "r_work= 0\.|Sorry" /tmp/agent_r5_6f1o/r4.log | tail -6; tail -2 /tmp/agent_r5_6f1o/r4.log
```

**41.**
```bash
cd /tmp/agent_r5_6f1o && ls -la r4_00* 2>/dev/null; echo "--- exit context ---"; grep -B15 "CCTBX_ASSERT" r4.log | head -25
```

**42.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools --show-defaults 2>/dev/null | grep -n "anisotropic\|isotropic" | head -10
```

**43.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools --show-defaults 2>/dev/null | sed -n '1,30p'
```

**44.** — anisotropic conversion outside refinement (not a refinement invocation)
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.pdbtools r3_003.pdb modify.adp.convert_to_anisotropic=True modify.adp.atom_selection="not element H" output.file_name=r3_aniso.pdb > pdbtools_aniso.log 2>&1; python3 -c "
import gemmi
st=gemmi.read_structure('r3_aniso.pdb')
n=sum(1 for c in st[0] for r in c for a in r if a.element!=gemmi.Element('H'))
na=sum(1 for c in st[0] for r in c for a in r if a.element!=gemmi.Element('H') and a.aniso.nonzero())
print('heavy',n,'aniso',na)"
```

**45.** **[REFINE 5/6]** — all-anisotropic + solvent (result later rejected as overfit)
```bash
cd /tmp/agent_r5_6f1o && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_aniso.pdb /tmp/nc_round1_cache/6f1o.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.main.number_of_macro_cycles=5 refinement.main.nproc=8 output.prefix=r5 output.serial=5 --overwrite > r5.log 2>&1 &
echo "launched $!"; sleep 420; grep -E "r_work= 0\.|Sorry|RuntimeError" /tmp/agent_r5_6f1o/r5.log | tail -6; tail -2 /tmp/agent_r5_6f1o/r5.log
```

**46.**
```bash
sleep 360; cd /tmp/agent_r5_6f1o && grep -E "Start R-work|Final R-work" r5.log; grep -E "r_work= 0\." r5.log | tail -3; tail -2 r5.log
```

**47.** — independent re-measurement of both candidates
```bash
cd /tmp/agent_r5_6f1o && for m in r3_003 r5_005; do echo "=== $m ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $m.pdb /tmp/nc_round1_cache/6f1o.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free"; done
```

**48.**
```bash
cd /tmp/agent_r5_6f1o && for m in r3_003 r5_005; do echo "=== $m ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity $m.pdb > mp_$m.log 2>&1; sed -n '/Summary/,$p' mp_$m.log | head -11; grep -c HOH $m.pdb; done
```

**49.** **[REFINE 6/6]** — weight optimization from r3_003 (final, chosen)
```bash
cd /tmp/agent_r5_6f1o && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_003.pdb /tmp/nc_round1_cache/6f1o.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.number_of_macro_cycles=5 refinement.main.nproc=8 output.prefix=r6 output.serial=6 --overwrite > r6.log 2>&1 &
echo "launched $!"; sleep 600; grep -E "r_work= 0\.|Sorry|RuntimeError" /tmp/agent_r5_6f1o/r6.log | tail -5; tail -2 /tmp/agent_r5_6f1o/r6.log
```
*(The harness timed out at 600 s and moved this poll to the background; the nohup'd
refinement itself ran to completion, exit code 0.)*

**50.**
```bash
sleep 420; cd /tmp/agent_r5_6f1o && grep -E "r_work= 0\.|Sorry|RuntimeError|Final R-work" r6.log | tail -6; echo "--- weights tried:"; grep -iE "optimal|wxc|best weight" r6.log | tail -6; tail -2 r6.log
```

**51.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r6_006.pdb /tmp/nc_round1_cache/6f1o.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free"
```

**52.**
```bash
cd /tmp/agent_r5_6f1o && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r6_006.pdb > mp_r6.log 2>&1; sed -n '/Summary/,$p' mp_r6.log | head -14; echo "=== Rama-Z ==="; grep -A6 "Rama-Z values" mp_r6.log | tail -5
```

**53.** — final chemical sanity check
```bash
cd /tmp/agent_r5_6f1o && python3 -c "
import gemmi, statistics
st=gemmi.read_structure('r6_006.pdb'); st.setup_entities()
nw=sum(1 for c in st[0] for r in c for a in r if r.name=='HOH' and a.element!=gemmi.Element('H'))
hv=[a for c in st[0] for r in c for a in r if a.element!=gemmi.Element('H')]
b=[a.b_iso for a in hv]
print('waters:',nw,' heavy atoms:',len(hv))
print('B min/mean/max: %.1f %.1f %.1f'%(min(b),statistics.mean(b),max(b)))
occ=[a.occ for a in hv]; print('occ min/max: %.2f %.2f'%(min(occ),max(occ)))
alt=set(a.altloc for c in st[0] for r in c for a in r if a.altloc); print('altlocs:',sorted(alt))
ns=st[0].subchains()
# disulfide check
cys=[(c.name,r.seqid.num,a) for c in st[0] for r in c for a in r if r.name=='CYS' and a.name=='SG']
import itertools
print('SG-SG pairs < 2.5A:')
for (c1,n1,a1),(c2,n2,a2) in itertools.combinations(cys,2):
    d=a1.pos.dist(a2.pos)
    if d<2.5: print('  CYS%s-CYS%s  %.2f A'%(n1,n2,d))
"
```

**54.** — deliver the final model
```bash
cd /tmp/agent_r5_6f1o && cp r6_006.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6F1O/final.pdb && ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6F1O/
```

**55.** — post-write verification of the delivered files
```bash
cd /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6F1O && ls -la && md5 final.pdb /tmp/agent_r5_6f1o/r6_006.pdb
```

---

## Rule-compliance notes

- **No network access of any kind.** No `curl`, `wget`, `phenix.fetch_pdb`, or any other
  retrieval was issued — the list above is complete and contains none.
- **No deposited coordinates read.** No file under this repository's `ref/` or `data/`
  trees was read (the only `data/` interaction is *writing* my own deliverables), and no
  `*_mask.json` or `*_validation.xml` was opened.
- **Only `/tmp/nc_round1_cache/6f1o.mtz`** was read from the cache directory; no other
  file there was touched. The MTZ never disappeared, so the fallback-recovery path was
  never needed.
- **Within the MTZ, I used only `FOBS,SIGFOBS` and `R-free-flags`.** The deposited map
  coefficients `FWT/PHWT` and `DELFWT/PHDELWT` present in the file were deliberately not
  used, since they encode phases from the deposited model.
- **Refinement budget: 6 of 6 used** — commands 26, 32, 34, 40 (crashed mid-refinement,
  counted), 45, 49. Commands 19 and 20 failed before refinement began and are not
  counted, per the rules.
