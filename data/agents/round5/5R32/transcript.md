# 5R32 blinded agentic recovery — full shell transcript

Every shell command issued, in execution order. Commands are reproduced verbatim as sent to
the shell (each block was a single `bash -c` invocation). Long inline heredoc scripts are
included in full.

Refinement-program invocations are marked **[REFINE n/6]**. One launch was rejected before
refinement began and is marked **[REJECTED — not counted]**, per the budget rule.

---

### 1
```bash
mkdir -p /tmp/agent_r5_5r32 && cd /tmp/agent_r5_5r32 && ls -la /tmp/nc_round1_work/r4p_5r32.pdb /tmp/nc_round1_cache/5r32.mtz
```

### 2
```bash
/opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/5r32.mtz 2>&1 | head -60
```

### 3
```bash
cd /tmp/agent_r5_5r32 && head -30 /tmp/nc_round1_work/r4p_5r32.pdb && echo "=== counts ===" && grep -c '^ATOM' /tmp/nc_round1_work/r4p_5r32.pdb; grep -c '^HETATM' /tmp/nc_round1_work/r4p_5r32.pdb; grep -c '^ANISOU' /tmp/nc_round1_work/r4p_5r32.pdb; echo "=== HET residue types ===" ; grep '^HETATM' /tmp/nc_round1_work/r4p_5r32.pdb | cut -c18-20 | sort | uniq -c | sort -rn
```

### 4
```bash
cd /tmp/agent_r5_5r32 && grep -E '^(CRYST1|SCALE|REMARK   2|REMARK   3   R VALUE|EXPDTA|MODEL|ENDMDL|TER|LINK|SSBOND)' /tmp/nc_round1_work/r4p_5r32.pdb | head -20; echo "=== first ATOM lines ==="; grep '^ATOM' /tmp/nc_round1_work/r4p_5r32.pdb | head -5; echo "=== altloc counts ==="; grep '^ATOM' /tmp/nc_round1_work/r4p_5r32.pdb | cut -c17 | sort | uniq -c; echo "=== chains ==="; grep -E '^(ATOM|HETATM)' /tmp/nc_round1_work/r4p_5r32.pdb | cut -c22 | sort | uniq -c; echo "=== ANISOU on waters? ==="; grep '^ANISOU' /tmp/nc_round1_work/r4p_5r32.pdb | cut -c18-20 | sort | uniq -c | sort -rn | head
```

### 5 — failed (bad parameter name)
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_5r32.pdb /tmp/nc_round1_cache/5r32.mtz labels="FOBS,SIGFOBS" > baseline_mvd.log 2>&1; tail -60 baseline_mvd.log
```

### 6
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data --help 2>&1 | head -60
```

### 7 — baseline fit
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_5r32.pdb /tmp/nc_round1_cache/5r32.mtz f_obs_label="FOBS" r_free_flags_label="R-free-flags" > baseline_mvd.log 2>&1; cat baseline_mvd.log
```

### 8
```bash
cd /tmp/agent_r5_5r32 && cat > flagcheck.py <<'EOF'
from iotbx import reflection_file_reader
import collections
rf = reflection_file_reader.any_reflection_file("/tmp/nc_round1_cache/5r32.mtz")
for ma in rf.as_miller_arrays():
    lbl = ",".join(ma.info().labels)
    if "free" in lbl.lower():
        c = collections.Counter(ma.data())
        print(lbl, ma.size(), dict(c))
    else:
        print(lbl, ma.size())
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python flagcheck.py
```

### 9
```bash
cd /tmp/agent_r5_5r32 && cat > flagcheck2.py <<'EOF'
from iotbx import reflection_file_reader
import collections
rf = reflection_file_reader.any_reflection_file("/tmp/nc_round1_cache/5r32.mtz")
arrs = {",".join(ma.info().labels): ma for ma in rf.as_miller_arrays()}
fobs = arrs["FOBS,SIGFOBS"]
print("fobs n =", fobs.size(), "d_min", fobs.d_min())
for lbl in ["R-free-flags","R-free-flags-1","R-free-flags-2","R-free-flags-3"]:
    fl = arrs[lbl]
    c, f2 = fobs.common_sets(fl)
    cnt = collections.Counter(f2.data())
    n0 = cnt.get(0,0); n1 = cnt.get(1,0)
    print(lbl, "common", f2.size(), "zeros", n0, "%.3f%%"%(100.0*n0/f2.size()), "ones", n1, "%.3f%%"%(100.0*n1/f2.size()))
# are -2 and -3 identical to base?
import numpy as np
b = arrs["R-free-flags"]
for lbl in ["R-free-flags-2","R-free-flags-3"]:
    o = arrs[lbl]
    same = (b.data()==o.data()).count(True)
    print(lbl,"identical to R-free-flags for",same,"of",b.size())
EOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python flagcheck2.py
```

### 10
```bash
ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -iE 'molprobity|clashscore|ramalyze|rotalyze|ready_set|reduce|cablam|real_space|refine|dynamics|elbow|douse'
```

### 11 — baseline geometry
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity /tmp/nc_round1_work/r4p_5r32.pdb output.prefix=baseline_mp output.quiet=False > baseline_mp.log 2>&1; grep -A60 'Summary' baseline_mp.log | head -70
```

### 12
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import collections
atoms=[]; aniso=set()
for L in open('/tmp/nc_round1_work/r4p_5r32.pdb'):
    if L.startswith(('ATOM','HETATM')):
        key=(L[12:27])
        atoms.append((key, float(L[54:60]), float(L[60:66]), L[17:20], L[22:26].strip(), L[76:78].strip()))
    elif L.startswith('ANISOU'):
        aniso.add(L[12:27])
print("n atoms",len(atoms),"n aniso",len(aniso))
b=[a[2] for a in atoms]
import statistics
print("B: min %.2f max %.2f mean %.2f median %.2f"%(min(b),max(b),statistics.mean(b),statistics.median(b)))
occ=collections.Counter(round(a[1],2) for a in atoms)
print("occupancies:",dict(occ))
# which residues lack aniso
noan=collections.Counter()
withan=collections.Counter()
for a in atoms:
    (withan if a[0] in aniso else noan)[a[3]]+=1
