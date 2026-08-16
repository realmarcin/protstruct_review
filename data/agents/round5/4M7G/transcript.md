# Transcript — blinded agentic recovery of 4M7G (round 5)

Every shell command executed, in order. Refinement-program invocations are
numbered **[REFINE n/6]** against the 6-invocation budget. All other commands are
validation, measurement, file inspection, or reading PHENIX's own source/parameters.

Scratch directory: `/tmp/agent_r5_4m7g/`

Non-shell actions (not shell commands, listed here for completeness): the two
deliverable files `decisions.md` and `transcript.md` were written directly with a
file-writing tool rather than a shell heredoc.

---

## 1. Inputs and baseline characterisation

```bash
mkdir -p /tmp/agent_r5_4m7g && cd /tmp/agent_r5_4m7g && ls -la /tmp/nc_round1_work/r4p_4m7g.pdb /tmp/nc_round1_cache/4m7g.mtz && head -30 /tmp/nc_round1_work/r4p_4m7g.pdb
```

```bash
cd /tmp/agent_r5_4m7g && gemmi mtz --headers /tmp/nc_round1_cache/4m7g.mtz 2>&1 | head -60
```

```bash
cd /tmp/agent_r5_4m7g && grep -c '^ATOM' /tmp/nc_round1_work/r4p_4m7g.pdb; grep -c '^HETATM' /tmp/nc_round1_work/r4p_4m7g.pdb; grep '^HETATM' /tmp/nc_round1_work/r4p_4m7g.pdb | cut -c18-20 | sort | uniq -c | sort -rn; grep '^CRYST1\|^REMARK   2\|^REMARK   3' /tmp/nc_round1_work/r4p_4m7g.pdb | head -20; grep '^ATOM\|^HETATM' /tmp/nc_round1_work/r4p_4m7g.pdb | cut -c22 | sort | uniq -c
```

```bash
cd /tmp/agent_r5_4m7g && python3 -c "
import sys
occ={}; b=[]; alt=set(); anis=0
res=set()
for line in open('/tmp/nc_round1_work/r4p_4m7g.pdb'):
    if line.startswith('ANISOU'): anis+=1
    if line.startswith(('ATOM','HETATM')):
        alt.add(line[16])
        o=float(line[54:60]); occ[o]=occ.get(o,0)+1
        b.append(float(line[60:66]))
        if line.startswith('ATOM'): res.add(int(line[22:26]))
print('altlocs',sorted(alt))
print('occ',sorted(occ.items())[:10])
print('B min/max/mean', min(b), max(b), sum(b)/len(b))
print('ANISOU', anis)
print('nres', len(res), 'range', min(res), max(res))
r=sorted(res); gaps=[(r[i],r[i+1]) for i in range(len(r)-1) if r[i+1]!=r[i]+1]
print('gaps', gaps)
"
```

```bash
cd /tmp/agent_r5_4m7g && python3 -c "
import collections
bs=[]; anis_res=collections.Counter(); tot=collections.Counter()
import math
bad=0; n=0
prev=None
lines=open('/tmp/nc_round1_work/r4p_4m7g.pdb').read().splitlines()
for i,line in enumerate(lines):
    if line.startswith(('ATOM','HETATM')):
        prev=line
        tot['HOH' if line[17:20]=='HOH' else 'prot']+=1
    if line.startswith('ANISOU'):
        anis_res['HOH' if line[17:20]=='HOH' else 'prot']+=1
        u=[int(line[28+7*k:35+7*k]) for k in range(3)]
        beq=sum(u)/3.0*1e-4*8*math.pi**2
        b=float(prev[60:66])
        n+=1
        if abs(beq-b)>0.5: bad+=1
print('ANISOU by type',dict(anis_res),'atoms by type',dict(tot))
print('anisou-B mismatch',bad,'of',n)
import numpy as np
b=[float(l[60:66]) for l in lines if l.startswith(('ATOM','HETATM'))]
print(np.percentile(b,[0,5,25,50,75,95,99,100]))
print('count at 45.00:', sum(1 for x in b if x>=44.999))
"
```

