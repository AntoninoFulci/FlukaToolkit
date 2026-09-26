#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from fluka.grid.backends import queue_adapter
from fluka.grid.backends.queue_adapter import manifest_extra
from fluka.grid.config import load_config, validate_config
from fluka.grid.grid import combo_name, generate_combinations
from fluka.grid.seeds import find_duplicate_seeds, next_seed, scan_used_seeds
from fluka.grid.workspace import create_run_workspace, patch_inp, reseed_inp
from fluka.run.manifest import Job, manifest_path_for, parse_job_id, record_job
from fluka.run.simconfig import resolve


def _parse_args():
    import argparse

    p = argparse.ArgumentParser(
        description="FLUKA grid search launcher: generate input files and submit them "
        "to the farm via FlukaQueueSub."
    )
    p.add_argument("config", type=Path)
    p.add_argument("--reset", action="store_true", help="Delete output dir and start fresh")
    p.add_argument("--dry-run", action="store_true", help="Print commands without submitting")
    p.add_argument(
        "--check-seeds",
        action="store_true",
        help="Audit the output dir for duplicate RANDOMIZ seeds and exit",
    )
    return p.parse_args()


def _print_summary(config, args, rfluka_bin) -> None:
    from math import prod

    from colorama import Fore, Style
    from colorama import init as colorama_init
    from tabulate import tabulate

    colorama_init(autoreset=True)
    C, M, B, Y, G = Fore.CYAN, Fore.MAGENTA, Fore.BLUE, Fore.YELLOW, Fore.GREEN
    RE = Style.RESET_ALL

    n_combos = prod(len(v) for v in config.grid.parameters.values())
    n_jobs = n_combos * config.grid.runs_per_combo

    rows = [["Field", "Value"]]
    rows.append([f"{C}Config{RE}", f"{M}{args.config}{RE}"])
    rows.append([f"{C}Input{RE}", f"{M}{config.fluka.input}{RE}"])
    rows.append([f"{C}Output dir{RE}", f"{M}{config.output_dir}{RE}"])
    rows.append([f"{C}Backend{RE}", f"{M}{config.execution.backend}{RE}"])
    rows.append([f"{C}rfluka bin{RE}", f"{M}{rfluka_bin}{RE}"])
    if config.fluka.custom_executable:
        rows.append([f"{C}Custom exe{RE}", f"{M}{config.fluka.custom_executable}{RE}"])
    if config.fluka.primaries:
        rows.append([f"{C}Primaries{RE}", f"{M}{config.fluka.primaries}{RE}"])
    rows.append(["", ""])
    for param, values in config.grid.parameters.items():
        rows.append([f"{B}  {param}{RE}", f"{Y}{', '.join(str(v) for v in values)}{RE}"])
    rows.append(["", ""])
    rows.append([f"{C}Runs / combo{RE}", f"{M}{config.grid.runs_per_combo}{RE}"])
    rows.append([f"{C}Max parallel{RE}", f"{M}{config.execution.max_parallel}{RE}"])
    rows.append([f"{G}Total combos{RE}", f"{G}{n_combos}{RE}"])
    rows.append([f"{G}Total jobs{RE}", f"{G}{n_jobs}{RE}"])
    rows.append([f"{Y}Dry run{RE}", f"{Y}{args.dry_run}{RE}"])

    print(tabulate(rows, headers="firstrow", tablefmt="simple_outline"))

    if not args.dry_run:
        confirm = input("Proceed with launching jobs? (yes/no): ")
        if confirm.strip().lower() not in ("yes", "y"):
            print("Aborted.")
            sys.exit(0)


def _resolve_rfluka(config) -> Path:
    import subprocess

    if config.fluka.rfluka_path:
        return Path(config.fluka.rfluka_path)
    result = subprocess.run(["fluka-config", "--bin"], capture_output=True, text=True, check=True)
    return Path(result.stdout.strip())


def _set_ts_slots(max_parallel: int) -> None:
    """Set the task-spooler slot count (local concurrency) before submitting."""
    import subprocess

    subprocess.run(["ts", "-S", str(max_parallel)], check=False)


