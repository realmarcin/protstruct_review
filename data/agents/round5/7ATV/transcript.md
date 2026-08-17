# 7ATV — verbatim shell transcript, in execution order

Every shell command issued during this task, in the order it was run. Commands
issued in the same turn (run in parallel) are marked. `PB=/Users/marcin/phenix-2.0-5936/phenix_bin`
is written out in full below exactly as it was typed.

Refinement-program invocations are flagged **[REFINE n/6]**. The one command marked
**[REFINE — FAILED PARSE]** exited during PHIL parameter parsing without performing
any refinement.

---

### 1. (parallel) Inputs and data columns

```bash
mkdir -p /tmp/agent_r5_7atv && cd /tmp/agent_r5_7atv && ls -la /tmp/nc_round1_work/r4p_7atv.pdb /tmp/nc_round1_cache/7atv.mtz
```

```bash
/opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/7atv.mtz 2>&1 | head -60
```

### 2. (parallel) Model composition

```bash
cd /tmp/agent_r5_7atv && /opt/homebrew/bin/gemmi contents /tmp/nc_round1_work/r4p_7atv.pdb 2>&1 | head -40
```

```bash
head -30 /tmp/nc_round1_work/r4p_7atv.pdb; echo "---GREP---"; grep -c "^ATOM\|^HETATM" /tmp/nc_round1_work/r4p_7atv.pdb; echo "---HETATM types---"; grep "^HETATM" /tmp/nc_round1_work/r4p_7atv.pdb | cut -c18-20 | sort | uniq -c; echo "---ANISOU?---"; grep -c "^ANISOU" /tmp/nc_round1_work/r4p_7atv.pdb
```

### 3. (parallel) Baseline R factors and geometry

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_7atv.pdb /tmp/nc_round1_cache/7atv.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > baseline_mvd.log 2>&1; tail -60 baseline_mvd.log
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/nc_round1_work/r4p_7atv.pdb > baseline_clash.log 2>&1; tail -5 baseline_clash.log; echo "=== RAMA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/nc_round1_work/r4p_7atv.pdb > baseline_rama.log 2>&1; tail -8 baseline_rama.log; echo "=== ROTA ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/nc_round1_work/r4p_7atv.pdb > baseline_rota.log 2>&1; tail -6 baseline_rota.log
```

### 4. (parallel) Free-flag columns; B-factors and occupancies

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import gemmi
m=gemmi.read_mtz_file('/tmp/nc_round1_cache/7atv.mtz')
import collections
for lbl in ['R-free-flags','R-free-flags-1']:
    c=m.column_with_label(lbl)
    cnt=collections.Counter(int(v) for v in c.array)
    print(lbl, dict(cnt))
"
```

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import gemmi
st=gemmi.read_structure('/tmp/nc_round1_work/r4p_7atv.pdb')
st.setup_entities()
import collections
bs=[];occ=collections.Counter();el=collections.Counter();alt=0;n=0
wat=[]
for mdl in st:
    for ch in mdl:
        for r in ch:
            for a in r:
                n+=1; el[a.element.name]+=1; bs.append(a.b_iso)
                occ[round(a.occ,2)]+=1
                if a.altloc: alt+=1
                if r.name=='HOH': wat.append(a.b_iso)
print('atoms',n,'altloc atoms',alt)
print('elements',dict(el))
print('occ',dict(occ))
import statistics
nonh=[b for b in bs]
print('B all: min %.2f max %.2f mean %.2f'%(min(bs),max(bs),statistics.mean(bs)))
print('B water: n=%d min %.2f max %.2f mean %.2f'%(len(wat),min(wat),max(wat),statistics.mean(wat)))
"
```

### 5. Free-set overlap, altloc counts, ANISOU coverage, RXE atoms

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import gemmi, collections
m=gemmi.read_mtz_file('/tmp/nc_round1_cache/7atv.mtz')
a=m.column_with_label('R-free-flags').array
b=m.column_with_label('R-free-flags-1').array
fobs=m.column_with_label('FOBS').array
import numpy as np
a=np.array(a);b=np.array(b);fobs=np.array(fobs)
obs=~np.isnan(fobs)
print('total',len(a),'with FOBS',obs.sum())
setA = (a==0); setB=(b==1)
print('A free(0) all/obs:',setA.sum(), (setA&obs).sum())
print('B free(1) all/obs:',setB.sum(), (setB&obs).sum())
print('overlap all:',(setA&setB).sum())
"
echo "=== altloc/aniso ==="
python3 -c "
import gemmi, collections
st=gemmi.read_structure('/tmp/nc_round1_work/r4p_7atv.pdb')
alt=collections.Counter()
for ch in st[0]:
    for r in ch:
        for at in r:
            alt[at.altloc if at.altloc.strip() else '.']+=1
print('altloc counts',dict(alt))
"
echo "=== which atoms have ANISOU ==="
grep "^ANISOU" /tmp/nc_round1_work/r4p_7atv.pdb | cut -c77-78 | sort | uniq -c
echo "=== RXE atoms ==="
grep "RXE" /tmp/nc_round1_work/r4p_7atv.pdb | grep "^HETATM" | head -20
```

