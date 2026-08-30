#!/usr/bin/env python3
"""Regression tests for shell-free tool execution and centralized config."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

import toolchain


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS  {label}")


with tempfile.TemporaryDirectory(prefix="tool path ; $() ") as tmp:
    root = Path(tmp)
    helper = root / "helper ; $(never-run).py"
    output = root / "output ; literal.log"
    argument = "value ; $(touch SHOULD_NOT_EXIST) with spaces"
    helper.write_text(
        "import json, sys\n"
        "print(json.dumps({'argument': sys.argv[1], 'cwd': __import__('os').getcwd()}))\n"
    )
    result = toolchain.run_logged(
        [sys.executable, helper, argument], output, cwd=root, timeout=10
    )
    record = json.loads(output.read_text())
    check("metacharacter path executes successfully", result.returncode == 0)
    check("argument reaches the child literally", record["argument"] == argument)
    check(
        "cwd with spaces/metacharacters is preserved",
        Path(record["cwd"]).resolve() == root.resolve(),
    )
    check("shell command substitution never runs", not (root / "SHOULD_NOT_EXIST").exists())

    tmalign = root / "TM align ; $(never-run)"
    tmalign.write_text(
        "#!/usr/bin/env python3\n"
        "print('Aligned length= 3, RMSD= 1.25')\n"
        "print('TM-score= 0.8000 (if normalized by length of Chain_2')\n"
    )
    tmalign.chmod(0o755)
    spec = importlib.util.spec_from_file_location(
        "bench_t01_shell_safety", Path(__file__).with_name("bench_t01_superposition.py")
    )
    bench_t01 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench_t01)
    bench_t01.TMALIGN = tmalign
    fixed = root / "fixed ; model.pdb"
    moving = root / "moving $(literal).pdb"
    fixed.write_text("MODEL\n")
    moving.write_text("MODEL\n")
    parsed = bench_t01.run_tmalign(fixed, moving, root, all_chains=True)
    check(
        "representative benchmark output remains parseable",
        parsed == {"n_aligned": 3, "rmsd": 1.25, "tm_score": 0.8},
    )

with tempfile.TemporaryDirectory(prefix="ccp4 setup ; ") as tmp:
    setup = Path(tmp) / "vendor setup ; literal.sh"
    setup.write_text("export PROTSTRUCT_ADAPTER_TEST='literal ; $() value'\n")
    environment = toolchain.ccp4_environment(setup)
    check(
        "CCP4 setup path and exported metacharacters remain literal",
        environment["PROTSTRUCT_ADAPTER_TEST"] == "literal ; $() value",
    )

with tempfile.TemporaryDirectory(prefix="tool version evidence ") as tmp:
    root = Path(tmp)
    expected_dir = root / "suite-1.2.3"
    expected_dir.mkdir()
    lying_tool = expected_dir / "tool-version"
    lying_tool.write_text("#!/bin/sh\necho 'tool version 9.9.9'\n")
    lying_tool.chmod(0o755)
    setup_file = expected_dir / "ccp4.setup-sh"
    setup_file.write_text("export CCP4='configured'\n")
    original_specs = toolchain.EXTERNAL_TOOL_SPECS
    try:
        toolchain.EXTERNAL_TOOL_SPECS = {
            "measured": {
                "expected_version": "1.2.3",
                "configured_path": lying_tool,
                "executables": ("tool-version",),
                "version_args": (),
            },
            "empty-directory": {
                "expected_version": "1.2.3",
                "configured_path": expected_dir,
                "executables": ("missing-tool",),
                "version_args": None,
            },
            "configured-artifact": {
                "expected_version": "1.2.3",
                "configured_path": setup_file,
                "executables": ("missing-until-setup",),
                "version_args": None,
                "availability_probe": "configured_file",
            },
        }
        report = toolchain.external_tool_report()
    finally:
        toolchain.EXTERNAL_TOOL_SPECS = original_specs
    check(
        "measured version output is never replaced by the configured path",
        report["measured"]["reported_version"] == "tool version 9.9.9",
    )
    check(
        "measured version provenance is labeled",
        report["measured"]["reported_version_source"] == "command_output",
    )
    check(
        "measured mismatch overrides a matching path hint",
        report["measured"]["version_divergence"] is True,
    )
    check(
        "empty expected-version directory is not an available tool",
        report["empty-directory"]["available"] is False,
    )
    check(
        "configured-file availability is an explicit CCP4-style exception",
        report["configured-artifact"]["available"] is True
        and report["configured-artifact"]["availability_probe"] == "configured_file",
    )
    check(
        "configured-file path inference is kept out of reported_version",
        report["configured-artifact"]["reported_version"] is None
        and report["configured-artifact"]["configured_path_version_hint"] == "1.2.3",
    )

with tempfile.TemporaryDirectory(prefix="bare executable cwd trap ") as tmp:
    root = Path(tmp)
    cwd_tool = root / "mkdssp"
    cwd_tool.write_text("#!/bin/sh\necho wrong-cwd-tool\n")
    cwd_tool.chmod(0o755)
    old_cwd = Path.cwd()
    old_path = os.environ.get("PATH", "")
    try:
        os.chdir(root)
        os.environ["PATH"] = ""
        discovered = toolchain._discover_executable(Path("mkdssp"), ("mkdssp",))
    finally:
        os.chdir(old_cwd)
        os.environ["PATH"] = old_path
    check("bare configured names are PATH-only, never cwd files", discovered is None)

with tempfile.TemporaryDirectory(prefix="foreign import cwd ") as tmp:
    root = Path(tmp)
    driver = Path(__file__).with_name("bench_t01_superposition.py")
    import_probe = (
        "import importlib.util, pathlib, sys; "
        "p=pathlib.Path(sys.argv[1]); "
        "s=importlib.util.spec_from_file_location('foreign_driver', p); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "print(m.__name__)"
    )
    loaded = toolchain.run_capture(
        [sys.executable, "-I", "-c", import_probe, driver], cwd=root, timeout=10
    )
    check(
        "driver imports toolchain from an isolated foreign cwd",
        loaded.returncode == 0 and loaded.stdout.strip() == "foreign_driver",
    )

scripts_dir = Path(__file__).resolve().parent
shell_calls = []
duplicate_constants = []
for script in sorted(scripts_dir.glob("*.py")):
    tree = ast.parse(script.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            has_bash_c = any(
                isinstance(child, (ast.List, ast.Tuple))
                and len(child.elts) >= 2
                and isinstance(child.elts[0], ast.Constant)
                and child.elts[0].value in {"bash", "/bin/bash"}
                and isinstance(child.elts[1], ast.Constant)
                and child.elts[1].value == "-c"
                for child in ast.walk(node)
            )
            has_shell_true = any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )
            if script.name != "toolchain.py" and (has_bash_c or has_shell_true):
                shell_calls.append(f"{script.name}:{node.lineno}")
        if (
            script.name != "toolchain.py"
            and not script.name.startswith("test_")
            and isinstance(node, (ast.Assign, ast.AnnAssign))
        ):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id in {
                    "PHENIX_BIN",
                    "CCP4_SETUP",
                    "TMALIGN",
                    "REDUCE",
                    "PROBE",
                    "GEMMI",
                }:
                    duplicate_constants.append(f"{script.name}:{target.id}")
check("no runner invokes bash -c", not shell_calls)
# #496: no script builds an argv that starts with a bare "gemmi" — the CLI is
# resolved once through toolchain.gemmi_executable() so the manifest and the
# measurements name the same binary even under the ccp4 environment rewrite.
bare_gemmi = []
for script in sorted(Path(__file__).parent.glob("*.py")):
    if script.name in {"toolchain.py"} or script.name.startswith("test_"):
        continue
    for node in ast.walk(ast.parse(script.read_text())):
        # argv literals are lists here; ("gemmi", fn) label tuples are not argv.
        if (isinstance(node, (ast.List, ast.Tuple)) and node.elts
                and isinstance(node.elts[0], ast.Constant)
                and node.elts[0].value == "gemmi"
                and isinstance(node, ast.List)):
            bare_gemmi.append(f"{script.name}:{node.lineno}")
        # shutil.which("gemmi") re-introduces a second resolver (#505).
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "which" and node.args
                and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "gemmi"):
            bare_gemmi.append(f"{script.name}:{node.lineno} (shutil.which)")
check("no script invokes a bare 'gemmi' argv (#496)", not bare_gemmi)

with tempfile.TemporaryDirectory(prefix="gemmi resolver ") as tmp:
    root = Path(tmp)
    fake = root / "gemmi"
    fake.write_text("#!/bin/sh\necho gemmi 9.9.9\n")
    fake.chmod(0o755)
    old_gemmi = toolchain.GEMMI
    old_path = os.environ.get("PATH", "")
    try:
        toolchain.GEMMI = fake
        check("PROTSTRUCT_GEMMI absolute path is honoured",
              toolchain.gemmi_executable() == fake.resolve())
        toolchain.GEMMI = Path("gemmi")
        os.environ["PATH"] = str(root)
        check("bare default resolves the PATH binary to an absolute path",
              toolchain.gemmi_executable() == fake.resolve())
        rel = Path(os.path.relpath(fake))
        toolchain.GEMMI = rel
        check("a relative PROTSTRUCT_GEMMI resolves to an absolute path (#503)",
              toolchain.gemmi_executable().is_absolute()
              and toolchain.gemmi_executable() == fake.resolve())
        toolchain.GEMMI = Path("gemmi")
        os.environ["PATH"] = ""
        check("absent CLI: required=False returns None",
              toolchain.gemmi_executable(required=False) is None)
        try:
            toolchain.gemmi_executable()
            named = False
        except FileNotFoundError as exc:
            named = "PROTSTRUCT_GEMMI" in str(exc)
        check("absent CLI: required raises a failure naming PROTSTRUCT_GEMMI", named)
    finally:
        toolchain.GEMMI = old_gemmi
        os.environ["PATH"] = old_path
check("gemmi is in the external tool report",
      "gemmi" in toolchain.EXTERNAL_TOOL_SPECS
      and toolchain.EXTERNAL_TOOL_SPECS["gemmi"]["expected_version"] == toolchain.GEMMI_VERSION)
check("tool paths are defined only in toolchain.py", not duplicate_constants)

print("\nall toolchain unit tests passed")
