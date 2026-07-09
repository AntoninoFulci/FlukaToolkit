from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

from fluka.cli._common import resolve_config

_ROOT_DIR = Path(__file__).resolve().parents[2] / "root_output"

def build_commands(section: dict, root_dir: str | Path = _ROOT_DIR) -> list[list[str]]:
    """Map the `root:` section to `make` invocations for root_output/Makefile.
    The Makefile selects source via USE_RNTUPLE (0=FluLib.cpp, 1=FluLibRNTuple.cpp)
    and NAME is the output binary name. One make command per listed source file."""
    root_dir = str(root_dir)
    files = list(section.get("files") or [])
    if not files and section.get("format"):
        files = ["FluLibRNTuple.cpp" if section["format"] == "rntuple" else "FluLib.cpp"]
    cmds: list[list[str]] = []
    for src in files:
        use_rntuple = "1" if "RNTuple" in src else "0"
        name = section.get("name") or src.rsplit(".", 1)[0]
        cmds.append(["make", "-C", root_dir, f"USE_RNTUPLE={use_rntuple}", f"NAME={name}"])
    return cmds

def run_sim(path) -> None:
    section, _ = resolve_config(path, "root")
    for cmd in build_commands(section):
        subprocess.run(cmd, check=True)

def main() -> None:
    ap = argparse.ArgumentParser(description="Compile FLUKA ROOT-output routines")
    ap.add_argument("config", type=Path, help="root.yaml or sim.yaml")
    run_sim(ap.parse_args().config)
