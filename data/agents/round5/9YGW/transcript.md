# 9YGW — verbatim shell transcript

Every shell command issued for this task, in execution order. Commands are given
exactly as typed. Long PHENIX/gemmi output is not reproduced here (it lives in
`/tmp/agent_r5_9ygw/*.log`); this file is the command record.

Working scratch directory: `/tmp/agent_r5_9ygw/`

Refinement-invocation accounting is annotated inline as `[REFINEMENT n/6]` for
launches that actually performed refinement, and `[FAILED LAUNCH — NOT COUNTED]`
for launches that aborted during file/PHIL processing before any refinement began.

---

## 1. Setup and input inspection

```bash
mkdir -p /tmp/agent_r5_9ygw && cd /tmp/agent_r5_9ygw && ls -la /tmp/nc_round1_work/r4p_9ygw.pdb /tmp/nc_round1_cache/9ygw.mtz
```

```bash
/opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/9ygw.mtz 2>&1 | head -60
```

```bash
cd /tmp/agent_r5_9ygw && f=/tmp/nc_round1_work/r4p_9ygw.pdb && echo "=== altloc counts ===" && grep -E '^(ATOM|HETATM)' $f | cut -c17 | sort | uniq -c && echo "=== chains ===" && grep -E '^(ATOM|HETATM)' $f | cut -c22 | sort | uniq -c && echo "=== element H? ===" && grep -E '^(ATOM|HETATM)' $f | cut -c77-78 | sort | uniq -c && echo "=== occupancy distribution ===" && grep -E '^(ATOM|HETATM)' $f | cut -c55-60 | sort | uniq -c | sort -rn | head && echo "=== B stats sample ===" && grep -E '^(ATOM|HETATM)' $f | cut -c61-66 | sort -n | head -3 && grep -E '^(ATOM|HETATM)' $f | cut -c61-66 | sort -n | tail -3
```

```bash
grep -E '^(REMARK|CRYST|EXPDTA|TITLE|HEADER|SEQRES|LINK|SSBOND|MODRES)' /tmp/nc_round1_work/r4p_9ygw.pdb | head -30; echo "=== tail ==="; tail -5 /tmp/nc_round1_work/r4p_9ygw.pdb
```

```bash
cd /tmp/agent_r5_9ygw && head -40 /tmp/nc_round1_work/r4p_9ygw.pdb && echo "=== counts ===" && grep -c '^ATOM' /tmp/nc_round1_work/r4p_9ygw.pdb; grep -c '^HETATM' /tmp/nc_round1_work/r4p_9ygw.pdb; grep -c '^ANISOU' /tmp/nc_round1_work/r4p_9ygw.pdb; echo "=== hetres ===" ; grep '^HETATM' /tmp/nc_round1_work/r4p_9ygw.pdb | cut -c18-20 | sort | uniq -c | sort -rn
```

```bash
grep -E '^ATOM' /tmp/nc_round1_work/r4p_9ygw.pdb | head -25; echo "..."; grep -E '^(ATOM|HETATM)' /tmp/nc_round1_work/r4p_9ygw.pdb | awk '{print substr($0,77,2)}' | sort | uniq -c
```

## 2. Free-flag column characterisation (deliberate choice of test set)