### 6. (parallel) Ligand restraint availability; starting-model geometry

```bash
ls /Users/marcin/phenix-2.0-5936/modules/chem_data/geostd/r/ 2>/dev/null | grep -i "rxe\|edo" ; echo "---"; ls /Users/marcin/phenix-2.0-5936/modules/chem_data/geostd/e/ 2>/dev/null | grep -i edo; echo "--- mon_lib ---"; ls /Users/marcin/phenix-2.0-5936/modules/chem_data/mon_lib/r/ 2>/dev/null | grep -i rxe
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
pdb_inp=iotbx.pdb.input('/tmp/nc_round1_work/r4p_7atv.pdb')
m=mmtbx.model.manager(model_input=pdb_inp)
m.process(make_restraints=True)
gs=m.geometry_statistics()
gs.show()
" 2>&1 | tail -40
```

### 7. (parallel) Locate RXE restraints; check for unknown-residue warnings

```bash
find /Users/marcin/phenix-2.0-5936/modules/chem_data -iname "*rxe*" 2>/dev/null | head; echo "--- geostd dirs ---"; ls /Users/marcin/phenix-2.0-5936/modules/chem_data/ ; echo "--- any CCD/components ---"; ls /Users/marcin/phenix-2.0-5936/modules/chem_data/geostd/ | head
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb, sys
pdb_inp=iotbx.pdb.input('/tmp/nc_round1_work/r4p_7atv.pdb')
m=mmtbx.model.manager(model_input=pdb_inp)
m.process(make_restraints=True)
print('OK restraints built')
" 2>&1 | grep -iE "rxe|unknown|not found|missing|GRAND|link|warn" | head -30
```

### 8. Find the real chem_data location

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import libtbx.load_env, os
p=libtbx.load_env.find_in_repositories('chem_data')
print('chem_data:',p)
" 2>&1; echo "---"; find /Users/marcin/phenix-2.0-5936 -maxdepth 4 -type d -name geostd 2>/dev/null | head
```

```bash
find /Users/marcin/phenix-2.0-5936 -maxdepth 6 -type d \( -name geostd -o -name mon_lib \) 2>/dev/null | head; echo "=== env ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import os
for k in os.environ:
    if 'MON' in k.upper() or 'CHEM' in k.upper() or 'CLIBD' in k.upper(): print(k,os.environ[k])
"; echo "=== search rxe anywhere ==="; find /Users/marcin/phenix-2.0-5936 -iname "rxe.cif" 2>/dev/null | head
```

```bash
ls /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/chem_data/geostd/r/ | grep -i rxe; echo "rc=$?"; ls /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/chem_data/mon_lib/r/ | grep -i rxe; echo "rc=$?"; echo "--- EDO ---"; ls /Users/marcin/phenix-2.0-5936/lib/python3.9/site-packages/chem_data/geostd/e/ | grep -i "^data_comp_EDO\|edo"
```

### 9. **[REFINE — FAILED PARSE]** first phenix.refine attempt

Rejected for an unrecognized PHIL path (`refinement.input.xray_data.r_free_flags.test_flag_value`);
exited during parameter parsing, no refinement performed.

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/nc_round1_work/r4p_7atv.pdb /tmp/nc_round1_cache/7atv.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags refinement.input.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_adp+occupancies refinement.refine.adp.individual.anisotropic="not element H" refinement.main.number_of_macro_cycles=6 refinement.main.nproc=8 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1; echo "EXIT=$?"; grep -E "Start R-work|Final R-work|^  r_work|^  r_free" r1.log | head; echo "=== tail ==="; tail -35 r1.log
```

### 10. Discover correct PHIL paths

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | grep -n "test_flag_value\|r_free_flags" | head -20
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | sed -n '25,50p'
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | sed -n '1,25p'
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | grep -n "^  refine\b\|^refinement\|strategy =\|anisotropic =\|number_of_macro_cycles\|nproc =\|ordered_solvent =\|optimize_xyz_weight\|optimize_adp_weight" | head -25
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | sed -n '150,235p' | grep -n "^  [a-z_]* {\|^    [a-z_]* {\|strategy =\|anisotropic\|ordered_solvent\|number_of_macro_cycles\|nproc"
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | sed -n '156,176p'; echo "=== weights ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | sed -n '1015,1030p'
```

```bash
sysctl -n hw.ncpu; sysctl -n hw.memsize | awk '{print $1/1073741824" GB"}'
```

### 11. **[REFINE 1/6]** coordinate + aniso ADP + occupancy recovery

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/nc_round1_work/r4p_7atv.pdb /tmp/nc_round1_cache/7atv.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.main.number_of_macro_cycles=6 refinement.main.nproc=8 output.prefix=r1 output.serial=1 output.overwrite=True > r1.log 2>&1; echo "EXIT=$?"; ls -la r1_001*; echo "=== R factors ==="; grep -E "r_work|r_free" r1.log | tail -20
```

