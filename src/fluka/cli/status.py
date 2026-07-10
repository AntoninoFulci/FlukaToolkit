from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

from tabulate import tabulate

from fluka.cli._common import resolve_config
from fluka.grid.backends.queue_adapter import BACKENDS as _BACKEND_CLASSES
from fluka.run.manifest import load_manifest, manifest_path_for
from fluka.run import status as S
from fluka.run.status import resolve_all, all_terminal, summary_counts
from fluka.run.orchestrator import analyze_phase


def _output_dir(cfg: dict) -> Path:
    try:
        return Path(cfg["output"]["directory"])
    except (KeyError, TypeError):
        raise KeyError("config has no output.directory to locate the job manifest")


def _backends():
    return {name: cls() for name, cls in _BACKEND_CLASSES.items()}


def build_status(cfg_path) -> list[S.JobStatus]:
    cfg, mode = resolve_config(cfg_path, "grid")
    if mode == "standalone" and "output" not in cfg and "grid" in cfg:
        # sim.yaml with only a `grid:` section (no sibling sections) is passed
        # through unwrapped by resolve_config; unwrap it here.
        cfg = cfg["grid"]
    out_dir = _output_dir(cfg)
    jobs = load_manifest(manifest_path_for(out_dir))
    if not jobs:
        print(f"no jobs recorded for {out_dir}; run fluka-grid / fluka-run submit first",
              file=sys.stderr)
        raise SystemExit(1)
    return resolve_all(jobs, _backends())


def render_table(statuses) -> str:
    rows = [[s.job.combo, s.job.run_name, s.job.backend, s.state, s.detail]
            for s in statuses]
    table = tabulate(rows, headers=["combo", "run", "backend", "state", "detail"])
    counts = summary_counts(statuses)
    summary = "  ".join(f"{k}={v}" for k, v in counts.items() if v)
    return f"{table}\n\n{summary}"


def _emit(statuses, as_json: bool) -> None:
    if as_json:
        print(json.dumps([
            {"combo": s.job.combo, "run": s.job.run_name, "backend": s.job.backend,
             "state": s.state, "detail": s.detail} for s in statuses
        ]))
    else:
        print(render_table(statuses))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Report FLUKA job status")
    ap.add_argument("config", type=Path, help="sim.yaml or grid config")
    ap.add_argument("--watch", nargs="?", const=15, type=int, default=None,
                    metavar="SEC", help="poll every SEC seconds until all jobs finish")
    ap.add_argument("--collect", action="store_true",
                    help="when all jobs are DONE, run collect+analyze")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args(argv)

    if args.watch is not None:
        while True:
            statuses = build_status(args.config)
            _emit(statuses, args.json)
            if all_terminal(statuses):
                break
            time.sleep(args.watch)
    else:
        statuses = build_status(args.config)
        _emit(statuses, args.json)

    if args.collect:
        statuses = build_status(args.config)
        if not all_terminal(statuses):
            print("jobs still pending; nothing to collect yet", file=sys.stderr)
            return
        failed = [s for s in statuses if s.state == S.FAIL]
        if failed:
            names = ", ".join(f"{s.job.combo}/{s.job.run_name}" for s in failed)
            print(f"refusing to collect: failed jobs: {names}", file=sys.stderr)
            raise SystemExit(1)
        analyze_phase(args.config)


if __name__ == "__main__":
    main()
