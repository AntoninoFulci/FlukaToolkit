from __future__ import annotations
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from importlib.resources import files
from pathlib import Path

from fluka.run.simconfig import resolve

def _root_output_dir() -> Path:
    return Path(files("fluka").joinpath("root_output"))


_ROOT_DIR = _root_output_dir()
_DEFAULTS_DIR = _ROOT_DIR / "routines"
_BASE = ("usrini.f", "usrout.f", "mgdraw.f")


def resolve_routines(routines, defaults_dir=_DEFAULTS_DIR, use_defaults=True) -> list[Path]:
    if not use_defaults:
        resolved = [Path(r) for r in (routines or [])]
        names = {p.name for p in resolved}
        if "usrini.f" not in names or "usrout.f" not in names:
            print("warning: ROOT open/close routines (usrini.f/usrout.f) missing; "
                  "dump.root may not be produced", file=sys.stderr)
        return resolved
    resolved = {n: Path(defaults_dir) / n for n in _BASE}
    extras: list[Path] = []
    for r in routines or []:
        p = Path(r)
        if p.name in _BASE:
            resolved[p.name] = p
        else:
            extras.append(p)
    return [resolved[n] for n in _BASE] + extras


def build_command(section: dict, build_dir, resolved_routines) -> list[str]:
    use_rntuple = "1" if section.get("rntuple") else "0"
    name = section.get("name") or "rootfluka"
    objs = [Path(r).with_suffix(".o").name for r in resolved_routines]
    return ["make", "-C", str(build_dir),
            f"USE_RNTUPLE={use_rntuple}", f"NAME={name}", f"OBJS={' '.join(objs)}"]


def _exe_path(section) -> Path:
    return Path(section.get("exe_path") or (_ROOT_DIR / "fluka_custom_exe"))


def compile_exe(section: dict, *, force: bool = False) -> Path:
    exe = _exe_path(section)
    if exe.exists() and not force:
        return exe
    name = section.get("name") or "rootfluka"
    routines = resolve_routines(section.get("routines"), _DEFAULTS_DIR,
                                use_defaults=section.get("use_defaults", True))
    build_dir = Path(tempfile.mkdtemp(prefix="fluka-compile-"))
    try:
        for item in ("Makefile", "src"):
            s = _ROOT_DIR / item
            (shutil.copytree(s, build_dir / item) if s.is_dir()
             else shutil.copy(s, build_dir / item))
        for f in routines:
            shutil.copy(f, build_dir / Path(f).name)
        subprocess.run(build_command(section, build_dir, routines), check=True)
        built = build_dir / "RootFlukaExecutables" / name
        if not built.exists():
            raise RuntimeError(f"expected compiled binary not found: {built}")
        exe.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(built, exe)
        os.chmod(exe, 0o755)
        return exe
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


def run_sim(path) -> None:
    exe = compile_exe(resolve(path, "custom_exe"), force=True)
    print(f"compiled: {exe}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Compile FLUKA ROOT-output routines")
    ap.add_argument("config", type=Path, help="sim.yaml")
    run_sim(ap.parse_args().config)
