"""Local CheckMyMetal-style metal-identity check.

Implements the published Zheng et al. 2014/2017 criteria for classifying
modelled metal ions by coordination geometry. Uses gemmi for atom
extraction. Not the canonical web service — that's at
https://checkmymetal.research.uchicago.edu/. Use this as a
geometry-based first pass; submit to the web service when accessible
for the canonical verdict.

Published canonical values (Zheng 2017, Methods Enzymol; mean ± std
over high-resolution non-redundant structures):

  Element   Bond Å      CN typical   B-factor typical
  Ca²⁺      2.40 ± 0.15  6–8          15–30
  Mg²⁺      2.07 ± 0.05  6 (oct)      15–25
  Na⁺       2.40 ± 0.20  6–8 weak     20–40
  K⁺        2.80 ± 0.20  6–9 weak     20–40
  Zn²⁺      2.07 ± 0.10  4–6 (often Td)  15–25
  Mn²⁺      2.18 ± 0.10  6 (oct)      15–25
  Fe³⁺      2.05 ± 0.10  6 (oct)      15–25

Score: per-element Z-score on observed mean bond length, plus
boolean checks on CN range. Lowest |Z| and CN-in-range = best fit.
"""
import statistics
import gemmi

CANONICAL = {
    "Ca": {"d": 2.40, "sd": 0.15, "cn_lo": 6, "cn_hi": 8, "b_lo": 15, "b_hi": 30},
    "Mg": {"d": 2.07, "sd": 0.05, "cn_lo": 6, "cn_hi": 6, "b_lo": 15, "b_hi": 25},
    "Na": {"d": 2.40, "sd": 0.20, "cn_lo": 6, "cn_hi": 8, "b_lo": 20, "b_hi": 40},
    "K":  {"d": 2.80, "sd": 0.20, "cn_lo": 6, "cn_hi": 9, "b_lo": 20, "b_hi": 40},
    "Zn": {"d": 2.07, "sd": 0.10, "cn_lo": 4, "cn_hi": 6, "b_lo": 15, "b_hi": 25},
    "Mn": {"d": 2.18, "sd": 0.10, "cn_lo": 6, "cn_hi": 6, "b_lo": 15, "b_hi": 25},
    "Fe": {"d": 2.05, "sd": 0.10, "cn_lo": 6, "cn_hi": 6, "b_lo": 15, "b_hi": 25},
}

# Inner-sphere cutoff: ~ canonical Ca-O + 1.5σ for the most permissive case.
INNER_SPHERE_CUTOFF = 3.20  # Å


def find_metal(struct, chain_id, resname):
    for model in struct:
        for chain in model:
            if chain.name != chain_id:
                continue
            for res in chain:
                if res.name == resname:
                    for at in res:
                        return at, res
    return None, None


def neighbours(struct, atom, cutoff):
    """List of (other_atom, residue, distance) within cutoff, excluding self."""
    out = []
    for model in struct:
        for chain in model:
            for res in chain:
                for at in res:
                    if at is atom:
                        continue
                    d = atom.pos.dist(at.pos)
                    if d <= cutoff:
                        out.append((at, res, d, chain.name))
    return out


def score(observed_d_mean, observed_d_min, observed_d_max, cn, b, element):
    c = CANONICAL[element]
    z = (observed_d_mean - c["d"]) / c["sd"]
    cn_ok = c["cn_lo"] <= cn <= c["cn_hi"]
    b_ok = c["b_lo"] <= b <= c["b_hi"]
    return {
        "z_bond": round(z, 2),
        "cn_in_range": cn_ok,
        "b_in_range": b_ok,
    }


def analyse(struct_path, chain_id, resname):
    s = gemmi.read_structure(struct_path)
    metal_at, metal_res = find_metal(s, chain_id, resname)
    if metal_at is None:
        print(f"NOT FOUND: {chain_id} {resname}")
        return
    contacts = neighbours(s, metal_at, INNER_SPHERE_CUTOFF)
    contacts.sort(key=lambda x: x[2])
    inner = [(at, res, d, ch) for at, res, d, ch in contacts if d < INNER_SPHERE_CUTOFF]

    print(f"\n=== {chain_id} {resname} {metal_res.seqid.num} ===")
    print(f"Position: ({metal_at.pos.x:.3f}, {metal_at.pos.y:.3f}, {metal_at.pos.z:.3f})")
    print(f"B-factor: {metal_at.b_iso:.2f}")
    print(f"\nInner-sphere contacts (≤ {INNER_SPHERE_CUTOFF} Å):")
    bond_lengths = []
    for at, res, d, ch in inner:
        print(f"  {at.element.name:>2} {ch} {res.seqid.num} {res.name} {at.name}  {d:.3f} Å")
        bond_lengths.append(d)

    if not bond_lengths:
        print("  (none — outside inner-sphere cutoff)")
        return

    mean_d = statistics.fmean(bond_lengths)
    min_d = min(bond_lengths)
    max_d = max(bond_lengths)
    cn = len(bond_lengths)
    b = metal_at.b_iso

    print(f"\nObserved: mean d = {mean_d:.3f} Å (range {min_d:.3f}-{max_d:.3f}), CN = {cn}, B = {b:.2f}")
    print("\nCheckMyMetal-style scoring:")
    print(f"{'Element':>8} {'|Z| bond':>10} {'CN range':>12} {'B range':>12} {'verdict':>20}")
    rows = []
    for el in CANONICAL:
        s = score(mean_d, min_d, max_d, cn, b, el)
        zabs = abs(s["z_bond"])
        flags = []
        if zabs > 3:
            flags.append("bond too long" if s["z_bond"] > 0 else "bond too short")
        if not s["cn_in_range"]:
            flags.append("CN out of range")
        if not s["b_in_range"]:
            flags.append("B out of range")
        verdict = "✓ consistent" if not flags else " | ".join(flags)
        rows.append((el, zabs, s, verdict))
        print(f"{el:>8} {zabs:>10.2f} {str(s['cn_in_range']):>12} {str(s['b_in_range']):>12}  {verdict}")

    rows.sort(key=lambda r: r[1])
    print(f"\nBest geometric fit: {rows[0][0]} (|Z| {rows[0][1]:.2f})")
    if rows[0][3] != "✓ consistent":
        print(f"  → flagged: {rows[0][3]}")


if __name__ == "__main__":
    import argparse, sys
    p = argparse.ArgumentParser(description="CheckMyMetal-style local metal-identity heuristic.")
    p.add_argument("pdb", help="Input PDB / mmCIF file.")
    p.add_argument("metal", nargs="+",
                   help="Metal site(s) to analyse, formatted as CHAIN:RESNAME (e.g. A:CA, B:NA, A:ZN).")
    args = p.parse_args()
    for spec in args.metal:
        try:
            chain_id, resname = spec.split(":", 1)
        except ValueError:
            print(f"Bad spec {spec!r}; expected CHAIN:RESNAME", file=sys.stderr)
            sys.exit(1)
        analyse(args.pdb, chain_id, resname)
