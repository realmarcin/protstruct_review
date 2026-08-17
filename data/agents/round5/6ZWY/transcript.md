# Transcript — blinded agentic recovery of 6ZWY (round 5)

Every shell command executed, in order, verbatim. Working dir `/tmp/agent_r5_6zwy/`
unless stated otherwise.

Refinement-program invocations are numbered **[REFINE n/6]**. Launches that failed
before the program executed are annotated **[NOT COUNTED]** with the reason.

---

## Phase 0 — setup and input inspection (no refinement)

```bash
mkdir -p /tmp/agent_r5_6zwy && cd /tmp/agent_r5_6zwy && ls -la /tmp/nc_round1_work/r4p_6zwy.pdb /tmp/nc_round1_cache/6zwy.mtz
```

```bash
/opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/6zwy.mtz 2>&1 | head -60
```

```bash
cd /tmp/agent_r5_6zwy && head -30 /tmp/nc_round1_work/r4p_6zwy.pdb && echo "=== COUNTS ===" && grep -c '^ATOM' /tmp/nc_round1_work/r4p_6zwy.pdb && grep -c '^HETATM' /tmp/nc_round1_work/r4p_6zwy.pdb && echo "=== HET residue types ===" && awk '/^HETATM/{print substr($0,18,3)}' /tmp/nc_round1_work/r4p_6zwy.pdb | sort | uniq -c | sort -rn
```

```bash
cd /tmp/agent_r5_6zwy && /opt/homebrew/bin/gemmi mtz -s /tmp/nc_round1_cache/6zwy.mtz 2>&1 | tail -50
```

```bash
cd /tmp/agent_r5_6zwy && /opt/homebrew/bin/gemmi mtz2cif /tmp/nc_round1_cache/6zwy.mtz - 2>/dev/null | head -5 ; python3 -c "
import gemmi, math
m = gemmi.read_mtz_file('/tmp/nc_round1_cache/6zwy.mtz')
print('cell', m.cell, 'sg', m.spacegroup.hm)
import numpy as np
arr = np.array(m, copy=False)
cols = [c.label for c in m.columns]
print(cols)
h = arr[:,0:3]
d = np.array([m.cell.calculate_d(gemmi.Miller(int(a),int(b),int(c))) for a,b,c in h[:2000]])
fobs = arr[:, cols.index('FOBS')]
sel = ~np.isnan(fobs)
print('n obs', sel.sum())
ds = np.array([m.cell.calculate_d(gemmi.Miller(int(a),int(b),int(c))) for a,b,c in h[sel]])
print('dmin obs %.3f dmax %.2f' % (ds.min(), ds.max()))
allds = np.array([m.cell.calculate_d(gemmi.Miller(int(a),int(b),int(c))) for a,b,c in h])
print('dmin all %.3f' % allds.min())
f1 = arr[:, cols.index('FOBS-1')]
r = f1[sel]/fobs[sel]
print('FOBS-1/FOBS ratio: mean %.4f std %.4f min %.4f max %.4f' % (r.mean(), r.std(), r.min(), r.max()))
for lbl in ['R-free-flags','R-free-flags-1','R-free-flags-2','R-free-flags-3']:
    v = arr[sel, cols.index(lbl)]
    u,c = np.unique(v, return_counts=True)
    print(lbl, dict(zip(u.astype(int)[:5], c[:5])), 'nvals', len(u))
"
```
(failed: `gemmi.Miller` does not exist in this gemmi python build — re-run below with `make_d_array`)

