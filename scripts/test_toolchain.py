#!/usr/bin/env python3
"""Regression tests for shell-free tool execution and centralized config."""

from __future__ import annotations

import ast
import importlib.util
import json
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
                }:
                    duplicate_constants.append(f"{script.name}:{target.id}")
check("no runner invokes bash -c", not shell_calls)
check("tool paths are defined only in toolchain.py", not duplicate_constants)

print("\nall toolchain unit tests passed")