```bash
cd /tmp/agent_r5_9ygw && /opt/homebrew/bin/gemmi mtz2csv /tmp/nc_round1_cache/9ygw.mtz /tmp/agent_r5_9ygw/flags.csv 2>/dev/null || /opt/homebrew/bin/gemmi mtz --print-tsv /tmp/nc_round1_cache/9ygw.mtz 2>&1 | head -3; echo "---try python---"; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
from iotbx import mtz
m=mtz.object('/tmp/nc_round1_cache/9ygw.mtz')
from collections import Counter
for lab in ['R-free-flags','R-free-flags-1']:
    ma=[a for a in m.as_miller_arrays() if a.info().labels[0]==lab][0]
    d=ma.data()
    c=Counter(d)
    print(lab, 'n=',ma.size(), 'anom?',ma.anomalous_flag())
    print('  ',sorted(c.items())[:8], '...')
    tot=sum(c.values())
    for k,v in sorted(c.items())[:5]:
        print('   val',k,v, round(100.0*v/tot,2),'%')
"
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
from iotbx import mtz
m=mtz.object('/tmp/nc_round1_cache/9ygw.mtz')
arrs={a.info().labels[0]:a for a in m.as_miller_arrays()}
a0=arrs['R-free-flags']; a1=arrs['R-free-flags-1']
s0=set(h for h,v in zip(a0.indices(),a0.data()) if v==0)
for tv in range(3):
    s1=set(h for h,v in zip(a1.indices(),a1.data()) if v==tv)
    print('R-free-flags==0 vs R-free-flags-1==%d : |A|=%d |B|=%d overlap=%d'%(tv,len(s0),len(s1),len(s0&s1)))
print()
print('data res range', a0.d_max_min())
fobs=arrs['FOBS']
print('FOBS size',fobs.size(),'res',fobs.d_max_min(),'completeness',round(fobs.completeness(),4))
iobs=arrs['IOBS']
print('IOBS size',iobs.size())
"
```

## 3. Baseline measurement of the perturbed model

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data /tmp/nc_round1_work/r4p_9ygw.pdb /tmp/nc_round1_cache/9ygw.mtz f_obs_label=FOBS r_free_flags_label=R-free-flags > mvd_baseline.log 2>&1; tail -60 mvd_baseline.log
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore /tmp/nc_round1_work/r4p_9ygw.pdb > clash_baseline.log 2>&1; tail -5 clash_baseline.log; echo "=== rama ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze /tmp/nc_round1_work/r4p_9ygw.pdb 2>&1 | tail -8; echo "=== rota ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze /tmp/nc_round1_work/r4p_9ygw.pdb 2>&1 | tail -6
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
from libtbx.utils import null_out
pdb_inp=iotbx.pdb.input('/tmp/nc_round1_work/r4p_9ygw.pdb')
m=mmtbx.model.manager(model_input=pdb_inp,log=null_out())
m.process(make_restraints=True)
gs=m.geometry_statistics()
gs.show()
" 2>&1 | tail -40
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import iotbx.pdb, math
from cctbx import adptbx
h=iotbx.pdb.input('/tmp/nc_round1_work/r4p_9ygw.pdb').construct_hierarchy()
import numpy as np
bs=[];bad=0;n=0;dev=[]
for a in h.atoms():
    bs.append(a.b)
    if a.uij != (-1,-1,-1,-1,-1,-1):
        n+=1
        beq=adptbx.u_as_b(adptbx.u_star_as_u_iso if False else (a.uij[0]+a.uij[1]+a.uij[2])/3.0)
        dev.append(beq-a.b)
bs=np.array(bs); dev=np.array(dev)
print('B: n=%d min=%.2f max=%.2f mean=%.2f median=%.2f'%(len(bs),bs.min(),bs.max(),bs.mean(),np.median(bs)))
print('aniso atoms=%d  Beq-B: mean=%.3f max|.|=%.3f'%(n,dev.mean(),np.abs(dev).max()))
"
echo "=== water B ==="; grep '^HETATM' /tmp/nc_round1_work/r4p_9ygw.pdb | grep 'HOH' | cut -c61-66 | sort -n | head -2
grep '^HETATM' /tmp/nc_round1_work/r4p_9ygw.pdb | grep 'HOH' | cut -c61-66 | sort -n | tail -2
```

## 4. PHENIX parameter reconnaissance (no refinement performed)

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | grep -nE 'labels|test_flag_value|anisotropic|riding|ordered_solvent|number_of_macro|optimize_.*weight' | head -40
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>&1 | grep -nE 'miller_array|labels' | head -30; echo "=== nproc ==="; sysctl -n hw.ncpu
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>&1 | sed -n '1,20p'; echo "=== xray_data scope ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=3 2>&1 | sed -n '1275,1315p'
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | sed -n '25,70p'; echo "=== adp/hyd ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=0 2>&1 | sed -n '125,145p'; echo "=== hydrogens ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 2>&1 | grep -nE 'refine = individual|riding|real_space|^\s+hydrogens' | head
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import iotbx.pdb
h=iotbx.pdb.input('/tmp/nc_round1_work/r4p_9ygw.pdb').construct_hierarchy()
c=h.atom_selection_cache()
for s in ['element H or element D','not (element H or element D)','water','element D']:
    print(repr(s), c.selection(s).count(True))
"
```

