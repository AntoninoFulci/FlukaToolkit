from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fluka.queue.core.config import build_submit_args
from fluka.queue.launch_jobs import (
    BACKENDS,
    configure_logging,
    log_submission_batch,
    run_submission,
)
from fluka.queue.service import SubmissionBatchError
from fluka.run.simconfig import resolve


class CollectionError(RuntimeError):
    """Raised when submitted run results cannot be collected safely."""


def run_sim(path) -> None:
    run_submission(build_submit_args(resolve(path, "submit"), BACKENDS))


def collect_sim(path) -> None:
    """Collect ROOT files produced by a submitted run into root_files/.

    Collect from general.output, resolved relative to sim.yaml.
    """
    from fluka.queue import collect_results

    output_dir = Path(resolve(path, "submit")["output"])
    if collect_results.main(output_dir) != 0:
        raise CollectionError(f"collection failed for {output_dir}")


def main() -> None:
    configure_logging()
    ap = argparse.ArgumentParser(description="FLUKA job submission")
    ap.add_argument("config", type=Path, help="submit config.yaml or sim.yaml")
    ap.add_argument("--grid", action="store_true", help="run grid generation before submitting")
    args = ap.parse_args()
    try:
        if args.grid:
            from fluka.cli.grid import run_sim as run_grid

            run_grid(args.config)
            return
        run_sim(args.config)
    except SubmissionBatchError as error:
        log_submission_batch(error)
        raise SystemExit(1) from error
    except (OSError, ValueError, RuntimeError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
