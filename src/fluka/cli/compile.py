from __future__ import annotations
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from fluka.run.simconfig import resolve

_ROOT_DIR = Path(__file__).resolve().parents[2] / "root_output"
_DEFAULTS_DIR = _ROOT_DIR / "routines"
_BASE = ("usrini.f", "usrout.f", "mgdraw.f")


def resolve_routines(routines, defaults_dir=_DEFAULTS_DIR) -> list[Path]:
    """Default usrini/usrout/mgdraw, overridden by basename, plus extras."""
    resolved = {n: Path(defaults_dir) / n for n in _BASE}
    extras: list[Path] = []
    for r in routines or []:
        p = Path(r)
        if p.name in _BASE:
            resolved[p.name] = p
        else:
            extras.append(p)
    return [resolved[n] for n in _BASE] + extras


def build_command(section: dict, root_dir, build_dir) -> list[str]:
    use_rntuple = "1" if section.get("rntuple") else "0"
    name = section.get("name") or "rootfluka"
    routines = section.get("routines") or []
    objs = ["usrini.o", "usrout.o", "mgdraw.o"]
    for r in routines:
        stem = Path(r).name
        if stem not in _BASE:
            objs.append(Path(stem).with_suffix(".o").name)
    return ["make", "-C", str(build_dir),
            f"USE_RNTUPLE={use_rntuple}", f"NAME={name}", f"OBJS={' '.join(objs)}"]


def run_sim(path) -> None:
    section = resolve(path, "custom_exe")
    build_dir = Path(tempfile.mkdtemp(prefix="fluka-root-"))
    # copy the Makefile + FluLib sources into the build dir
    for item in ("Makefile", "src"):
        src = _ROOT_DIR / item
        dst = build_dir / item
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy(src, dst)
    # stage the resolved routines into the build dir
    for f in resolve_routines(section.get("routines"), _DEFAULTS_DIR):
        shutil.copy(f, build_dir / Path(f).name)
    cmd = build_command(section, _ROOT_DIR, build_dir)
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Compile FLUKA ROOT-output routines")
    ap.add_argument("config", type=Path, help="sim.yaml")
    run_sim(ap.parse_args().config)
