#!/usr/bin/env python3
"""Fail when distributed scientific fixtures lack exact, checked provenance."""

from __future__ import annotations

import gzip
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO / "data" / "pdb_mtz"
MANIFEST = FIXTURE_DIR / "fixture_provenance.yaml"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_manifest(fixture_dir: Path, manifest_path: Path) -> list[str]:
    """Return manifest/inventory errors without raising on malformed input."""
    errors: list[str] = []
    try:
        document: Any = yaml.safe_load(manifest_path.read_text())
    except Exception as exc:
        return [f"cannot read {manifest_path}: {exc}"]

    if not isinstance(document, dict) or document.get("version") != 1:
        return ["fixture manifest must be a mapping with version: 1"]
    if not str(document.get("source_policy", "")).startswith("https://"):
        errors.append("source_policy must be an HTTPS URL")

    entries = document.get("fixtures")
    if not isinstance(entries, list) or not entries:
        return errors + ["fixture manifest must contain a non-empty fixtures list"]

    listed: set[str] = set()
    root = fixture_dir.resolve()
    for index, entry in enumerate(entries):
        label = f"fixtures[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be a mapping")
            continue
        relative = entry.get("path")
        if not isinstance(relative, str) or not relative or Path(relative).name != relative:
            errors.append(f"{label}.path must be one filename without directories")
            continue
        if relative in listed:
            errors.append(f"duplicate fixture path: {relative}")
            continue
        listed.add(relative)

        path = fixture_dir / relative
        try:
            if path.resolve().parent != root:
                errors.append(f"fixture path escapes data/pdb_mtz: {relative}")
                continue
        except OSError as exc:
            errors.append(f"cannot resolve fixture {relative}: {exc}")
            continue

        for field in ("identifier", "citation_url", "source_url", "retrieved_on", "sha256"):
            if field not in entry:
                errors.append(f"{relative}: missing {field}")
        if not str(entry.get("source_url", "")).startswith("https://"):
            errors.append(f"{relative}: source_url must be HTTPS")
        if not str(entry.get("citation_url", "")).startswith("https://"):
            errors.append(f"{relative}: citation_url must be HTTPS")
        if not DATE_RE.fullmatch(str(entry.get("retrieved_on", ""))):
            errors.append(f"{relative}: retrieved_on must be YYYY-MM-DD")
        expected = str(entry.get("sha256", ""))
        if not SHA256_RE.fullmatch(expected):
            errors.append(f"{relative}: sha256 must be 64 lowercase hex characters")
        if not isinstance(entry.get("transformations"), list):
            errors.append(f"{relative}: transformations must be a list (empty when none)")
        if not path.is_file() or path.is_symlink():
            errors.append(f"{relative}: listed fixture is missing or is a symlink")
            continue
        if SHA256_RE.fullmatch(expected):
            actual = _sha256(path)
            if actual != expected:
                errors.append(f"{relative}: sha256 mismatch (expected {expected}, got {actual})")

        content_expected = entry.get("content_sha256")
        if content_expected is not None:
            content_expected = str(content_expected)
            if not relative.endswith(".gz"):
                errors.append(f"{relative}: content_sha256 is only supported for .gz fixtures")
            elif not SHA256_RE.fullmatch(content_expected):
                errors.append(f"{relative}: content_sha256 must be 64 lowercase hex characters")
            else:
                try:
                    digest = hashlib.sha256()
                    with gzip.open(path, "rb") as handle:
                        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                            digest.update(chunk)
                    if digest.hexdigest() != content_expected:
                        errors.append(f"{relative}: decompressed content_sha256 mismatch")
                except (OSError, EOFError) as exc:
                    errors.append(f"{relative}: invalid gzip content: {exc}")

    actual = {
        path.relative_to(fixture_dir).as_posix()
        for path in fixture_dir.rglob("*")
        if (path.is_file() or path.is_symlink()) and path != manifest_path
    }
    for name in sorted(actual - listed):
        errors.append(f"unlisted fixture: {name}")
    for name in sorted(listed - actual):
        errors.append(f"manifest lists absent fixture: {name}")
    return errors


def check_publication_boundary(repo: Path) -> list[str]:
    """Ensure a local PHENIX cache cannot drift into tracked release contents."""
    errors: list[str] = []
    ignored = (repo / ".gitignore").read_text().splitlines()
    if "/ref/phenix_docs/" not in ignored:
        errors.append(".gitignore must exclude /ref/phenix_docs/")
    if not (repo / ".git").exists():
        return errors  # Source archives intentionally have no tracked-file index.
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--", "ref/phenix_docs"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    except FileNotFoundError:
        errors.append("Git metadata exists but the git executable is unavailable")
        return errors
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() if exc.stderr else f"exit {exc.returncode}"
        errors.append(f"cannot inspect tracked PHENIX files: {detail}")
        return errors
    if tracked:
        errors.append(f"PHENIX documentation mirror is tracked ({len(tracked)} files)")
    return errors


def main() -> int:
    errors = check_manifest(FIXTURE_DIR, MANIFEST) + check_publication_boundary(REPO)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    count = len(yaml.safe_load(MANIFEST.read_text())["fixtures"])
    print(f"fixture provenance OK ({count} files; PHENIX mirror excluded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