## 5. [REFINEMENT 1/6] Full-resolution coordinate + anisotropic-ADP recovery

```bash
cd /tmp/agent_r5_9ygw && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/nc_round1_work/r4p_9ygw.pdb /tmp/nc_round1_cache/9ygw.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=6 main.ordered_solvent=False main.nproc=8 output.prefix=r1 output.serial=1 --overwrite > r1.log 2>&1 &
echo "launched pid $!"; sleep 90; tail -30 r1.log
```

```bash
ls -la /tmp/agent_r5_9ygw/ 2>&1; echo "=== ps ==="; ps aux | grep -i phenix | grep -v grep | head
```

```bash
cd /tmp/agent_r5_9ygw && grep -nE 'anisotropic|Number of atoms|scattering|hydrogens|riding|Test flag|flag value|strategy|Total number of|r_work|r_free|start' r1.log | head -50
```

```bash
mkdir -p /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9YGW && sleep 600; cd /tmp/agent_r5_9ygw && grep -nE '^\s*(start|MACRO|macro)|r_work=.*r_free=|Macro-cycle' r1.log | tail -25
```

```bash
cd /tmp/agent_r5_9ygw && grep -nE 'Macro-cycle|^  r_work=|^r_work=' r1.log | tail -30; echo "=== last lines ==="; tail -5 r1.log
```

```bash
sleep 540; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=' r1.log | tail -8; echo "=== done? ==="; ls -la r1_001.pdb 2>&1 | tail -1; tail -3 r1.log
```

```bash
cd /tmp/agent_r5_9ygw && sed -n '/Final refinement statistics/,/^$/p' r1.log | head -40; echo "=== FINAL BLOCK ==="; grep -nE 'Start R-work|Final R-work|bond|angle|clashscore|Ramachandran|rotamer|outliers' r1.log | tail -30
```

```bash
cd /tmp/agent_r5_9ygw && sed -n '2005,2075p' r1.log
```

## 6. [FAILED LAUNCH — NOT COUNTED] first attempt at run 2

Aborted in PHIL processing with `Sorry: No reflection files are available to
continue processing PHIL.` — no refinement was performed. Cause (diagnosed
below): the input MTZ had been deleted from `/tmp/nc_round1_cache/` by something
outside this task.

```bash
cd /tmp/agent_r5_9ygw && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine r1_001.pdb /tmp/nc_round1_cache/9ygw.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=8 main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle_after_first main.nproc=8 output.prefix=r2 output.serial=1 --overwrite > r2.log 2>&1 &
echo "launched"; sleep 120; grep -nE 'Sorry|error|ERROR' r2.log | head; tail -3 r2.log
```

```bash
ls -la /tmp/agent_r5_9ygw/*.log; echo "=== r2 tail ==="; tail -5 /tmp/agent_r5_9ygw/r2.log 2>&1; ps aux | grep 9ygw | grep -v grep | wc -l
```

```bash
cat /tmp/agent_r5_9ygw/r2.log; echo "=== files ==="; ls /tmp/agent_r5_9ygw/
```

```bash
sed -n '1,30p' /tmp/agent_r5_9ygw/r1.log
```

## 7. [FAILED LAUNCH — NOT COUNTED] second attempt at run 2

