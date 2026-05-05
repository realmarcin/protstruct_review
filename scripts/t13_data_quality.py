"""T13 non-cctbx data-quality oracle wrapper.

Drives CCP4 aimless first (canonical recommendation); when the input MTZ
is merged-only (no unmerged intensities), aimless aborts and we fall
back to ctruncate, which does work on merged amplitudes and is also
non_cctbx.

Parses Wilson B, L-test twin fraction, moments-based twin estimate,
anisotropy ΔB, tNCS flag, and ice-ring flags.
Prints a YAML fragment of EvaluationMeasurement rows ready to paste
into an existing EvaluationRun's `measurements:` section.

Usage:
    python scripts/t13_data_quality.py <mtz> --eval-id <EVAL-id> \
        --columns 'F-obs,SIGF-obs' [--logdir <dir>]

Notes:
    - aimless requires unmerged intensities (M/ISYM column). On merged-F
      input it errors with "hkl_unmerge_list::prepare - EMPTY"; that
      branch is captured in the printed YAML as a noted limitation.
    - ctruncate outputs are persisted under <logdir> (default:
      adjacent to <mtz>) so the QDS evidence_refs can point to them.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], stdin: str = "", env: dict | None = None,
         cwd: str | None = None, log_path: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        cmd, input=stdin, capture_output=True, text=True, env=env, cwd=cwd
    )
    out = proc.stdout + proc.stderr
    if log_path is not None:
        log_path.write_text(out)
    return proc.returncode, out


def try_aimless(mtz: Path, logdir: Path) -> dict:
    """Run aimless against the input MTZ. Returns a dict with keys:
        status: "ran" | "failed" | "missing"
        reason: short explanation
        log: path to stored log
    """
    if not shutil.which("aimless"):
        return {"status": "missing",
                "reason": "aimless binary not on PATH (source CCP4 setup)",
                "log": None}
    log = logdir / "aimless.log"
    out_mtz = logdir / "aimless_scaled.mtz"
    rc, output = _run(
        ["aimless", "HKLIN", str(mtz), "HKLOUT", str(out_mtz)],
        stdin="END\n",
        log_path=log,
    )
    if rc != 0:
        if "hkl_unmerge_list::prepare - EMPTY" in output:
            reason = "MTZ has merged amplitudes only; aimless requires unmerged intensities"
        else:
            reason = "aimless exited non-zero"
        return {"status": "failed", "reason": reason, "log": str(log)}
    return {"status": "ran", "reason": "ok", "log": str(log)}


def run_ctruncate(mtz: Path, columns: str, logdir: Path) -> dict:
    if not shutil.which("ctruncate"):
        raise SystemExit("ctruncate not on PATH (source CCP4 setup)")
    log = logdir / "ctruncate.log"
    out_mtz = logdir / "ctruncate_out.mtz"
    rc, output = _run(
        [
            "ctruncate",
            "-hklin", str(mtz),
            "-hklout", str(out_mtz),
            "-colin", f"/*/*/[{columns}]",
        ],
        log_path=log,
    )
    if rc != 0:
        raise SystemExit(f"ctruncate failed (rc={rc}); see {log}")
    return parse_ctruncate(output, str(log))


def parse_ctruncate(text: str, log_path: str) -> dict:
    """Pull the T13-relevant scalars out of ctruncate's stdout."""
    out = {"log": log_path}

    # Resolution range
    m = re.search(r"Resolution range of data:\s*([\d.]+)\s*-\s*([\d.]+)\s*A", text)
    if m:
        out["resolution_low_a"] = float(m.group(1))
        out["resolution_high_a"] = float(m.group(2))

    # Wilson B
    m = re.search(r"Estimate of Wilson B factor:\s*([-\d.]+)\s*A\^\(-2\)"
                  r"(?:,\s*with sigma\s*([\d.]+))?", text)
    if m:
        out["wilson_b"] = float(m.group(1))
        if m.group(2):
            out["wilson_b_sigma"] = float(m.group(2))

    # Anisotropy eigenvalues
    m = re.search(r"Eigenvalues:\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", text)
    if m:
        eigs = [float(x) for x in m.groups()]
        out["aniso_eigenvalues"] = eigs
        out["delta_b_aniso"] = max(eigs) - min(eigs)
    if "Some anisotropy detetect" in text or "Some anisotropy detected" in text:
        out["aniso_flag"] = "some"
    else:
        out["aniso_flag"] = "none_flagged"

    # Twinning — L-test fraction
    m = re.search(r"Twin fraction estimate from L-test:\s*([\d.]+)", text)
    if m:
        out["twin_fraction_l"] = float(m.group(1))
    m = re.search(r"Twin fraction estimate from moments:\s*([\d.]+)", text)
    if m:
        out["twin_fraction_moments"] = float(m.group(1))
    m = re.search(r"L statistic\s*=\s*([\d.]+)", text)
    if m:
        out["l_statistic"] = float(m.group(1))
    if "First principles calculation has found no potential twinning operators" in text:
        out["twin_operators_found"] = 0
    else:
        m = re.search(r"Twin fraction estimates by twinning operator", text)
        out["twin_operators_found"] = 1 if m else 0

    # Moments of I
    m = re.search(r"<I\^2>/<I>\^2\s*=\s*([\d.]+)", text)
    if m:
        out["moment_2_acentric"] = float(m.group(1))

    # tNCS
    if "No translational NCS detected" in text:
        out["tncs_flag"] = False
    elif re.search(r"translational NCS.*detected", text, flags=re.IGNORECASE):
        out["tncs_flag"] = True

    # Ice rings — count "yes" rows in the ice ring summary table
    ice_block = re.search(
        r"ICE RING SUMMARY:.*?(?=WILSON SCALING|TWINNING ANALYSIS|\Z)",
        text, flags=re.DOTALL,
    )
    if ice_block:
        ice_rows = re.findall(
            r"^\s*([\d.]+)\s+(yes|no)\s",
            ice_block.group(0), flags=re.MULTILINE,
        )
        flagged = [r for r in ice_rows if r[1] == "yes"]
        out["ice_ring_resolutions_flagged"] = [float(r[0]) for r in flagged]
        out["ice_ring_count_total"] = len(ice_rows)

    return out