### 12. Run-1 assessment

```bash
cd /tmp/agent_r5_7atv && grep -A25 "Final:" r1.log | head -40; echo "=== GEOM SUMMARY ==="; grep -E "bond|angle|chirality|planarity|dihedral|clashscore|Ramachandran|rotamer|outliers|favored" r1_001.log | tail -30
```

```bash
cd /tmp/agent_r5_7atv && sed -n '/stage r-work r-free bonds angles/,/^$/p' r1_001.log | head -20; echo "=== MOLPROBITY BLOCK ==="; awk '/MolProbity|Molprobity|=== Summary/,0' r1_001.log | head -50
```

(parallel)

```bash
cd /tmp/agent_r5_7atv && tail -25 <(sed -n '/stage r-work r-free bonds angles/,/^ *$/p' r1_001.log)
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r1_001.pdb'))
m.process(make_restraints=True)
m.geometry_statistics().show()
" 2>&1 | grep -A30 "GEOMETRY RESTRAINTS\|BOND\|MOLPROBITY" | head -45
```

### 13. (parallel) Map coefficients; peak-finding tools

```bash
cd /tmp/agent_r5_7atv && /opt/homebrew/bin/gemmi mtz --dump r1_001.mtz 2>&1 | grep -A20 "Column  " | head -25
```

```bash
cd /tmp/agent_r5_7atv && ls /Users/marcin/phenix-2.0-5936/phenix_bin/ | grep -iE "peak|hole|water|douse|polder"
```

### 14. Residual density after run 1

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.find_peaks_holes r1_001.pdb r1_001.mtz map_type=mFo-DFc peak_search.min_cross_distance=1.8 > peaks_r1.log 2>&1; echo EXIT=$?; grep -iE "^Found|peaks|holes|sigma" peaks_r1.log | head -30; echo "=== tail ==="; tail -30 peaks_r1.log
```

```bash
cd /tmp/agent_r5_7atv && grep "^peak=" peaks_r1.log | grep -v -- "peak=  *-" | sort -k1 -t= -rn | head -0; echo "=== top positive peaks ==="; awk '/Positive difference map peaks/,/Negative difference map holes/' peaks_r1.log | grep "^peak=" | head -35
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults 2>/dev/null | awk '/^  ordered_solvent \{/,/^  \}/' | head -45
```

### 15. **[REFINE 2/6]** ordered-solvent rebuilding

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/7atv.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.main.number_of_macro_cycles=6 refinement.main.nproc=8 output.prefix=r2 output.serial=1 output.overwrite=True > r2.log 2>&1; echo "EXIT=$?"; sed -n '/stage r-work r-free bonds angles/,/^ *-----/p' r2_001.log | tail -20
```

### 16. (parallel) Run-2 verification

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r2_001.pdb /tmp/nc_round1_cache/7atv.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free|Number of F-obs"
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r2_001.pdb'))
m.process(make_restraints=True)
m.geometry_statistics().show()
" 2>&1 | grep -E "BOND|ANGLE|CHIRAL|PLANAR|CLASHSCORE|OUTLIERS|FAVORED|ALLOWED|WHOLE:|MIN NONBONDED" | head -20
```

### 17. Clash diagnosis

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r2_001.pdb verbose=True > clash_r2.log 2>&1; grep -E "^ " clash_r2.log | head -40; echo "=== count by type ==="; grep -E ":[0-9]\.[0-9]+$" clash_r2.log | awk '{print ($3=="HOH"?"HOH":"prot"), ($6=="HOH"?"HOH":"prot")}' | sort | uniq -c
```

Water audit, first attempt (failed — cctbx pair_asu_table needs sites):

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import iotbx.pdb, scitbx.matrix
from cctbx import crystal
import numpy as np
pdb=iotbx.pdb.input('r2_001.pdb')
h=pdb.construct_hierarchy()
xrs=pdb.xray_structure_simple()
sites=xrs.sites_cart()
atoms=list(h.atoms())
# classify
isw=[]; elem=[]
for i,a in enumerate(atoms):
    r=a.parent(); rg=r.parent()
    isw.append(r.resname.strip()=='HOH')
    elem.append(a.element.strip())
isw=np.array(isw); elem=np.array(elem)
S=np.array(sites)
# only P1, but need symmetry; use crystal symmetry pair generator
from cctbx import xray
cs=xrs.crystal_symmetry()
asu=crystal.symmetry(unit_cell=cs.unit_cell(), space_group=cs.space_group())
pair_asu=asu.special_position_settings().pair_asu_table(distance_cutoff=3.6)
pat=pair_asu.extract_pair_sym_table()
import collections
minC=collections.defaultdict(lambda:99.); minAny=collections.defaultdict(lambda:99.); polar=collections.defaultdict(int)
uc=cs.unit_cell()
for i,rec in enumerate(pat):
    for j,ops in rec.items():
        for op in ops:
            d=uc.distance(scitbx.matrix.col(xrs.scatterers()[i].site), scitbx.matrix.col(op*xrs.scatterers()[j].site))
            for (a,b) in ((i,j),(j,i)):
                if not isw[a]: continue
                if elem[a]!='O': continue
                eb=elem[b]
                if eb=='H': continue
                if isw[b] and isw[a] and a==b: continue
                minAny[a]=min(minAny[a],d)
                if eb=='C': minC[a]=min(minC[a],d)
                if eb in ('N','O','S','CL','BR') and 2.2<=d<=3.5: polar[a]+=1
