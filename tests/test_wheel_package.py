"""Regression coverage for compiler assets in the distributable wheel."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from shutil import copytree, ignore_patterns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COMPILER_ASSETS = (
    "Makefile",
    "routines/usrini.f",
    "routines/usrout.f",
    "routines/mgdraw.f",
    "src/FluLib.cpp",
    "src/FluLibRNTuple.cpp",
    "scripts/compilerf.sh",
)


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def test_wheel_contains_compiler_assets_and_installed_package_finds_them(tmp_path):
    """Catch regressions that omit compiler assets from a built distribution."""
    source_copy = tmp_path / "source"
    copytree(
        PROJECT_ROOT,
        source_copy,
        ignore=ignore_patterns(".git", ".worktrees", "build", "dist", "*.egg-info", "__pycache__"),
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        cwd=source_copy,
        check=True,
    )
    wheel = next(tmp_path.glob("flukatoolkit-*.whl"))

    with zipfile.ZipFile(wheel) as archive:
        packaged_files = set(archive.namelist())
        assert {
            f"fluka/root_output/{asset}" for asset in REQUIRED_COMPILER_ASSETS
        } <= packaged_files

    venv_dir = tmp_path / "installed-wheel"
    subprocess.run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(venv_dir)],
        check=True,
    )
    venv_python = _venv_python(venv_dir)
    install_env = os.environ | {"PYTHONPATH": ""}
    subprocess.run(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            "--no-deps",
            "--no-index",
            str(wheel),
        ],
        check=True,
        env=install_env,
    )

    lookup = subprocess.run(
        [
            str(venv_python),
            "-I",
            "-c",
            (
                "import json; "
                "from fluka.cli.compile import _root_output_dir; "
                "root = _root_output_dir(); "
                f"assets = {REQUIRED_COMPILER_ASSETS!r}; "
                "print(json.dumps({asset: (root / asset).is_file() for asset in assets}))"
            ),
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(lookup.stdout) == {
        asset: True for asset in REQUIRED_COMPILER_ASSETS
    }