```bash
cd /tmp/agent_r5_4m7g && python3 -c "
lines=open('/tmp/nc_round1_work/r4p_4m7g.pdb').read().splitlines()
noan=set(); has=set()
prev=None
idx={}
atoms=[]
for i,l in enumerate(lines):
    if l.startswith(('ATOM','HETATM')): atoms.append((i,l))
anis={i-1 for i,l in enumerate(lines) if l.startswith('ANISOU')}
for i,l in atoms:
    key=(l[17:20],int(l[22:26]))
    if i in anis: has.add(key)
    else: noan.add(key)
pn=sorted(r for n,r in noan if n!='HOH')
print('residues with >=1 atom lacking ANISOU:',len(pn))
print(pn)
"
```

```bash
cd /tmp/agent_r5_4m7g && grep '^ATOM\|^HETATM' /tmp/nc_round1_work/r4p_4m7g.pdb | cut -c77-78 | sort | uniq -c | sort -rn
```

```bash
cd /tmp/agent_r5_4m7g && python3 -c "
import collections
c=collections.Counter(); alt=collections.Counter()
prot_lt1=0
for l in open('/tmp/nc_round1_work/r4p_4m7g.pdb'):
    if l.startswith(('ATOM','HETATM')):
        o=float(l[54:60]); c['occ=1' if o>0.999 else 'occ<1']+=1
        alt[l[16]]+=1
print(dict(c)); print('altloc counts',dict(alt))
" ; echo '--- altloc residues ---'; grep '^ATOM\|^HETATM' /tmp/nc_round1_work/r4p_4m7g.pdb | awk 'substr($0,17,1)!=" "{print substr($0,18,9)}' | sort -u | tr '\n' ' ' | fold -w 200
```

Failed first attempt at `model_vs_data` (wrong parameter name), kept for the record:

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_4m7g.pdb /tmp/nc_round1_cache/4m7g.mtz labels="FOBS,SIGFOBS" > baseline_mvd.log 2>&1; tail -60 baseline_mvd.log
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data --help 2>&1 | head -60
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_4m7g.pdb /tmp/nc_round1_cache/4m7g.mtz f_obs_label="FOBS" r_free_flags_label="R-free-flags" > baseline_mvd.log 2>&1; cat baseline_mvd.log
```

```bash
cd /tmp/agent_r5_4m7g && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.clashscore /tmp/nc_round1_work/r4p_4m7g.pdb > base_clash.log 2>&1; tail -5 base_clash.log; echo '=== RAMA ==='; $P/phenix.ramalyze /tmp/nc_round1_work/r4p_4m7g.pdb > base_rama.log 2>&1; tail -6 base_rama.log; echo '=== ROTA ==='; $P/phenix.rotalyze /tmp/nc_round1_work/r4p_4m7g.pdb > base_rota.log 2>&1; tail -6 base_rota.log
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity /tmp/nc_round1_work/r4p_4m7g.pdb output.prefix=base > base_mp.log 2>&1; sed -n '/Geometry Restraints/,/^$/p;/RMS(bonds)/,+4p' base_mp.log | head -40; grep -iE 'rms|molprobity score|clashscore|Ramachandran|rotamer|cbeta|outlier' base_mp.log | head -40
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 > refine_params.txt 2>&1; grep -nE 'strategy|ordered_solvent|number_of_macro_cycles|optimize_x|optimize_ad|simulated_annealing|anisotropic|isotropic|fix_rotamers|real_space|nqh|flip' refine_params.txt | head -60
```

```bash
cd /tmp/agent_r5_4m7g && sed -n '125,200p' refine_params.txt
```

## 2. [REFINE 1/6] — full-resolution xyz + ADP + occupancy

```bash
cd /tmp/agent_r5_4m7g && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/nc_round1_work/r4p_4m7g.pdb /tmp/nc_round1_cache/4m7g.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=5 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1; echo EXIT=$?; ls -la r1*
```

```bash
sleep 120; cd /tmp/agent_r5_4m7g && tail -25 r1.log
```

```bash
sleep 300; cd /tmp/agent_r5_4m7g && grep -nE '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}' r1.log | tail -8; echo ---; tail -5 r1.log
```

```bash
sleep 420; cd /tmp/agent_r5_4m7g && grep -nE '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}' r1.log | tail -8; echo ---; tail -3 r1.log; ls r1_1.pdb 2>/dev/null && echo DONE
```

```bash
sleep 60; cd /tmp/agent_r5_4m7g && ls -la r1_1.pdb r1_1.mtz 2>&1; grep -A25 'Final R-work' r1.log | head -35
```

```bash
cd /tmp/agent_r5_4m7g && ls -la | grep -i r1
```

```bash
cd /tmp/agent_r5_4m7g && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.molprobity r1_001.pdb output.prefix=r1mp > r1_mp.log 2>&1; grep -E 'Bond  |Angle |All-atom Clashscore|Outliers|Favored|MolProbity score|RMS' r1_mp.log | head -20; echo '=== waters ==='; grep -c 'HOH' r1_001.pdb
```

```bash
cd /tmp/agent_r5_4m7g && ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -iE 'peak|hole|water|solvent|douse'
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r1_001.pdb r1_001.mtz f_label=F-obs-filtered map_cutoff=3.5 anom_map_cutoff=3.0 > peaks.log 2>&1; tail -40 peaks.log
```

```bash
cd /tmp/agent_r5_4m7g && grep -B2 -A200 'Interesting sites' peaks.log 2>/dev/null | head -5; echo '=== top peaks by height ==='; grep '^peak=' peaks.log | sort -k2 -g -r | head -20
```

```bash
cd /tmp/agent_r5_4m7g && sed -n '394,445p' refine_params.txt
```

## 3. [REFINE 2/6] — ordered-solvent rebuild

```bash
cd /tmp/agent_r5_4m7g && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/4m7g.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True output.prefix=r2 output.serial=1 --overwrite > r2.log 2>&1; echo EXIT=$?
```

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/4M7G && echo created; sleep 400; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}' r2.log | tail -6; tail -3 r2.log
```