wo=[i for i in range(len(atoms)) if isw[i] and elem[i]=='O']
print('n water O',len(wo))
bad_c=[i for i in wo if minC[i]<3.0]
bad_close=[i for i in wo if minAny[i]<2.4]
no_polar=[i for i in wo if polar[i]==0]
print('waters within 3.0A of C:',len(bad_c))
print('waters within 2.4A of any non-H:',len(bad_close))
print('waters with NO polar partner 2.2-3.5A:',len(no_polar))
print('union bad:',len(set(bad_c)|set(bad_close)|set(no_polar)))
" 2>&1 | tail -12
```

Second attempt (failed — wrong gemmi NeighborSearch signature):

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import gemmi, collections
st=gemmi.read_structure('r2_001.pdb')
st.setup_entities()
ns=gemmi.NeighborSearch(st[0], st, 4.0).populate()
model=st[0]
waters=[]
for ci,ch in enumerate(model):
    for ri,r in enumerate(ch):
        if r.name!='HOH': continue
        for ai,a in enumerate(r):
            if a.element.name!='O': continue
            waters.append((ch.name,r.seqid.num,ci,ri,ai,a))
print('water O count',len(waters))
minC={};minAny={};polar={}
for key in waters:
    chn,num,ci,ri,ai,a=key
    marks=ns.find_atoms(a.pos, '\\0', radius=3.6)
    mc=99.;ma=99.;np_=0
    for m in marks:
        cra=m.to_cra(model)
        if cra.residue.name=='HOH' and cra.residue.seqid.num==num and cra.chain.name==chn: continue
        e=cra.atom.element.name
        if e=='H': continue
        d=a.pos.dist(cra.atom.pos)
        if d<0.1: continue
        ma=min(ma,d)
        if e=='C': mc=min(mc,d)
        if e in ('N','O','S','Cl','Br') and 2.2<=d<=3.5: np_+=1
    minC[(chn,num)]=mc; minAny[(chn,num)]=ma; polar[(chn,num)]=np_
badC=[k for k in minC if minC[k]<3.0]
badclose=[k for k in minAny if minAny[k]<2.4]
nopolar=[k for k in polar if polar[k]==0]
print('within 3.0A of C:',len(badC))
print('within 2.4A of any non-H:',len(badclose))
print('no polar partner 2.2-3.5A:',len(nopolar))
u=set(badC)|set(badclose)|set(nopolar)
print('union:',len(u))
print('sample badC:',sorted(badC)[:15])
print('sample nopolar:',sorted(nopolar)[:15])
"
```

Third attempt (worked; result later discarded because it ignores altloc compatibility):

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import gemmi
st=gemmi.read_structure('r2_001.pdb')
st.setup_entities()
ns=gemmi.NeighborSearch(st, 4.0).populate()
model=st[0]
waters=[]
for ch in model:
    for r in ch:
        if r.name!='HOH': continue
        for a in r:
            if a.element.name!='O': continue
            waters.append((ch.name,r.seqid.num,a))
print('water O count',len(waters))
minC={};minAny={};polar={}
for chn,num,a in waters:
    marks=ns.find_atoms(a.pos, '\0', radius=3.6)
    mc=99.;ma=99.;np_=0
    for m in marks:
        cra=m.to_cra(model)
        if cra.residue.name=='HOH' and cra.residue.seqid.num==num and cra.chain.name==chn: continue
        e=cra.atom.element.name
        if e=='H': continue
        d=a.pos.dist(cra.atom.pos)
        if d<0.1: continue
        ma=min(ma,d)
        if e=='C': mc=min(mc,d)
        if e in ('N','O','S','Cl','Br') and 2.2<=d<=3.5: np_+=1
    minC[(chn,num)]=mc; minAny[(chn,num)]=ma; polar[(chn,num)]=np_
badC=[k for k in minC if minC[k]<3.0]
badclose=[k for k in minAny if minAny[k]<2.4]
nopolar=[k for k in polar if polar[k]==0]
print('within 3.0A of C:',len(badC))
print('within 2.4A of any non-H:',len(badclose))
print('no polar partner 2.2-3.5A:',len(nopolar))
u=set(badC)|set(badclose)|set(nopolar)
print('union:',len(u))
print('badC:',sorted(badC)[:20])
print('nopolar:',sorted(nopolar)[:20])
"
```

### 18. Run-1 clash list for comparison

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r1_001.pdb verbose=True > clash_r1.log 2>&1; echo "=== run1 clashes involving HOH (overlap>=0.4) ==="; grep -E ":0\.[4-9][0-9]*$|:[1-9]\.[0-9]*$" clash_r1.log | grep HOH; echo "=== run1 total listed clashes ==="; grep -cE ":[0-9]\.[0-9]+$" clash_r1.log; grep "clashscore" clash_r1.log
```

