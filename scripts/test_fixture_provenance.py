#!/usr/bin/env python3
"""Adversarial tests for the fixture-provenance guard."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from check_fixture_provenance import check_manifest, check_publication_boundary


def _write_case(root: Path, *, digest: str | None = None) -> Path:
    fixtures = root / "data" / "pdb_mtz"
    fixtures.mkdir(parents=True)
    payload = fixtures / "known.pdb"
    payload.write_bytes(b"fixture\n")
    manifest = fixtures / "fixture_provenance.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "source_policy": "https://example.test/policy",
                "fixtures": [
                    {
                        "path": "known.pdb",
                        "identifier": "PDB:TEST",
                        "source_url": "https://example.test/known.pdb",
                        "citation_url": "https://example.test/citation",
                        "retrieved_on": "2026-08-21",
                        "sha256": digest or hashlib.sha256(b"fixture\n").hexdigest(),
                        "transformations": [],
                    }
                ],
            },
            sort_keys=False,
        )
    )
    return manifest


def test_happy_path() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        manifest = _write_case(Path(temporary))
        assert check_manifest(manifest.parent, manifest) == []


def test_checksum_drift_fails() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        manifest = _write_case(Path(temporary), digest="0" * 64)
        errors = check_manifest(manifest.parent, manifest)
        assert any("sha256 mismatch" in error for error in errors), errors


def test_unlisted_fixture_fails() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        manifest = _write_case(Path(temporary))
        (manifest.parent / "surprise.mtz").write_bytes(b"unreviewed")
        errors = check_manifest(manifest.parent, manifest)
        assert "unlisted fixture: surprise.mtz" in errors, errors


def test_nested_file_and_symlink_fail() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        manifest = _write_case(Path(temporary))
        nested = manifest.parent / "nested"
        nested.mkdir()
        (nested / "surprise.mtz").write_bytes(b"unreviewed")
        (manifest.parent / "alias.pdb").symlink_to("known.pdb")
        errors = check_manifest(manifest.parent, manifest)
        assert "unlisted fixture: nested/surprise.mtz" in errors, errors
        assert "unlisted fixture: alias.pdb" in errors, errors


def test_duplicate_and_unsafe_paths_fail() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        manifest = _write_case(Path(temporary))
        document = yaml.safe_load(manifest.read_text())
        document["fixtures"].append(dict(document["fixtures"][0]))
        document["fixtures"].append({"path": "../escape.pdb"})
        manifest.write_text(yaml.safe_dump(document, sort_keys=False))
        errors = check_manifest(manifest.parent, manifest)
        assert "duplicate fixture path: known.pdb" in errors, errors
        assert any("one filename" in error for error in errors), errors


def test_publication_boundary_fails_closed_with_git_metadata() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        (repo / ".git").mkdir()
        (repo / ".gitignore").write_text("/ref/phenix_docs/\n")
        failure = subprocess.CalledProcessError(128, ["git"], stderr="index unavailable")
        with patch("check_fixture_provenance.subprocess.run", side_effect=failure):
            errors = check_publication_boundary(repo)
        assert errors == ["cannot inspect tracked PHENIX files: index unavailable"], errors


def test_publication_boundary_rejects_tracked_mirror() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        (repo / ".git").mkdir()
        (repo / ".gitignore").write_text("/ref/phenix_docs/\n")
        result = subprocess.CompletedProcess(
            ["git"], 0, stdout="ref/phenix_docs/upstream/index.html\n", stderr=""
        )
        with patch("check_fixture_provenance.subprocess.run", return_value=result):
            errors = check_publication_boundary(repo)
        assert errors == ["PHENIX documentation mirror is tracked (1 files)"], errors


def main() -> None:
    tests = [
        test_happy_path,
        test_checksum_drift_fails,
        test_unlisted_fixture_fails,
        test_nested_file_and_symlink_fail,
        test_duplicate_and_unsafe_paths_fail,
        test_publication_boundary_fails_closed_with_git_metadata,
        test_publication_boundary_rejects_tracked_mirror,
    ]
    for test in tests:
        test()
        print(f"PASS  {test.__name__}")


if __name__ == "__main__":
    main()
