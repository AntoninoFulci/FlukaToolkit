from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AnalysisConfig:
    directory: Path
    units: list[int]
    isotopes: list[tuple[int, int]]
    volume: float
    executable: str = "usrsuw"
    output: str = "isotopes.xlsx"


def load_analysis_config(view: dict) -> AnalysisConfig:
    for field in ("run", "units", "volume", "isotopes"):
        if field not in view:
            raise ValueError(f"analysis.{field} is required")
    base = view.get("_general_output")
    if not base:
        raise ValueError("general.output is required to locate the analysis run")
    directory = Path(base) / view["run"]
    if not directory.exists():
        raise ValueError(f"analysis run directory does not exist: {directory}")
    units = [int(u) for u in view["units"]]
    if not units:
        raise ValueError("analysis.units must list at least one unit number")
    isotopes: list[tuple[int, int]] = []
    for k, v in view["isotopes"].items():
        z = int(k)
        for mass in v if isinstance(v, list) else [v]:
            isotopes.append((z, int(mass)))
    isotopes.sort()
    if not isotopes:
        raise ValueError("analysis.isotopes must list at least one Z: A pair")
    return AnalysisConfig(
        directory=directory,
        units=units,
        isotopes=isotopes,
        volume=float(view["volume"]),
        executable=view.get("executable", "usrsuw"),
        output=view.get("output", "isotopes.xlsx"),
    )