Same abort, same cause; ruled out an output-filename collision as the explanation.

```bash
cd /tmp/agent_r5_9ygw && cp r1_001.pdb stage1.pdb && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/agent_r5_9ygw/stage1.pdb /tmp/nc_round1_cache/9ygw.mtz miller_array.labels.name=FOBS,SIGFOBS miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=8 main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle_after_first main.nproc=8 output.prefix=r2 output.serial=1 --overwrite > /tmp/agent_r5_9ygw/r2.log 2>&1 &
sleep 60; sed -n '1,12p' /tmp/agent_r5_9ygw/r2.log; echo "..."; tail -3 /tmp/agent_r5_9ygw/r2.log
```

## 8. Diagnosis: the input MTZ was deleted mid-task; recover data from run 1 output

```bash
ls -la /tmp/nc_round1_cache/9ygw.mtz; /opt/homebrew/bin/gemmi mtz --dump /tmp/nc_round1_cache/9ygw.mtz 2>&1 | head -5; echo "=== exit $? ==="; df -h /tmp | tail -1
```

```bash
ls -la /tmp/nc_round1_cache/ 2>&1 | head -20; echo "=== work dir ==="; ls -la /tmp/nc_round1_work/ 2>&1 | head -20; echo "=== my r1_001.mtz ==="; ls -la /tmp/agent_r5_9ygw/r1_001.mtz; /opt/homebrew/bin/gemmi mtz --dump /tmp/agent_r5_9ygw/r1_001.mtz 2>&1 | sed -n '1,40p'
```

```bash
cd /tmp/agent_r5_9ygw && cp r1_001.mtz data_9ygw_recovered.mtz && chmod 444 data_9ygw_recovered.mtz && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
from iotbx import mtz
from collections import Counter
m=mtz.object('/tmp/agent_r5_9ygw/data_9ygw_recovered.mtz')
arrs={a.info().labels[0]:a for a in m.as_miller_arrays()}
for k in arrs: print(k, arrs[k].size())
a=arrs['R-free-flags']; c=Counter(a.data())
print('flags:',sorted(c.items()))
f=arrs['F-obs']; print('F-obs res',f.d_max_min(),'compl',round(f.completeness(),4))
"
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data stage1.pdb data_9ygw_recovered.mtz f_obs_label=F-obs r_free_flags_label=R-free-flags > mvd_stage1.log 2>&1; grep -E 'flag value|r_work|r_free|outliers' mvd_stage1.log | tail -6
```

## 9. [REFINEMENT 2/6] Ordered-solvent rebuild

```bash
cd /tmp/agent_r5_9ygw && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/agent_r5_9ygw/stage1.pdb /tmp/agent_r5_9ygw/data_9ygw_recovered.mtz miller_array.labels.name=F-obs,SIGF-obs miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=8 main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle_after_first main.nproc=6 output.prefix=r2 output.serial=1 --overwrite > /tmp/agent_r5_9ygw/r2.log 2>&1 &
sleep 90; sed -n '1,10p' /tmp/agent_r5_9ygw/r2.log; echo "..."; tail -4 /tmp/agent_r5_9ygw/r2.log
```

```bash
sleep 900; cd /tmp/agent_r5_9ygw && grep -E '^\s+[0-9]_(bss|occ)' r2.log | tail -12; echo "=== last ==="; tail -3 r2.log
```

```bash
cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=|n_water|ordered solvent|Number of waters' r2.log | tail -15; echo "=== last ==="; tail -3 r2.log
```

```bash
sleep 560; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=.*n_water' r2.log | tail -8; echo "=== plain ==="; grep -nE '^  r_work=0' r2.log | tail -5; tail -2 r2.log
```

```bash
sleep 590; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0' r2.log | tail -6; tail -2 r2.log; ls -la r2_001.pdb 2>&1|tail -1
```

```bash
sleep 900; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0' r2.log | tail -6; tail -2 r2.log; ls -la r2_001.pdb 2>&1|tail -1
```