### 19. Identify and remove clashing waters (no data used, no budget used)

```bash
cd /tmp/agent_r5_7atv && grep -E ":[0-9]\.[0-9]+$" clash_r2.log | grep HOH | awk -F: '$2+0>=0.35' | sed 's/:.*//' | grep -oE "[AS] *[0-9]+ +HOH" | awk '{print $1"_"$2}' | sort -u | tee bad_waters.txt; echo "count: $(wc -l < bad_waters.txt)"
```

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import re
bad=set()
for line in open('clash_r2.log'):
    m=re.match(r'^\s*(.*?):([0-9.]+)\s*\$', line.rstrip())
    if not m: continue
    spec, ov = m.group(1), float(m.group(2))
    if ov < 0.35: continue
    for cm in re.finditer(r'([A-Za-z])\s*(\d+)\s+HOH\s', spec):
        bad.add((cm.group(1), int(cm.group(2))))
print('clashing waters (overlap>=0.35):', sorted(bad))
badS={k for k in bad if k[0]=='S'}
print('chain-S (added in run2):', len(badS), sorted(badS))
open('bad_waters.txt','w').write('\n'.join('%s %d'%k for k in sorted(badS)))
"
```

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import gemmi
bad={tuple(l.split()) for l in open('bad_waters.txt') if l.strip()}
bad={(c,int(n)) for c,n in bad}
st=gemmi.read_structure('r2_001.pdb')
st.setup_entities()
n0=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
for ch in st[0]:
    todel=[i for i,r in enumerate(ch) if r.name=='HOH' and (ch.name,r.seqid.num) in bad]
    for i in reversed(todel): del ch[i]
n1=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
print('waters %d -> %d (removed %d)'%(n0,n1,n0-n1))
st.setup_entities()
st.write_pdb('r2_clean.pdb')
"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r2_clean.pdb 2>&1 | grep clashscore
```

### 20. **[REFINE 3/6]** weight optimization (launched in background)

```bash
cd /tmp/agent_r5_7atv && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r2_clean.pdb /tmp/nc_round1_cache/7atv.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.ordered_solvent.primary_map_cutoff=3.5 refinement.ordered_solvent.secondary_map_and_map_cc_filter.poor_cc_threshold=0.80 refinement.ordered_solvent.dist_min=2.0 refinement.target_weights.optimize_xyz_weight=True refinement.target_weights.optimize_adp_weight=True refinement.main.number_of_macro_cycles=5 refinement.main.nproc=8 output.prefix=r3 output.serial=1 output.overwrite=True > r3.log 2>&1 &
echo "launched pid $!"
```

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7ATV && echo created; cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r2_clean.pdb verbose=True 2>&1 | grep -E ":[0-9]\.[0-9]+$"
```

```bash
cd /tmp/agent_r5_7atv && tail -3 r3.log; echo "=== stage table tail ==="; sed -n '/stage r-work r-free bonds angles/,/^ *-----/p' r3_001.log | tail -14
```

```bash
cd /tmp/agent_r5_7atv && wc -l r3.log; ls -la r3_001* 2>/dev/null; echo "=== errors ==="; grep -iE "sorry|error|traceback|abort" r3.log | head -20; echo "=== last 40 ==="; tail -40 r3.log
```

```bash
ps aux | grep -i "phenix.refine\|phenix_python\|libtbx" | grep -v grep | head -10; echo "=== log growth ==="; wc -l /tmp/agent_r5_7atv/r3.log; sleep 20; wc -l /tmp/agent_r5_7atv/r3.log
```

```bash
sleep 900; cd /tmp/agent_r5_7atv && ls -la r3_001.pdb 2>/dev/null; grep -c "MACRO_CYCLE" r3.log; sed -n '/stage r-work r-free bonds angles/,/^ *-----/p' r3_001.log 2>/dev/null | tail -8
```

```bash
sleep 900; cd /tmp/agent_r5_7atv && ls -la r3_001.pdb 2>/dev/null && echo "DONE" || echo "still running"; grep -c "MACRO_CYCLE" r3.log; tail -5 r3.log
```

### 21. (parallel) Run-3 assessment

```bash
cd /tmp/agent_r5_7atv && sed -n '/stage r-work r-free bonds angles/,/^ *-----/p' r3_001.log | tail -16
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r3_001.pdb 2>&1 | grep clashscore
```

### 22. (parallel) What weight did the optimizer pick, and what is clashing

```bash
cd /tmp/agent_r5_7atv && echo "=== wxc used, run2 vs run3 ==="; grep -hE "wxc *=|xyz weight|wxc_scale|Automatic weight|optimal" r2_001.log | tail -8; echo "--- r3 ---"; grep -hE "wxc *=|xyz weight|wxc_scale|Automatic weight|optimal" r3_001.log | tail -12
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r3_001.pdb verbose=True 2>&1 | grep -E ":[0-9]\.[0-9]+$" | head -30; echo "=== water vs protein split ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r3_001.pdb verbose=True 2>&1 | grep -cE ":[0-9]\.[0-9]+$"
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r3_001.pdb verbose=True > clash_r3.log 2>&1; python3 -c "
import re, gemmi
bad=set()
for line in open('clash_r3.log'):
    m=re.match(r'^\s*(.*?):([0-9.]+)\s*\$', line.rstrip())
    if not m: continue
    if float(m.group(2))<0.35: continue
    for cm in re.finditer(r'([A-Za-z])\s*(\d+)\s+HOH\s', m.group(1)):
        bad.add((cm.group(1), int(cm.group(2))))