```bash
cd /tmp/agent_r5_6zwy && python3 -c "
import gemmi, numpy as np
m = gemmi.read_mtz_file('/tmp/nc_round1_cache/6zwy.mtz')
arr = np.array(m, copy=False)
cols = [c.label for c in m.columns]
d = m.make_d_array()
fobs = arr[:, cols.index('FOBS')]
sel = ~np.isnan(fobs)
print('n obs %d  dmin_obs %.3f dmax_obs %.2f  dmin_all %.3f' % (sel.sum(), d[sel].min(), d[sel].max(), d.min()))
import collections
edges=[64,3,2,1.6,1.4,1.3,1.2,1.15,1.1,1.05,1.0,0.9,0.83]
for lo,hi in zip(edges[:-1],edges[1:]):
    inshell=(d<=lo)&(d>hi)
    if inshell.sum():
        print('  %5.2f-%5.2f  ntot %6d  nobs %6d  compl %.3f' % (lo,hi,inshell.sum(),(inshell&sel).sum(),(inshell&sel).sum()/inshell.sum()))
f1 = arr[:, cols.index('FOBS-1')]
r = f1[sel]/fobs[sel]
print('FOBS-1/FOBS ratio mean %.4f std %.4f min %.4f max %.4f' % (r.mean(), r.std(), r.min(), r.max()))
for lbl in ['R-free-flags','R-free-flags-1','R-free-flags-2','R-free-flags-3']:
    v = arr[sel, cols.index(lbl)]
    u,c = np.unique(v, return_counts=True)
    print(lbl,'nvals',len(u), list(zip(u.astype(int)[:4], c[:4])))
a=arr[sel,cols.index('R-free-flags')]; b=arr[sel,cols.index('R-free-flags-2')]
print('flags 0 vs 2 identical:', np.array_equal(a,b))
"
```

```bash
cd /tmp/agent_r5_6zwy && python3 -c "
import gemmi, numpy as np
st = gemmi.read_structure('/tmp/nc_round1_work/r4p_6zwy.pdb')
print('models',len(st),'name',st.name,'resolution',st.resolution)
for ch in st[0]:
    print('chain',ch.name,'nres',len(ch))
b=[];occ=[];alt=set();aniso=0;n=0
for ch in st[0]:
  for r in ch:
    for a in r:
      b.append(a.b_iso); occ.append(a.occ); n+=1
      if a.altloc: alt.add(a.altloc)
      if a.aniso.nonzero(): aniso+=1
b=np.array(b);occ=np.array(occ)
print('natoms',n,'aniso',aniso)
print('B: min %.2f max %.2f mean %.2f'%(b.min(),b.max(),b.mean()))
print('occ: min %.2f max %.2f  n_occ<1: %d'%(occ.min(),occ.max(),(occ<1).sum()))
print('altlocs',sorted(alt))
"
```

```bash
cd /tmp/agent_r5_6zwy && awk '/^HETATM/{print substr($0,18,10)}' /tmp/nc_round1_work/r4p_6zwy.pdb | sort -u | grep -v HOH | head -20; echo "--- tail ---"; grep -E '^(LINK|SSBOND|MODRES|REMARK   2|REMARK   3   R VALUE)' /tmp/nc_round1_work/r4p_6zwy.pdb | head -20
```

## Phase 1 — baseline measurement (no refinement)

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_6zwy.pdb /tmp/nc_round1_cache/6zwy.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > mvd_start.log 2>&1; tail -60 mvd_start.log
```

```bash
ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -iE 'molprob|clash|rama|rota|ready_set|reduce|geometry|validat|dynamics|refine|holton|cablam|real_space'
```

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity /tmp/nc_round1_work/r4p_6zwy.pdb output.prefix=mp_start output.quiet=False > mp_start.log 2>&1; sed -n '/Summary/,$p' mp_start.log | head -40; echo "=== RMS ==="; grep -iE 'rms|bond|angle|clashscore|ramachandran|rotamer|C-beta|outlier' mp_start.log | head -40
```

