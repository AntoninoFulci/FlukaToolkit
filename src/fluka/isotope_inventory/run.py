#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

from fluka.run.simconfig import resolve
from fluka.isotope_inventory.config import load_analysis_config
from fluka.isotope_inventory.analysis import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse a single FLUKA simulation directory (RESNUCLEi isotopes)."
    )
    parser.add_argument("config", type=Path, help="path to sim.yaml")
    args = parser.parse_args()

    config = load_analysis_config(resolve(args.config, "analysis"))
    run_analysis(config)


if __name__ == "__main__":
    main()