print('clashing waters:',len(bad))
st=gemmi.read_structure('r3_001.pdb'); st.setup_entities()
n0=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
for ch in st[0]:
    d=[i for i,r in enumerate(ch) if r.name=='HOH' and (ch.name,r.seqid.num) in bad]
    for i in reversed(d): del ch[i]
n1=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
print('waters %d -> %d'%(n0,n1))
st.setup_entities(); st.write_pdb('r3_clean.pdb')
"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r3_clean.pdb 2>&1 | grep clashscore
```

### 23. (parallel) Cleaned run-3 model measurement

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r3_clean.pdb /tmp/nc_round1_cache/7atv.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work|^  r_free"
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r3_clean.pdb'))
m.process(make_restraints=True)
m.geometry_statistics().show()
" 2>&1 | grep -E "BOND|ANGLE|CHIRAL|PLANAR|CLASHSCORE|OUTLIERS|FAVORED|ALLOWED|WHOLE:|MIN NONBONDED"
```

### 24. **[REFINE 4/6]** restore geometry at the automatic weight

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r3_clean.pdb /tmp/nc_round1_cache/7atv.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.main.number_of_macro_cycles=8 refinement.main.nproc=4 output.prefix=r4 output.serial=1 output.overwrite=True > r4.log 2>&1; echo "EXIT=$?"; sed -n '/stage r-work r-free bonds angles/,/^ *-----/p' r4_001.log | tail -8
```

### 25. (parallel) Locate run-3 outliers; run-4 clashes

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r3_clean.pdb'))
m.process(make_restraints=True)
gs=m.geometry_statistics().result()
print('bond max', gs.bond.max, 'angle max', gs.angle.max, 'chir max', gs.chirality.max)
" 2>&1 | tail -3; echo "=== worst restraint deviations from .geo (run3) ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import re,sys
# parse bond section of r3_001.geo for largest deltas
cur=None; worst=[]
lines=open('r3_001.geo').read().split('\n')
i=0
while i < len(lines):
    l=lines[i]
    if l.startswith('bond '):
        a=l[5:].strip(); b=lines[i+1].strip()
        for j in range(i+2, min(i+8,len(lines))):
            if 'ideal' in lines[j]:
                vals=lines[j+1].split()
                try: delta=float(vals[2])
                except: delta=0
                worst.append((abs(delta), a, b, lines[j+1].strip()))
                break
        i+=4
    else: i+=1
worst.sort(reverse=True)
for w in worst[:12]: print('%.3f'%w[0], w[1], '|', w[2])
" 2>&1 | tail -14
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r4_001.pdb verbose=True > clash_r4.log 2>&1; grep clashscore clash_r4.log; grep -cE ":[0-9]\.[0-9]+$" clash_r4.log
```

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import re, gemmi
bad=set()
for line in open('clash_r4.log'):
    m=re.match(r'^\s*(.*?):([0-9.]+)\s*\$', line.rstrip())
    if not m: continue
    if float(m.group(2))<0.35: continue
    for cm in re.finditer(r'([A-Za-z])\s*(\d+)\s+HOH\s', m.group(1)):
        bad.add((cm.group(1), int(cm.group(2))))
st=gemmi.read_structure('r4_001.pdb'); st.setup_entities()
n0=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
for ch in st[0]:
    d=[i for i,r in enumerate(ch) if r.name=='HOH' and (ch.name,r.seqid.num) in bad]
    for i in reversed(d): del ch[i]