```bash
cd /tmp/agent_r5_6zwy && python3 -c "
import gemmi, numpy as np
st = gemmi.read_structure('/tmp/nc_round1_work/r4p_6zwy.pdb')
st.setup_entities()
prot=[];wat=[];lig=[]
for ch in st[0]:
  for r in ch:
    for a in r:
      t = wat if r.name=='HOH' else (lig if r.het_flag=='H' else prot)
      t.append(a.b_iso)
for n,v in [('protein',prot),('water',wat),('ligand',lig)]:
    v=np.array(v); print('%-8s n=%4d B mean %6.2f med %6.2f min %5.2f max %6.2f'%(n,len(v),v.mean(),np.median(v),v.min(),v.max()))
dev=[]
for ch in st[0]:
  for r in ch:
    for a in r:
      if a.aniso.nonzero():
        u=a.aniso; tr=(u.u11+u.u22+u.u33)/3.0
        dev.append(8*np.pi**2*tr - a.b_iso)
dev=np.array(dev); print('ANISOU trace-vs-Biso deviation: mean %.4f max abs %.4f'%(dev.mean(),np.abs(dev).max()))
ns = gemmi.NeighborSearch(st[0], st, 5).populate()
cs = gemmi.ContactSearch(3.5); cs.ignore = gemmi.ContactSearch.Ignore.SameResidue
res = cs.find_contacts(ns)
wc = [c for c in res if c.partner1.residue.name=='HOH' or c.partner2.residue.name=='HOH']
dd=np.array([c.dist for c in wc])
print('water contacts <3.5A: n=%d  min %.2f  frac<2.2A %.3f'%(len(dd),dd.min(),(dd<2.2).mean()))
"
```
(B-factor and ANISOU sections printed; the NeighborSearch call raised a TypeError on
argument order and the contact block did not run — not repeated, the information was
not needed)

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | grep -inE 'rotamer|ordered_solvent|optimize_x|optimize_a|nqh|number_of_macro|simulated_anneal|anisotropic|test_flag_value|target_weight' | head -50
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | sed -n '150,230p'
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | sed -n '255,300p;470,500p;840,880p;1020,1035p'
```

```bash
cd /tmp/agent_r5_6zwy && python3 -c "
import gemmi
from collections import defaultdict
expected = {
 'ALA':6,'ARG':11,'ASN':8,'ASP':8,'CYS':6,'GLN':9,'GLU':9,'GLY':4,'HIS':10,
 'ILE':8,'LEU':8,'LYS':9,'MET':8,'PHE':11,'PRO':7,'SER':7,'THR':7,'TRP':14,
 'TYR':12,'VAL':7}
st = gemmi.read_structure('/tmp/nc_round1_work/r4p_6zwy.pdb')
st.remove_hydrogens()
bad=[]
for ch in st[0]:
  for r in ch:
    if r.name in expected:
        names = set(a.name for a in r if not a.altloc or a.altloc=='A')
        n = len(names)
        if n < expected[r.name]:
            bad.append((r.seqid.num, r.name, n, expected[r.name]))
print('residues with missing heavy atoms (altloc A/blank):', len(bad))
for b in bad[:25]: print('   ', b)
seq=[r.seqid.num for ch in st[0] for r in ch if r.name in expected or r.name=='CSS']
print('polymer residue range', min(seq), max(seq), 'count', len(seq))
gaps=[(a,b) for a,b in zip(seq,seq[1:]) if b!=a+1]
print('numbering gaps:', gaps)
"
```
(buggy: gemmi returns `'\x00'` for a blank altloc, so the altloc filter excluded every
atom. Superseded by the corrected version below.)

```bash
cd /tmp/agent_r5_6zwy && cp /tmp/nc_round1_work/r4p_6zwy.pdb start.pdb && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ready_set start.pdb add_h_to_water=False optimise_final_geometry_of_hydrogens=False > ready_set.log 2>&1; echo "exit=$?"; tail -30 ready_set.log; ls -la /tmp/agent_r5_6zwy/
```

```bash
cd /tmp/agent_r5_6zwy && python3 -c "
import gemmi
expected = {'ALA':6,'ARG':11,'ASN':8,'ASP':8,'CYS':6,'GLN':9,'GLU':9,'GLY':4,'HIS':10,'ILE':8,'LEU':8,'LYS':9,'MET':8,'PHE':11,'PRO':7,'SER':7,'THR':7,'TRP':14,'TYR':12,'VAL':7}
st = gemmi.read_structure('/tmp/nc_round1_work/r4p_6zwy.pdb'); st.remove_hydrogens()
bad=[]
for ch in st[0]:
  for r in ch:
    if r.name in expected:
        names=set(a.name for a in r)
        if len(names) < expected[r.name]:
            bad.append((r.seqid.num,r.name,len(names),expected[r.name]))