print("residue types lacking ANISOU (top):", noan.most_common(12))
# per-residue: fully aniso / fully iso / mixed
res=collections.defaultdict(lambda:[0,0])
for a in atoms:
    r=(a[3],a[4])
    res[r][0 if a[0] in aniso else 1]+=1
full=sum(1 for v in res.values() if v[1]==0); none_=sum(1 for v in res.values() if v[0]==0); mixed=sum(1 for v in res.values() if v[0] and v[1])
print("residues: total %d  all-aniso %d  all-iso %d  mixed %d"%(len(res),full,none_,mixed))
# B stats split
ba=[a[2] for a in atoms if a[0] in aniso]; bi=[a[2] for a in atoms if a[0] not in aniso]
print("B aniso-atoms mean %.2f ; B iso-atoms mean %.2f"%(statistics.mean(ba),statistics.mean(bi)))
EOF
```

### 13
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import collections
aniso=set(); atoms=[]
for L in open('/tmp/nc_round1_work/r4p_5r32.pdb'):
    if L.startswith(('ATOM','HETATM')):
        atoms.append((L[12:27], L[12:16].strip(), L[17:20], L[22:26].strip(), L[16]))
    elif L.startswith('ANISOU'):
        aniso.add(L[12:27])
mc={'N','CA','C','O','OXT'}
cnt=collections.Counter()
for k,name,res,num,alt in atoms:
    if res=='HOH': continue
    cls = 'main' if name in mc else ('CB' if name=='CB' else 'side')
    cnt[(cls, k in aniso)]+=1
for cls in ['main','CB','side']:
    a=cnt[(cls,True)]; i=cnt[(cls,False)]
    print("%-5s aniso %4d  iso %4d  (%.1f%% iso)"%(cls,a,i,100*i/(a+i)))
# altloc atoms
alt_a=sum(1 for k,n,r,nu,al in atoms if al!=' ' and k in aniso)
alt_i=sum(1 for k,n,r,nu,al in atoms if al!=' ' and k not in aniso)
print("altloc atoms: aniso",alt_a,"iso",alt_i)
# per-residue fraction iso
per=collections.defaultdict(lambda:[0,0])
for k,n,r,nu,al in atoms:
    if r=='HOH': continue
    per[(r,nu)][0 if k in aniso else 1]+=1
frac=[(v[1]/(v[0]+v[1]),r,nu) for (r,nu),v in per.items()]
frac.sort(reverse=True)
print("residues 100%% iso:",sum(1 for f,_,_ in frac if f==1.0))
print("top:",frac[:10])
print("bottom:",frac[-6:])
EOF
```

### 14 — this is the check that overturned the "scrambled side chains" hypothesis
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import collections
aniso=set(); atoms=[]
for L in open('/tmp/nc_round1_work/r4p_5r32.pdb'):
    if L.startswith(('ATOM','HETATM')): atoms.append((L[12:27],L[12:16].strip(),L[17:20]))
    elif L.startswith('ANISOU'): aniso.add(L[12:27])
c=collections.Counter()
for k,n,r in atoms:
    if r=='HOH' or n in {'N','CA','C','O','OXT','CB'}: continue
    c[(n, k in aniso)]+=1
names=sorted({n for n,_ in c})
print("atom  aniso  iso")
for n in names:
    print("%-4s %5d %5d"%(n,c[(n,True)],c[(n,False)]))
EOF
ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -iE 'autobuild|fit_side|mtriage|fmodel|maps|xtriage|find_alt|ensemble'
```

### 15
```bash
sysctl -n hw.ncpu; cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null > defaults.txt; wc -l defaults.txt; grep -nE 'anisotropic|ordered_solvent|number_of_macro_cycles|optimize_x|optimize_a|simulated_annealing|nproc|^ *strategy|target_weights|scattering_table' defaults.txt | head -50
```

### 16
```bash
cd /tmp/agent_r5_5r32 && sed -n '145,175p;255,268p;842,880p' defaults.txt
```

### 17 — **[REFINE 1/6]**
```bash
cd /tmp/agent_r5_5r32 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/nc_round1_work/r4p_5r32.pdb /tmp/nc_round1_cache/5r32.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not element H" main.number_of_macro_cycles=8 main.nproc=10 ordered_solvent=true ordered_solvent.filter_at_start=False output.prefix=run1 output.serial=1 --overwrite > run1_stdout.log 2>&1 &
echo "launched pid $!"; sleep 60; tail -20 /tmp/agent_r5_5r32/run1_stdout.log
```

### 18
```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/5R32 && sleep 240; cd /tmp/agent_r5_5r32 && grep -E 'MACRO_CYCLE|r_work=|Start R-work' run1_stdout.log | tail -25
```

### 19
```bash
sleep 420; cd /tmp/agent_r5_5r32 && grep -E 'MACRO_CYCLE|coordinate error' run1_stdout.log | tail -12; echo "--- running? ---"; ps -p 68420 > /dev/null && echo YES || echo NO
```

### 20 — timed out at the harness level; job kept running
```bash
sleep 600; cd /tmp/agent_r5_5r32 && grep -E 'MACRO_CYCLE|coordinate error' run1_stdout.log | tail -8; echo "--- running? ---"; ps -p 68420 > /dev/null && echo YES || echo NO; ls -la run1*.pdb run1*.mtz 2>/dev/null
```

### 21
```bash
cd /tmp/agent_r5_5r32 && grep -E 'MACRO_CYCLE|coordinate error' run1_stdout.log | tail -8; echo "--- running? ---"; ps -p 68420 > /dev/null && echo YES || echo NO; ls -la run1*.pdb run1*.mtz 2>/dev/null; tail -5 run1_stdout.log
```

### 22
```bash
sleep 540; cd /tmp/agent_r5_5r32 && ps -p 68420 > /dev/null && echo RUNNING || echo DONE; grep -E 'MACRO_CYCLE|coordinate error' run1_stdout.log | tail -4; tail -3 run1_stdout.log
```

### 23
```bash
cd /tmp/agent_r5_5r32 && ls run1*; echo "=== final stats block ==="; grep -B5 -A30 'Final R-work' run1_stdout.log | head -60
```

### 24
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity run1_001.pdb output.prefix=run1_mp > run1_mp.log 2>&1; grep -A14 '=== Summary' run1_mp.log; echo "=== waters ==="; grep -c 'HOH' run1_001.pdb; grep '^HETATM' run1_001.pdb | grep -c ' O   HOH'
```