```bash
sleep 240; cd /tmp/agent_r5_4m7g && grep -nE '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|Number of.*water|ordered solvent' r2.log | tail -40
```

```bash
cd /tmp/agent_r5_4m7g && sed -n '600,740p' r2.log | grep -nE 'r_work|r_free|Start R|water|solvent|Number of' | head -30; echo '=== solvent updates ==='; sed -n '1141,1215p' r2.log | head -50
```

```bash
cd /tmp/agent_r5_4m7g && sed -n '726,840p' r2.log
```

```bash
cd /tmp/agent_r5_4m7g && grep -nE 'optimize_xyz_weight|optimize_adp_weight|wxc_scale|wxu_scale|target_weights' refine_params.txt | head -20; echo '=== target auto ==='; sed -n '/^  target_weights/,/^  }/p' refine_params.txt | head -40
```

```bash
cd /tmp/agent_r5_4m7g && grep -nE 'optimize|wxc|wxu' refine_params.txt | head -30
```

```bash
cd /tmp/agent_r5_4m7g && sed -n '525,575p' refine_params.txt
```

```bash
sleep 200; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|n_water=' r2.log | tail -20; echo ---; tail -3 r2.log
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 > refine_params3.txt 2>&1; grep -nE 'optimize_xyz_weight|optimize_adp_weight|wxc_scale|wxu_scale' refine_params3.txt | head; echo ---; sed -n "$(grep -n 'target_weights' refine_params3.txt | head -1 | cut -d: -f1),+30p" refine_params3.txt
```

```bash
cd /tmp/agent_r5_4m7g && sed -n '1015,1050p' refine_params3.txt
```

```bash
sleep 420; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|Final R' r2.log | tail -12; tail -3 r2.log
```

```bash
sleep 90; cd /tmp/agent_r5_4m7g && grep 'Final R' r2.log; ls -la r2_001.pdb; grep -c ' HOH ' r2_001.pdb; grep 'Final R' r1.log
```