```bash
cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0' r2.log | tail -6; tail -2 r2.log; ls -la r2_001.pdb 2>&1|tail -1
```

```bash
sleep 780; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0' r2.log | tail -4; tail -2 r2.log; ls -la r2_001.pdb 2>&1|tail -1
```

```bash
cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0' r2.log | tail -4; tail -2 r2.log; ls -la r2_001.pdb 2>&1|tail -1
```

```bash
cd /tmp/agent_r5_9ygw && grep -nE 'Final R-work|Final R-free|^  Start R-work' r2.log | tail; echo "=== table tail ==="; grep -E '^\s+[0-9]+_(bss|occ|adp)' r2.log | tail -10; echo "=== mvd on r2 ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r2_001.pdb data_9ygw_recovered.mtz f_obs_label=F-obs r_free_flags_label=R-free-flags > mvd_r2.log 2>&1; grep -E '^  r_work|^  r_free' mvd_r2.log; grep -c HOH r2_001.pdb
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import iotbx.pdb
h=iotbx.pdb.input('/tmp/agent_r5_9ygw/r2_001.pdb').construct_hierarchy()
c=h.atom_selection_cache()
nonh=c.selection('not (element H or element D)')
wat=c.selection('water')
iso_nonh=0; iso_wat=0; nwat=0
for i,a in enumerate(h.atoms()):
    isaniso = a.uij != (-1,-1,-1,-1,-1,-1)
    if nonh[i] and not isaniso: iso_nonh+=1
    if wat[i]:
        nwat+=1
        if not isaniso: iso_wat+=1
print('total atoms',h.atoms_size(),'non-H/D',nonh.count(True),'isotropic non-H/D',iso_nonh)
print('waters',nwat,'isotropic waters',iso_wat)
"
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=1 2>&1 | grep -nE 'optimize|weight' | head -20
```

```bash
/Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine --show-defaults=2 2>&1 | grep -nE 'optimize_xyz_weight|optimize_adp_weight|target_weights|wxc_scale|wxu_scale' | head -20
```

## 10. [REFINEMENT 3/6] Anisotropic waters + target-weight optimisation

```bash
cd /tmp/agent_r5_9ygw && cp r2_001.pdb stage2.pdb && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/agent_r5_9ygw/stage2.pdb /tmp/agent_r5_9ygw/data_9ygw_recovered.mtz miller_array.labels.name=F-obs,SIGF-obs miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=4 main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle_after_first target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True main.nproc=6 output.prefix=r3 output.serial=1 --overwrite > /tmp/agent_r5_9ygw/r3.log 2>&1 &
sleep 120; sed -n '5,10p' /tmp/agent_r5_9ygw/r3.log; tail -3 /tmp/agent_r5_9ygw/r3.log
```

```bash
sleep 570; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0' r3.log | tail -6; echo "=== weights ==="; grep -nE 'optimal|wxc|wxu' r3.log | tail -8; tail -2 r3.log
```

```bash
sleep 590; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0' r3.log | tail -5; echo "=== weight trials ==="; sed -n '/work  free  delta/,$p' r3.log | tail -25
```

```bash
sleep 590; cd /tmp/agent_r5_9ygw && grep -nE '^  r_work=0|^r_work=0' r3.log | tail -6; tail -2 r3.log
```

```bash
cd /tmp/agent_r5_9ygw && grep -E 'Final R-work' r3.log; grep -E '^\s+[0-9]+_(bss|occ|adp|xyzrec)' r3.log | tail -8; echo "=== mvd ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r3_001.pdb data_9ygw_recovered.mtz f_obs_label=F-obs r_free_flags_label=R-free-flags > mvd_r3.log 2>&1; grep -E '^  r_work|^  r_free' mvd_r3.log
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
from libtbx.utils import null_out
m=mmtbx.model.manager(model_input=iotbx.pdb.input('/tmp/agent_r5_9ygw/r3_001.pdb'),log=null_out())
m.process(make_restraints=True)
m.geometry_statistics().show()
" 2>&1 | grep -E 'BOND|ANGLE|CLASHSCORE|OUTLIERS|FAVORED|ALLOWED|RAMA|WHOLE|MIN NONBONDED'
```