### 25
```bash
ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -iE 'find_peaks|holes|water_pick|polder'; cd /tmp/agent_r5_5r32 && /opt/homebrew/bin/gemmi mtz --dump run1_001.mtz 2>&1 | grep -A25 'Column '
```

### 26
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes run1_001.pdb run1_001.mtz f_map_label="2FOFCWT" diff_map_label="FOFCWT" map_cutoff=3.5 anom_map_cutoff=3.0 > peaks1.log 2>&1; grep -E 'Peaks|Holes|peak|hole' peaks1.log | head -40; echo "=== tail ==="; tail -50 peaks1.log
```

### 27 — ligand check (peak clustering)
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import math
pk=[]
for L in open('peaks_holes.pdb'):
    if L.startswith(('ATOM','HETATM')):
        occ=float(L[54:60]); b=float(L[60:66])
        xyz=(float(L[30:38]),float(L[38:46]),float(L[46:54]))
        pk.append((b,occ,xyz,L[17:20],L[22:26]))
pos=[p for p in pk if p[0]>0]
pos.sort(key=lambda p:-p[0])
print("n peaks in file",len(pk),"positive",len(pos))
print("top 15 sigma:",[round(p[0],2) for p in pos[:15]])
# cluster top peaks (>4.5 sigma) by 2.2 A linkage
strong=[p for p in pos if p[0]>4.5]
print("n strong(>4.5):",len(strong))
import itertools
parent=list(range(len(strong)))
def find(a):
    while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
    return a
for i,j in itertools.combinations(range(len(strong)),2):
    d=math.dist(strong[i][2],strong[j][2])
    if d<2.2:
        a,b=find(i),find(j)
        if a!=b: parent[a]=b
import collections
cl=collections.defaultdict(list)
for i in range(len(strong)): cl[find(i)].append(i)
sizes=sorted((len(v) for v in cl.values()),reverse=True)
print("cluster sizes:",sizes[:10])
for k,v in cl.items():
    if len(v)>=3:
        print("CLUSTER size",len(v),[ (round(strong[i][0],2), strong[i][2]) for i in v])
EOF
```

### 28
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import math
# top peak location
pk=[]
for L in open('peaks_holes.pdb'):
    if L.startswith(('ATOM','HETATM')):
        pk.append((float(L[60:66]),(float(L[30:38]),float(L[38:46]),float(L[46:54]))))
top=max(pk,key=lambda p:p[0])
print("top peak sigma %.2f at %s"%(top[0],top[1]))
# neighbours in model
at=[]
for L in open('run1_001.pdb'):
    if L.startswith(('ATOM','HETATM')) and L[76:78].strip()!='H':
        at.append((L[12:27],(float(L[30:38]),float(L[38:46]),float(L[46:54]))))
d=sorted(((math.dist(top[1],a[1]),a[0]) for a in at))[:6]
for dd,n in d: print("  %.2f  %s"%(dd,n))
# aniso status of run1 waters
aniso=set(); wat=[]
for L in open('run1_001.pdb'):
    if L.startswith('ANISOU'): aniso.add(L[12:27])
    elif L.startswith(('ATOM','HETATM')) and L[17:20]=='HOH': wat.append(L[12:27])
print("waters:",len(wat),"aniso:",sum(1 for w in wat if w in aniso))
# occupancy distribution of waters
import collections
occ=collections.Counter()
for L in open('run1_001.pdb'):
    if L.startswith(('ATOM','HETATM')) and L[17:20]=='HOH': occ[round(float(L[54:60]),1)]+=1
print("water occ:",dict(sorted(occ.items())))
EOF
```

### 29 — **[REFINE 2/6]** (crashed inside ordered-solvent update; counted)
```bash
cd /tmp/agent_r5_5r32 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine run1_001.pdb /tmp/nc_round1_cache/5r32.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not element H" main.number_of_macro_cycles=6 main.nproc=10 ordered_solvent=true ordered_solvent.mode=every_macro_cycle ordered_solvent.include_altlocs=True ordered_solvent.new_solvent=anisotropic output.prefix=run2 output.serial=1 --overwrite > run2_stdout.log 2>&1 &
echo "launched pid $!"; sleep 300; grep -E 'MACRO_CYCLE|coordinate error' /tmp/agent_r5_5r32/run2_stdout.log | tail -8
```

### 30
```bash
sleep 540; cd /tmp/agent_r5_5r32 && grep -E 'MACRO_CYCLE|coordinate error' run2_stdout.log | tail -8; ps -p 1801 >/dev/null && echo RUNNING || echo DONE
```

### 31
```bash
cd /tmp/agent_r5_5r32 && tail -40 run2_stdout.log; ls -la run2*
```

### 32
```bash
cd /tmp/agent_r5_5r32 && grep -nE '^=+ .* =+$|MACRO_CYCLE|r_work=' run2_stdout.log | head -40
```

### 33 — **[REFINE 3/6]**
```bash
cd /tmp/agent_r5_5r32 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine run1_001.pdb /tmp/nc_round1_cache/5r32.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not element H" main.number_of_macro_cycles=6 main.nproc=10 ordered_solvent=true ordered_solvent.mode=every_macro_cycle ordered_solvent.include_altlocs=True output.prefix=run3 output.serial=1 --overwrite > run3_stdout.log 2>&1 &
echo "launched pid $!"; sleep 420; grep -E 'MACRO_CYCLE|coordinate error|n_water' /tmp/agent_r5_5r32/run3_stdout.log | tail -12
```

### 34
```bash
sleep 560; cd /tmp/agent_r5_5r32 && grep -E 'MACRO_CYCLE|coordinate error' run3_stdout.log | tail -8; ps -p 14261 >/dev/null && echo RUNNING || echo DONE
```

### 35 — harness timeout; job kept running
```bash
sleep 600; cd /tmp/agent_r5_5r32 && ps -p 14261 >/dev/null && echo RUNNING || echo DONE; grep -E 'MACRO_CYCLE|coordinate error' run3_stdout.log | tail -5; grep -E 'Start R-work|Final R-work' run3_stdout.log
```

### 36
```bash
cd /tmp/agent_r5_5r32 && ps -p 14261 >/dev/null && echo RUNNING || echo DONE; grep -E 'MACRO_CYCLE|coordinate error' run3_stdout.log | tail -5; grep -E 'Start R-work|Final R-work' run3_stdout.log; tail -3 run3_stdout.log
```

### 37
```bash
sleep 420; cd /tmp/agent_r5_5r32 && ps -p 14261 >/dev/null && echo RUNNING || echo DONE; grep -E 'Start R-work|Final R-work' run3_stdout.log; ls -la run3_001.pdb 2>/dev/null && grep -c ' O   HOH' run3_001.pdb
```

### 38
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
aniso=set(); wat=[]; prot=[]
for L in open('run3_001.pdb'):
    if L.startswith('ANISOU'): aniso.add(L[12:27])
    elif L.startswith(('ATOM','HETATM')):
        if L[17:20]=='HOH': wat.append(L[12:27])
        elif L[76:78].strip()!='H': prot.append(L[12:27])
print("waters %d, aniso %d"%(len(wat),sum(1 for w in wat if w in aniso)))
print("protein heavy %d, aniso %d"%(len(prot),sum(1 for p in prot if p in aniso)))
EOF
grep -n 'ignore_final_filtering_step\|poor_cc_threshold\|poor_map_value' defaults.txt
```