print('residues missing heavy atoms:',len(bad))
for b in bad: print('   ',b)
" ; echo "=== H added ==="; grep -c ' H' /tmp/agent_r5_6zwy/start.updated.pdb; python3 -c "
import gemmi
s=gemmi.read_structure('/tmp/agent_r5_6zwy/start.updated.pdb')
n=sum(1 for ch in s[0] for r in ch for a in r)
h=sum(1 for ch in s[0] for r in ch for a in r if a.element==gemmi.Element('H'))
print('total atoms',n,'H',h,'non-H',n-h)"
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | grep -n 'miller_array' | head; echo "=== xray_data block ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | sed -n '1,70p'
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>/dev/null | grep -nE '^[a-z_]+ \{|^[a-z_]+ =' | head -20; echo "=== help ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --help 2>&1 | grep -iE 'dry|overwrite|serial|prefix|nproc' | head -20
```

## Phase 2 — refinement

### Dry-run validation of the run-1 command — **[NOT COUNTED]** (`--dry-run`: arguments validated, refinement program never executed)

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start.updated.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=5 output.prefix=r1 output.serial=1 --overwrite --dry-run > dryrun1.log 2>&1; echo "exit=$?"; tail -35 dryrun1.log
```

```bash
cd /tmp/agent_r5_6zwy && grep -nE 'labels|user_selected|FOBS|R-free' dryrun1.log | head -25
```

### **[REFINE 1/6]** — xyz + local real-space + individual ADP + occupancies, 5 macro-cycles, no solvent update

```bash
cd /tmp/agent_r5_6zwy && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine start.updated.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=5 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1 &
echo "launched pid $!"; sleep 90; tail -5 /tmp/agent_r5_6zwy/r1.log; grep -cE 'macro_cycle' /tmp/agent_r5_6zwy/r1.log
```

```bash
sleep 300; cd /tmp/agent_r5_6zwy && grep -E '^ *(start|final|macro_cycle|r_work|r_free)' r1.log | tail -20; echo "---"; grep -nE 'R-WORK|R-FREE|r_work=|r_free=' r1.log | tail -12
```

```bash
sleep 420; cd /tmp/agent_r5_6zwy && tail -3 r1.log; echo "=== R history ==="; grep -E '^\| r_work=' r1.log | tail -10; ls -la r1_*.pdb 2>/dev/null
```

```bash
cd /tmp/agent_r5_6zwy && sed -n '/Final refinement statistics/,/^$/p' r1.log | head -60; echo "=== geom summary ==="; grep -A25 'Geometry statistics' r1.log | tail -30
```

```bash
cd /tmp/agent_r5_6zwy && tail -120 r1.log | head -100
```

```bash
ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -iE 'peak|hole|find_'
```

```bash
cd /tmp/agent_r5_6zwy && ls -la r1_001.* 2>/dev/null; python3 -c "
import gemmi
s=gemmi.read_structure('/tmp/agent_r5_6zwy/r1_001.pdb')
n=sum(1 for ch in s[0] for r in ch for a in r)
w=sum(1 for ch in s[0] for r in ch if r.name=='HOH')
print('atoms',n,'waters',w)
for ch in s[0]: print('chain',ch.name,len(ch))
"
```

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r1_001.pdb r1_001.mtz > peaks_r1.log 2>&1; echo "exit=$?"; grep -iE 'peak|hole|found|sigma' peaks_r1.log | tail -40
```

```bash
cd /tmp/agent_r5_6zwy && sed -n '/SUMMARY OF MAP PEAKS/,$p' peaks_r1.log; echo "=== counts ==="; grep -c '^peak=' peaks_r1.log; grep '^peak=' peaks_r1.log | awk '{print ($2>0)?"pos":"neg"}' | sort | uniq -c
```

```bash
cd /tmp/agent_r5_6zwy && grep '^peak=' peaks_r1.log | sort -k2 -rn | head -30
```

### Dry-run validation of the run-2 command — **[NOT COUNTED]**

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first output.prefix=r2 output.serial=2 --overwrite --dry-run > dryrun2.log 2>&1; echo "exit=$?"; tail -6 dryrun2.log
```

