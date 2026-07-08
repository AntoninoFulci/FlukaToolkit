from __future__ import annotations
from pathlib import Path
import yaml

SECTIONS = ("grid", "submit", "analysis", "root")

def load_sim(path: str | Path) -> dict:
    with open(path) as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping of sections")
    return data

def section(data: dict, name: str) -> dict:
    if name not in data:
        raise KeyError(f"section '{name}' missing from sim config (have: {sorted(data)})")
    return data[name]

def extract(path: str | Path, name: str) -> dict:
    return section(load_sim(path), name)
