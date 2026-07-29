from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re
import subprocess


@dataclass
class FlukaConfig:
    input: Path
    custom_executable: Optional[str] = None
    rfluka_path: Optional[str] = None
    primaries: Optional[int] = None
    use_dpm: bool = False


@dataclass
class GridConfig:
    parameters: dict[str, list]
    runs_per_combo: int


@dataclass
class ExecutionConfig:
    max_parallel: int
    backend: str = "ts"          # ts | slurm | lsf | condor
    queue: Optional[str] = None  # partition (slurm) / queue (lsf) / universe (condor)
    mem: str = "1500"
    time: str = "1-00:00:00"     # slurm/lsf time limit D-HH:MM:SS
    ntasks: int = 1
    nodes: int = 1
    gres: str = "disk:1G"        # slurm only
    ncpu: int = 1                # condor only
    disk: int = 100000           # condor request_disk (kB)
    condor_max_runtime: int = 86400  # condor +MaxRuntime (seconds)
    farm_out: str = "/farm_out"        # slurm: accessible out/err/sentinel dir


@dataclass
class Config:
    fluka: FlukaConfig
    output_dir: Path
    grid: GridConfig
    execution: ExecutionConfig


def load_config(view: dict) -> Config:
    inp = Path(view["input"])          # already resolved by simconfig.resolve
    return Config(
        fluka=FlukaConfig(
            input=inp,
            custom_executable=view.get("custom_executable"),
            rfluka_path=view.get("rfluka_path"),
            primaries=view.get("primaries"),
            use_dpm=bool(view.get("use_dpm", False)),
        ),
        output_dir=Path(view["output"]),
        grid=GridConfig(
            parameters=view["parameters"],
            runs_per_combo=view["runs_per_combo"],
        ),
        execution=ExecutionConfig(
            max_parallel=int(view.get("max_parallel", 1)),
            backend=view.get("backend", "ts"),
            queue=view.get("queue"),
            mem=str(view.get("mem", "1500")),
            time=view.get("time", "1-00:00:00"),
            ntasks=int(view.get("ntasks", 1)),
            nodes=int(view.get("nodes", 1)),
            gres=view.get("gres", "disk:1G"),
            ncpu=int(view.get("ncpu", 1)),
            disk=int(view.get("disk", 100000)),
            condor_max_runtime=int(view.get("condor_max_runtime", 86400)),
            farm_out=view.get("farm_out", "/farm_out"),
        ),
    )


def validate_config(config: Config) -> None:
    inp_text = config.fluka.input.read_text()
    for param in config.grid.parameters:
        if not re.search(rf"^#define\s+{re.escape(param)}\s", inp_text, re.MULTILINE):
            raise ValueError(
                f"Parameter '{param}' not found as '#define {param}' in {config.fluka.input}"
            )

    if config.fluka.rfluka_path is None:
        try:
            subprocess.run(
                ["fluka-config", "--bin"],
                capture_output=True, text=True, check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise RuntimeError(
                "fluka-config not found. Install FLUKA or set fluka.rfluka_path in config."
            ) from exc

    valid_backends = {"ts", "slurm", "lsf", "condor"}
    if config.execution.backend not in valid_backends:
        raise ValueError(
            f"Unknown execution.backend {config.execution.backend!r}. "
            f"Valid: {sorted(valid_backends)}"
        )

    if config.fluka.use_dpm and config.fluka.custom_executable:
        raise ValueError(
            "fluka.use_dpm and fluka.custom_executable are mutually exclusive; "
            "set only one."
        )