### **[REFINE 2/6]** — same, plus ordered-solvent rebuilding every macro-cycle after the first, 6 macro-cycles

```bash
cd /tmp/agent_r5_6zwy && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=6 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first output.prefix=r2 output.serial=2 --overwrite > r2.log 2>&1 &
echo "launched pid $!"; sleep 240; tail -2 /tmp/agent_r5_6zwy/r2.log
```

```bash
sleep 600; cd /tmp/agent_r5_6zwy && grep -E '^\| r_work=' r2.log | tail -8; echo "--- last line ---"; tail -2 r2.log
```

```bash
sleep 700; cd /tmp/agent_r5_6zwy && grep -E '^\| r_work=' r2.log | tail -6; echo "--- last ---"; tail -2 r2.log; ls -la r2_002.pdb 2>/dev/null
```

```bash
sleep 600; cd /tmp/agent_r5_6zwy && grep -E '^\| r_work=' r2.log | tail -4; echo "--- last ---"; tail -3 r2.log; ls -la r2_002.pdb 2>/dev/null; ps aux | grep -c '[p]henix.refine'
```

```bash
cd /tmp/agent_r5_6zwy && sed -n '/REFINEMENT STATISTICS STEP BY STEP/,/^ *$/p' r2.log | grep -E '^\s+[0-9]' | awk '{print}' | tail -60
```

```bash
cd /tmp/agent_r5_6zwy && tail -40 r2.log | grep -E 'Final|r_work|r_free|bond|angle' ; echo "=== FINAL BLOCK ==="; grep -B2 -A18 'Final R-work' r2.log | tail -30
```

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r2_002.pdb output.prefix=mp_r2 > mp_r2.log 2>&1; sed -n '/Summary/,$p' mp_r2.log | head -20
```

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r2_002.pdb r2_002.mtz > peaks_r2.log 2>&1; sed -n '/SUMMARY OF MAP PEAKS/,$p' peaks_r2.log; echo "=== top positive ==="; grep '^peak=' peaks_r2.log | sort -k2 -rn | head -15; echo "=== top negative ==="; grep '^peak=' peaks_r2.log | sort -k2 -n | head -8
```

### Dry-run validation of the run-3 command — **[NOT COUNTED]** (combined with a core count)

```bash
sysctl -n hw.ncpu hw.physicalcpu; echo "---"; cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_002.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=4 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=6 output.prefix=r3 output.serial=3 --overwrite --dry-run > dryrun3.log 2>&1; echo "exit=$?"; tail -4 dryrun3.log
```

### **[REFINE 3/6]** — XYZ- *and* ADP-weight optimization + ordered solvent, 4 macro-cycles, nproc=6

```bash
cd /tmp/agent_r5_6zwy && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_002.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=4 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=6 output.prefix=r3 output.serial=3 --overwrite > r3.log 2>&1 &
echo "launched pid $!"; sleep 900; grep -E '^\| r_work=' /tmp/agent_r5_6zwy/r3.log | tail -5; tail -2 /tmp/agent_r5_6zwy/r3.log
```

```bash
sleep 900; cd /tmp/agent_r5_6zwy && grep -E '^\| r_work=' r3.log | tail -5; echo "--- last ---"; tail -2 r3.log; ps aux | grep '[p]henix.refine' | wc -l
```

```bash
cd /tmp/agent_r5_6zwy && grep -E 'Final R-work|Start R-work' r3.log; echo "=== step table tail ==="; sed -n '/REFINEMENT STATISTICS STEP BY STEP/,/^ *$/p' r3.log | grep -E '^\s+[0-9]' | tail -14; echo "=== molprobity ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r3_003.pdb output.prefix=mp_r3 > mp_r3.log 2>&1; sed -n '/Summary/,$p' mp_r3.log | head -16
```

