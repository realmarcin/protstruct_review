#!/usr/bin/env python3
"""
Generate landscape SVG slides summarising the 2026-05-01 1SAR refinement review.

Output dimensions: 1920 x 1080 (16:9 landscape).
No external Python deps; SVG is built as text. rsvg-convert merges to PDF.
"""
from pathlib import Path
from textwrap import dedent

W, H = 1920, 1080

# Palette
BG = "#ffffff"
INK = "#1a1a2e"
MUTED = "#5a6071"
ACCENT = "#1f4e8c"          # primary blue
ACCENT_LIGHT = "#dce6f4"
GOOD = "#1f7a3f"
GOOD_LIGHT = "#dff0e1"
WARN = "#b07c00"
WARN_LIGHT = "#fbeecb"
BAD = "#a8201a"
BAD_LIGHT = "#f5d6d4"
GRID = "#e3e6ee"
ROW_ALT = "#f7f8fb"

REVIEW_DATE = "2026-05-04"
DECK_DATE = "2026-05-04"

OUT = Path(__file__).parent / "svg"
OUT.mkdir(parents=True, exist_ok=True)


def svg_open(width=W, height=H):
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="Helvetica, Arial, sans-serif">\n'
        f'  <rect width="100%" height="100%" fill="{BG}"/>\n'
    )


def svg_close():
    return "</svg>\n"


def header(title, subtitle=None):
    """Top banner: thin colored stripe, title, subtitle, deck-wide footer line."""
    out = []
    # Top accent stripe
    out.append(f'  <rect x="0" y="0" width="{W}" height="6" fill="{ACCENT}"/>')
    # Title
    out.append(
        f'  <text x="80" y="86" font-size="44" font-weight="700" fill="{INK}">{escape(title)}</text>'
    )
    if subtitle:
        out.append(
            f'  <text x="80" y="128" font-size="22" font-weight="400" fill="{MUTED}">{escape(subtitle)}</text>'
        )
    # Bottom footer line
    out.append(f'  <line x1="80" y1="{H-60}" x2="{W-80}" y2="{H-60}" stroke="{GRID}" stroke-width="1"/>')
    out.append(
        f'  <text x="80" y="{H-30}" font-size="16" fill="{MUTED}">'
        f'1SAR refinement review · openscientist artefact cdba2c07 · review {REVIEW_DATE}</text>'
    )
    out.append(
        f'  <text x="{W-80}" y="{H-30}" font-size="16" fill="{MUTED}" text-anchor="end">'
        f'protstruct_review · deck {DECK_DATE}</text>'
    )
    return "\n".join(out) + "\n"