n1=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
print('clashing waters removed: %d  (waters %d -> %d)'%(len(bad),n0,n1))
st.setup_entities(); st.write_pdb('r4_clean.pdb')
"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r4_clean.pdb 2>&1 | grep clashscore
```

### 26. **[REFINE 5/6]** bounded weight relaxation (wxc_scale = 1.0)

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_clean.pdb /tmp/nc_round1_cache/7atv.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.main.ordered_solvent=True refinement.ordered_solvent.mode=every_macro_cycle_after_first refinement.target_weights.wxc_scale=1.0 refinement.main.number_of_macro_cycles=6 refinement.main.nproc=4 output.prefix=r5 output.serial=1 output.overwrite=True > r5.log 2>&1; echo "EXIT=$?"; sed -n '/stage r-work r-free bonds angles/,/^ *-----/p' r5_001.log | tail -6
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r5_001.pdb verbose=True > clash_r5.log 2>&1; python3 -c "
import re, gemmi
bad=set()
for line in open('clash_r5.log'):
    m=re.match(r'^\s*(.*?):([0-9.]+)\s*\$', line.rstrip())
    if not m: continue
    if float(m.group(2))<0.35: continue
    for cm in re.finditer(r'([A-Za-z])\s*(\d+)\s+HOH\s', m.group(1)):
        bad.add((cm.group(1), int(cm.group(2))))
st=gemmi.read_structure('r5_001.pdb'); st.setup_entities()
n0=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
for ch in st[0]:
    d=[i for i,r in enumerate(ch) if r.name=='HOH' and (ch.name,r.seqid.num) in bad]
    for i in reversed(d): del ch[i]
n1=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
print('r5 clashing waters removed: %d (waters %d -> %d)'%(len(bad),n0,n1))
st.setup_entities(); st.write_pdb('r5_clean.pdb')
"; grep clashscore clash_r5.log; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore r5_clean.pdb 2>&1 | grep clashscore
```

### 27. Consistent comparison of all candidates

```bash
cd /tmp/agent_r5_7atv && for m in r2_clean r3_clean r4_clean r5_clean; do echo -n "$m: "; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $m.pdb /tmp/nc_round1_cache/7atv.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work:|^  r_free:" | tr '\n' ' '; echo; done
```

### 28. Where exactly did run 3 break the chemistry

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import re
lines=open('r3_001.geo').read().split('\n')
worst=[]; i=0; n=len(lines)
while i<n:
    if lines[i].startswith('bond '):
        a=lines[i][5:].strip(); b=lines[i+1].strip(); j=i+2
        if j<n and 'ideal' in lines[j] and j+1<n:
            v=lines[j+1].split()
            if len(v)>=3:
                try: worst.append((abs(float(v[2])), a, b, lines[j+1].strip()))
                except: pass
        i=j+2
    else: i+=1
print('parsed bonds:',len(worst))
worst.sort(reverse=True)
for w in worst[:10]: print('delta %.3f  %s | %s' % (w[0], w[1], w[2]))
"
```

(The `.geo` turned out to be the pre-refinement dump, so the deltas were read
directly from the model instead — first attempt failed on tuple arithmetic:)

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r3_clean.pdb'))
m.process(make_restraints=True)
grm=m.get_restraints_manager().geometry
sites=m.get_sites_cart()
atoms=m.get_hierarchy().atoms()
labs=[a.id_str() for a in atoms]
sorted_p=grm.pair_proxies(sites_cart=sites)
out=[]
for p in sorted_p.bond_proxies.simple:
    i,j=p.i_seqs
    d=(sites[i]-sites[j]).length()
    out.append((abs(d-p.distance_ideal), d, p.distance_ideal, labs[i], labs[j]))
out.sort(reverse=True)
print('n bonds', len(out))
for o in out[:12]:
    print('delta %.3f  model %.3f ideal %.3f   %s | %s'%(o[0],o[1],o[2],o[3],o[4]))
" 2>&1 | tail -15
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb, math
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r3_clean.pdb'))
m.process(make_restraints=True)
grm=m.get_restraints_manager().geometry
sites=m.get_sites_cart()
labs=[a.id_str() for a in m.get_hierarchy().atoms()]
pp=grm.pair_proxies(sites_cart=sites)
out=[]
for p in pp.bond_proxies.simple:
    i,j=p.i_seqs
    a=sites[i]; b=sites[j]
    d=math.sqrt(sum((a[k]-b[k])**2 for k in range(3)))
    out.append((abs(d-p.distance_ideal), d, p.distance_ideal, labs[i], labs[j]))
out.sort(reverse=True)
print('n bonds', len(out))
for o in out[:12]:
    print('delta %.3f  model %.3f ideal %.3f   %s | %s'%(o[0],o[1],o[2],o[3],o[4]))
" 2>&1 | tail -15
```

### 29. Ligand and water density support

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation r4_001.pdb r4_001.mtz detail=residue > rscc_r4.log 2>&1; echo EXIT=$?; grep -E "EDO|RXE| CL " rscc_r4.log | head; echo "=== worst protein residues by CC ==="; awk 'NF>=6 && $NF ~ /^[0-9.]+$/' rscc_r4.log | sort -k6 -n 2>/dev/null | head -12
```

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import re
rows=[]
for l in open('rscc_r4.log'):
    p=l.split()
    if len(p)==8 and p[1]=='HOH':
        try: rows.append((p[0], int(p[2]), float(p[3]), float(p[4]), float(p[5])))
        except: pass
print('waters scored:',len(rows))
for thr in (0.5,0.6,0.7,0.8):
    print('  CC < %.1f : %d'%(thr, sum(1 for r in rows if r[4]<thr)))
import statistics
print('median CC %.3f'%statistics.median(r[4] for r in rows))
print('waters with occ<0.5: %d'%sum(1 for r in rows if r[2]<0.5))
"
```