def _submit_combo(params, config, rfluka_bin, args) -> None:
    name = combo_name(params)
    n_runs = config.grid.runs_per_combo

    # Phase 1: prepare every run (dir + patched .inp + unique seed)
    used = scan_used_seeds(config.output_dir)
    prepared = []  # (run_idx, run_name, run_dir, inp_path)
    for i in range(1, n_runs + 1):
        run_name = f"run_{i:04d}"
        run_dir = create_run_workspace(config.output_dir, name, i)
        seed = next_seed(used)
        inp_path = run_dir / f"simulation_{i:04d}.inp"
        patch_inp(config.fluka.input, inp_path, params, seed, config.fluka.primaries)
        prepared.append((i, run_name, run_dir, inp_path))

    # Phase 2: repair any duplicate seeds in place (do NOT abort) and continue
    dups = find_duplicate_seeds(config.output_dir)
    if dups:
        used = scan_used_seeds(config.output_dir)
        current = {ip for (_, _, _, ip) in prepared}
        for seed, files in sorted(dups.items()):
            shared = ", ".join(f"{f.parent.parent.name}/{f.parent.name}" for f in files)
            print(f"[seed] duplicate seed {seed} found in: {shared}")
            # keep one file (prefer one outside this combo, likely already submitted);
            # regenerate the rest with fresh unique seeds, then keep going
            ordered = sorted(files, key=lambda f: f in current)
            for f in ordered[1:]:
                new = next_seed(used)
                reseed_inp(f, new)
                print(f"[seed]   {f.parent.parent.name}/{f.parent.name}: reseeded {seed} -> {new}")

    # Phase 3: submit every run via FlukaQueueSub (submit-only; no monitoring here)
    for i, run_name, run_dir, inp_path in prepared:
        job_id = queue_adapter.submit_run(
            backend_name=config.execution.backend,
            config=config,
            run_dir=run_dir,
            inp_filename=inp_path.name,
            iteration=i,
            fluka_bin=str(rfluka_bin),
            dry_run=args.dry_run,
        )
        print(f"[{config.execution.backend}] {name}/{run_name}: {job_id}")
        if not args.dry_run:
            record_job(
                manifest_path_for(config.output_dir),
                Job(
                    combo=name,
                    run_idx=i,
                    run_name=run_name,
                    run_dir=str(run_dir),
                    backend=config.execution.backend,
                    job_id=parse_job_id(config.execution.backend, job_id),
                    input_file=inp_path.name,
                    submitted_at=datetime.now(timezone.utc).isoformat(),
                    extra=manifest_extra(config.execution.backend, config, run_dir, inp_path.name),
                ),
            )

    print(
        f"Submitted {name}: {n_runs} runs via {config.execution.backend}. "
        f"Monitoring, post-processing and analysis are handled by FlukaQueueSub / "
        f"FlukaIsotopeAnalysis."
    )


def run_config(config, *, dry_run: bool = False, reset: bool = False) -> None:
    """Run the grid submission for an already-loaded, validated `Config`.

    This is the reusable seam for other entrypoints (e.g. `fluka.cli.grid`)
    that already have a `Config` object and don't want to go through argv.
    """
    from types import SimpleNamespace

    args = SimpleNamespace(dry_run=dry_run, reset=reset, config=config.fluka.input)

    if reset:
        import shutil

        if config.output_dir.exists():
            confirm = input(f"Delete {config.output_dir} and all contents? [yes/N] ")
            if confirm.strip().lower() not in ("yes", "y"):
                print("Aborted.")
                sys.exit(0)
            shutil.rmtree(config.output_dir)
            print(f"Deleted {config.output_dir}")

    config.output_dir.mkdir(parents=True, exist_ok=True)

    rfluka_bin = _resolve_rfluka(config)
    _print_summary(config, args, rfluka_bin)

    if config.execution.backend == "ts" and not dry_run:
        _set_ts_slots(config.execution.max_parallel)

    for params in generate_combinations(config.grid.parameters):
        _submit_combo(params, config, rfluka_bin, args)


def main() -> None:
    args = _parse_args()

    config = load_config(resolve(args.config, "grid"))
    validate_config(config)

    if args.check_seeds:
        dups = find_duplicate_seeds(config.output_dir)
        if dups:
            for seed, files in sorted(dups.items()):
                shared = ", ".join(f"{f.parent.parent.name}/{f.parent.name}" for f in files)
                print(f"duplicate seed {seed}: {shared}")
            sys.exit(f"{len(dups)} duplicate seed(s) found in {config.output_dir}")
        print(f"No duplicate seeds in {config.output_dir}")
        return

    run_config(config, dry_run=args.dry_run, reset=args.reset)


if __name__ == "__main__":
    main()