## 11. [REFINEMENT 4/6] Continued polish — tests whether gains remain

```bash
cd /tmp/agent_r5_9ygw && cp r3_001.pdb stage3.pdb && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/agent_r5_9ygw/stage3.pdb /tmp/agent_r5_9ygw/data_9ygw_recovered.mtz miller_array.labels.name=F-obs,SIGF-obs miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=6 main.ordered_solvent=True ordered_solvent.mode=every_macro_cycle_after_first target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True main.nproc=6 output.prefix=r4 output.serial=1 --overwrite > /tmp/agent_r5_9ygw/r4.log 2>&1 &
sleep 30; sed -n '5,10p' /tmp/agent_r5_9ygw/r4.log; echo "=== r3 waters ==="; grep -c ' HOH ' /tmp/agent_r5_9ygw/r3_001.pdb; grep 'HETATM' /tmp/agent_r5_9ygw/r3_001.pdb | grep -c ' HOH '
```

```bash
sleep 595; cd /tmp/agent_r5_9ygw && grep -nE '^r_work=0|^  r_work=0' r4.log | tail -5; tail -2 r4.log
```

```bash
sleep 595; cd /tmp/agent_r5_9ygw && grep -nE '^r_work=0|^  r_work=0' r4.log | tail -5; tail -2 r4.log
```

```bash
sleep 595; cd /tmp/agent_r5_9ygw && grep -nE '^r_work=0|^  r_work=0' r4.log | tail -4; tail -2 r4.log
```

```bash
sleep 595; cd /tmp/agent_r5_9ygw && grep -nE '^r_work=0|^  r_work=0' r4.log | tail -4; tail -2 r4.log
```

```bash
sleep 595; cd /tmp/agent_r5_9ygw && grep -E 'Final R-work' r4.log; grep -nE '^  r_work=0' r4.log | tail -3; tail -2 r4.log
```

```bash
cd /tmp/agent_r5_9ygw && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data r4_001.pdb data_9ygw_recovered.mtz f_obs_label=F-obs r_free_flags_label=R-free-flags > mvd_r4.log 2>&1; grep -E '^  r_work|^  r_free' mvd_r4.log; echo "=== r4 geometry ==="; /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import mmtbx.model, iotbx.pdb
from libtbx.utils import null_out
for f in ['r3_001.pdb','r4_001.pdb']:
    m=mmtbx.model.manager(model_input=iotbx.pdb.input('/tmp/agent_r5_9ygw/'+f),log=null_out())
    m.process(make_restraints=True)
    print('=====',f)
    m.geometry_statistics().show()
" 2>&1 | grep -E '=====|BOND      :|ANGLE     :|CLASHSCORE|OUTLIERS|FAVORED|WHOLE:|MIN NONBONDED'
```

## 12. [REFINEMENT 5/6] Fixed-solvent consolidation (hypothesis test — refuted)

```bash
cd /tmp/agent_r5_9ygw && cp r3_001.pdb stage3b.pdb && nohup /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.refine /tmp/agent_r5_9ygw/stage3b.pdb /tmp/agent_r5_9ygw/data_9ygw_recovered.mtz miller_array.labels.name=F-obs,SIGF-obs miller_array.labels.name=R-free-flags data_manager.fmodel.xray_data.r_free_flags.test_flag_value=0 refine.adp.individual.anisotropic="not (element H or element D)" main.number_of_macro_cycles=4 main.ordered_solvent=False target_weights.optimize_xyz_weight=True target_weights.optimize_adp_weight=True main.nproc=6 output.prefix=r5 output.serial=1 --overwrite > /tmp/agent_r5_9ygw/r5.log 2>&1 &
sleep 30; sed -n '5,10p' /tmp/agent_r5_9ygw/r5.log
```