```bash
cd /tmp/agent_r5_4m7g && python3 -c "
lines=open('r2_001.pdb').read().splitlines()
atoms=[(i,l) for i,l in enumerate(lines) if l.startswith(('ATOM','HETATM'))]
anis={i-1 for i,l in enumerate(lines) if l.startswith('ANISOU')}
w=[(i,l) for i,l in atoms if l[17:20]=='HOH']
print('n_water_atoms',len(w),'aniso',sum(1 for i,l in w if i in anis),'iso',sum(1 for i,l in w if i not in anis))
p=[(i,l) for i,l in atoms if l[17:20]!='HOH' and l[76:78].strip()!='H']
print('protein heavy',len(p),'aniso',sum(1 for i,l in p if i in anis))
import collections
print('chains',collections.Counter(l[21] for i,l in atoms))
b=[float(l[60:66]) for i,l in w]
print('water B mean %.1f min %.1f max %.1f'%(sum(b)/len(b),min(b),max(b)))
"; echo '=== peaks after run2 ==='; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r2_001.pdb r2_001.mtz f_label=F-obs-filtered map_cutoff=3.5 > peaks2.log 2>&1; tail -12 peaks2.log
```

## 4. [REFINE 3/6] — anisotropic new solvent + weight optimisation (CRASHED)

```bash
cd /tmp/agent_r5_4m7g && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb /tmp/nc_round1_cache/4m7g.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=5 refinement.main.ordered_solvent=True refinement.ordered_solvent.new_solvent=anisotropic refinement.refine.adp.individual.anisotropic="not element H" refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True output.prefix=r3 output.serial=1 --overwrite > r3.log 2>&1; echo EXIT=$?
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r2_001.pdb output.prefix=r2mp > r2_mp.log 2>&1; grep -E 'Bond  |Angle |All-atom Clashscore|Outliers|Favored|MolProbity score|RMS\(|Rama-Z|whole:' r2_mp.log | head -16
```

```bash
sleep 600; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|n_water=' r3.log | tail -15; echo ---; tail -3 r3.log
```

```bash
cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|n_water=' r3.log | tail -15; echo ---; tail -4 r3.log
```

```bash
cd /tmp/agent_r5_4m7g && sed -n "$(grep -n 'MACRO_CYCLE 1 OF 5' r3.log | cut -d: -f1),$(grep -n 'MACRO_CYCLE 2 OF 5' r3.log | cut -d: -f1)p" r3.log | grep -nE 'wxc|WEIGHT|weight|R-FACTORS|^ 0\.|Optimiz|trial' | head -40
```

```bash
sleep 580; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|Best ADP weight|Best xyz weight|n_water=' r3.log | tail -20; echo ---; tail -3 r3.log
```

```bash
cd /tmp/agent_r5_4m7g && echo '=== run1 wxc ==='; grep -E 'wxc = ' r1.log; echo '=== run2 wxc ==='; grep -E 'wxc = ' r2.log; echo '=== run2 wxu ==='; grep -E 'wxu = ' r2.log
```

```bash
grep -rn "fix_wxc" /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/targets.py /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/*.py 2>/dev/null | head -20
```

```bash
sed -n '395,430p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/weights.py; echo '=== usage of wxc downstream ==='; grep -n "wxc_scale\|self.wxc" /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/weights.py | head -20
```

```bash
grep -n "fix_wxu" /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/weights.py | head; sed -n '/elif(self.twp.fix_wxu is not None)/,+3p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/weights.py
```

## 5. [REFINE 4/6] — pinned weights (FAILED EXPERIMENT, killed)

```bash
cd /tmp/agent_r5_4m7g && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb /tmp/nc_round1_cache/4m7g.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True refinement.target_weights.fix_wxc=0.9 refinement.target_weights.fix_wxu=4.5 output.prefix=r4 output.serial=1 --overwrite > r4.log 2>&1; echo EXIT=$?
```

```bash
sleep 420; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|wxc = |n_water=' r4.log | tail -20
```

```bash
sed -n '320,395p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/weights.py
```

