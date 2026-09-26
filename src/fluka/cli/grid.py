from __future__ import annotations

import argparse
from pathlib import Path

from fluka.grid.config import load_config, validate_config
from fluka.grid.run import run_config
from fluka.run.simconfig import resolve


def run_sim(path) -> None:
    config = load_config(resolve(path, "grid"))
    validate_config(config)
    run_config(config)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="FLUKA grid search launcher: generate input files and submit them to the farm."
    )
    ap.add_argument("config", type=Path, help="grid config.yaml or sim.yaml")
    run_sim(ap.parse_args().config)