```bash
cd /tmp/agent_r5_6zwy && grep -iE 'wxc|wxu|xyz weight|adp weight|optimal' r3.log | tail -30
```

```bash
cd /tmp/agent_r5_6zwy && echo "=== run2 wxc ==="; grep -E '^\| wxc =' r2.log | tail -8; echo "=== run1 wxc ==="; grep -E '^\| wxc =' r1.log | tail -5
```

```bash
cd /tmp/agent_r5_6zwy && sed -n '/REFINEMENT STATISTICS STEP BY STEP/,/^ *$/p' r3.log | grep -E '^\s+[0-9]' | head -30
```

### Dry-run validation of run 4 — **[NOT COUNTED]** — immediately followed by **[REFINE 4/6]** (ADP-weight optimization only, default XYZ weight, 3 macro-cycles)

Both were issued in one shell command; the `--dry-run` completed and exited before the
real run was launched.

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_003.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=3 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.optimize_xyz_weight=False refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=6 output.prefix=r4 output.serial=4 --overwrite --dry-run > dryrun4.log 2>&1; echo "dryrun exit=$?"; nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_003.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=3 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.optimize_xyz_weight=False refinement.target_weights.optimize_adp_weight=True refinement.main.nproc=6 output.prefix=r4 output.serial=4 --overwrite > r4.log 2>&1 &
echo "launched pid $!"; sleep 780; grep -E '^\| r_work=' /tmp/agent_r5_6zwy/r4.log | tail -5; tail -2 /tmp/agent_r5_6zwy/r4.log
```

```bash
sleep 600; cd /tmp/agent_r5_6zwy && grep -E 'Final R-work|Start R-work' r4.log; grep -E '^\| r_work=' r4.log | tail -3; echo "--- step tail ---"; sed -n '/REFINEMENT STATISTICS STEP BY STEP/,/^ *$/p' r4.log | grep -E '^\s+[0-9]' | tail -12; tail -2 r4.log
```

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity r4_004.pdb output.prefix=mp_r4 > mp_r4.log 2>&1; sed -n '/Summary/,$p' mp_r4.log | head -16
```

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r4_004.pdb r4_004.mtz > peaks_r4.log 2>&1; sed -n '/SUMMARY OF MAP PEAKS/,$p' peaks_r4.log
```

```bash
cd /tmp/agent_r5_6zwy && sed -n '/clash/I,/^$/p' mp_r4.out | head -40; echo "=== clash atom types ==="; grep -iE '^ *pdb=' mp_r4.out | head -5; python3 - <<'EOF'
import re
txt=open('/tmp/agent_r5_6zwy/mp_r4.out').read()
m=re.search(r'Bad Clashes[^\n]*\n(.*?)\n\n', txt, re.S)
print(m.group(1)[:3000] if m else 'section not found; dumping headers:')
if not m:
    for line in txt.splitlines():
        if line.strip() and not line.startswith(' '): print(line)
EOF
```

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r4_004.pdb verbose=True keep_hydrogens=True > clash_r4.log 2>&1; grep -E ':' clash_r4.log | grep -iE 'HOH|clash' | head -30; echo "=== how many involve water ==="; grep -c 'HOH' clash_r4.log; grep -c 'pdb=' clash_r4.log
```

```bash
cd /tmp/agent_r5_6zwy && python3 -c "
import gemmi
s=gemmi.read_structure('/tmp/agent_r5_6zwy/r4_004.pdb')
targets={('S',1798),('A',801),('S',1882)}
allw=[]
for ch in s[0]:
  for r in ch:
    if r.name=='HOH':
      for a in r:
        allw.append(a.b_iso)
        if (ch.name,r.seqid.num) in targets:
          print('%s %4d  occ %.2f  B %6.2f'%(ch.name,r.seqid.num,a.occ,a.b_iso))
import numpy as np
allw=np.array(allw)
print('all waters: n=%d  B mean %.1f  median %.1f  90th pct %.1f'%(len(allw),allw.mean(),np.median(allw),np.percentile(allw,90)))
"
```

