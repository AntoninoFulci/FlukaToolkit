from __future__ import annotations
import argparse
from pathlib import Path

def _run_grid(sim: Path) -> None:
    from fluka.cli.grid import run_sim; run_sim(sim)
def _run_submit(sim: Path) -> None:
    from fluka.cli.submit import run_sim; run_sim(sim)
def _run_collect(sim: Path) -> None:
    from fluka.cli.submit import collect_sim; collect_sim(sim)
def _run_analysis(sim: Path) -> None:
    from fluka.cli.analysis import run_sim; run_sim(sim)

def submit_phase(sim_path, *, do_grid: bool) -> None:
    sim = Path(sim_path)
    if do_grid:
        _run_grid(sim)
    _run_submit(sim)

def analyze_phase(sim_path) -> None:
    sim = Path(sim_path)
    _run_collect(sim)
    _run_analysis(sim)

def main() -> None:
    ap = argparse.ArgumentParser(description="Run a FLUKA simulation from one sim.yaml")
    sub = ap.add_subparsers(dest="phase", required=True)
    ps = sub.add_parser("submit"); ps.add_argument("sim", type=Path)
    ps.add_argument("--no-grid", action="store_true", help="skip grid generation")
    pa = sub.add_parser("analyze"); pa.add_argument("sim", type=Path)
    args = ap.parse_args()
    if args.phase == "submit":
        submit_phase(args.sim, do_grid=not args.no_grid)
    else:
        analyze_phase(args.sim)
