from pathlib import Path
import pytest
import yaml
from unittest.mock import patch
from fluka.run.simconfig import resolve
from fluka.grid.config import (
    load_config, Config, FlukaConfig, GridConfig, ExecutionConfig, validate_config,
)


def _write_sim(tmp_path, **overrides):
    """Write the canonical v2 sim.yaml (general+submit+grid), with overrides
    merged into the relevant top-level sections."""
    data = {
        "general": {
            "input": "example.inp",
            "backend": "ts",
            "output": "results/",
            "primaries": 1000,
            "use_dpm": False,
        },
        "submit": {
            "njobs": 2,
            "max_parallel": 10,
            "mem": "1500",
            "time": "1-00:00:00",
            "ntasks": 1,
            "nodes": 1,
            "gres": "disk:1G",
            "ncpu": 1,
            "disk": 100000,
            "condor_max_runtime": 86400,
            "queue": None,
            "farm_out": "/farm_out",
        },
        "grid": {
            "parameters": {"beame": [0.1]},
            "runs_per_combo": 2,
        },
    }
    for section, patch_ in overrides.items():
        data.setdefault(section, {})
        data[section].update(patch_)
    p = tmp_path / "sim.yaml"
    p.write_text(yaml.dump(data))
    return p


def test_load_config_from_v2_view(tmp_path):
    (tmp_path / "example.inp").write_text("#define beame 0.5\nSTOP\n")
    p = _write_sim(tmp_path)
    cfg = load_config(resolve(p, "grid"))
    assert isinstance(cfg, Config)
    assert cfg.fluka.input.is_absolute()
    assert cfg.fluka.input.name == "example.inp"
    assert cfg.output_dir.name == "results"
    assert cfg.execution.backend == "ts"
    assert cfg.execution.max_parallel == 10
    assert cfg.execution.farm_out == "/farm_out"
    assert cfg.grid.parameters == {"beame": [0.1]}
    assert cfg.grid.runs_per_combo == 2
    assert cfg.fluka.primaries == 1000


MINIMAL_INP = """\
#define beame 0.5
#define mat GALLIUM
RANDOMIZ         1.0
START         10000.
STOP
"""


def test_validate_config_passes(tmp_path):
    inp = tmp_path / "example.inp"
    inp.write_text(MINIMAL_INP)
    p = _write_sim(tmp_path, grid={"parameters": {"beame": [0.5], "mat": ["GALLIUM"]}})
    cfg = load_config(resolve(p, "grid"))
    with patch("fluka.grid.config.subprocess.run") as mock_run:
        mock_run.return_value.stdout = "/usr/local/fluka/bin\n"
        mock_run.return_value.returncode = 0
        validate_config(cfg)  # should not raise


def test_validate_config_missing_define(tmp_path):
    inp = tmp_path / "example.inp"
    inp.write_text("#define mat GALLIUM\nSTOP\n")  # missing beame
    p = _write_sim(tmp_path, grid={"parameters": {"beame": [0.5]}})
    cfg = load_config(resolve(p, "grid"))
    with pytest.raises(ValueError, match="beame"):
        validate_config(cfg)


def test_validate_config_fluka_not_found(tmp_path):
    inp = tmp_path / "example.inp"
    inp.write_text(MINIMAL_INP)
    p = _write_sim(tmp_path, grid={"parameters": {"beame": [0.5], "mat": ["GALLIUM"]}})
    cfg = load_config(resolve(p, "grid"))
    with patch("fluka.grid.config.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(RuntimeError, match="fluka-config"):
            validate_config(cfg)


def test_load_config_use_dpm_default(tmp_path):
    (tmp_path / "example.inp").write_text(MINIMAL_INP)
    p = _write_sim(tmp_path)
    cfg = load_config(resolve(p, "grid"))
    assert cfg.fluka.use_dpm is False


def test_load_config_use_dpm_true(tmp_path):
    (tmp_path / "example.inp").write_text(MINIMAL_INP)
    p = _write_sim(tmp_path, general={"use_dpm": True})
    cfg = load_config(resolve(p, "grid"))
    assert cfg.fluka.use_dpm is True


# ---------------------------------------------------------------------------
# backend + dpm guard (submission delegated to FlukaQueueSub)
# ---------------------------------------------------------------------------

def _base_sim(tmp_path, backend="ts", use_dpm=False):
    inp = tmp_path / "sim.inp"
    inp.write_text("#define beame 0.1\nRANDOMIZ          1.        1.\nSTART 1000.\nSTOP\n")
    return _write_sim(
        tmp_path,
        general={
            "input": "sim.inp",
            "backend": backend,
            "output": str(tmp_path / "out"),
            "rfluka_path": "/fake/bin",
            "use_dpm": use_dpm,
        },
        submit={"queue": "production"},
        grid={"parameters": {"beame": [0.1]}, "runs_per_combo": 1},
    )


def test_execution_backend_loaded(tmp_path):
    p = _base_sim(tmp_path, backend="slurm")
    cfg = load_config(resolve(p, "grid"))
    assert cfg.execution.backend == "slurm"
    assert cfg.execution.queue == "production"


def test_backend_defaults_to_ts(tmp_path):
    inp = tmp_path / "sim.inp"
    inp.write_text("#define beame 0.1\nRANDOMIZ          1.        1.\nSTART 1000.\nSTOP\n")
    p = _write_sim(
        tmp_path,
        general={
            "input": "sim.inp",
            "output": str(tmp_path / "out"),
            "rfluka_path": "/fake/bin",
        },
        grid={"parameters": {"beame": [0.1]}, "runs_per_combo": 1},
    )
    # remove backend from general so it defaults
    raw = yaml.safe_load(p.read_text())
    del raw["general"]["backend"]
    p.write_text(yaml.dump(raw))
    cfg = load_config(resolve(p, "grid"))
    assert cfg.execution.backend == "ts"


def test_use_dpm_alone_passes(tmp_path):
    p = _base_sim(tmp_path, backend="ts", use_dpm=True)
    cfg = load_config(resolve(p, "grid"))
    # rfluka_path set in _base_sim, so validate must not raise
    validate_config(cfg)


def test_use_dpm_plus_custom_exe_rejected(tmp_path):
    p = _base_sim(tmp_path, backend="ts", use_dpm=True)
    raw = yaml.safe_load(p.read_text())
    raw["general"]["custom_executable"] = "/custom/fluka"
    p.write_text(yaml.dump(raw))
    cfg = load_config(resolve(p, "grid"))
    with pytest.raises(ValueError, match="mutually exclusive"):
        validate_config(cfg)


def test_unknown_backend_rejected(tmp_path):
    p = _base_sim(tmp_path, backend="pbs")
    cfg = load_config(resolve(p, "grid"))
    with pytest.raises(ValueError, match="backend"):
        validate_config(cfg)