### 39 — **[REFINE 4/6]**
```bash
cd /tmp/agent_r5_5r32 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine run3_001.pdb /tmp/nc_round1_cache/5r32.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not element H" main.number_of_macro_cycles=5 main.nproc=10 ordered_solvent=true ordered_solvent.mode=every_macro_cycle ordered_solvent.include_altlocs=True ordered_solvent.ignore_final_filtering_step=True ordered_solvent.secondary_map_and_map_cc_filter.poor_cc_threshold=0.60 ordered_solvent.secondary_map_and_map_cc_filter.poor_map_value_threshold=0.8 target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True output.prefix=run4 output.serial=1 --overwrite > run4_stdout.log 2>&1 &
echo "launched pid $!"; sleep 480; grep -E 'MACRO_CYCLE|coordinate error|n_water' /tmp/agent_r5_5r32/run4_stdout.log | tail -14
```

### 40
```bash
sleep 580; cd /tmp/agent_r5_5r32 && ps -p 80388 >/dev/null && echo RUNNING || echo DONE; grep -E 'MACRO_CYCLE|coordinate error' run4_stdout.log | tail -6
```

### 41
```bash
sleep 580; cd /tmp/agent_r5_5r32 && ps -p 80388 >/dev/null && echo RUNNING || echo DONE; grep -E 'Start R-work|Final R-work' run4_stdout.log; grep -E 'MACRO_CYCLE|coordinate error' run4_stdout.log | tail -3; tail -2 run4_stdout.log
```

### 42
```bash
sleep 500; cd /tmp/agent_r5_5r32 && ps -p 80388 >/dev/null && echo RUNNING || echo DONE; grep -E 'Start R-work|Final R-work' run4_stdout.log; ls -la run4_001.pdb 2>/dev/null; tail -2 run4_stdout.log
```

### 43
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity run4_001.pdb output.prefix=run4_mp > run4_mp.log 2>&1; grep -A16 '=== Summary' run4_mp.log; python3 - <<'EOF'
aniso=set(); wat=[]; prot=[]
for L in open('run4_001.pdb'):
    if L.startswith('ANISOU'): aniso.add(L[12:27])
    elif L.startswith(('ATOM','HETATM')):
        if L[17:20]=='HOH': wat.append((L[12:27],float(L[54:60]),float(L[60:66])))
        elif L[76:78].strip()!='H': prot.append(L[12:27])
print("waters %d aniso %d ; protein heavy %d aniso %d"%(len(wat),sum(1 for w in wat if w[0] in aniso),len(prot),sum(1 for p in prot if p in aniso)))
import statistics
print("water occ mean %.2f ; frac occ<0.5: %.2f ; B mean %.1f"%(statistics.mean(w[1] for w in wat), sum(1 for w in wat if w[1]<0.5)/len(wat), statistics.mean(w[2] for w in wat)))
print("waters per residue: %.2f"%(len(wat)/330))
EOF
```

### 44
```bash
cd /tmp/agent_r5_5r32 && grep -A40 -i 'clash' run4_mp.out | head -50; echo "=== CB dev ==="; grep -A6 -i 'C-beta' run4_mp.out | head -12
```

### 45 — the diagnosis: all clashes are waters
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore run4_001.pdb verbose=True > run4_clash.log 2>&1; head -40 run4_clash.log; echo "=== involving HOH ==="; grep -ci 'HOH' run4_clash.log; grep -c ':' run4_clash.log
```

### 46
```bash
cd /tmp/agent_r5_5r32 && sed -n '/Bad Clashes/,$p' run4_clash.log
```

### 47 — first pruning attempt; 2.20 A cutoff proved wrong
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import math
lines=open('run4_001.pdb').read().splitlines()
prot=[]; wat={}
for L in lines:
    if L.startswith(('ATOM','HETATM')):
        el=L[76:78].strip()
        if el=='H': continue
        xyz=(float(L[30:38]),float(L[38:46]),float(L[46:54]))
        alt=L[16]
        key=(L[21],L[22:27],alt)
        if L[17:20]=='HOH': wat[key]=xyz
        else: prot.append((alt,xyz))