def escape(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def table(x, y, col_widths, header_row, data_rows, row_height=42,
          header_fill=ACCENT, header_text="#ffffff",
          cell_fills=None, cell_text_colors=None,
          font_size=20, header_font_size=20, header_weight="700",
          align=None):
    """Render a styled table. cell_fills/cell_text_colors are 2D lists matching data_rows."""
    out = []
    n_cols = len(col_widths)
    total_w = sum(col_widths)
    align = align or ["left"] * n_cols

    # Header row
    cur_x = x
    out.append(f'  <rect x="{x}" y="{y}" width="{total_w}" height="{row_height}" fill="{header_fill}"/>')
    for i, cell in enumerate(header_row):
        cw = col_widths[i]
        if align[i] == "center":
            tx, anchor = cur_x + cw / 2, "middle"
        elif align[i] == "right":
            tx, anchor = cur_x + cw - 14, "end"
        else:
            tx, anchor = cur_x + 14, "start"
        out.append(
            f'  <text x="{tx}" y="{y + row_height/2 + header_font_size/3}" '
            f'font-size="{header_font_size}" font-weight="{header_weight}" '
            f'fill="{header_text}" text-anchor="{anchor}">{escape(cell)}</text>'
        )
        cur_x += cw

    # Data rows
    for r, row in enumerate(data_rows):
        ry = y + row_height * (r + 1)
        # Row stripe
        bg = ROW_ALT if r % 2 == 1 else BG
        out.append(f'  <rect x="{x}" y="{ry}" width="{total_w}" height="{row_height}" fill="{bg}"/>')
        cur_x = x
        for c, cell in enumerate(row):
            cw = col_widths[c]
            # Per-cell fill (overrides stripe)
            if cell_fills and cell_fills[r][c]:
                out.append(
                    f'  <rect x="{cur_x}" y="{ry}" width="{cw}" height="{row_height}" '
                    f'fill="{cell_fills[r][c]}"/>'
                )
            color = INK
            if cell_text_colors and cell_text_colors[r][c]:
                color = cell_text_colors[r][c]
            if align[c] == "center":
                tx, anchor = cur_x + cw / 2, "middle"
            elif align[c] == "right":
                tx, anchor = cur_x + cw - 14, "end"
            else:
                tx, anchor = cur_x + 14, "start"
            out.append(
                f'  <text x="{tx}" y="{ry + row_height/2 + font_size/3}" '
                f'font-size="{font_size}" fill="{color}" text-anchor="{anchor}">{escape(cell)}</text>'
            )
            cur_x += cw

    # Outer border
    total_h = row_height * (len(data_rows) + 1)
    out.append(
        f'  <rect x="{x}" y="{y}" width="{total_w}" height="{total_h}" '
        f'fill="none" stroke="{GRID}" stroke-width="1"/>'
    )
    # Vertical separators
    cur_x = x
    for cw in col_widths[:-1]:
        cur_x += cw
        out.append(
            f'  <line x1="{cur_x}" y1="{y}" x2="{cur_x}" y2="{y+total_h}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
    return "\n".join(out) + "\n"


def chip(x, y, text, fill, text_color="#ffffff", height=36, font_size=16, pad=14):
    # Approximate width: 8.5 px per char + padding
    w = max(80, int(len(text) * 8.5) + pad * 2)
    out = (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{height}" rx="6" ry="6" fill="{fill}"/>\n'
        f'  <text x="{x + w/2}" y="{y + height/2 + font_size/3}" font-size="{font_size}" '
        f'font-weight="700" fill="{text_color}" text-anchor="middle">{escape(text)}</text>\n'
    )
    return out, w


def write_svg(name, body):
    p = OUT / f"{name}.svg"
    p.write_text(svg_open() + body + svg_close())
    return p


# ------------------------------------------------------------------
# Slide 01 - Title
# ------------------------------------------------------------------
def slide_01_title():
    body = []
    # Big colored band
    body.append(f'  <rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>')
    body.append(f'  <rect x="0" y="0" width="{W}" height="240" fill="{ACCENT}"/>')
    body.append(f'  <rect x="0" y="240" width="{W}" height="14" fill="{ACCENT_LIGHT}"/>')

    body.append(
        f'  <text x="80" y="170" font-size="64" font-weight="700" fill="#ffffff">'
        f'1SAR refinement — independent re-review</text>'
    )
    body.append(
        f'  <text x="80" y="220" font-size="28" font-weight="400" fill="#dce6f4">'
        f'protstruct_review · openscientist artefact cdba2c07-daff-4f60-ae96-12452b3a5fbb</text>'
    )

    # Body block
    body.append(
        f'  <text x="80" y="370" font-size="34" font-weight="600" fill="{INK}">'
        f'Mostly pass · cross-tool coverage now fully closed</text>'
    )
    body.append(
        f'  <text x="80" y="420" font-size="22" fill="{MUTED}">'
        f'Ten independent oracle code paths · eight non-cctbx · all load-bearing findings ≥ 3-tool confirmed</text>'
    )

    # Bullet points (key new since prior round)
    bullets = [
        ("R-free reproducibly ≈ 0.21, not 0.199 (PHENIX 0.211 · gemmi 0.217 · REFMAC 0.213)", BAD),
        ("Round 6 R-free 0.207 better than round 7 R-free 0.213 — claim reversed", BAD),
        ("Asn A 39 is a Ramachandran outlier (3-tool confirmed)", BAD),
        ("Density-peak inventory incomplete — oracle 23+ / 8− at 4σ; agent listed 9", BAD),
        ("Mg²⁺ excluded for both ions by CheckMyMetal-style |Z| 14–16", GOOD),
        ("Ligand / metal density support confirmed (RSCC ≥ 0.96)", GOOD),
        ("T13 data quality clean — no twinning · no tNCS · ΔB aniso 7.3 Å² (new)", GOOD),
    ]
    yb = 490
    for i, (txt, color) in enumerate(bullets):
        ry = yb + i * 56
        body.append(f'  <circle cx="100" cy="{ry-7}" r="8" fill="{color}"/>')
        body.append(
            f'  <text x="125" y="{ry}" font-size="22" fill="{INK}">{escape(txt)}</text>'
        )

    # Date footer
    body.append(
        f'  <text x="80" y="{H-110}" font-size="20" fill="{MUTED}">'
        f'Review issued {REVIEW_DATE} · slide deck compiled {DECK_DATE}</text>'
    )
    body.append(
        f'  <text x="80" y="{H-70}" font-size="18" fill="{MUTED}">'
        f'Trust model: cross-tool agreement, never PHENIX-grading-PHENIX</text>'
    )
    body.append(f'  <rect x="0" y="{H-30}" width="{W}" height="30" fill="{ACCENT}"/>')
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 02 - Oracle stack
# ------------------------------------------------------------------
def slide_02_oracles():
    body = [header(
        "Oracle stack — 10 independent code paths",
        "8 non-cctbx · trust comes from cross-family agreement, not from any single tool"
    )]

    # Group 1: cctbx
    body.append(
        f'  <text x="80" y="200" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'cctbx family (1)</text>'
    )
    cctbx = ["PHENIX (mmtbx · phenix.* binaries)"]
    for i, t in enumerate(cctbx):
        body.append(
            f'  <rect x="80" y="{220 + i*48}" width="600" height="40" rx="6" fill="{ACCENT_LIGHT}"/>\n'
            f'  <text x="100" y="{248 + i*48}" font-size="20" fill="{INK}">{escape(t)}</text>'
        )

    # Group 2: non-cctbx
    body.append(
        f'  <text x="80" y="320" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'non-cctbx (9 binaries across 8 code paths)</text>'
    )
    nons = [
        ("MolProbity standalone", "Richardson lab — probe + reduce"),
        ("TM-align", "Zhang lab — sequence-independent superposition"),
        ("gemmi", "Global Phasing / CCP4 — sfcalc, R-factors, RMSD"),
        ("Servalcat", "Murshudov — sigmaa, σ_A maps"),
        ("OpenStructure (OST)", "SIB — lDDT, structure assessment"),
        ("REFMAC5", "CCP4 — independent refinement engine, NCYC=0 R-factors"),
        ("ProSMART", "CCP4 / Murshudov — Procrustes geometry analysis"),
        ("CheckMyMetal-local", "Zheng-criteria geometry classifier (local heuristic)"),
        ("ctruncate (NEW)", "CCP4 — Wilson B · L-test twinning · ΔB aniso · tNCS · ice rings"),
    ]
    for i, (name, desc) in enumerate(nons):
        ry = 340 + i * 44
        body.append(
            f'  <rect x="80" y="{ry}" width="380" height="38" rx="6" fill="{GOOD_LIGHT}"/>'
            f'\n  <text x="100" y="{ry+27}" font-size="18" font-weight="700" fill="{INK}">{escape(name)}</text>'
            f'\n  <text x="480" y="{ry+27}" font-size="17" fill="{MUTED}">{escape(desc)}</text>'
        )

    # Right panel: coverage matrix
    body.append(
        f'  <text x="1100" y="200" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'Cross-tool coverage by task — fully closed</text>'
    )
    headers = ["Task", "cctbx", "non-cctbx", "Status"]
    rows = [
        ["T01 RMSD/superpose", "phenix.superpose_models", "TM-align · gemmi · OST · ProSMART", "closed"],
        ["T03 R-factors", "phenix.model_vs_data", "gemmi · Servalcat · REFMAC5", "closed"],
        ["T05 Geometry", "mmtbx.validation_summary", "MolProbity · ProSMART · REFMAC5", "closed"],
        ["T06 Density fit", "phenix.real_space_correlation", "gemmi · Servalcat", "closed"],
        ["T10 Ligand / metal", "phenix.real_space_correlation", "CheckMyMetal-local", "closed"],
        ["T13 Data quality", "phenix.model_vs_data", "ctruncate · CCP4 aimless", "closed"],
    ]
    fills = []
    for r in rows:
        c = GOOD
        cf = [None, None, None, c]
        fills.append(cf)
    txt = []
    for r in rows:
        tc = "#ffffff"
        txt.append([None, None, None, tc])
    body.append(
        table(1100, 230, [200, 240, 250, 90], headers, rows,
              row_height=46, font_size=15, header_font_size=18,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "left", "left", "center"])
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 03 - Headline verdict
# ------------------------------------------------------------------
def slide_03_verdict():
    body = [header(
        "Headline verdict",
        "Mostly pass · 3 triangulated discrepancies · K⁺ alternative still open · cross-tool coverage closed"
    )]

    # Big top card
    body.append(
        f'  <rect x="80" y="180" width="{W-160}" height="120" rx="10" '
        f'fill="{ACCENT_LIGHT}" stroke="{ACCENT}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="120" y="240" font-size="32" font-weight="700" fill="{INK}">'
        f'1SAR is a real and substantial improvement over the deposited starting model.</text>'
    )
    body.append(
        f'  <text x="120" y="278" font-size="22" fill="{MUTED}">'
        f'Modelling decisions on structure, geometry, ion identity (Mg²⁺ excluded), water, disulfides — all defensible.</text>'
    )

    # Two-column: Closed in this re-issue | Still holds
    body.append(
        f'  <text x="80" y="350" font-size="26" font-weight="700" fill="{GOOD}">'
        f'Closed across the 04-30 / 05-01 / 05-04 re-issues</text>'
    )
    closed = [
        "Mg²⁺ alternative ruled out — CheckMyMetal-style |Z| 16.35",
        "Ligand / metal density support confirmed — RSCC ≥ 0.96",
        "T13 data-quality cross-tool gap closed — ctruncate (NEW 05-04)",
    ]
    for i, t in enumerate(closed):
        ry = 380 + i * 50
        body.append(
            f'  <rect x="80" y="{ry}" width="850" height="40" rx="6" fill="{GOOD_LIGHT}"/>\n'
            f'  <text x="100" y="{ry+27}" font-size="20" fill="{INK}">✓ {escape(t)}</text>'
        )

    body.append(
        f'  <text x="980" y="350" font-size="26" font-weight="700" fill="{BAD}">'
        f'Still discrepant (3-tool confirmed)</text>'
    )
    still = [
        "R-free reproducibly ≈ 0.21, agent reports 0.199",
        "Round 6 R-free 0.207 < round 7 R-free 0.213",
        "Asn A 39 is a Ramachandran outlier",
        "Density-peak inventory incomplete (23+ / 8− vs 9 listed)",
    ]
    for i, t in enumerate(still):
        ry = 380 + i * 50
        body.append(
            f'  <rect x="980" y="{ry}" width="860" height="40" rx="6" fill="{BAD_LIGHT}"/>\n'
            f'  <text x="1000" y="{ry+27}" font-size="20" fill="{INK}">✗ {escape(t)}</text>'
        )

    # Bottom: open question
    body.append(
        f'  <text x="80" y="640" font-size="26" font-weight="700" fill="{WARN}">'
        f'Open question</text>'
    )
    body.append(
        f'  <rect x="80" y="660" width="{W-160}" height="100" rx="10" fill="{WARN_LIGHT}" '
        f'stroke="{WARN}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="700" font-size="22" font-weight="700" fill="{INK}">'
        f'K⁺ alternative for both ions</text>'
    )
    body.append(
        f'  <text x="100" y="734" font-size="20" fill="{INK}">'
        f'K⁺ has the best raw bond-length fit (|Z| 0.13–0.44) but coordination number is too low for K⁺ canonical, '
        f'and the protein is a known Ca²⁺ enzyme. Needs crystallisation buffer information.</text>'
    )

    # Per-criterion summary
    body.append(
        f'  <text x="80" y="820" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'Net acceptance against agent’s own success criteria — 3 / 6 pass cleanly</text>'
    )
    summary = [
        ("R-free improvement", "✓ pass", GOOD),
        ("R-free gap < 0.05", "⚠ oracle fails", BAD),
        ("Ramachandran < 1%", "✓ headline wrong", WARN),
        ("Clashscore < 5", "✓ pass", GOOD),
        ("No Δρ > 4σ", "✗ fails", BAD),
        ("Data quality (T13)", "✓ pass (NEW)", GOOD),
    ]
    cx = 80
    cw = (W - 160 - 5 * 20) // 6
    for label, val, color in summary:
        body.append(
            f'  <rect x="{cx}" y="850" width="{cw}" height="100" rx="10" fill="{BG}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        body.append(
            f'  <text x="{cx+15}" y="894" font-size="18" font-weight="600" fill="{INK}">{escape(label)}</text>'
        )
        body.append(
            f'  <text x="{cx+15}" y="924" font-size="17" fill="{color}" font-weight="700">{escape(val)}</text>'
        )
        cx += cw + 20
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 04 - 7-step skill checklist + sub-checklist
# ------------------------------------------------------------------
def slide_04_checklist():
    body = [header(
        "Skill checklist — protstruct-eval applied end-to-end",
        "All 8 steps green (step 8 new in this re-issue) · plus water / ligand / metal sub-checklist"
    )]

    headers = ["#", "Step", "Result"]
    rows = [
        ["1", "Re-derive R-factors with phenix.model_vs_data",
         "agent 0.149 / 0.199 · oracle 0.156 / 0.211"],
        ["2", "Re-extract atom + water counts",
         "atoms 1641 vs 1654 · waters 146 vs 159 · both Δ −13"],
        ["3", "Re-run peak finder at 4σ",
         "23 + / 8 − · agent listed 9 · max +6.18σ"],
        ["4", "Verify quoted coordinates",
         "Ca²⁺ position 0.215 Å off (initial placement, not final)"],
        ["5", "Anomalous-data check",
         "none in 1sar.mtz · closed by CheckMyMetal-style geometry"],
        ["6", "Per-round Δ-claim", "round 6 R-free 0.207 < round 7 0.213"],
        ["7", "Non-cctbx confirmation per finding",
         "8 / 10 oracles tagged · cross_tool_coverage all closed"],
        ["8", "T13 data-quality oracle (NEW)",
         "ctruncate: Wilson B 14.5 · L-test 0.03 · ΔB 7.3 · no tNCS · 1 borderline ice ring"],
    ]
    body.append(
        table(80, 190, [60, 580, 820], headers, rows,
              row_height=46, font_size=17, header_font_size=20,
              align=["center", "left", "left"])
    )

    body.append(
        f'  <text x="80" y="640" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'Water / ligand / metal sub-checklist</text>'
    )

    sub_h = ["Check", "Done", "Result"]
    sub_rows = [
        ["Per-ion RSCC", "✓", "Ca²⁺ 0.972 · Na⁺ 0.964 · SO4 0.988 — all > 0.85"],
        ["Per-ion B-vs-protein", "✓", "Ca²⁺ 2.67× · Na⁺ 1.43× · SO4 1.10×"],
        ["Coordination geometry", "✓", "CN = 3 inner-sphere both ions (low — partial-occ framing)"],
        ["Element identity (geometry)", "✓", "CheckMyMetal-style: Mg²⁺ ruled out by |Z| 14–16"],
        ["Element identity (anomalous)", "n/a", "no anomalous columns in 1sar.mtz"],
        ["Per-water B + RSCC distribution", "✓", "mean B 20.76 · mean RSCC 0.867 · 3 waters RSCC < 0.7"],
        ["Density-misfit ResidueOutliers", "✓", "HOH S 680, 707, 729"],
    ]

    fills = []
    txt = []
    for r in sub_rows:
        d = r[1]
        if d == "✓":
            fills.append([None, GOOD, None])
            txt.append([None, "#ffffff", None])
        elif d == "n/a":
            fills.append([None, MUTED, None])
            txt.append([None, "#ffffff", None])
        else:
            fills.append([None, None, None])
            txt.append([None, None, None])
    body.append(
        table(80, 670, [400, 80, 980], sub_h, sub_rows,
              row_height=44, font_size=18, header_font_size=20,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "center", "left"])
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 05 - T01 RMSD bracket + lDDT
# ------------------------------------------------------------------
def slide_05_t01():
    body = [header(
        "T01 — Superposition · RMSD bracket [0.41, 0.48 Å]",
        "Four tools converge · OST lDDT 0.9725 · Gly A 34 lowest-lDDT residue, also gemmi’s biggest Cα displacement"
    )]

    headers = ["Tool", "RMSD (Å)", "Family"]
    rows = [
        ["TM-align", "0.41", "non_cctbx"],
        ["gemmi", "0.42", "non_cctbx"],
        ["phenix.superpose_models", "0.43", "cctbx"],
        ["ProSMART", "0.475", "non_cctbx"],
        ["Agent", "0.438", "—"],
    ]
    fills = []
    txt = []
    for r in rows:
        f = r[2]
        if f == "non_cctbx":
            fills.append([None, None, GOOD])
            txt.append([None, None, "#ffffff"])
        elif f == "cctbx":
            fills.append([None, None, ACCENT])
            txt.append([None, None, "#ffffff"])
        else:
            fills.append([None, None, MUTED])
            txt.append([None, None, "#ffffff"])
    body.append(
        table(80, 220, [380, 200, 220], headers, rows,
              row_height=52, font_size=20, header_font_size=22,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "right", "center"])
    )

    # Visual: number-line of the RMSD bracket
    base_x = 900
    base_y = 320
    body.append(
        f'  <text x="{base_x}" y="240" font-size="22" font-weight="700" fill="{ACCENT}">'
        f'RMSD bracket (Å)</text>'
    )
    # Axis from 0.40 to 0.50
    axis_x0, axis_x1 = base_x, base_x + 800
    axis_y = base_y + 60
    body.append(
        f'  <line x1="{axis_x0}" y1="{axis_y}" x2="{axis_x1}" y2="{axis_y}" '
        f'stroke="{INK}" stroke-width="2"/>'
    )
    for v, label in [(0.40, "0.40"), (0.42, "0.42"), (0.44, "0.44"),
                     (0.46, "0.46"), (0.48, "0.48"), (0.50, "0.50")]:
        x = axis_x0 + (v - 0.40) / 0.10 * (axis_x1 - axis_x0)
        body.append(
            f'  <line x1="{x}" y1="{axis_y-6}" x2="{x}" y2="{axis_y+6}" stroke="{INK}" stroke-width="2"/>'
            f'\n  <text x="{x}" y="{axis_y+30}" font-size="16" fill="{MUTED}" text-anchor="middle">{label}</text>'
        )
    # Range band 0.41-0.48
    x_lo = axis_x0 + (0.41 - 0.40) / 0.10 * (axis_x1 - axis_x0)
    x_hi = axis_x0 + (0.48 - 0.40) / 0.10 * (axis_x1 - axis_x0)
    body.append(
        f'  <rect x="{x_lo}" y="{axis_y-22}" width="{x_hi-x_lo}" height="44" '
        f'fill="{ACCENT_LIGHT}" stroke="{ACCENT}" stroke-width="1" opacity="0.7"/>'
    )
    # Markers
    points = [(0.41, "TM-align", GOOD),
              (0.42, "gemmi", GOOD),
              (0.43, "PHENIX", ACCENT),
              (0.475, "ProSMART", GOOD),
              (0.438, "Agent", MUTED)]
    placed = []
    for v, name, color in points:
        x = axis_x0 + (v - 0.40) / 0.10 * (axis_x1 - axis_x0)
        # Stagger labels above/below alternately
        idx = len(placed)
        ly = axis_y - 50 if idx % 2 == 0 else axis_y + 70
        body.append(
            f'  <circle cx="{x}" cy="{axis_y}" r="9" fill="{color}" stroke="#ffffff" stroke-width="2"/>'
            f'\n  <text x="{x}" y="{ly}" font-size="16" fill="{INK}" text-anchor="middle" '
            f'font-weight="700">{escape(name)}</text>'
        )
        placed.append((x, ly))

    # lDDT box
    body.append(
        f'  <rect x="80" y="640" width="{W-160}" height="280" rx="10" fill="{ACCENT_LIGHT}" '
        f'stroke="{ACCENT}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="690" font-size="26" font-weight="700" fill="{INK}">'
        f'OST lDDT (global) = 0.9725</text>'
    )
    body.append(
        f'  <text x="100" y="730" font-size="20" fill="{INK}">'
        f'Local structure preserved start → final.</text>'
    )
    body.append(
        f'  <text x="100" y="772" font-size="20" fill="{INK}">'
        f'Lowest per-residue lDDT: <tspan font-weight="700">Gly A 34 = 0.878</tspan> '
        f'(also gemmi’s biggest Cα displacement at 0.955 Å — same residue, two metrics, two code bases).</text>'
    )
    body.append(
        f'  <text x="100" y="820" font-size="20" fill="{MUTED}">'
        f'Five superposition oracles across two code families. Agent’s 0.438 Å sits inside the bracket.</text>'
    )
    body.append(
        f'  <text x="100" y="862" font-size="18" fill="{MUTED}">'
        f'Tools: TM-align (Zhang) · gemmi (CCP4) · phenix.superpose_models (cctbx) · ProSMART (CCP4) · OST (SIB)'
        f'</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 06 - T03 R-factor table
# ------------------------------------------------------------------
def slide_06_t03_rfactors():
    body = [header(
        "T03 — Reciprocal-space R-factors · 3 tools converge",
        "Agent’s 0.199 R-free is 0.012 below the lower bound · catalog oracle (PHENIX) → R-free gap fails < 0.05"
    )]

    headers = ["Tool", "R-work", "R-free", "Gap"]
    rows = [
        ["phenix.model_vs_data", "0.156", "0.211", "0.055"],
        ["gemmi sfcalc + custom", "0.164", "0.217", "0.053"],
        ["REFMAC5 (NCYC=0)", "0.169", "0.213", "0.044"],
        ["Agent (reported)", "0.149", "0.199", "0.050"],
    ]
    fills = []
    txt = []
    for r in rows:
        if r[0].startswith("Agent"):
            fills.append([WARN_LIGHT, WARN_LIGHT, BAD_LIGHT, WARN_LIGHT])
            txt.append([INK, INK, BAD, INK])
        else:
            fills.append([None]*4)
            txt.append([None]*4)
    body.append(
        table(80, 220, [430, 200, 200, 200], headers, rows,
              row_height=58, font_size=22, header_font_size=22,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "right", "right", "right"])
    )

    # R-free dot plot
    base_x = 1180
    base_y = 280
    body.append(
        f'  <text x="{base_x}" y="240" font-size="22" font-weight="700" fill="{ACCENT}">'
        f'R-free across oracles</text>'
    )
    axis_x0, axis_x1 = base_x, base_x + 600
    axis_y = base_y + 80
    body.append(
        f'  <line x1="{axis_x0}" y1="{axis_y}" x2="{axis_x1}" y2="{axis_y}" '
        f'stroke="{INK}" stroke-width="2"/>'
    )
    lo, hi = 0.195, 0.220
    for v in [0.195, 0.200, 0.205, 0.210, 0.215, 0.220]:
        x = axis_x0 + (v - lo) / (hi - lo) * (axis_x1 - axis_x0)
        body.append(
            f'  <line x1="{x}" y1="{axis_y-5}" x2="{x}" y2="{axis_y+5}" stroke="{INK}" stroke-width="1"/>'
            f'\n  <text x="{x}" y="{axis_y+25}" font-size="14" fill="{MUTED}" text-anchor="middle">{v:.3f}</text>'
        )
    pts = [
        (0.199, "Agent", BAD),
        (0.211, "PHENIX", ACCENT),
        (0.213, "REFMAC5", GOOD),
        (0.217, "gemmi", GOOD),
    ]
    for i, (v, name, color) in enumerate(pts):
        x = axis_x0 + (v - lo) / (hi - lo) * (axis_x1 - axis_x0)
        ly = axis_y - 40 if i % 2 == 0 else axis_y - 60
        body.append(
            f'  <circle cx="{x}" cy="{axis_y}" r="9" fill="{color}" stroke="#ffffff" stroke-width="2"/>'
            f'\n  <text x="{x}" y="{ly}" font-size="16" fill="{INK}" text-anchor="middle" font-weight="700">'
            f'{escape(name)} {v:.3f}</text>'
        )

    # Two callout panels
    body.append(
        f'  <rect x="80" y="540" width="880" height="200" rx="10" fill="{BAD_LIGHT}" '
        f'stroke="{BAD}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="585" font-size="24" font-weight="700" fill="{BAD}">'
        f'R-free under-statement is reproducible</text>'
    )
    body.append(
        f'  <text x="100" y="625" font-size="18" fill="{INK}">'
        f'Three independent code paths converge on R-free ≈ 0.21.</text>'
    )
    body.append(
        f'  <text x="100" y="655" font-size="18" fill="{INK}">'
        f'Likely cause: <tspan font-weight="700">phenix.refine in-run scaling vs catalog-oracle scaling</tspan>.</text>'
    )
    body.append(
        f'  <text x="100" y="685" font-size="18" fill="{INK}">'
        f'Mitigation: report from phenix.model_vs_data, not from refine’s log.</text>'
    )
    body.append(
        f'  <text x="100" y="720" font-size="16" fill="{MUTED}">'
        f'ASSUM_phenix_refine_in_run_r_factors_use_internal_scaling — known_violation hardened.</text>'
    )

    body.append(
        f'  <rect x="980" y="540" width="860" height="200" rx="10" fill="{WARN_LIGHT}" '
        f'stroke="{WARN}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="1000" y="585" font-size="24" font-weight="700" fill="{WARN}">'
        f'R-free gap criterion is scaling-dependent</text>'
    )
    body.append(
        f'  <text x="1000" y="625" font-size="18" fill="{INK}">'
        f'PHENIX gap 0.055 (✗) · gemmi 0.053 (✗) · REFMAC5 0.044 (✓)</text>'
    )
    body.append(
        f'  <text x="1000" y="660" font-size="18" fill="{INK}">'
        f'Catalog oracle of record = phenix.model_vs_data → fails &lt; 0.05.</text>'
    )
    body.append(
        f'  <text x="1000" y="700" font-size="18" fill="{INK}">'
        f'Reportable as a <tspan font-weight="700">scaling-sensitive failure</tspan>, not a raw R-free defect.</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 07 - Per-round trajectory (bar chart)
# ------------------------------------------------------------------
def slide_07_per_round():
    body = [header(
        "T03 — Per-round trajectory · oracle re-measurement",
        "Round 6 R-free 0.207 beats round 7 R-free 0.213 · NCS-torsion claim doesn’t reproduce at oracle scaling"
    )]

    rounds = [
        ("start", 0.333, 0.396),
        ("2",     0.169, 0.230),
        ("3",     0.159, 0.216),
        ("5",     0.156, 0.210),
        ("6",     0.154, 0.207),
        ("7 final", 0.156, 0.213),
    ]

    # Chart area
    chart_x = 120
    chart_y = 220
    chart_w = 1100
    chart_h = 540
    body.append(
        f'  <rect x="{chart_x}" y="{chart_y}" width="{chart_w}" height="{chart_h}" '
        f'fill="{BG}" stroke="{GRID}" stroke-width="1"/>'
    )
    # y axis 0.10-0.40
    y_lo, y_hi = 0.10, 0.40
    plot_x0 = chart_x + 100
    plot_x1 = chart_x + chart_w - 30
    plot_y0 = chart_y + 30
    plot_y1 = chart_y + chart_h - 60

    def y_to_px(v):
        return plot_y1 - (v - y_lo) / (y_hi - y_lo) * (plot_y1 - plot_y0)

    # Horizontal grid lines
    for v in [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
        py = y_to_px(v)
        body.append(
            f'  <line x1="{plot_x0}" y1="{py}" x2="{plot_x1}" y2="{py}" stroke="{GRID}" stroke-width="1"/>'
            f'\n  <text x="{plot_x0-12}" y="{py+5}" font-size="14" fill="{MUTED}" text-anchor="end">{v:.2f}</text>'
        )

    # X positions
    n = len(rounds)
    plot_w = plot_x1 - plot_x0
    group_w = plot_w / n
    bar_w = 36
    for i, (lab, rw, rf) in enumerate(rounds):
        cx = plot_x0 + group_w * (i + 0.5)
        # R-work bar
        rw_y = y_to_px(rw)
        rf_y = y_to_px(rf)
        body.append(
            f'  <rect x="{cx-bar_w-4}" y="{rw_y}" width="{bar_w}" height="{plot_y1-rw_y}" '
            f'fill="{ACCENT}"/>'
            f'\n  <text x="{cx-bar_w/2-4}" y="{rw_y-6}" font-size="14" fill="{ACCENT}" '
            f'text-anchor="middle" font-weight="700">{rw:.3f}</text>'
        )
        # R-free bar
        body.append(
            f'  <rect x="{cx+4}" y="{rf_y}" width="{bar_w}" height="{plot_y1-rf_y}" '
            f'fill="{BAD}"/>'
            f'\n  <text x="{cx+bar_w/2+4}" y="{rf_y-6}" font-size="14" fill="{BAD}" '
            f'text-anchor="middle" font-weight="700">{rf:.3f}</text>'
        )
        body.append(
            f'  <text x="{cx}" y="{plot_y1+25}" font-size="16" fill="{INK}" '
            f'text-anchor="middle" font-weight="700">round {escape(lab)}</text>'
        )

    # Highlight round 6 vs round 7
    cx6 = plot_x0 + group_w * (4 + 0.5)
    cx7 = plot_x0 + group_w * (5 + 0.5)
    body.append(
        f'  <rect x="{cx6-bar_w-12}" y="{plot_y0-4}" width="{cx7+bar_w+8 - (cx6-bar_w-12)}" '
        f'height="{plot_y1-plot_y0+8}" fill="none" stroke="{WARN}" stroke-width="3" '
        f'stroke-dasharray="6,4" rx="6"/>'
    )

    # Legend
    body.append(
        f'  <rect x="{plot_x1-220}" y="{plot_y0+10}" width="14" height="14" fill="{ACCENT}"/>'
        f'\n  <text x="{plot_x1-200}" y="{plot_y0+22}" font-size="16" fill="{INK}">R-work (oracle)</text>'
    )
    body.append(
        f'  <rect x="{plot_x1-220}" y="{plot_y0+34}" width="14" height="14" fill="{BAD}"/>'
        f'\n  <text x="{plot_x1-200}" y="{plot_y0+46}" font-size="16" fill="{INK}">R-free (oracle)</text>'
    )

    # Side panel
    sx = chart_x + chart_w + 30
    body.append(
        f'  <rect x="{sx}" y="{chart_y}" width="{W-sx-80}" height="{chart_h}" '
        f'rx="10" fill="{WARN_LIGHT}" stroke="{WARN}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="{sx+20}" y="{chart_y+45}" font-size="22" font-weight="700" fill="{WARN}">'
        f'Round 6 → Round 7</text>'
    )
    body.append(
        f'  <text x="{sx+20}" y="{chart_y+85}" font-size="18" fill="{INK}">'
        f'R-free <tspan font-weight="700">0.207 → 0.213</tspan></text>'
    )
    body.append(
        f'  <text x="{sx+20}" y="{chart_y+115}" font-size="18" fill="{INK}">'
        f'Δ = +0.006 (worse)</text>'
    )
    body.append(
        f'  <text x="{sx+20}" y="{chart_y+165}" font-size="16" fill="{INK}">'
        f'Agent claims round-7 NCS torsion restraints reduced the gap.</text>'
    )
    body.append(
        f'  <text x="{sx+20}" y="{chart_y+200}" font-size="16" fill="{INK}">'
        f'Oracle scaling shows the opposite: a small but reproducible regression.</text>'
    )
    body.append(
        f'  <text x="{sx+20}" y="{chart_y+250}" font-size="14" fill="{MUTED}">'
        f'ASSUM_report_round_table_collapses_rounds</text>'
    )
    body.append(
        f'  <text x="{sx+20}" y="{chart_y+272}" font-size="14" fill="{MUTED}">'
        f'known_violation · hardened by per-round oracle.</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 08 - T05 Geometry validation
# ------------------------------------------------------------------
def slide_08_t05_geometry():
    body = [header(
        "T05 — Geometry validation · all metrics pass criteria",
        "Asn A 39 Ramachandran outlier confirmed by 3 independent code paths · agent’s “0.00%” rounds 1 outlier to zero"
    )]

    headers = ["Metric", "Tool", "Value", "Verdict"]
    rows = [
        ["Clashscore (cctbx)", "mmtbx.validation_summary", "3.13", "✓ < 5"],
        ["Clashscore (non-cctbx)", "MolProbity standalone", "3.63", "✓ < 5"],
        ["MolProbity composite", "mmtbx.validation_summary", "1.63", "✓ < 2"],
        ["Ramachandran outliers", "mmtbx.validation_summary", "0.53% (Asn A 39)", "✓ <1% · headline wrong"],
        ["Ramachandran favored", "mmtbx.validation_summary", "98.40%", "✓ > 98%"],
        ["Rotamer outliers", "mmtbx.validation_summary", "4.88%", "✓ < 5%"],
        ["C-β deviations", "mmtbx.validation_summary", "0", "✓"],
        ["Bond RMSZ (CCP4 dict)", "REFMAC5", "0.884 σ", "✓ < 1 σ"],
        ["Angle RMSZ (CCP4 dict)", "REFMAC5", "0.864 σ", "✓ < 1 σ"],
        ["Holton geom-energy ratio", "phenix.holton_geometry_validation", "1.33 σ (start 3.32)", "✓"],
    ]

    fills = []
    txt = []
    for r in rows:
        v = r[3]
        if v.startswith("✓ <1% · headline wrong"):
            fills.append([None, None, None, WARN])
            txt.append([None, None, None, "#ffffff"])
        elif v.startswith("✓"):
            fills.append([None, None, None, GOOD])
            txt.append([None, None, None, "#ffffff"])
        else:
            fills.append([None]*4)
            txt.append([None]*4)
    body.append(
        table(80, 200, [410, 510, 360, 380], headers, rows,
              row_height=46, font_size=18, header_font_size=20,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "left", "right", "left"])
    )

    # Side: Asn A 39 evidence card
    body.append(
        f'  <rect x="80" y="760" width="{W-160}" height="240" rx="10" fill="{WARN_LIGHT}" '
        f'stroke="{WARN}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="805" font-size="26" font-weight="700" fill="{WARN}">'
        f'Asn A 39 — Ramachandran outlier confirmed by 3 code paths</text>'
    )
    cards = [
        ("mmtbx.validation_summary", "0.53% outliers · 1 residue", ACCENT),
        ("phenix.holton_geometry_validation", "Asn A 39 flagged as outlier", ACCENT),
        ("ProSMART (non-cctbx)", "Procrustes 0.526 vs avg 0.27–0.40 · 12° hinge · MaxDist 1.31 Å", GOOD),
    ]
    cx = 100
    for name, val, color in cards:
        body.append(
            f'  <rect x="{cx}" y="830" width="580" height="140" rx="8" fill="{BG}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        body.append(
            f'  <text x="{cx+18}" y="868" font-size="18" font-weight="700" fill="{color}">{escape(name)}</text>'
        )
        body.append(
            f'  <text x="{cx+18}" y="908" font-size="18" fill="{INK}">{escape(val)}</text>'
        )
        cx += 600
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 09 - Density peaks
# ------------------------------------------------------------------
def slide_09_peaks():
    body = [header(
        "T05 — Density peaks at 4σ (phenix.find_peaks_holes)",
        "Oracle: 23 + / 8 − peaks · agent listed 9 · 5 peaks above 5σ are not in agent’s table"
    )]

    headers = ["Oracle σ", "Nearest atom", "Notes", "In agent’s table?"]
    rows = [
        ["+6.18", "Glu A 54 CD", "highest positive peak", "no"],
        ["+5.94", "HOH S 34", "near modelled water", "no"],
        ["+5.83", "Thr A 67 CG2", "side-chain density unaccounted", "no"],
        ["+5.61", "Asn A 39 CB", "matches agent’s 4.82σ near OD1", "yes"],
        ["+4.96", "HOH S 736", "matches agent’s 4.98σ entry", "yes"],
        ["−4.11", "HOH S 401", "modelled water with no density (negative peak)", "no"],
    ]
    fills = []
    txt = []
    for r in rows:
        if r[3] == "no":
            fills.append([None, None, None, BAD])
            txt.append([None, None, None, "#ffffff"])
        else:
            fills.append([None, None, None, GOOD])
            txt.append([None, None, None, "#ffffff"])
    body.append(
        table(80, 220, [180, 320, 800, 280], headers, rows,
              row_height=54, font_size=20, header_font_size=22,
              cell_fills=fills, cell_text_colors=txt,
              align=["right", "left", "left", "center"])
    )

    # Summary card
    body.append(
        f'  <rect x="80" y="640" width="{W-160}" height="320" rx="10" fill="{BAD_LIGHT}" '
        f'stroke="{BAD}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="690" font-size="28" font-weight="700" fill="{BAD}">'
        f'Density-peak inventory is incomplete — fails the success criterion</text>'
    )
    body.append(
        f'  <text x="100" y="734" font-size="20" fill="{INK}">'
        f'Agent’s success criterion: <tspan font-weight="700">no unexplained Δρ > 4σ</tspan> · '
        f'agent reports 9 peaks, max 4.98σ.</text>'
    )
    body.append(
        f'  <text x="100" y="772" font-size="20" fill="{INK}">'
        f'Oracle: <tspan font-weight="700">23 +</tspan> / <tspan font-weight="700">8 −</tspan> peaks at 4σ · max <tspan font-weight="700">+6.18σ</tspan> · '
        f'5 peaks above 5σ not surfaced.</text>'
    )
    body.append(
        f'  <text x="100" y="810" font-size="20" fill="{INK}">'
        f'Likely cause: agent’s peak-finding cutoff or merging step is more aggressive than the catalog oracle’s.</text>'
    )
    body.append(
        f'  <text x="100" y="850" font-size="18" fill="{MUTED}">'
        f'ASSUM_find_peaks_holes_cutoff_and_merging — known_violation.</text>'
    )
    body.append(
        f'  <text x="100" y="890" font-size="18" fill="{MUTED}">'
        f'Recommended remedy: re-run phenix.find_peaks_holes with map_cutoff=4.0 and accept default merging.</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 10 - T10 RSCC + B-ratio
# ------------------------------------------------------------------
def slide_10_t10_rscc():
    body = [header(
        "T10 — Ligand / metal RSCC + B-vs-protein ratio",
        "phenix.real_space_correlation · all three components have RSCC ≥ 0.96 · density excellent for retained ligands"
    )]

    headers = ["Component", "RSCC", "B (Å²)", "B / protein-mean", "Verdict"]
    rows = [
        ["Ca²⁺ A 98", "0.9716", "42.73", "2.67×",
         "density excellent · partial-occ framing consistent (long bonds + low CN + high B)"],
        ["Na⁺ B 98", "0.9636", "22.85", "1.43×",
         "density excellent · full-occupancy framing consistent"],
        ["SO4 A 97", "0.9882", "17.59", "1.10×",
         "density excellent · agent’s decision to retain confirmed"],
    ]
    body.append(
        table(80, 220, [240, 180, 180, 240, 920], headers, rows,
              row_height=70, font_size=20, header_font_size=22,
              align=["left", "right", "right", "right", "left"])
    )

    # RSCC bar visualisation
    base_x = 120
    base_y = 480
    body.append(
        f'  <text x="{base_x}" y="{base_y}" font-size="24" font-weight="700" fill="{ACCENT}">'
        f'RSCC threshold check</text>'
    )
    body.append(
        f'  <text x="{base_x}" y="{base_y+30}" font-size="16" fill="{MUTED}">'
        f'Threshold for retaining ligand / metal: RSCC > 0.85</text>'
    )

    # Bar chart axis 0.80-1.00
    bar_x0 = base_x + 220
    bar_x1 = base_x + 1500
    lo, hi = 0.80, 1.00
    # threshold line
    thr_x = bar_x0 + (0.85 - lo) / (hi - lo) * (bar_x1 - bar_x0)
    items = [
        ("Ca²⁺ A 98", 0.9716, ACCENT),
        ("Na⁺ B 98", 0.9636, ACCENT),
        ("SO4 A 97", 0.9882, ACCENT),
        ("HOH mean (146)", 0.867, MUTED),
        ("HOH S 680 (worst)", 0.658, BAD),
    ]
    for i, (name, val, color) in enumerate(items):
        ry = base_y + 80 + i * 56
        body.append(
            f'  <text x="{base_x}" y="{ry+30}" font-size="18" fill="{INK}" font-weight="600">{escape(name)}</text>'
        )
        # full bar background
        body.append(
            f'  <rect x="{bar_x0}" y="{ry+10}" width="{bar_x1-bar_x0}" height="36" fill="{ROW_ALT}"/>'
        )
        bar_w = (val - lo) / (hi - lo) * (bar_x1 - bar_x0)
        body.append(
            f'  <rect x="{bar_x0}" y="{ry+10}" width="{max(0, bar_w)}" height="36" fill="{color}"/>'
        )
        body.append(
            f'  <text x="{bar_x0 + max(0, bar_w) + 10}" y="{ry+34}" font-size="18" '
            f'fill="{INK}" font-weight="700">{val:.3f}</text>'
        )
    # Threshold marker
    body.append(
        f'  <line x1="{thr_x}" y1="{base_y+78}" x2="{thr_x}" y2="{base_y+78+5*56-20}" '
        f'stroke="{BAD}" stroke-width="3" stroke-dasharray="6,4"/>'
    )
    body.append(
        f'  <text x="{thr_x}" y="{base_y+72}" font-size="14" fill="{BAD}" '
        f'font-weight="700" text-anchor="middle">threshold 0.85</text>'
    )
    # Axis ticks
    for v in [0.80, 0.85, 0.90, 0.95, 1.00]:
        x = bar_x0 + (v - lo) / (hi - lo) * (bar_x1 - bar_x0)
        ay = base_y + 78 + 5 * 56 - 12
        body.append(
            f'  <text x="{x}" y="{ay}" font-size="14" fill="{MUTED}" text-anchor="middle">{v:.2f}</text>'
        )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 11 - CheckMyMetal-style Z-scores
# ------------------------------------------------------------------
def slide_11_checkmymetal():
    body = [header(
        "T10 — CheckMyMetal-style |Z| ion-identity verdict",
        "Local Zheng-criteria heuristic · Mg²⁺ excluded for both ions · K⁺ has best raw bond-length fit but low CN + biology"
    )]

    body.append(
        f'  <text x="80" y="200" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'Ca²⁺ A 98 · mean bond 2.887 Å · CN 3 · B 42.73</text>'
    )
    headers1 = ["Element", "|Z| (bond)", "Verdict"]
    rows1 = [
        ["Mg²⁺", "16.35", "EXCLUDED — bonds 16σ too long for Mg²⁺ canonical (2.07 Å)"],
        ["Ca²⁺", "3.25", "consistent with partial-occupancy framing"],
        ["Na⁺", "2.44", "possible"],
        ["K⁺", "0.44", "best raw match · CN low · protein is known Ca²⁺-enzyme"],
    ]
    fills1 = [
        [None, BAD, BAD_LIGHT],
        [None, ACCENT, ACCENT_LIGHT],
        [None, MUTED, None],
        [None, WARN, WARN_LIGHT],
    ]
    txt1 = [
        [None, "#ffffff", BAD],
        [None, "#ffffff", ACCENT],
        [None, "#ffffff", None],
        [None, "#ffffff", WARN],
    ]
    body.append(
        table(80, 220, [260, 220, 1280], headers1, rows1,
              row_height=58, font_size=20, header_font_size=22,
              cell_fills=fills1, cell_text_colors=txt1,
              align=["left", "right", "left"])
    )

    body.append(
        f'  <text x="80" y="540" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'Na⁺ B 98 · mean bond 2.773 Å · CN 3 · B 22.85</text>'
    )
    headers2 = ["Element", "|Z| (bond)", "Verdict"]
    rows2 = [
        ["Mg²⁺", "14.06", "EXCLUDED"],
        ["Na⁺", "1.87", "borderline"],
        ["K⁺", "0.13", "better bond-length fit than Na⁺ (open question)"],
    ]
    fills2 = [
        [None, BAD, BAD_LIGHT],
        [None, ACCENT, ACCENT_LIGHT],
        [None, WARN, WARN_LIGHT],
    ]
    txt2 = [
        [None, "#ffffff", BAD],
        [None, "#ffffff", ACCENT],
        [None, "#ffffff", WARN],
    ]
    body.append(
        table(80, 560, [260, 220, 1280], headers2, rows2,
              row_height=58, font_size=20, header_font_size=22,
              cell_fills=fills2, cell_text_colors=txt2,
              align=["left", "right", "left"])
    )

    # Net verdict card
    body.append(
        f'  <rect x="80" y="800" width="{W-160}" height="180" rx="10" fill="{ACCENT_LIGHT}" '
        f'stroke="{ACCENT}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="845" font-size="24" font-weight="700" fill="{INK}">'
        f'Net verdict: agent’s modelling of Ca²⁺ and Na⁺ is defensible</text>'
    )
    body.append(
        f'  <text x="100" y="885" font-size="20" fill="{INK}">'
        f'Mg²⁺ alternative excluded for both ions. Ca²⁺ for chain A is the best biological + geometric fit '
        f'(Asp33 is the canonical SNase Ca²⁺-binder).</text>'
    )
    body.append(
        f'  <text x="100" y="925" font-size="20" fill="{INK}">'
        f'<tspan font-weight="700" fill="{WARN}">Open follow-up:</tspan> '
        f'K⁺ has the best raw bond-length fit. Need crystallisation buffer information to close.</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 12 - Water audit
# ------------------------------------------------------------------
def slide_12_waters():
    body = [header(
        "T10 — Per-water audit (146 waters)",
        "Three waters with RSCC < 0.7 flagged as density_misfit · 143 / 146 are well-supported"
    )]

    # Stats panel
    body.append(
        f'  <rect x="80" y="200" width="700" height="320" rx="10" fill="{ACCENT_LIGHT}" '
        f'stroke="{ACCENT}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="250" font-size="26" font-weight="700" fill="{INK}">'
        f'Distribution statistics</text>'
    )
    stats = [
        ("Mean B", "20.76 Å² (above protein mean 15.98)"),
        ("Mean RSCC", "0.867  (range 0.658–0.983)"),
        ("Waters with RSCC < 0.7", "3  (2.1%)"),
        ("Waters with B > 50 Å²", "1  (HOH S 724)"),
        ("Waters with B > 60 Å²", "0"),
    ]
    for i, (k, v) in enumerate(stats):
        ry = 290 + i * 40
        body.append(
            f'  <text x="100" y="{ry}" font-size="20" font-weight="700" fill="{INK}">{escape(k)}</text>'
            f'\n  <text x="380" y="{ry}" font-size="20" fill="{INK}">{escape(v)}</text>'
        )

    # Misfit waters table
    body.append(
        f'  <text x="820" y="240" font-size="26" font-weight="700" fill="{BAD}">'
        f'Three waters to re-evaluate</text>'
    )
    headers = ["Residue", "B (Å²)", "RSCC", "Severity"]
    rows = [
        ["HOH S 680", "44.56", "0.658", "severe"],
        ["HOH S 707", "33.27", "0.668", "moderate"],
        ["HOH S 729", "48.75", "0.691", "moderate"],
    ]
    fills = []
    txt = []
    for r in rows:
        s = r[3]
        if s == "severe":
            fills.append([None, None, None, BAD])
            txt.append([None, None, None, "#ffffff"])
        else:
            fills.append([None, None, None, WARN])
            txt.append([None, None, None, "#ffffff"])
    body.append(
        table(820, 280, [240, 200, 180, 220], headers, rows,
              row_height=58, font_size=22, header_font_size=22,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "right", "right", "center"])
    )

    # Histogram-style RSCC bar
    body.append(
        f'  <text x="80" y="580" font-size="26" font-weight="700" fill="{ACCENT}">'
        f'Water RSCC histogram (qualitative)</text>'
    )
    bins = [
        ("< 0.70", 3, BAD),
        ("0.70–0.75", 6, WARN),
        ("0.75–0.80", 14, WARN),
        ("0.80–0.85", 23, MUTED),
        ("0.85–0.90", 41, ACCENT),
        ("0.90–0.95", 38, GOOD),
        ("> 0.95", 21, GOOD),
    ]
    bx = 80
    by = 620
    bin_w = 240
    bin_h_max = 280
    max_n = max(b[1] for b in bins)
    for i, (lab, n, color) in enumerate(bins):
        h = bin_h_max * n / max_n
        x = bx + i * bin_w
        y = by + bin_h_max - h
        body.append(
            f'  <rect x="{x+30}" y="{y}" width="{bin_w-60}" height="{h}" fill="{color}" rx="4"/>'
        )
        body.append(
            f'  <text x="{x+bin_w/2}" y="{y-8}" font-size="18" fill="{INK}" '
            f'font-weight="700" text-anchor="middle">{n}</text>'
        )
        body.append(
            f'  <text x="{x+bin_w/2}" y="{by+bin_h_max+30}" font-size="16" fill="{INK}" '
            f'text-anchor="middle">{escape(lab)}</text>'
        )
    body.append(
        f'  <text x="{bx+bin_w*7/2}" y="{by+bin_h_max+62}" font-size="16" fill="{MUTED}" '
        f'text-anchor="middle">RSCC bin · count of waters (146 total)</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 13 - T13 data-quality oracle (new in this re-issue)
# ------------------------------------------------------------------
def slide_13_t13():
    body = [header(
        "T13 — X-ray data-quality oracle (new in this re-issue)",
        "scripts/t13_data_quality.py · CCP4 ctruncate (with aimless attempted) · closes the last cross-tool gap"
    )]

    headers = ["Metric", "Tool", "Value", "Verdict"]
    rows = [
        ["Wilson B", "ctruncate", "14.54 Å² (σ 21.12)",
         "informational · matches refined protein-mean B 16.0"],
        ["L-test twin fraction", "ctruncate", "0.03",
         "✓ < 0.05 — untwinned"],
        ["Moments-based twin", "ctruncate", "0.02",
         "✓ untwinned (<I²>/<I>² = 1.997, expected 2.0)"],
        ["L statistic", "ctruncate", "0.505",
         "✓ untwinned (untwinned 0.500, perfect twin 0.375)"],
        ["First-principles twin operators", "ctruncate", "0",
         "✓ none found by lattice / symmetry search"],
        ["ΔB anisotropy", "ctruncate", "7.32 Å² (eigvals 10.56 / 17.88 / 14.63)",
         "✓ < 20 Å² rule of thumb · mild but present"],
        ["tNCS (Patterson 4 Å)", "ctruncate", "false",
         "✓ no off-origin peaks > 14 Å"],
        ["Ice rings", "ctruncate", "1 flagged at 3.44 Å (Z 5.21, completeness 1.00)",
         "⚪ informational · borderline · not a refinement blocker"],
        ["aimless (canonical T13)", "CCP4 aimless", "aborted",
         "⚪ MTZ has merged amplitudes only (no M/ISYM)"],
    ]
    fills = []
    txt = []
    for r in rows:
        v = r[3]
        if v.startswith("✓"):
            fills.append([None, None, None, GOOD])
            txt.append([None, None, None, "#ffffff"])
        elif v.startswith("⚪"):
            fills.append([None, None, None, MUTED])
            txt.append([None, None, None, "#ffffff"])
        else:
            fills.append([None, None, None, ACCENT])
            txt.append([None, None, None, "#ffffff"])
    body.append(
        table(80, 200, [320, 200, 480, 760], headers, rows,
              row_height=48, font_size=17, header_font_size=20,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "left", "left", "left"])
    )

    # Two cards: "Coverage now closed" + "Aimless limitation"
    body.append(
        f'  <rect x="80" y="700" width="880" height="280" rx="10" fill="{GOOD_LIGHT}" '
        f'stroke="{GOOD}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="745" font-size="24" font-weight="700" fill="{GOOD}">'
        f'Coverage now closed — every catalog task green</text>'
    )
    body.append(
        f'  <text x="100" y="785" font-size="18" fill="{INK}">'
        f'T13 was the only "partial" entry in the cross-tool matrix at 2026-05-01.</text>'
    )
    body.append(
        f'  <text x="100" y="818" font-size="18" fill="{INK}">'
        f'ctruncate (CCP4 / non-cctbx) supplies 5 metrics computable from merged F-obs.</text>'
    )
    body.append(
        f'  <text x="100" y="851" font-size="18" fill="{INK}">'
        f'Five findings now have ≥ 3 confirmations (R-free · Asn A 39 · RMSD bracket ·</text>'
    )
    body.append(
        f'  <text x="100" y="884" font-size="18" fill="{INK}">'
        f'ligand RSCC · Mg²⁺ exclusion); data quality has 1 cctbx + 1 non-cctbx.</text>'
    )
    body.append(
        f'  <text x="100" y="935" font-size="16" fill="{MUTED}">'
        f'Wrapper persists logs at data/coscientists/openscientist/t13_oracle_logs/</text>'
    )

    body.append(
        f'  <rect x="980" y="700" width="860" height="280" rx="10" fill="{WARN_LIGHT}" '
        f'stroke="{WARN}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="1000" y="745" font-size="24" font-weight="700" fill="{WARN}">'
        f'aimless limitation — captured as provenance</text>'
    )
    body.append(
        f'  <text x="1000" y="785" font-size="18" fill="{INK}">'
        f'aimless requires unmerged intensities (M/ISYM column).</text>'
    )
    body.append(
        f'  <text x="1000" y="818" font-size="18" fill="{INK}">'
        f'1sar.mtz ships only F-obs / SIGF-obs → aimless aborts:</text>'
    )
    body.append(
        f'  <text x="1000" y="852" font-size="16" fill="{INK}" font-family="monospace">'
        f'hkl_unmerge_list::prepare - EMPTY</text>'
    )
    body.append(
        f'  <text x="1000" y="892" font-size="18" fill="{INK}">'
        f'CC½, ⟨I/σ⟩ outer, Rmerge / Rmeas remain unobtainable —</text>'
    )
    body.append(
        f'  <text x="1000" y="922" font-size="18" fill="{INK}">'
        f'data-availability gap, not an oracle failure.</text>'
    )
    body.append(
        f'  <text x="1000" y="958" font-size="16" fill="{MUTED}">'
        f'Documented in skill `Tool assumptions` for future artefacts.</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 14 - Assumptions delta
# ------------------------------------------------------------------
def slide_14_assumptions():
    body = [header(
        "Tool / framework assumptions — status delta",
        "QDS assumptions_report grew from 33 → 36+ rows · two upgrades, four hardenings, two new mitigations"
    )]

    headers = ["Assumption", "Was", "Now"]
    rows = [
        ["ASSUM_interp_ion_identity_no_anomalous", "known_violation", "mitigated (CheckMyMetal)"],
        ["ASSUM_phenix_refine_in_run_r_factors_use_internal_scaling",
         "known_violation", "known_violation (3-tool hardened)"],
        ["ASSUM_find_peaks_holes_cutoff_and_merging", "known_violation", "known_violation"],
        ["ASSUM_report_round_table_collapses_rounds",
         "known_violation", "known_violation (per-round oracle hardens)"],
        ["ASSUM_report_position_initial_not_final", "known_violation", "known_violation"],
        ["ASSUM_report_water_count_stage_drift", "known_violation", "known_violation"],
        ["ASSUM_agg_zero_rama_rounds_one_outlier_to_zero",
         "mitigated", "mitigated (3-tool Asn A 39 hardens)"],
        ["ASSUM_checkmymetal_geometry_based", "—", "unchecked → mitigated by 1SAR run"],
        ["ASSUM_t13_oracle_pending  (new)", "open follow-up", "closed — ctruncate wired"],
        ["ASSUM_aimless_requires_unmerged_intensities  (new)",
         "—", "mitigated — wrapper falls back to ctruncate"],
    ]
    fills = []
    txt = []
    for r in rows:
        was, now = r[1], r[2]
        # color the Now cell
        if "mitigated" in now or "closed" in now:
            fills.append([None, None, GOOD])
            txt.append([None, None, "#ffffff"])
        elif "known_violation" in now:
            fills.append([None, None, WARN])
            txt.append([None, None, "#ffffff"])
        else:
            fills.append([None]*3)
            txt.append([None]*3)
    body.append(
        table(80, 190, [800, 360, 600], headers, rows,
              row_height=46, font_size=17, header_font_size=20,
              cell_fills=fills, cell_text_colors=txt,
              align=["left", "left", "left"])
    )

    body.append(
        f'  <rect x="80" y="720" width="{W-160}" height="240" rx="10" fill="{ACCENT_LIGHT}" '
        f'stroke="{ACCENT}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="765" font-size="26" font-weight="700" fill="{INK}">'
        f'Open assumption — K⁺ alternative</text>'
    )
    body.append(
        f'  <text x="100" y="805" font-size="20" fill="{INK}">'
        f'K⁺ alternative for both ions has the best raw bond-length fit but coordination is too low.</text>'
    )
    body.append(
        f'  <text x="100" y="838" font-size="20" fill="{INK}">'
        f'Will be added as an "unchecked" assumption if buffer content is investigated.</text>'
    )
    body.append(
        f'  <text x="100" y="888" font-size="20" fill="{INK}">'
        f'Trust model preserved: every load-bearing finding has ≥ 1 non-cctbx confirmation; '
        f'5 most consequential have ≥ 3.</text>'
    )
    body.append(
        f'  <text x="100" y="930" font-size="18" fill="{MUTED}">'
        f'Five findings with ≥ 3 confirmations: R-free · Asn A 39 · RMSD bracket · ligand RSCC · Mg²⁺ exclusion.</text>'
    )
    return "\n".join(body) + "\n"


# ------------------------------------------------------------------
# Slide 14 - Net acceptance summary / takeaways
# ------------------------------------------------------------------
def slide_15_net():
    body = [header(
        "Net acceptance summary",
        "Four reportable issues · one open question · cross-tool coverage closed"
    )]

    # Big "verdict" block
    body.append(
        f'  <rect x="80" y="180" width="{W-160}" height="160" rx="10" fill="{GOOD_LIGHT}" '
        f'stroke="{GOOD}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="230" font-size="32" font-weight="700" fill="{GOOD}">'
        f'Modelling decisions are defensible</text>'
    )
    body.append(
        f'  <text x="100" y="278" font-size="20" fill="{INK}">'
        f'Structure · geometry · ion identity (Mg²⁺ excluded) · water placement (143 / 146 well-supported) · disulfide bonds.</text>'
    )
    body.append(
        f'  <text x="100" y="312" font-size="18" fill="{MUTED}">'
        f'1SAR refinement is a real and substantial improvement over the deposited starting model.</text>'
    )

    # Four issues as numbered cards
    issues = [
        ("R-free under-stated", "≈ 0.012 below 3-tool consensus", BAD,
         "Three code paths converge on R-free ≈ 0.21. Success-criterion gap < 0.05 fails."),
        ("Round 7 ≮ Round 6", "0.213 vs 0.207 at oracle scaling", BAD,
         "NCS-torsion-restraints justification doesn’t reproduce."),
        ("Asn A 39 outlier", "3-tool confirmed", BAD,
         "Agent’s 0.00% Ramachandran outliers headline rounds 1 outlier to zero."),
        ("Peak inventory", "5 peaks > 5σ not reported", BAD,
         "23 + / 8 − peaks at 4σ; agent listed 9. Max +6.18σ."),
    ]
    cx = 80
    cy = 380
    cw = (W - 160 - 30 * 3) // 4
    ch = 220
    for i, (title, sub, color, body_text) in enumerate(issues):
        body.append(
            f'  <rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="10" fill="{BG}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        body.append(
            f'  <circle cx="{cx+30}" cy="{cy+34}" r="22" fill="{color}"/>'
            f'\n  <text x="{cx+30}" y="{cy+42}" font-size="22" font-weight="700" '
            f'fill="#ffffff" text-anchor="middle">{i+1}</text>'
        )
        body.append(
            f'  <text x="{cx+70}" y="{cy+42}" font-size="22" font-weight="700" fill="{INK}">{escape(title)}</text>'
        )
        body.append(
            f'  <text x="{cx+18}" y="{cy+90}" font-size="18" fill="{color}" font-weight="700">{escape(sub)}</text>'
        )
        # Wrap body text
        tx = cx + 18
        ty = cy + 130
        for line in wrap_text(body_text, 30):
            body.append(
                f'  <text x="{tx}" y="{ty}" font-size="17" fill="{INK}">{escape(line)}</text>'
            )
            ty += 24
        cx += cw + 30

    # Open items
    body.append(
        f'  <text x="80" y="660" font-size="26" font-weight="700" fill="{WARN}">'
        f'Open</text>'
    )
    body.append(
        f'  <rect x="80" y="680" width="{(W-160-30)//2}" height="200" rx="10" fill="{WARN_LIGHT}" '
        f'stroke="{WARN}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="100" y="720" font-size="22" font-weight="700" fill="{WARN}">'
        f'Open question</text>'
    )
    body.append(
        f'  <text x="100" y="755" font-size="18" fill="{INK}">'
        f'K⁺ alternative for both ions</text>'
    )
    body.append(
        f'  <text x="100" y="790" font-size="17" fill="{INK}">'
        f'Best raw bond-length fit, but coordination number low and the protein is a known Ca²⁺ enzyme.</text>'
    )
    body.append(
        f'  <text x="100" y="822" font-size="17" fill="{INK}">'
        f'Needs crystallisation-buffer information.</text>'
    )

    body.append(
        f'  <rect x="{80 + (W-160-30)//2 + 30}" y="680" width="{(W-160-30)//2}" height="200" rx="10" '
        f'fill="{GOOD_LIGHT}" stroke="{GOOD}" stroke-width="2"/>'
    )
    body.append(
        f'  <text x="{80 + (W-160-30)//2 + 50}" y="720" font-size="22" font-weight="700" fill="{GOOD}">'
        f'Closed in this re-issue (2026-05-04)</text>'
    )
    body.append(
        f'  <text x="{80 + (W-160-30)//2 + 50}" y="755" font-size="18" fill="{INK}">'
        f'T13 non-cctbx data-quality oracle wired</text>'
    )
    body.append(
        f'  <text x="{80 + (W-160-30)//2 + 50}" y="790" font-size="17" fill="{INK}">'
        f'ctruncate via scripts/t13_data_quality.py · aimless captured as provenance.</text>'
    )
    body.append(
        f'  <text x="{80 + (W-160-30)//2 + 50}" y="822" font-size="17" fill="{INK}">'
        f'Cross-tool coverage matrix is now fully green — every catalog task in scope</text>'
    )
    body.append(
        f'  <text x="{80 + (W-160-30)//2 + 50}" y="848" font-size="17" fill="{INK}">'
        f'has both cctbx and non-cctbx confirmation.</text>'
    )
    return "\n".join(body) + "\n"


def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur and cur_len + len(w) + 1 > max_chars:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
        else:
            cur.append(w)
            cur_len += len(w) + (1 if cur_len else 0)
    if cur:
        lines.append(" ".join(cur))
    return lines


# ------------------------------------------------------------------
# Driver
# ------------------------------------------------------------------
def main():
    slides = [
        ("01_title", slide_01_title),
        ("02_oracles", slide_02_oracles),
        ("03_verdict", slide_03_verdict),
        ("04_checklist", slide_04_checklist),
        ("05_t01_rmsd", slide_05_t01),
        ("06_t03_rfactors", slide_06_t03_rfactors),
        ("07_per_round", slide_07_per_round),
        ("08_t05_geometry", slide_08_t05_geometry),
        ("09_peaks", slide_09_peaks),
        ("10_t10_rscc", slide_10_t10_rscc),
        ("11_checkmymetal", slide_11_checkmymetal),
        ("12_waters", slide_12_waters),
        ("13_t13", slide_13_t13),
        ("14_assumptions", slide_14_assumptions),
        ("15_net", slide_15_net),
    ]
    for name, fn in slides:
        body = fn()
        path = write_svg(name, body)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
