import sys
import pytest
import yaml as _yaml
from argparse import Namespace
from unittest.mock import patch

from backends.slurm import SlurmBackend
from backends.ts import TSBackend
from launch_jobs import _apply_benchmark_overrides


def test_apply_quick_overrides_njobs_nprim_queue():
    backend = SlurmBackend()
    args = Namespace(njobs=10, nprim=50000, queue="production",
                     benchmark_priority_queue="priority")
    _apply_benchmark_overrides(args, "quick", backend)
    assert args.njobs == 2
    assert args.nprim == 100
    assert args.queue == "priority"


def test_apply_extensive_overrides_njobs_nprim_only():
    backend = SlurmBackend()
    args = Namespace(njobs=10, nprim=50000, queue="production")
    _apply_benchmark_overrides(args, "extensive", backend)
    assert args.njobs == 5
    assert args.nprim == 1000
    assert args.queue == "production"  # unchanged


def test_apply_unknown_mode_raises():
    backend = SlurmBackend()
    args = Namespace(njobs=1, nprim=100)
    with pytest.raises(ValueError, match="Modalita'"):
        _apply_benchmark_overrides(args, "turbo", backend)


def test_apply_quick_without_priority_queue_raises():
    backend = SlurmBackend()
    args = Namespace(njobs=10, nprim=50000, queue="production")
    with pytest.raises(ValueError, match="benchmark_priority_queue"):
        _apply_benchmark_overrides(args, "quick", backend)


def test_apply_ts_quick_noop_on_queue():
    backend = TSBackend()
    args = Namespace(njobs=10, nprim=50000, benchmark_priority_queue="priority")
    attrs_before = set(vars(args))
    _apply_benchmark_overrides(args, "quick", backend)
    assert args.njobs == 2
    assert args.nprim == 100
    assert set(vars(args)) == attrs_before  # nothing added or removed


def test_benchmark_quick_single_yaml_creates_2_job_dirs(tmp_path, monkeypatch):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({
        "backend": "ts", "input": str(inp), "njobs": 10, "dry_run": True,
        "benchmark_priority_queue": "priority",
    }))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", "benchmark", "quick", str(cfg)]

    with patch("core.fluka.detect_fluka_path", return_value=("/usr/local/bin", "/usr/local")), \
         patch("core.display.confirm", return_value=True):
        import importlib
        import launch_jobs
        importlib.reload(launch_jobs)
        launch_jobs.main()

    output_dir = tmp_path / "sim"
    assert output_dir.is_dir()
    assert len(list(output_dir.iterdir())) == 2


def test_benchmark_extensive_single_yaml_creates_5_job_dirs(tmp_path, monkeypatch):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({
        "backend": "ts", "input": str(inp), "njobs": 10, "dry_run": True,
    }))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", "benchmark", "extensive", str(cfg)]

    with patch("core.fluka.detect_fluka_path", return_value=("/usr/local/bin", "/usr/local")), \
         patch("core.display.confirm", return_value=True):
        import importlib
        import launch_jobs
        importlib.reload(launch_jobs)
        launch_jobs.main()

    output_dir = tmp_path / "sim"
    assert output_dir.is_dir()
    assert len(list(output_dir.iterdir())) == 5


def test_benchmark_quick_missing_priority_queue_exits(tmp_path, monkeypatch):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({
        "backend": "ts", "input": str(inp), "njobs": 10, "dry_run": True,
    }))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", "benchmark", "quick", str(cfg)]

    with patch("core.fluka.detect_fluka_path", return_value=("/usr/local/bin", "/usr/local")):
        import importlib
        import launch_jobs
        importlib.reload(launch_jobs)
        with pytest.raises(SystemExit):
            launch_jobs.main()


def test_benchmark_wrong_arg_count_exits():
    sys.argv = ["launch_jobs.py", "benchmark", "quick"]  # missing target

    import importlib
    import launch_jobs
    importlib.reload(launch_jobs)
    with pytest.raises(SystemExit):
        launch_jobs.main()


def test_benchmark_unknown_mode_exits(tmp_path, monkeypatch):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({
        "backend": "ts", "input": str(inp), "njobs": 1, "dry_run": True,
    }))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", "benchmark", "ultra", str(cfg)]

    with patch("core.fluka.detect_fluka_path", return_value=("/usr/local/bin", "/usr/local")), \
         patch("core.display.confirm", return_value=True):
        import importlib
        import launch_jobs
        importlib.reload(launch_jobs)
        with pytest.raises(SystemExit):
            launch_jobs.main()


def test_benchmark_folder_mode_extensive(tmp_path, monkeypatch):
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    for stem in ["sim_a", "sim_b"]:
        inp = tmp_path / f"{stem}.inp"
        inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")
        (configs_dir / f"{stem}.yaml").write_text(_yaml.dump({
            "backend": "ts", "input": str(inp), "njobs": 10, "dry_run": True,
        }))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", "benchmark", "extensive", str(configs_dir)]

    with patch("core.fluka.detect_fluka_path", return_value=("/usr/local/bin", "/usr/local")), \
         patch("core.display.confirm", return_value=True):
        import importlib
        import launch_jobs
        importlib.reload(launch_jobs)
        launch_jobs.main()

    output_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name != "configs"]
    assert len(output_dirs) == 2
    for od in output_dirs:
        assert len(list(od.iterdir())) == 5  # extensive: njobs=5


def test_benchmark_folder_mode_cancelled(tmp_path, monkeypatch, caplog):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "a.yaml").write_text(_yaml.dump({
        "backend": "ts", "input": str(inp), "njobs": 10, "dry_run": True,
    }))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", "benchmark", "extensive", str(configs_dir)]

    import logging
    with patch("core.fluka.detect_fluka_path", return_value=("/usr/local/bin", "/usr/local")), \
         patch("core.display.confirm", return_value=False), \
         caplog.at_level(logging.INFO):
        import importlib
        import launch_jobs
        importlib.reload(launch_jobs)
        launch_jobs.main()

    assert "annullato" in caplog.text
    output_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name != "configs"]
    assert len(output_dirs) == 0
