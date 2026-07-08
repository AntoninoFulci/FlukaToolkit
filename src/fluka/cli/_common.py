from __future__ import annotations
from pathlib import Path
from fluka.run.config import load_sim, SECTIONS


def resolve_config(path: str | Path, tool: str) -> tuple[dict, str]:
    """Return (config_dict, mode). mode is 'section' if `path` is a multi-section
    sim.yaml (contains a SECTIONS key other than `tool`), else 'standalone'."""
    data = load_sim(path)
    others = [k for k in SECTIONS if k != tool and k in data]
    if others:
        if tool not in data:
            raise KeyError(f"sim file has sections {others} but no '{tool}' section")
        return data[tool], "section"
    return data, "standalone"