```bash
cd /tmp/agent_r5_7atv && python3 -c "
import gemmi
rows={}
for l in open('rscc_r4.log'):
    p=l.split()
    if len(p)==8 and p[1]=='HOH':
        try: rows[(p[0],int(p[2]))]=float(p[5])
        except: pass
for thr in (0.5,0.6,0.7):
    st=gemmi.read_structure('r4_clean.pdb'); st.setup_entities()
    n0=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
    for ch in st[0]:
        d=[i for i,r in enumerate(ch) if r.name=='HOH' and rows.get((ch.name,r.seqid.num),1.0)<thr]
        for i in reversed(d): del ch[i]
    n1=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
    st.setup_entities(); st.write_pdb('r4_cc%d.pdb'%int(thr*100))
    print('thr %.1f: waters %d -> %d'%(thr,n0,n1))
"
for f in r4_cc50 r4_cc60 r4_cc70; do echo -n "$f: "; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/agent_r5_7atv/$f.pdb /tmp/nc_round1_cache/7atv.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work:|^  r_free:" | tr '\n' ' '; echo; done
```

### 30. **[REFINE 6/6]** final settle, solvent update off

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r4_cc60.pdb /tmp/nc_round1_cache/7atv.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refinement.refine.strategy=individual_sites+individual_sites_real_space+individual_adp+occupancies refinement.refine.adp.individual.anisotropic="not element H" refinement.refine.adp.individual.isotropic="element H" refinement.main.ordered_solvent=False refinement.main.number_of_macro_cycles=6 refinement.main.nproc=4 output.prefix=r6 output.serial=1 output.overwrite=True > r6.log 2>&1; echo "EXIT=$?"; sed -n '/stage r-work r-free bonds angles/,/^ *-----/p' r6_001.log | tail -6
```

### 31. Final candidate selection

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.real_space_correlation r6_001.pdb r6_001.mtz detail=residue > rscc_r6.log 2>&1; python3 -c "
import gemmi
rows={}
for l in open('rscc_r6.log'):
    p=l.split()
    if len(p)==8 and p[1]=='HOH':
        try: rows[(p[0],int(p[2]))]=float(p[5])
        except: pass
st=gemmi.read_structure('r6_001.pdb'); st.setup_entities()
n0=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
for ch in st[0]:
    d=[i for i,r in enumerate(ch) if r.name=='HOH' and rows.get((ch.name,r.seqid.num),1.0)<0.6]
    for i in reversed(d): del ch[i]
n1=sum(1 for ch in st[0] for r in ch if r.name=='HOH')
st.setup_entities(); st.write_pdb('r6_cc60.pdb')
print('r6 waters %d -> %d (CC<0.6 removed)'%(n0,n1))
"
```

```bash
cd /tmp/agent_r5_7atv && for f in r6_001 r6_cc60 r4_cc60; do echo -n "$f R: "; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $f.pdb /tmp/nc_round1_cache/7atv.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags 2>&1 | grep -E "^  r_work:|^  r_free:" | tr '\n' ' '; echo -n " | "; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore $f.pdb 2>&1 | grep clashscore; done
```

### 32. (parallel) Final model validation

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r6_001.pdb'))
m.process(make_restraints=True)
m.geometry_statistics().show()
" 2>&1 | grep -E "BOND|ANGLE|CHIRAL|PLANAR|DIHEDRAL|CLASHSCORE|OUTLIERS|ALLOWED|FAVORED|WHOLE:|CBETA|MIN NONBONDED|CIS-|TWISTED"
```

```bash
cd /tmp/agent_r5_7atv && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb, math
m=mmtbx.model.manager(model_input=iotbx.pdb.input('r6_001.pdb'))
m.process(make_restraints=True)
grm=m.get_restraints_manager().geometry
sites=m.get_sites_cart(); labs=[a.id_str() for a in m.get_hierarchy().atoms()]
pp=grm.pair_proxies(sites_cart=sites); out=[]
for p in pp.bond_proxies.simple:
    i,j=p.i_seqs; a=sites[i]; b=sites[j]
    d=math.sqrt(sum((a[k]-b[k])**2 for k in range(3)))
    out.append((abs(d-p.distance_ideal), d, p.distance_ideal, labs[i], labs[j]))
out.sort(reverse=True)
for o in out[:6]: print('delta %.3f model %.3f ideal %.3f  %s | %s'%o[:5])
" 2>&1 | tail -7
```

### 33. Stage deliverable

```bash
D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/7ATV; cp /tmp/agent_r5_7atv/r6_001.pdb $D/final.pdb && ls -la $D/final.pdb; echo "=== sanity ==="; /opt/homebrew/bin/gemmi contents $D/final.pdb 2>&1 | grep -vi warning | head -8; grep -c "^ATOM\|^HETATM" $D/final.pdb; grep -c "^ANISOU" $D/final.pdb; grep "^HETATM" $D/final.pdb | cut -c18-20 | sort | uniq -c
```