```bash
cd /tmp/agent_r5_6zwy && awk '/Resolution    Compl Nwork Nfree R_work/{f=1} f{print} f&&/1.046-1.000/{exit}' r4.log | tail -16
```

### Dry-run validation of the run-5 command — **[NOT COUNTED]**

```bash
cd /tmp/agent_r5_6zwy && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_004.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=3 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.optimize_xyz_weight=False refinement.target_weights.optimize_adp_weight=True refinement.main.optimize_mask=True refinement.main.nproc=6 output.prefix=r5 output.serial=5 --overwrite --dry-run > dryrun5.log 2>&1; echo "dryrun exit=$?"; tail -3 dryrun5.log
```

### **[REFINE 5/6]** — bulk-solvent mask optimization + continued refinement, 3 macro-cycles (result REJECTED)

```bash
cd /tmp/agent_r5_6zwy && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_004.pdb /tmp/nc_round1_cache/6zwy.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.main.number_of_macro_cycles=3 refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.optimize_xyz_weight=False refinement.target_weights.optimize_adp_weight=True refinement.main.optimize_mask=True refinement.main.nproc=6 output.prefix=r5 output.serial=5 --overwrite > r5.log 2>&1 &
echo "launched pid $!"; sleep 840; grep -E '^\| r_work=' /tmp/agent_r5_6zwy/r5.log | tail -4; tail -2 /tmp/agent_r5_6zwy/r5.log
```

```bash
sleep 600; cd /tmp/agent_r5_6zwy && grep -E 'Final R-work|Start R-work' r5.log; grep -E '^\| r_work=' r5.log | tail -4; echo "--- step tail ---"; sed -n '/REFINEMENT STATISTICS STEP BY STEP/,/^ *$/p' r5.log | grep -E '^\s+[0-9]' | tail -8; tail -2 r5.log
```

## Phase 3 — independent re-measurement, selection and delivery

```bash
cd /tmp/agent_r5_6zwy && for m in r1_001 r2_002 r3_003 r4_004 r5_005; do printf "%-8s " $m; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $m.pdb /tmp/nc_round1_cache/6zwy.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > mvd_$m.log 2>&1; grep -E '^ *r_work:|^ *r_free:' mvd_$m.log | tr '\n' ' '; echo; done
```

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY && cp /tmp/agent_r5_6zwy/r4_004.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb && ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/ && python3 -c "
import gemmi
s=gemmi.read_structure('/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb')
n=sum(1 for ch in s[0] for r in ch for a in r)
h=sum(1 for ch in s[0] for r in ch for a in r if a.element==gemmi.Element('H'))
w=sum(1 for ch in s[0] for r in ch if r.name=='HOH')
print('total atoms %d  H %d  non-H %d  water residues %d'%(n,h,n-h,w))
print('chains:', [(ch.name,len(ch)) for ch in s[0]])
print('spacegroup', s.spacegroup_hm, 'cell', s.cell)
"
```

```bash
cd /tmp/agent_r5_6zwy && F=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.molprobity $F output.prefix=mp_final > mp_final.log 2>&1; sed -n '/Summary/,$p' mp_final.log | head -16; echo "=== model_vs_data ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $F /tmp/nc_round1_cache/6zwy.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > mvd_final.log 2>&1; grep -E '^ *r_work:|^ *r_free:|outliers' mvd_final.log | head -4
```

```bash
cd /tmp/agent_r5_6zwy && python3 -c "
import gemmi, numpy as np
a=gemmi.read_structure('/tmp/nc_round1_work/r4p_6zwy.pdb'); a.remove_hydrogens()
b=gemmi.read_structure('/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb'); b.remove_hydrogens()
def idx(s):
    d={}
    for ch in s[0]:
        for r in ch:
            for at in r:
                d[(ch.name,r.seqid.num,r.name,at.name,at.altloc)]=at
    return d
