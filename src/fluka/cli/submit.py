from __future__ import annotations
import argparse
import tempfile
import yaml
from pathlib import Path

from fluka.cli._common import resolve_config
from fluka.queue.core.config import load_yaml_config
from fluka.queue.launch_jobs import BACKENDS, run_from_args


def _section_to_tempfile(section: dict) -> str:
    fh = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    yaml.safe_dump(section, fh)
    fh.close()
    return fh.name


def run_sim(path) -> None:
    cfg, mode = resolve_config(path, "submit")
    src = str(path) if mode == "standalone" else _section_to_tempfile(cfg)
    args = load_yaml_config(src, BACKENDS)
    run_from_args(args)


def main() -> None:
    ap = argparse.ArgumentParser(description="FLUKA job submission")
    ap.add_argument("config", type=Path, help="submit config.yaml or sim.yaml")
    run_sim(ap.parse_args().config)
