from __future__ import annotations
import argparse
from pathlib import Path

from fluka.isotope_inventory.config import load_analysis_config
from fluka.isotope_inventory.analysis import run_analysis


def run_sim(path) -> None:
    run_analysis(load_analysis_config(path))


def main() -> None:
    ap = argparse.ArgumentParser(description="FLUKA RESNUCLEi isotope inventory")
    ap.add_argument("config", type=Path, help="analysis.yaml or sim.yaml")
    run_sim(ap.parse_args().config)
