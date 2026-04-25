"""Independent R-work / R-free using gemmi (no cctbx).

Reads Fobs from one MTZ and Fcalc (already includes bulk solvent + scaling
from gemmi sfcalc) from another MTZ, joins on hkl, applies bin-wise
isotropic rescale, and reports R-work and R-free.
"""
import sys, gemmi, numpy as np

obs_path, calc_path = sys.argv[1], sys.argv[2]
mtz_o = gemmi.read_mtz_file(obs_path)
mtz_c = gemmi.read_mtz_file(calc_path)

def cols_to_dict(mtz):
    arr = np.array(mtz, copy=False)
    return {c.label: arr[:, i] for i, c in enumerate(mtz.columns)}

co = cols_to_dict(mtz_o)
cc = cols_to_dict(mtz_c)

ho = np.column_stack([co["H"], co["K"], co["L"]]).astype(int)
hc = np.column_stack([cc["H"], cc["K"], cc["L"]]).astype(int)

# Build hash for matching reflections.
key_o = (ho[:, 0].astype(np.int64) << 32) | ((ho[:, 1].astype(np.int64) & 0xffff) << 16) | (ho[:, 2].astype(np.int64) & 0xffff)
key_c = (hc[:, 0].astype(np.int64) << 32) | ((hc[:, 1].astype(np.int64) & 0xffff) << 16) | (hc[:, 2].astype(np.int64) & 0xffff)
order_c = np.argsort(key_c)
sorted_c = key_c[order_c]
idx_in_c = np.searchsorted(sorted_c, key_o)
match = (idx_in_c < len(sorted_c)) & (sorted_c[np.minimum(idx_in_c, len(sorted_c) - 1)] == key_o)
idx_c = order_c[idx_in_c[match]]

fobs = co["F-obs"][match]
sig  = co["SIGF-obs"][match]
free = co["R-free-flags"][match].astype(int)
hkl  = ho[match]
fcalc = cc["FC"][idx_c]

ok = np.isfinite(fobs) & np.isfinite(fcalc) & np.isfinite(sig) & (sig > 0)
fobs, fcalc, sig, free, hkl = fobs[ok], fcalc[ok], sig[ok], free[ok], hkl[ok]

# 1/d^2 per reflection (for bin assignment).
cell = mtz_o.cell
s2 = np.array([cell.calculate_1_d2((int(h), int(k), int(l))) for h, k, l in hkl])

# Bin-wise scale to remove residual resolution drift.
nbins = 20
order = np.argsort(s2)
edges = np.array_split(order, nbins)
scale = np.ones_like(fcalc)
for ix in edges:
    if len(ix) == 0:
        continue
    s = (fobs[ix] * fcalc[ix]).sum() / max((fcalc[ix] ** 2).sum(), 1e-12)
    scale[ix] = s
fcalc_s = fcalc * scale

# Convention check: this MTZ uses flag=1 for the test (free) set.
work_mask = (free == 0)
free_mask = (free != 0)

def r(o, c, mask):
    o2, c2 = o[mask], c[mask]
    return np.abs(o2 - c2).sum() / np.abs(o2).sum()

print(f"matched reflections: {len(fobs)}")
print(f"  work: {int(work_mask.sum())}, free: {int(free_mask.sum())}")
print(f"R-work (gemmi)  = {r(fobs, fcalc_s, work_mask):.4f}")
print(f"R-free (gemmi)  = {r(fobs, fcalc_s, free_mask):.4f}")
print(f"R-free gap      = {r(fobs, fcalc_s, free_mask) - r(fobs, fcalc_s, work_mask):.4f}")
