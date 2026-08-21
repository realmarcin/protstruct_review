#!/usr/bin/env python3
"""Version metadata emitted before every benchmark run."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


PYTHON_DISTRIBUTIONS = (
    "PyYAML",
    "pydantic",
    "linkml",
    "numpy",
    "scipy",
    "gemmi",
    "biotite",
    "DockQ",
)

EXTERNAL_TOOLS = {
    "PHENIX": {
        "expected_version": "2.0-5936",
        "environment": ("PROTSTRUCT_PHENIX_BIN", "PHENIX"),
        "executables": ("phenix.version", "phenix.refine"),
    },
    "CCP4": {
        "expected_version": "9.0.015",
        "environment": ("PROTSTRUCT_CCP4_SETUP", "CCP4"),
        "executables": ("refmac5", "ctruncate"),
    },
    "TM-align": {
        "expected_version": "20220412",
        "environment": ("PROTSTRUCT_TMALIGN",),
        "executables": ("TMalign",),
    },
    "DSSP": {
        "expected_version": "4.6.1",
        "environment": ("PROTSTRUCT_DSSP",),
        "executables": ("mkdssp",),
    },
    "probe": {
        "expected_version": "2.26.021123",
        "environment": ("PROTSTRUCT_PROBE",),
        "executables": ("probe",),
    },
    "reduce": {
        "expected_version": "4.16.250520",
        "environment": ("PROTSTRUCT_REDUCE",),
        "executables": ("reduce",),
    },
}


def _distribution_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for distribution in PYTHON_DISTRIBUTIONS:
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return versions


def _configured_path(environment_names: tuple[str, ...]) -> str | None:
    for name in environment_names:
        if value := os.environ.get(name):
            return str(Path(value).expanduser())
    return None


def _discovered_executable(names: tuple[str, ...]) -> str | None:
    for name in names:
        if path := shutil.which(name):
            return path
    return None


def benchmark_environment() -> dict[str, object]:
    """Return actual Python versions and pinned/discovered external tool state."""
    external: dict[str, dict[str, str | bool | None]] = {}
    for name, specification in EXTERNAL_TOOLS.items():
        configured = _configured_path(specification["environment"])
        discovered = _discovered_executable(specification["executables"])
        external[name] = {
            "expected_version": specification["expected_version"],
            "configured_path": configured,
            "discovered_executable": discovered,
            "available": configured is not None or discovered is not None,
        }
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "python_packages": _distribution_versions(),
        "external_tools": external,
    }


def announce_benchmark_environment(stream: TextIO = sys.stderr) -> dict[str, object]:
    """Write one JSON metadata record before measurements and return it."""
    metadata = benchmark_environment()
    print(json.dumps({"benchmark_environment": metadata}, sort_keys=True), file=stream)
    return metadata


if __name__ == "__main__":
    announce_benchmark_environment(sys.stdout)
