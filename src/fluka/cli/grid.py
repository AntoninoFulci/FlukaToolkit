from __future__ import annotations
import argparse
from pathlib import Path

from fluka.cli._common import resolve_config
from fluka.grid.config import load_config, validate_config
from fluka.grid.run import run_config


def run_sim(path) -> None:
    cfg, mode = resolve_config(path, "grid")
    source = cfg if mode == "section" else path
    config = load_config(source)
    validate_config(config)
    run_config(config)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="FLUKA grid search launcher: generate input files and submit "
                     "them to the farm."
    )
    ap.add_argument("config", type=Path, help="grid config.yaml or sim.yaml")
    run_sim(ap.parse_args().config)