```bash
sleep 595; cd /tmp/agent_r5_9ygw && grep -nE '^r_work=0|^  r_work=0' r5.log | tail -4; tail -2 r5.log
```

```bash
cd /tmp/agent_r5_9ygw && grep -E '^\s+[0-9]+_' r5.log | head -20
```

```bash
cd /tmp/agent_r5_9ygw && grep -nE 'r_work=0' r5.log | head -20
```

```bash
sleep 595; cd /tmp/agent_r5_9ygw && grep -E 'Final R-work' r5.log; grep -nE '^  r_work=0' r5.log | tail -4; tail -2 r5.log
```

```bash
sleep 560; cd /tmp/agent_r5_9ygw && grep -E 'Final R-work' r5.log; grep -nE '^  r_work=0' r5.log | tail -3; tail -2 r5.log
```

## 13. Final selection, delivery and independent validation

Run 3's model was selected over runs 4 and 5 (both had equal-or-worse R-free with
worse geometry). Refinement invocation 6/6 was deliberately not used.

```bash
cd /tmp/agent_r5_9ygw && cp r3_001.pdb /Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9YGW/final.pdb && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9YGW && echo "=== model_vs_data on delivered final.pdb ===" && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.model_vs_data $D/final.pdb data_9ygw_recovered.mtz f_obs_label=F-obs r_free_flags_label=R-free-flags 2>&1 | grep -E 'flag value|^  r_work|^  r_free|outliers' ; echo "=== clashscore ===" && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.clashscore $D/final.pdb 2>&1 | tail -2; echo "=== ramalyze ===" && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.ramalyze $D/final.pdb 2>&1 | tail -3; echo "=== rotalyze ===" && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.rotalyze $D/final.pdb 2>&1 | tail -2
```

```bash
cd /tmp/agent_r5_9ygw && D=/Users/marcin/Documents/VIMSS/ontology/protstruct_review/data/agents/round5/9YGW && /Users/marcin/phenix-2.0-5936/phenix_bin/phenix.python -c "
import iotbx.pdb
for f in ['/tmp/nc_round1_work/r4p_9ygw.pdb','$D/final.pdb']:
    h=iotbx.pdb.input(f).construct_hierarchy()
    c=h.atom_selection_cache()
    aniso=sum(1 for a in h.atoms() if a.uij!=(-1,-1,-1,-1,-1,-1))
    print(f.split('/')[-1], 'atoms',h.atoms_size(),'non-H/D',c.selection('not (element H or element D)').count(True),'waters',c.selection('water').count(True),'aniso',aniso)
"; ls -la $D/
```

---

## Refinement-invocation accounting

| # | Section | Description | Outcome |
|---|---|---|---|
| 1/6 | §5 | Full-res sites + aniso ADP + occupancies, no solvent, 6 macro-cycles | 0.4136/0.4115 → 0.1318/0.1459 |
| — | §6 | Aborted in PHIL processing (MTZ deleted) — **not counted** | no refinement performed |
| — | §7 | Aborted in PHIL processing (same cause) — **not counted** | no refinement performed |
| 2/6 | §9 | Ordered-solvent rebuild, 8 macro-cycles | → 0.1258/0.1388 |
| 3/6 | §10 | Aniso waters + target-weight optimisation, 4 macro-cycles | → **0.1185/0.1317** (selected) |
| 4/6 | §11 | Continued polish, 6 macro-cycles | → 0.1167/0.1314, geometry worse — rejected |
| 5/6 | §12 | Fixed solvent set, 4 macro-cycles | → 0.1168/0.1320 — rejected |
| 6/6 | — | **Not used** — R-free plateau established by runs 4 and 5 | — |

Note on `sleep` commands: these are polling waits on background `nohup` jobs
(macOS has no `setsid`), not separate program launches.