A,B=idx(a),idx(b)
common=set(A)&set(B)
prot=[k for k in common if A[k].element!=gemmi.Element('O') or k[2]!='HOH']
pk=[k for k in common if k[2]!='HOH']
d=np.array([A[k].pos.dist(B[k].pos) for k in pk])
print('matched non-water atoms: %d'%len(pk))
print('shift from perturbed input: rms %.3f A  mean %.3f  median %.3f  max %.3f'%(np.sqrt((d**2).mean()),d.mean(),np.median(d),d.max()))
print('frac > 0.5 A: %.3f   frac > 1.0 A: %.3f'%((d>0.5).mean(),(d>1.0).mean()))
db=np.array([B[k].b_iso-A[k].b_iso for k in pk])
print('B change: mean %.2f  rms %.2f'%(db.mean(),np.sqrt((db**2).mean())))
"
```

---

## Refinement-invocation ledger

| # | program | what | outcome |
|---|---|---|---|
| 1 | phenix.refine | xyz + local real-space + aniso ADP + occ, 5 mc, no solvent update | 0.3538/0.3676 → 0.1248/0.1426 |
| 2 | phenix.refine | + ordered-solvent rebuilding, 6 mc | → 0.1217/0.1350, 485 waters |
| 3 | phenix.refine | + optimize xyz **and** ADP weights, 4 mc | → 0.1123/0.1293, geometry loosened |
| 4 | phenix.refine | optimize ADP weight only, default xyz weight, 3 mc | → **0.1133/0.1292**, geometry recovered — **CHOSEN** |
| 5 | phenix.refine | + bulk-solvent mask optimization, 3 mc | → 0.1132/0.1308 — **REJECTED**, discarded |
| 6 | — | not used; marginal gains had vanished | — |

Five of six invocations used. Every `--dry-run` above is annotated **[NOT COUNTED]**:
each validated arguments and exited without the refinement program executing. No other
launch failed.

## Rule-compliance notes

- No network access of any kind was attempted: no `curl`, `wget`, `phenix.fetch_pdb`,
  or any other fetch. Every command above is local.
- Nothing under this repository's `ref/` or `data/` trees was read. The only writes to
  `data/` are the three deliverables in `data/agents/round5/6ZWY/`, which the task
  directed me to create.
- The only file read from `/tmp/nc_round1_cache/` is `6zwy.mtz`. No `*_mask.json`, no
  `*_validation.xml`, no other cache file was opened.
- Beyond the stated rules, I restricted myself to the `FOBS`, `SIGFOBS` and
  `R-free-flags` columns and never used the MTZ's deposited-model-derived columns
  (`FC`, `PHIFC`, `FWT`, `PHWT`, `DELFWT`, `PHDELWT`, `FOM`). All difference maps used
  for peak searches were computed by PHENIX from my own model of the moment
  (`r1_001.mtz`, `r2_002.mtz`, `r4_004.mtz`), as the commands above show.

## Phase 4 — writing the deliverables

`decisions.md` and this `transcript.md` were written with the editor tool, not the
shell. The remaining shell commands, in order, were:

```bash
cp /tmp/agent_r5_6zwy/transcript.md /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/transcript.md && ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/ && echo "=== final.pdb sanity ===" && head -3 /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb && grep -c '^ATOM\|^HETATM' /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb && grep -c '^ANISOU' /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb
```

```bash
cat >> .../transcript.md <<'XEOF'   # (full text: this Phase 4 section)
...
XEOF
ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/; wc -l /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/*.md
```

**This command failed and was killed after a 10-minute timeout (exit 143).** The
heredoc body itself contained a line reading `XEOF`, which closed the heredoc early;
the shell then tried to execute the remainder as commands and blocked on stdin. It
appended a truncated copy of this section and produced no other effect — no refinement
program was involved and no model file was touched. The truncation was then repaired
with the editor tool, which is how this paragraph got here.

```bash
ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/; echo "=== tail of transcript ==="; tail -25 /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/transcript.md
```

```bash
ls -la /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/; wc -c /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/final.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/decisions.md /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/6ZWY/transcript.md
```

That is the complete command history for this task.
