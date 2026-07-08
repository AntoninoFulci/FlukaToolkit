from pathlib import Path
import pytest
import yaml
from unittest.mock import patch
from fluka.grid.config import (
    load_config, Config, FlukaConfig, GridConfig, ExecutionConfig, validate_config,
)


RAW = {
    "fluka": {
        "input": "example.inp",
        "custom_executable": None,
        "rfluka_path": None,
    },
    "output": {"directory": "results/"},
    "grid": {
        "parameters": {"beame": [0.05, 0.5], "mat": ["GALLIUM"]},
        "runs_per_combo": 3,
    },
    "execution": {"max_parallel": 4},
}


def test_load_config_from_dict():
    cfg = load_config(RAW)
    assert isinstance(cfg, Config)
    assert cfg.fluka.input == Path("example.inp")
    assert cfg.fluka.custom_executable is None
    assert cfg.fluka.rfluka_path is None
    assert cfg.output_dir == Path("results/")
    assert cfg.grid.parameters == {"beame": [0.05, 0.5], "mat": ["GALLIUM"]}
    assert cfg.grid.runs_per_combo == 3
    assert cfg.execution.max_parallel == 4


def test_load_config_from_file(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(yaml.dump(RAW))
    cfg = load_config(cfg_file)
    assert cfg.grid.runs_per_combo == 3
    # relative paths are resolved relative to the config file's directory
    assert cfg.fluka.input == tmp_path / "example.inp"
    assert cfg.fluka.custom_executable is None


def test_load_config_ignores_unknown_sections():
    # leftover postprocessing / isotope_analysis sections from old configs are ignored
    raw = {**RAW, "postprocessing": {".21": {"executable": "usbsuw"}},
           "isotope_analysis": {"isotopes": {27: 60}}}
    cfg = load_config(raw)
    assert isinstance(cfg, Config)
    assert not hasattr(cfg, "postprocessing")
    assert not hasattr(cfg, "isotope_analysis")


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
    raw = {**RAW, "fluka": {**RAW["fluka"], "input": str(inp)}}
    cfg = load_config(raw)
    with patch("fluka.grid.config.subprocess.run") as mock_run:
        mock_run.return_value.stdout = "/usr/local/fluka/bin\n"
        mock_run.return_value.returncode = 0
        validate_config(cfg)  # should not raise


def test_validate_config_missing_define(tmp_path):
    inp = tmp_path / "example.inp"
    inp.write_text("#define mat GALLIUM\nSTOP\n")  # missing beame
    raw = {**RAW, "fluka": {**RAW["fluka"], "input": str(inp)}}
    cfg = load_config(raw)
    with pytest.raises(ValueError, match="beame"):
        validate_config(cfg)


def test_validate_config_fluka_not_found(tmp_path):
    inp = tmp_path / "example.inp"
    inp.write_text(MINIMAL_INP)
    raw = {**RAW, "fluka": {**RAW["fluka"], "input": str(inp)}}
    cfg = load_config(raw)
    with patch("fluka.grid.config.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(RuntimeError, match="fluka-config"):
            validate_config(cfg)


def test_load_config_use_dpm_default():
    cfg = load_config(RAW)
    assert cfg.fluka.use_dpm is False


def test_load_config_use_dpm_true():
    raw = {**RAW, "fluka": {**RAW["fluka"], "use_dpm": True}}
    cfg = load_config(raw)
    assert cfg.fluka.use_dpm is True


# ---------------------------------------------------------------------------
# backend + dpm guard (submission delegated to FlukaQueueSub)
# ---------------------------------------------------------------------------

def _base_raw(tmp_path, backend="ts", use_dpm=False):
    inp = tmp_path / "sim.inp"
    inp.write_text("#define beame 0.1\nRANDOMIZ          1.        1.\nSTART 1000.\nSTOP\n")
    return {
        "fluka": {"input": str(inp), "rfluka_path": "/fake/bin", "use_dpm": use_dpm},
        "output": {"directory": str(tmp_path / "out")},
        "grid": {"parameters": {"beame": [0.1]}, "runs_per_combo": 1},
        "execution": {"max_parallel": 4, "backend": backend, "queue": "production"},
    }


def test_execution_backend_loaded(tmp_path):
    cfg = load_config(_base_raw(tmp_path, backend="slurm"))
    assert cfg.execution.backend == "slurm"
    assert cfg.execution.queue == "production"


def test_backend_defaults_to_ts(tmp_path):
    raw = _base_raw(tmp_path)
    del raw["execution"]["backend"]
    cfg = load_config(raw)
    assert cfg.execution.backend == "ts"


def test_use_dpm_alone_passes(tmp_path):
    cfg = load_config(_base_raw(tmp_path, backend="ts", use_dpm=True))
    # rfluka_path set in _base_raw, so validate must not raise
    validate_config(cfg)


def test_use_dpm_plus_custom_exe_rejected(tmp_path):
    raw = _base_raw(tmp_path, backend="ts", use_dpm=True)
    raw["fluka"]["custom_executable"] = "/custom/fluka"
    cfg = load_config(raw)
    with pytest.raises(ValueError, match="mutually exclusive"):
        validate_config(cfg)


def test_unknown_backend_rejected(tmp_path):
    cfg = load_config(_base_raw(tmp_path, backend="pbs"))
    with pytest.raises(ValueError, match="backend"):
        validate_config(cfg)
