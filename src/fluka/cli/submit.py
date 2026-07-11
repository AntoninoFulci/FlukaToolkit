from __future__ import annotations
import argparse
from pathlib import Path

from fluka.run.simconfig import resolve
from fluka.queue.core.config import build_submit_args
from fluka.queue.launch_jobs import BACKENDS, run_from_args


def run_sim(path) -> None:
    run_from_args(build_submit_args(resolve(path, "submit"), BACKENDS))


def collect_sim(path) -> None:
    """Collect ROOT files produced by a submitted run into root_files/.

    Thin wrapper around fluka.queue.collect_results, which operates on the
    current working directory; the sim/submit config isn't otherwise needed
    since collection is a directory scan, not a config-driven step.
    """
    from fluka.queue import collect_results
    collect_results.main()


def main() -> None:
    ap = argparse.ArgumentParser(description="FLUKA job submission")
    ap.add_argument("config", type=Path, help="submit config.yaml or sim.yaml")
    ap.add_argument("--grid", action="store_true", help="run grid generation before submitting")
    args = ap.parse_args()
    if args.grid:
        from fluka.run.orchestrator import submit_phase
        submit_phase(args.config, do_grid=True)
    else:
        run_sim(args.config)
