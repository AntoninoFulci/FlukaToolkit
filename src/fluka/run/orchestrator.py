from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fluka.cli.compile import compile_exe
from fluka.run.simconfig import load_sim, resolve


def _run_collect(sim: Path) -> None:
    from fluka.cli.submit import collect_sim

    collect_sim(sim)


def _run_analysis(sim: Path) -> None:
    from fluka.cli.analysis import run_sim

    run_sim(sim)


def _do_grid(sim_path, exe) -> None:
    from fluka.grid.config import load_config, validate_config
    from fluka.grid.run import run_config

    cfg = load_config(resolve(sim_path, "grid"))
    if exe is not None:
        cfg.fluka.custom_executable = str(exe)
    validate_config(cfg)
    run_config(cfg)


def _do_submit(sim_path, exe) -> None:
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.launch_jobs import BACKENDS, run_submission

    args = build_submit_args(resolve(sim_path, "submit"), BACKENDS)
    if exe is not None:
        args.custom_exe = str(exe)
        if getattr(args, "use_dpm", False):
            raise ValueError("use_dpm and custom_exe are mutually exclusive: set only one.")
    run_submission(args)


def launch(sim_path) -> None:
    sim = Path(sim_path)
    data = load_sim(sim)
    exe = None
    if "custom_exe" in data:
        recompile = bool((data.get("general") or {}).get("recompile", False))
        exe = compile_exe(resolve(sim, "custom_exe"), force=recompile)
    grid = data.get("grid") or {}
    if grid.get("parameters"):
        _do_grid(sim, exe)
    else:
        _do_submit(sim, exe)


def analyze_phase(sim_path) -> None:
    sim = Path(sim_path)
    _run_collect(sim)
    _run_analysis(sim)


def main() -> None:
    # An optional positional (`sim`, nargs="?") combined with an `analyze`
    # subparser confuses argparse: the top-level `sim` positional and the
    # subparser's own `sim` positional fight over the same argv token and
    # the same Namespace slot (whichever parses last wins, clobbering the
    # other). Branch on sys.argv instead of relying on subparsers.
    argv = sys.argv[1:]
    if argv and argv[0] == "analyze":
        ap = argparse.ArgumentParser(
            prog="fluka-run analyze",
            description="Collect results and run analysis for a FLUKA simulation",
        )
        ap.add_argument("sim", type=Path)
        args = ap.parse_args(argv[1:])
        try:
            analyze_phase(args.sim)
        except (OSError, ValueError, RuntimeError) as error:
            print(error, file=sys.stderr)
            raise SystemExit(1) from error
        return

    ap = argparse.ArgumentParser(description="Run a FLUKA simulation from one sim.yaml")
    ap.add_argument("sim", type=Path, help="sim.yaml (compile + grid/submit)")
    args = ap.parse_args(argv)
    try:
        launch(args.sim)
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