```bash
pkill -f 'phenix.refine.*r4' ; sleep 2; cd /tmp/agent_r5_4m7g && echo 'killed run4'; grep -n 'refinement target' r1.log r2.log r4.log | head; echo '=== auto target logic ==='; grep -rn "ls_wunit_k1" /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/driver.py /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/utils/__init__.py 2>/dev/null | head
```

```bash
sed -n '1175,1200p' /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/utils/__init__.py; echo '=== callers ==='; grep -rn "set_refinement_target\|macro_cycle.*<=.*2\|target == .auto" /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/mmtbx/refinement/driver.py 2>/dev/null | head
```

```bash
cd /tmp/agent_r5_4m7g && grep -A2 'Set refinement target' r2.log | grep 'using refinement target' | nl
```

## 6. [REFINE 5/6] — maximum-likelihood target throughout + ordered solvent

```bash
cd /tmp/agent_r5_4m7g && time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_001.pdb /tmp/nc_round1_cache/4m7g.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True refinement.main.target=ml output.prefix=r5 output.serial=1 --overwrite > r5.log 2>&1; echo EXIT=$?
```

```bash
sleep 480; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|using refinement target|n_water=' r5.log | tail -18
```

```bash
sleep 540; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|Final R' r5.log | tail -14; echo ---; tail -3 r5.log
```

```bash
sleep 500; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|Final R' r5.log | tail -8; ls -la r5_001.pdb 2>&1
```

```bash
sleep 120; cd /tmp/agent_r5_4m7g && grep 'Final R' r5.log; ls -la r5_001.pdb r5_001.mtz 2>&1; tail -3 r5.log
```

```bash
cd /tmp/agent_r5_4m7g && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r5_001.pdb output.prefix=r5mp > r5_mp.log 2>&1; grep -E 'Bond  |Angle |All-atom Clashscore|Outliers|Favored|MolProbity score|RMS\(|whole:' r5_mp.log | head -14; echo '=== water ADP types ==='; python3 -c "
lines=open('r5_001.pdb').read().splitlines()
atoms=[(i,l) for i,l in enumerate(lines) if l.startswith(('ATOM','HETATM'))]
anis={i-1 for i,l in enumerate(lines) if l.startswith('ANISOU')}
w=[(i,l) for i,l in atoms if l[17:20]=='HOH']
print('waters',len(w),'aniso',sum(1 for i,l in w if i in anis),'iso',sum(1 for i,l in w if i not in anis))
"; echo '=== peaks ==='; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r5_001.pdb r5_001.mtz f_label=F-obs-filtered map_cutoff=3.5 > peaks5.log 2>&1; tail -10 peaks5.log
```

## 7. [REFINE 6/6] — full anisotropic ADP polish

```bash
cd /tmp/agent_r5_4m7g && grep -E 'mFo-DFc >  3.5' peaks5.log; time /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r5_001.pdb /tmp/nc_round1_cache/4m7g.mtz "miller_array.labels.name=FOBS,SIGFOBS" "miller_array.labels.name=R-free-flags" refinement.main.number_of_macro_cycles=5 refinement.main.target=ml refinement.main.ordered_solvent=False refinement.refine.adp.individual.anisotropic="not element H" output.prefix=r6 output.serial=1 --overwrite > r6.log 2>&1; echo EXIT=$?
```

```bash
sleep 400; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|MACRO_CYCLE|Final R' r6.log | tail -14; echo ---; tail -3 r6.log
```

```bash
sleep 500; cd /tmp/agent_r5_4m7g && grep -E '^ *[0-9]\.[0-9]{4} +[0-9]\.[0-9]{4}|Final R' r6.log | tail -8; ls -la r6_001.pdb 2>&1; tail -3 r6.log
```

## 8. Final selection, installation and independent verification

```bash
cd /tmp/agent_r5_4m7g && P=/Users/marcin/phenix-2.0-5936/phenix_bin; for m in r2_001 r5_001 r6_001; do echo "=== $m ==="; $P/phenix.model_vs_data $m.pdb /tmp/nc_round1_cache/4m7g.mtz f_obs_label="FOBS" r_free_flags_label="R-free-flags" 2>&1 | grep -E '^  r_work|^  r_free'; done
```