# grid for speed
from collections import defaultdict
G=defaultdict(list)
def cell(p): return (int(p[0]//4),int(p[1]//4),int(p[2]//4))
for alt,p in prot: G[cell(p)].append((alt,p))
bad=set()
for key,p in wat.items():
    walt=key[2]
    c=cell(p); best=9e9
    for dx in(-1,0,1):
        for dy in(-1,0,1):
            for dz in(-1,0,1):
                for alt,q in G[(c[0]+dx,c[1]+dy,c[2]+dz)]:
                    if walt!=' ' and alt!=' ' and walt!=alt: continue
                    d=math.dist(p,q)
                    if d<best: best=d
    if best<2.20: bad.add(key)
print("waters total",len(wat),"flagged (<2.20 A to protein heavy)",len(bad))
for k in sorted(bad): print("  ",k)
out=[]
removed=0
for L in lines:
    if L.startswith(('ATOM','HETATM','ANISOU')) and L[17:20]=='HOH':
        if (L[21],L[22:27],L[16]) in bad:
            if L.startswith(('ATOM','HETATM')): removed+=1
            continue
    out.append(L)
open('run5_input.pdb','w').write("\n".join(out)+"\n")
print("removed atom records:",removed)
EOF
```

### 48 — element-aware pruning (34 waters)
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import math
from collections import defaultdict
lines=open('run4_001.pdb').read().splitlines()
prot=[]; wat={}
for L in lines:
    if L.startswith(('ATOM','HETATM')):
        el=L[76:78].strip()
        if el=='H': continue
        xyz=(float(L[30:38]),float(L[38:46]),float(L[46:54]))
        alt=L[16]; key=(L[21],L[22:27],alt)
        if L[17:20]=='HOH': wat[key]=(xyz,float(L[54:60]))
        else: prot.append((alt,xyz,el,L[12:27]))
G=defaultdict(list)
def cell(p): return (int(p[0]//4),int(p[1]//4),int(p[2]//4))
for a in prot: G[cell(a[1])].append(a)
bad={}
for key,(p,occ) in wat.items():
    walt=key[2]; c=cell(p); worst=None
    for dx in(-1,0,1):
     for dy in(-1,0,1):
      for dz in(-1,0,1):
       for alt,q,el,nm in G[(c[0]+dx,c[1]+dy,c[2]+dz)]:
        if walt!=' ' and alt!=' ' and walt!=alt: continue
        d=math.dist(p,q)
        lim = 3.00 if el in ('C','S') else 2.40
        if d<lim:
            sev=lim-d
            if worst is None or sev>worst[0]: worst=(sev,d,nm,el)
    if worst: bad[key]=worst
print("waters total",len(wat),"flagged",len(bad))
for k,v in sorted(bad.items(),key=lambda kv:-kv[1][0]):
    print("  %s%s%s  d=%.2f to %s (%s) occ=%.2f"%(k[0],k[1],k[2],v[1],v[2],v[3],wat[k][1]))
out=[];removed=0
for L in lines:
    if L.startswith(('ATOM','HETATM','ANISOU')) and L[17:20]=='HOH' and (L[21],L[22:27],L[16]) in bad:
        if not L.startswith('ANISOU'): removed+=1
        continue
    out.append(L)
open('run5_input.pdb','w').write("\n".join(out)+"\n")
print("removed water atoms:",removed,"remaining waters:",len(wat)-removed)
EOF
```

### 49 — **[REFINE 5/6]**
```bash
cd /tmp/agent_r5_5r32 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine run5_input.pdb /tmp/nc_round1_cache/5r32.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not element H" main.number_of_macro_cycles=5 main.nproc=10 ordered_solvent=False output.prefix=run5 output.serial=1 --overwrite > run5_stdout.log 2>&1 &
echo "launched pid $!"; sleep 480; grep -E 'MACRO_CYCLE|coordinate error' /tmp/agent_r5_5r32/run5_stdout.log | tail -8
```

### 50
```bash
sleep 480; cd /tmp/agent_r5_5r32 && ps -p 39870 >/dev/null && echo RUNNING || echo DONE; grep -E 'Start R-work|Final R-work' run5_stdout.log; grep -E 'MACRO_CYCLE|coordinate error' run5_stdout.log|tail -3
```

### 51
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity run5_001.pdb output.prefix=run5_mp > run5_mp.log 2>&1; grep -A14 '=== Summary' run5_mp.log; echo "=== clashes ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore run5_001.pdb verbose=True 2>/dev/null | sed -n '/Bad Clashes/,$p'
```

### 52
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes run5_001.pdb run5_001.mtz f_map_label="2FOFCWT" diff_map_label="FOFCWT" map_cutoff=3.5 > peaks5.log 2>&1; sed -n '/SUMMARY OF MAP PEAKS/,$p' peaks5.log; echo "=== strongest positive peaks near protein ==="; grep '^peak=' peaks5.log | sort -k2 -rn | head -12
```

### 53 — peak environments: separates over-pruned solvent from alternate conformers
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import math
pk=[]
for L in open('peaks_holes.pdb'):
    if L.startswith(('ATOM','HETATM')):
        s=float(L[60:66])
        if s>0: pk.append((s,(float(L[30:38]),float(L[38:46]),float(L[46:54]))))
pk.sort(key=lambda p:-p[0])
at=[]
for L in open('run5_001.pdb'):
    if L.startswith(('ATOM','HETATM')) and L[76:78].strip()!='H':
        at.append((L[12:27],(float(L[30:38]),float(L[38:46]),float(L[46:54])),float(L[54:60])))
for s,p in pk[:6]:
    print("PEAK %.1f sigma"%s)
    d=sorted(((math.dist(p,a[1]),a[0],a[2]) for a in at))[:7]
    for dd,n,o in d: print("    %.2f  %s occ=%.2f"%(dd,n,o))
EOF
```

### 54 — enumerate altloc candidates
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
import math
pk=[]
for L in open('peaks_holes.pdb'):
    if L.startswith(('ATOM','HETATM')):
        s=float(L[60:66])
        if s>3.5: pk.append((s,(float(L[30:38]),float(L[38:46]),float(L[46:54]))))
at=[]
for L in open('run5_001.pdb'):
    if L.startswith(('ATOM','HETATM')) and L[76:78].strip()!='H':
        at.append((L[12:16].strip(),L[16],L[17:20],L[22:26].strip(),
                   (float(L[30:38]),float(L[38:46]),float(L[46:54]))))
mc={'N','CA','C','O','OXT'}
print("Peaks with an impossible contact (<2.87 A) to a protein side-chain CARBON -> altloc candidates:")
seen={}
for s,p in sorted(pk,key=lambda x:-x[0]):
    for nm,alt,res,num,q in at:
        if res=='HOH' or nm in mc: continue
        d=math.dist(p,q)
        if d<2.87 and nm[0] in 'CS':
            key=(res,num)
            if key not in seen or s>seen[key][0]: seen[key]=(s,d,nm,alt)
for k,v in sorted(seen.items(),key=lambda kv:-kv[1][0]):
    print("   %s %-4s  peak %5.1f sigma at %.2f A from %s (altloc '%s')"%(k[0],k[1],v[0],v[1],v[2],v[3]))
EOF
```

### 55 — chi-scan altloc builder, 8 candidates (7 scored ~0 and were rejected)
```bash
cd /tmp/agent_r5_5r32 && cat > build_alt.py <<'PYEOF'
import math, copy
def rot(p, o, axis, ang):
    a=[axis[i]-o[i] for i in range(3)]; n=math.sqrt(sum(x*x for x in a)); a=[x/n for x in a]
    v=[p[i]-o[i] for i in range(3)]
    c=math.cos(ang); s=math.sin(ang)
    d=sum(v[i]*a[i] for i in range(3))
    cr=[a[1]*v[2]-a[2]*v[1], a[2]*v[0]-a[0]*v[2], a[0]*v[1]-a[1]*v[0]]
    return tuple(o[i]+v[i]*c+cr[i]*s+a[i]*d*(1-c) for i in range(3))

BB={'N','CA','C','O','OXT','H','H1','H2','H3','HA','HA2','HA3'}
CBSET={'CB','HB','HB1','HB2','HB3'}
GAMMA={'CG','CG1','CG2','OG','OG1','SG','HG','HG1','HG2','HG3','HG11','HG12','HG13','HG21','HG22','HG23'}

lines=open('run5_001.pdb').read().splitlines()
# peaks
peaks=[]
for L in open('peaks_holes.pdb'):
    if L.startswith(('ATOM','HETATM')):
        s=float(L[60:66])
        if s>3.5: peaks.append((s,(float(L[30:38]),float(L[38:46]),float(L[46:54]))))

targets=[('ASP','146'),('TYR','79'),('HIS','164'),('LEU','128'),('THR','143'),
         ('GLN','140'),('ILE','77'),('SER','84')]

# index model
recs=[]
for i,L in enumerate(lines):
    if L.startswith(('ATOM','HETATM','ANISOU')):
        recs.append((i,L[12:16].strip(),L[16],L[17:20],L[22:26].strip(),L[21]))
def xyz(L): return (float(L[30:38]),float(L[38:46]),float(L[46:54]))
allheavy=[(xyz(lines[i]),lines[i][17:20],lines[i][22:26].strip())
          for i,nm,alt,res,num,ch in recs if lines[i].startswith(('ATOM','HETATM')) and lines[i][76:78].strip()!='H']

report=[]
newlines=list(lines)
insert={}   # index -> list of extra lines
for res,num in targets:
    idxs=[i for i,nm,alt,r,n,ch in recs if r==res and n==num and alt==' ']
    if not idxs: report.append((res,num,'skip: no single-conformer atoms')); continue
    atoms={}
    for i in idxs:
        L=lines[i]
        if L.startswith('ANISOU'): continue
        atoms[L[12:16].strip()]=xyz(L)
    if 'CA' not in atoms or 'CB' not in atoms: report.append((res,num,'skip: no CA/CB')); continue
    # peaks belonging to this residue: within 4.0 A of any side-chain atom
    sc=[v for k,v in atoms.items() if k not in BB]
    mine=[(s,p) for s,p in peaks if any(math.dist(p,q)<4.0 for q in sc)]
    if not mine: report.append((res,num,'skip: no nearby peak')); continue
    mv1=[k for k in atoms if k not in BB and k not in CBSET]
    gam=[k for k in atoms if k in GAMMA and k[0] in 'COS']
    mv2=[k for k in mv1 if k not in GAMMA] if gam else []
    best=None
    for a1 in range(0,360,5):
        c1={k:(rot(v,atoms['CA'],atoms['CB'],math.radians(a1)) if k in mv1 else v) for k,v in atoms.items()}
        a2list=range(0,360,10) if mv2 else [0]
        for a2 in a2list:
            if mv2:
                g=gam[0]
                c2={k:(rot(v,c1['CB'],c1[g],math.radians(a2)) if k in mv2 else v) for k,v in c1.items()}
            else: c2=c1
            hv={k:v for k,v in c2.items() if not k.startswith('H')}
            # score: peaks explained
            sc_=0.0
            for s,p in mine:
                dm=min(math.dist(p,v) for k,v in hv.items() if k not in BB)
                sc_+= s*math.exp(-(dm/0.9)**2)
            # clash penalty vs other residues
            pen=0.0
            for k,v in hv.items():
                if k in BB: continue
                for q,r2,n2 in allheavy:
                    if r2==res and n2==num: continue
                    d=math.dist(v,q)
                    if d<3.0: pen+=(3.0-d)**2*8
            tot=sc_-pen
            if best is None or tot>best[0]: best=(tot,a1,a2,c2,sc_,pen)
    tot,a1,a2,conf,sc_,pen=best
    # require it to be a genuinely different conformer
    shift=max(math.dist(conf[k],atoms[k]) for k in mv1) if mv1 else 0
    report.append((res,num,"chi1 %+d chi2 %+d  peakscore %.1f pen %.1f maxshift %.2f A  npeaks %d"%(a1,a2,sc_,pen,shift,len(mine))))
    if shift<0.8: continue
    for i in idxs:
        L=lines[i]; nm=L[12:16].strip()
        occ=" 0.50"
        A=L[:16]+'A'+L[17:]
        if not L.startswith('ANISOU'): A=A[:54]+"  0.50"+A[60:]
        B=L[:16]+'B'+L[17:]
        if L.startswith('ANISOU'):
            newlines[i]=A; insert.setdefault(i,[]).append(B)
        else:
            x,y,z=conf[nm]
            B=B[:30]+"%8.3f%8.3f%8.3f"%(x,y,z)+B[54:]
            B=B[:54]+"  0.50"+B[60:]
            newlines[i]=A; insert.setdefault(i,[]).append(B)
out=[]
for i,L in enumerate(newlines):
    out.append(L)
    for e in insert.get(i,[]): out.append(e)
open('run6_input.pdb','w').write("\n".join(out)+"\n")
for r in report: print("  ",r)
print("wrote run6_input.pdb ; added altloc atoms:",sum(len(v) for v in insert.values()))
PYEOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python build_alt.py
```

### 56 — restrict to ASP 146
```bash
cd /tmp/agent_r5_5r32 && sed -i.bak "s/^targets=\[('ASP','146'),('TYR','79'),('HIS','164'),('LEU','128'),('THR','143'),$/targets=[('ASP','146'),/" build_alt.py && sed -i.bak2 "s/^         ('GLN','140'),('ILE','77'),('SER','84')\]$/         ]/" build_alt.py && grep -A2 '^targets' build_alt.py && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python build_alt.py && grep -c 'ASP A 146' run6_input.pdb
```

### 57 — **[REJECTED — not counted]** malformed PDB, rejected at parsing before refinement
```bash
cd /tmp/agent_r5_5r32 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine run6_input.pdb /tmp/nc_round1_cache/5r32.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not element H" main.number_of_macro_cycles=5 main.nproc=10 ordered_solvent=true ordered_solvent.mode=every_macro_cycle ordered_solvent.include_altlocs=True ordered_solvent.ignore_final_filtering_step=True output.prefix=run6 output.serial=1 --overwrite > run6_stdout.log 2>&1 &
echo "launched pid $!"; sleep 500; grep -E 'MACRO_CYCLE|coordinate error' /tmp/agent_r5_5r32/run6_stdout.log | tail -8
```
Output: `Sorry: An atomic model is required.` — no refinement performed.

### 58
```bash
cd /tmp/agent_r5_5r32 && grep -E 'MACRO_CYCLE|coordinate error|Sorry|Error' run6_stdout.log | tail -10; tail -5 run6_stdout.log
```

### 59
```bash
cd /tmp/agent_r5_5r32 && ls -la run6_input.pdb run5_001.pdb; head -3 run6_input.pdb; echo "..."; grep -c '^ATOM\|^HETATM' run6_input.pdb; echo "=== CRYST1 ==="; grep -c '^CRYST1' run6_input.pdb; echo "=== ASP146 block ==="; grep 'ASP A 146' run6_input.pdb | head -6
```

### 60 — rebuild the split through the iotbx hierarchy
```bash
cd /tmp/agent_r5_5r32 && cat > build_alt2.py <<'PYEOF'
import math
import iotbx.pdb
from scitbx.array_family import flex

def rot(p,o,ax,ang):
    a=[ax[i]-o[i] for i in range(3)]; n=math.sqrt(sum(x*x for x in a)); a=[x/n for x in a]
    v=[p[i]-o[i] for i in range(3)]; c=math.cos(ang); s=math.sin(ang)
    d=sum(v[i]*a[i] for i in range(3))
    cr=[a[1]*v[2]-a[2]*v[1],a[2]*v[0]-a[0]*v[2],a[0]*v[1]-a[1]*v[0]]
    return tuple(o[i]+v[i]*c+cr[i]*s+a[i]*d*(1-c) for i in range(3))

pdb_in=iotbx.pdb.input(file_name="run5_001.pdb")
h=pdb_in.construct_hierarchy()
peaks=[]
for L in open('peaks_holes.pdb'):
    if L.startswith(('ATOM','HETATM')):
        s=float(L[60:66])
        if s>3.5: peaks.append((s,(float(L[30:38]),float(L[38:46]),float(L[46:54]))))

BB={'N','CA','C','O','OXT','H','HA'}
target=('146','ASP')
done=False
for model in h.models():
    for chain in model.chains():
        for rg in chain.residue_groups():
            if rg.resseq.strip()!=target[0]: continue
            ags=list(rg.atom_groups())
            if len(ags)!=1 or ags[0].resname.strip()!=target[1]: continue
            ag=ags[0]
            coords={a.name.strip():tuple(a.xyz) for a in ag.atoms()}
            side=[a.name.strip() for a in ag.atoms() if a.name.strip() not in BB]
            mv1=[n for n in side if n not in ('CB','HB2','HB3','HB')]
            mv2=[n for n in mv1 if n not in ('CG',)]
            sc=[coords[n] for n in side]
            mine=[(s,p) for s,p in peaks if any(math.dist(p,q)<4.0 for q in sc)]
            print("nearby peaks:",[round(s,1) for s,_ in mine])
            other=[]
            for m2 in h.models():
                for c2 in m2.chains():
                    for r2 in c2.residue_groups():
                        if r2.resseq.strip()==target[0] and c2.id==chain.id: continue
                        for a2 in r2.atoms():
                            if a2.element.strip()!='H': other.append(tuple(a2.xyz))
            best=None
            for a1 in range(0,360,5):
                c1={k:(rot(v,coords['CA'],coords['CB'],math.radians(a1)) if k in mv1 else v) for k,v in coords.items()}
                for a2 in range(0,360,10):
                    c2={k:(rot(v,c1['CB'],c1['CG'],math.radians(a2)) if k in mv2 else v) for k,v in c1.items()}
                    hv={k:v for k,v in c2.items() if not k.startswith('H') and k not in BB}
                    sc_=sum(s*math.exp(-(min(math.dist(p,v) for v in hv.values())/0.9)**2) for s,p in mine)
                    pen=0.0
                    for v in hv.values():
                        for q in other:
                            d=math.dist(v,q)
                            if d<3.0: pen+=(3.0-d)**2*8
                    if best is None or sc_-pen>best[0]: best=(sc_-pen,a1,a2,c2,sc_,pen)
            tot,a1,a2,conf,s_,pen=best
            print("chosen chi1 %+d chi2 %+d peakscore %.1f pen %.1f"%(a1,a2,s_,pen))
            # split: keep backbone in a shared atom_group (altloc ''), side chain into A/B
            agA=ag.detached_copy(); agB=ag.detached_copy()
            agA.altloc='A'; agB.altloc='B'
            rg.remove_atom_group(ag)
            # backbone-only group
            import iotbx.pdb.hierarchy as hy
            agBB=hy.atom_group(altloc='', resname='ASP')
            for a in agA.atoms():
                if a.name.strip() in BB:
                    agBB.append_atom(a.detached_copy())
            for grp in (agA,agB):
                for a in list(grp.atoms()):
                    if a.name.strip() in BB: grp.remove_atom(a)
                    else: a.occ=0.5
            for a in agB.atoms():
                a.set_xyz(conf[a.name.strip()])
                a.uij=(-1,-1,-1,-1,-1,-1); a.set_uij((-1,-1,-1,-1,-1,-1))
            rg.append_atom_group(agBB); rg.append_atom_group(agA); rg.append_atom_group(agB)
            done=True
print("split done:",done)
h.atoms().reset_serial()
h.write_pdb_file(file_name="run6_input.pdb",
                 crystal_symmetry=pdb_in.crystal_symmetry())
print("wrote run6_input.pdb")
PYEOF
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python build_alt2.py && grep 'ASP A 146' run6_input.pdb | grep -v ANISOU
```

### 61 — **[REFINE 6/6]**
```bash
cd /tmp/agent_r5_5r32 && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine run6_input.pdb /tmp/nc_round1_cache/5r32.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not element H" main.number_of_macro_cycles=5 main.nproc=10 ordered_solvent=true ordered_solvent.mode=every_macro_cycle ordered_solvent.include_altlocs=True ordered_solvent.ignore_final_filtering_step=True output.prefix=run6 output.serial=1 --overwrite > run6_stdout.log 2>&1 &
echo "launched pid $!"; sleep 420; grep -E 'MACRO_CYCLE|coordinate error|Sorry' /tmp/agent_r5_5r32/run6_stdout.log | tail -8
```

### 62
```bash
sleep 560; cd /tmp/agent_r5_5r32 && ps -p 84323 >/dev/null && echo RUNNING || echo DONE; grep -E 'MACRO_CYCLE|coordinate error' run6_stdout.log | tail -6
```

### 63
```bash
sleep 560; cd /tmp/agent_r5_5r32 && ps -p 84323 >/dev/null && echo RUNNING || echo DONE; grep -E 'Start R-work|Final R-work' run6_stdout.log; grep -E 'MACRO_CYCLE|coordinate error' run6_stdout.log|tail -3; tail -2 run6_stdout.log
```

### 64
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity run6_001.pdb output.prefix=run6_mp > run6_mp.log 2>&1; grep -A14 '=== Summary' run6_mp.log; echo "=== clashes ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore run6_001.pdb verbose=True 2>/dev/null | sed -n '/Bad Clashes/,$p'; echo "=== ASP146 occupancies ==="; grep 'ASP A 146' run6_001.pdb | grep -v ANISOU | grep -v ' H'; echo "=== waters ==="; python3 -c "
import sys
w=set()
for L in open('/tmp/agent_r5_5r32/run6_001.pdb'):
    if L.startswith(('ATOM','HETATM')) and L[17:20]=='HOH': w.add((L[21],L[22:27],L[16]))
print(len(w))"
```

### 65 — remove 3 clashing waters, then re-measure all candidates independently
```bash
cd /tmp/agent_r5_5r32 && python3 - <<'EOF'
bad={('S','1013 ',' '),('S',' 794 ','B'),('S',' 796 ','A')}
out=[];rm=0
for L in open('run6_001.pdb'):
    L=L.rstrip('\n')
    if L.startswith(('ATOM','HETATM','ANISOU')) and L[17:20]=='HOH' and (L[21],L[22:27],L[16]) in bad:
        if not L.startswith('ANISOU'): rm+=1
        continue
    out.append(L)
open('final_candidate.pdb','w').write("\n".join(out)+"\n")
print("removed water atom records:",rm)
EOF
for m in run6_001 final_candidate run5_001; do echo "=== $m ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $m.pdb /tmp/nc_round1_cache/5r32.mtz f_obs_label="FOBS" r_free_flags_label="R-free-flags" 2>/dev/null | grep -E '^  r_work|^  r_free'; done
```

### 66 — final validation
```bash
cd /tmp/agent_r5_5r32 && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity final_candidate.pdb output.prefix=final_mp > final_mp.log 2>&1; grep -A14 '=== Summary' final_mp.log; echo "=== clashes ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore final_candidate.pdb verbose=True 2>/dev/null | sed -n '/Bad Clashes/,$p'
```

### 67 — deliver
```bash
cd /tmp/agent_r5_5r32 && cp final_candidate.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/5R32/final.pdb && ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/5R32/ && grep -c '^ATOM\|^HETATM' /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/5R32/final.pdb && grep -c '^CRYST1' /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/5R32/final.pdb
```

---

## Compliance notes

- **No network access of any kind.** No `curl`, `wget`, `phenix.fetch_pdb`, or any other
  fetch was issued at any point.
- **No repository `ref/` or `data/` read.** The only paths read are
  `/tmp/nc_round1_work/r4p_5r32.pdb`, `/tmp/nc_round1_cache/5r32.mtz`, and files I created
  under `/tmp/agent_r5_5r32/`. The only repository path touched is the deliverable directory
  `data/agents/round5/5R32/`, which is written, never read.
- **No `*_mask.json`, `*_validation.xml`,** or any file under `/tmp/nc_round1_cache/` other
  than `5r32.mtz`.
- **Deposited phases not used.** The MTZ's `FWT/PHWT` and `DELFWT/PHDELWT` columns (map
  coefficients from the deposited model) were deliberately not used for map inspection or
  rebuilding; only `FOBS`, `SIGFOBS` and `R-free-flags` were, and every map examined came
  from my own model's phases.
- **Refinement budget: 6 of 6 used.** Runs 1, 2 (crashed after modifying the model — counted
  anyway), 3, 4, 5, 6. The launch at step 57 was rejected at file parsing before refinement
  began and is not counted.
