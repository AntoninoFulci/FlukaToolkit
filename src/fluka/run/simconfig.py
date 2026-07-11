from __future__ import annotations
from pathlib import Path
import yaml

GENERAL_KEYS = ("input", "backend", "output", "primaries",
                "use_dpm", "custom_executable", "rfluka_path")

# keys whose values are filesystem paths, resolved relative to the config dir
_PATH_KEYS = ("input", "output", "custom_executable", "rfluka_path")


def load_sim(path) -> dict:
    p = Path(path)
    data = yaml.safe_load(p.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{p}: top level must be a mapping")
    if "general" not in data or not isinstance(data["general"], dict):
        raise ValueError(f"{p}: missing required 'general' section")
    return data


def resolve(path, tool: str) -> dict:
    p = Path(path)
    data = load_sim(p)
    config_dir = p.parent
    merged: dict = {}
    # general provides defaults
    for k, v in data["general"].items():
        merged[k] = v
    # grid reuses submit's batch-resource defaults (max_parallel, mem, farm_out, ...)
    if tool == "grid":
        submit_section = data.get("submit") or {}
        if isinstance(submit_section, dict):
            for k, v in submit_section.items():
                merged[k] = v
    # tool section overrides / adds
    section = data.get(tool) or {}
    if not isinstance(section, dict):
        raise ValueError(f"{p}: section '{tool}' must be a mapping")
    for k, v in section.items():
        merged[k] = v
    # resolve path-valued keys relative to the config dir
    for k in _PATH_KEYS:
        if merged.get(k):
            pv = Path(merged[k])
            merged[k] = str(pv if pv.is_absolute() else (config_dir / pv))
    # routines: list of paths relative to config dir
    if merged.get("routines"):
        merged["routines"] = [
            str(Path(r) if Path(r).is_absolute() else (config_dir / r))
            for r in merged["routines"]
        ]
    # keep the shared general.output available under a non-clashing name so an
    # analysis section's `output` (an xlsx filename) never overwrites the dir
    if data["general"].get("output"):
        base = Path(data["general"]["output"])
        merged["_general_output"] = str(base if base.is_absolute() else (config_dir / base))
    merged["_config_dir"] = str(config_dir)
    return merged