```bash
cd /tmp/agent_r5_4m7g && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/4M7G && cp r5_001.pdb $D/final.pdb && ls -la $D/final.pdb && echo '=== gemmi independent check ===' && gemmi validate $D/final.pdb 2>&1 | head -20; echo '=== gemmi contents ==='; gemmi convert --to=pdb $D/final.pdb /dev/null 2>&1 | head -5; python3 -c "
lines=open('$D/final.pdb').read().splitlines()
a=[l for l in lines if l.startswith(('ATOM','HETATM'))]
import collections
print('atoms',len(a))
print('elements',dict(collections.Counter(l[76:78].strip() for l in a)))
print('waters',sum(1 for l in a if l[17:20]=='HOH'))
print('altloc atoms',sum(1 for l in a if l[16]!=' '))
res=set(int(l[22:26]) for l in a if l[17:20]!='HOH')
print('protein residues',len(res),min(res),max(res))
"
```

```bash
cd /tmp/agent_r5_4m7g && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/4M7G && gemmi contents $D/final.pdb 2>&1 | head -20; echo '=== displacement from perturbed start (same frame) ==='; python3 -c "
import math
def load(f):
    d={}
    for l in open(f):
        if l.startswith(('ATOM','HETATM')) and l[17:20]!='HOH' and l[76:78].strip()!='H':
            d[(l[21],l[22:27],l[12:16],l[16])]=(float(l[30:38]),float(l[38:46]),float(l[46:54]))
    return d
a=load('/tmp/nc_round1_work/r4p_4m7g.pdb'); b=load('$D/final.pdb')
k=set(a)&set(b)
ds=[math.dist(a[x],b[x]) for x in k]
ds.sort()
n=len(ds)
print('matched protein heavy atoms',n,'of',len(a))
print('RMSD %.3f A  mean %.3f  median %.3f  max %.3f'%((sum(d*d for d in ds)/n)**.5,sum(ds)/n,ds[n//2],ds[-1]))
print('frac >0.5A %.3f  >1.0A %.3f'%(sum(1 for d in ds if d>0.5)/n,sum(1 for d in ds if d>1.0)/n))
"
```

```bash
cd /tmp/agent_r5_4m7g && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/4M7G && P=/Users/marcin/phenix-2.0-5936/phenix_bin && $P/phenix.molprobity $D/final.pdb output.prefix=final > final_mp.log 2>&1; grep -E 'Bond      :|Angle     :|Chirality|Planarity|All-atom Clashscore|Outliers|Allowed|Favored|MolProbity score|RMS\(|whole:|Cbeta|Cis-|Twisted' final_mp.log | head -24
```

```bash
D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/4M7G && ls -la $D && head -3 $D/final.pdb && grep -c '^ATOM\|^HETATM' $D/final.pdb
```

---

## Refinement-budget accounting

| # | invocation | outcome |
|---|---|---|
| 1 | full-resolution xyz+ADP+occ, 5 macrocycles | 0.3939/0.3984 → 0.1255/0.1368 |
| 2 | + ordered solvent, 6 macrocycles | → 0.1214/0.1304, 353→397 waters |
| 3 | aniso solvent + weight optimisation | **crashed** (`CCTBX_ASSERT(f.use_u_iso())`), no model |
| 4 | pinned `fix_wxc`/`fix_wxu` | **failed**, over-restrained, killed at macrocycle 3 |
| 5 | `target=ml` throughout + ordered solvent | → **0.1208/0.1298 — final.pdb** |
| 6 | anisotropic ADPs on all non-H | → 0.1210/0.1311, rejected (R-free worse) |

6 of 6 used. `phenix.model_vs_data`, `phenix.molprobity`, `phenix.clashscore`,
`phenix.ramalyze`, `phenix.rotalyze`, `phenix.find_peaks_holes` and `gemmi` are
validation/measurement tools and are not counted against the budget.

