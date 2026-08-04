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
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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
    # Decide on what follows the header, not on the header itself. ctruncate prints
    # "Twin fraction estimates by twinning operator" UNCONDITIONALLY and then says
    # either "No operators found" or lists a table -- so the header's presence is not
    # evidence of anything. Keying on it gave the right answer only because the
    # first-principles literal below happened to match first; reword that one line in
    # a later ctruncate and a "No operators found" log reported operators (#121).
    # EVERY occurrence, not just the first (#137). Keying on `re.search` would let a
    # leading "No operators found" section mask a later one carrying a real table --
    # the same shape of unexamined premise as the header-presence test this replaced.
    headers = list(re.finditer(r"Twin fraction estimates by twinning operator[^\n]*\n", text))
    if headers:
        out["twin_operators_found"] = int(any(
            not re.match(r"\s*No operators found", text[h.end():]) for h in headers))
    else:
        # No section at all: fall back to ctruncate's first-principles line if present,
        # and otherwise report none rather than inventing a result.
        out["twin_operators_found"] = 0

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

@dataclass
class Measurement:
    """One EvaluationMeasurement row emitted by the T13 oracle.

    `suffix` is appended to `<eval_id>_M_t13_` to form the row id; `value`
    is written as `value_numeric` when `kind == "numeric"` and as
    `value_text` otherwise.
    """

    suffix: str
    metric_definition_ref: str
    value: Any
    kind: str = "numeric"
    unit: str | None = None
    pass_criterion: str = "informational"
    pass_status: str = "informational"
    notes: str | None = None
    oracle_tool_ref: str = "ctruncate"

    def to_row(self, eval_id: str) -> dict[str, Any]:
        """Render as a plain dict in the field order the EVAL YAML uses."""
        measure: dict[str, Any] = {}
        if self.kind == "numeric":
            measure["value_numeric"] = self.value
        else:
            measure["value_text"] = self.value
        if self.unit:
            measure["unit"] = self.unit

        row: dict[str, Any] = {
            "id": f"{eval_id}_M_t13_{self.suffix}",
            "catalog_task_ref": "T13",
            "stage": "all",
            "metric_definition_ref": self.metric_definition_ref,
            "oracle_tool_ref": self.oracle_tool_ref,
            "oracle_family": "non_cctbx",
            "agent_claim": {"is_not_applicable": True},
            "oracle_measure": measure,
            "pass_criterion": self.pass_criterion,
            "pass_status": self.pass_status,
        }
        if self.notes:
            row["notes"] = self.notes
        return row


def build_measurements(stats: dict, aimless: dict) -> list[Measurement]:
    """Select the measurement rows supported by what ctruncate reported."""
    measurements: list[Measurement] = []

    if "wilson_b" in stats:
        measurements.append(Measurement(
            suffix="wilson_b",
            metric_definition_ref="T13_wilson_b",
            value=stats["wilson_b"],
            unit="Å²",
            notes=(f"ctruncate Wilson scaling; "
                   f"sigma {stats.get('wilson_b_sigma', '?')}."),
        ))

    if "twin_fraction_l" in stats:
        measurements.append(Measurement(
            suffix="twin_fraction_l",
            metric_definition_ref="T13_l-test_twinning",
            value=stats["twin_fraction_l"],
            unit="fraction",
            pass_criterion="< 0.05",
            pass_status="pass" if stats["twin_fraction_l"] < 0.05 else "fail",
            notes=(f"L statistic {stats.get('l_statistic')} (untwinned 0.5, "
                   f"perfect twin 0.375); moments-based estimate "
                   f"{stats.get('twin_fraction_moments')}; "
                   f"first-principles twin operators found: "
                   f"{stats.get('twin_operators_found')}."),
        ))

    if "delta_b_aniso" in stats:
        measurements.append(Measurement(
            suffix="delta_b_aniso",
            metric_definition_ref="T13_anisotropy_δb_aniso",
            value=round(stats["delta_b_aniso"], 3),
            unit="Å²",
            pass_criterion="< 20 Å² (rough rule of thumb)",
            pass_status="pass" if stats["delta_b_aniso"] < 20 else "fail",
            notes=(f"ctruncate anisotropy eigenvalues "
                   f"{stats.get('aniso_eigenvalues')}; "
                   f"flag = {stats.get('aniso_flag')}."),
        ))

    if "tncs_flag" in stats:
        measurements.append(Measurement(
            suffix="tncs_flag",
            metric_definition_ref="T13_tncs_flag",
            value=str(bool(stats["tncs_flag"])).lower(),
            kind="text",
            pass_criterion="false",
            pass_status="pass" if not stats["tncs_flag"] else "fail",
            notes="ctruncate Patterson search at 4 Å resolution limit.",
        ))

    if "ice_ring_resolutions_flagged" in stats:
        flagged = stats["ice_ring_resolutions_flagged"]
        measurements.append(Measurement(
            suffix="ice_ring_flags",
            metric_definition_ref="T13_ice-ring_flags",
            value=(",".join(f"{r:.2f}Å" for r in flagged) if flagged else "none"),
            kind="text",
            pass_criterion="no flagged rings (Z > 5)",
            pass_status="pass" if not flagged else "informational",
            notes=(f"ctruncate ice-ring summary: "
                   f"{stats.get('ice_ring_count_total')} "
                   f"sensitive bins scanned; "
                   f"{len(flagged)} flagged at Z-score > 5. "
                   f"Borderline rings near 3.44 Å are common and not necessarily "
                   f"actionable; surface as informational."),
        ))

    # Provenance row about the aimless attempt
    measurements.append(Measurement(
        suffix="aimless_attempt",
        metric_definition_ref="T13_aimless_status",
        value=aimless["status"],
        kind="text",
        oracle_tool_ref="CCP4 aimless",
        notes=aimless["reason"],
    ))

    return measurements


def render_yaml(stats: dict, eval_id: str, aimless: dict) -> str:
    """Produce the snippet of measurement rows for the EVAL yaml."""
    rows = [m.to_row(eval_id) for m in build_measurements(stats, aimless)]
    body = yaml.safe_dump(
        rows,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        # Never fold long notes onto continuation lines: the fragment is
        # pasted into an EVAL file by hand and must stay one row per field.
        width=10 ** 9,
    )
    # Two-space lead-in so the block drops straight under `measurements:`.
    return textwrap.indent(body, "  ")


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