# ---------------------------------------------------------------------------
# Render YAML fragment
# ---------------------------------------------------------------------------

def render_yaml(stats: dict, eval_id: str, aimless: dict) -> str:
    """Produce the snippet of measurement rows for the EVAL yaml."""
    lines: list[str] = []

    def m(suffix: str, metric: str, value, kind: str = "numeric",
          unit: str | None = None, criterion: str = "informational",
          status: str = "informational", notes: str | None = None):
        lines.append(f"  - id: {eval_id}_M_t13_{suffix}")
        lines.append(f"    catalog_task_ref: T13")
        lines.append(f"    stage: all")
        lines.append(f"    metric_definition_ref: {metric}")
        lines.append(f"    oracle_tool_ref: ctruncate")
        lines.append(f"    oracle_family: non_cctbx")
        lines.append(f"    agent_claim:")
        lines.append(f"      is_not_applicable: true")
        lines.append(f"    oracle_measure:")
        if kind == "numeric":
            lines.append(f"      value_numeric: {value}")
        else:
            lines.append(f"      value_text: {value!r}")
        if unit:
            lines.append(f"      unit: {unit!r}")
        lines.append(f"    pass_criterion: {criterion}")
        lines.append(f"    pass_status: {status}")
        if notes:
            lines.append(f"    notes: {notes!r}")

    if "wilson_b" in stats:
        m("wilson_b", "T13_wilson_b", stats["wilson_b"], unit="Å²",
          notes=f"ctruncate Wilson scaling; sigma {stats.get('wilson_b_sigma', '?')}.")

    if "twin_fraction_l" in stats:
        m("twin_fraction_l", "T13_l-test_twinning",
          stats["twin_fraction_l"], unit="fraction",
          criterion="< 0.05",
          status="pass" if stats["twin_fraction_l"] < 0.05 else "fail",
          notes=(f"L statistic {stats.get('l_statistic')} (untwinned 0.5, "
                 f"perfect twin 0.375); moments-based estimate "
                 f"{stats.get('twin_fraction_moments')}; "
                 f"first-principles twin operators found: "
                 f"{stats.get('twin_operators_found')}."))

    if "delta_b_aniso" in stats:
        m("delta_b_aniso", "T13_anisotropy_δb_aniso",
          round(stats["delta_b_aniso"], 3), unit="Å²",
          criterion="< 20 Å² (rough rule of thumb)",
          status="pass" if stats["delta_b_aniso"] < 20 else "fail",
          notes=(f"ctruncate anisotropy eigenvalues {stats.get('aniso_eigenvalues')}; "
                 f"flag = {stats.get('aniso_flag')}."))

    if "tncs_flag" in stats:
        m("tncs_flag", "T13_tncs_flag",
          str(bool(stats["tncs_flag"])).lower(),
          kind="text",
          criterion="false",
          status="pass" if not stats["tncs_flag"] else "fail",
          notes="ctruncate Patterson search at 4 Å resolution limit.")

    if "ice_ring_resolutions_flagged" in stats:
        flagged = stats["ice_ring_resolutions_flagged"]
        m("ice_ring_flags", "T13_ice-ring_flags",
          (",".join(f"{r:.2f}Å" for r in flagged) if flagged else "none"),
          kind="text",
          criterion="no flagged rings (Z > 5)",
          status="pass" if not flagged else "informational",
          notes=(f"ctruncate ice-ring summary: {stats.get('ice_ring_count_total')} "
                 f"sensitive bins scanned; "
                 f"{len(flagged)} flagged at Z-score > 5. "
                 f"Borderline rings near 3.44 Å are common and not necessarily "
                 f"actionable; surface as informational."))

    # Provenance row about the aimless attempt
    lines.append(f"  - id: {eval_id}_M_t13_aimless_attempt")
    lines.append(f"    catalog_task_ref: T13")
    lines.append(f"    stage: all")
    lines.append(f"    metric_definition_ref: T13_aimless_status")
    lines.append(f"    oracle_tool_ref: CCP4 aimless")
    lines.append(f"    oracle_family: non_cctbx")
    lines.append(f"    agent_claim:")
    lines.append(f"      is_not_applicable: true")
    lines.append(f"    oracle_measure:")
    lines.append(f"      value_text: {aimless['status']!r}")
    lines.append(f"    pass_criterion: informational")
    lines.append(f"    pass_status: informational")
    lines.append(f"    notes: {aimless['reason']!r}")

    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(
        description="Run aimless then ctruncate as the T13 non-cctbx oracle.")
    p.add_argument("mtz", type=Path, help="Input MTZ file.")
    p.add_argument("--eval-id", required=True,
                   help="EvaluationRun id whose measurement rows to emit "
                        "(e.g. EVAL_1sar_cdba2c07_2026-04-24).")
    p.add_argument("--columns", default="F-obs,SIGF-obs",
                   help="MTZ amplitude column pair (default: F-obs,SIGF-obs).")
    p.add_argument("--logdir", type=Path,
                   help="Directory for stdout / output MTZs "
                        "(default: <mtz parent>/t13_oracle_logs/).")
    args = p.parse_args()

    if not args.mtz.exists():
        raise SystemExit(f"input MTZ not found: {args.mtz}")
    logdir = args.logdir or (args.mtz.parent / "t13_oracle_logs")
    logdir.mkdir(parents=True, exist_ok=True)

    aimless = try_aimless(args.mtz, logdir)
    print(f"# aimless: {aimless['status']} ({aimless['reason']})", file=sys.stderr)
    if aimless["log"]:
        print(f"# aimless log: {aimless['log']}", file=sys.stderr)

    stats = run_ctruncate(args.mtz, args.columns, logdir)
    print(f"# ctruncate log: {stats['log']}", file=sys.stderr)
    print(f"# parsed: {stats}", file=sys.stderr)

    print(render_yaml(stats, args.eval_id, aimless))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
