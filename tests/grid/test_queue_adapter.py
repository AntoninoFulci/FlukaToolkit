import pytest
from pathlib import Path
from types import SimpleNamespace

from fluka.grid.backends import queue_adapter


def _config(backend):
    execution = SimpleNamespace(
        backend=backend, queue=None, mem="2000", time="2-00:00:00",
        ntasks=1, nodes=1, gres="disk:1G", ncpu=2, disk=100000,
        condor_max_runtime=86400, max_parallel=4,
    )
    fluka = SimpleNamespace(custom_executable=None, use_dpm=False)
    return SimpleNamespace(execution=execution, fluka=fluka)


def test_submit_run_ts_dpm_passes_d_flag(tmp_path):
    run_dir = tmp_path / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    (run_dir / "simulation_0001.inp").write_text("RANDOMIZ 1. 1.\n")
    cfg = _config("ts")
    cfg.fluka.use_dpm = True
    result = queue_adapter.submit_run(
        backend_name="ts", config=cfg, run_dir=run_dir,
        inp_filename="simulation_0001.inp", iteration=1,
        fluka_bin="/fake/fluka/bin", dry_run=True,
    )
    assert "-d" in result.split()
    assert "-e" not in result.split()


def test_build_namespace_slurm_defaults_queue():
    ns = queue_adapter._build_namespace("slurm", _config("slurm"), dry_run=True)
    assert ns.queue == "production"
    assert ns.mem == "2000"
    assert ns.gres == "disk:1G"
    assert ns.dry_run is True


def test_build_namespace_condor_defaults_universe():
    ns = queue_adapter._build_namespace("condor", _config("condor"), dry_run=True)
    assert ns.queue == "vanilla"
    assert ns.ncpu == 2
    assert ns.time == 86400


def test_submit_run_slurm_dry_run(tmp_path):
    run_dir = tmp_path / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    (run_dir / "simulation_0001.inp").write_text("RANDOMIZ 1. 1.\n")
    result = queue_adapter.submit_run(
        backend_name="slurm",
        config=_config("slurm"),
        run_dir=run_dir,
        inp_filename="simulation_0001.inp",
        iteration=1,
        fluka_bin="/fake/fluka/bin",
        dry_run=True,
    )
    assert result.startswith("[dry run] sbatch")
    # generate_script wrote the job script into the run dir
    assert (run_dir / "job_0001.sh").exists()


def test_build_namespace_unknown_backend_raises():
    cfg = SimpleNamespace(
        execution=SimpleNamespace(
            backend="pbs", queue=None, mem="1500", time="1-00:00:00",
            ntasks=1, nodes=1, gres="disk:1G", ncpu=1, disk=100000,
            condor_max_runtime=86400, max_parallel=4,
        ),
        fluka=SimpleNamespace(custom_executable=None),
    )
    with pytest.raises(ValueError, match="Unknown backend"):
        queue_adapter._build_namespace("pbs", cfg, dry_run=True)


def test_build_namespace_ts_minimal():
    ns = queue_adapter._build_namespace("ts", _config("ts"), dry_run=True)
    assert ns.dry_run is True
    # ts has no queue/cluster attrs
    assert not hasattr(ns, "queue")


def test_submit_run_ts_dry_run(tmp_path):
    run_dir = tmp_path / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    (run_dir / "simulation_0001.inp").write_text("RANDOMIZ 1. 1.\n")
    result = queue_adapter.submit_run(
        backend_name="ts",
        config=_config("ts"),
        run_dir=run_dir,
        inp_filename="simulation_0001.inp",
        iteration=1,
        fluka_bin="/fake/fluka/bin",
        dry_run=True,
    )
    assert result.startswith("[dry run] ts rfluka")


def test_build_namespace_lsf_has_expected_attrs():
    ns = queue_adapter._build_namespace("lsf", _config("lsf"), dry_run=True)
    assert ns.queue == "normal"          # lsf default
    assert ns.mem == "2000"
    assert ns.ntasks == 1
    assert ns.time == "2-00:00:00"
    # lsf namespace must NOT carry slurm-only attrs
    assert not hasattr(ns, "nodes")
    assert not hasattr(ns, "gres")


def test_submit_run_condor_dry_run(tmp_path):
    run_dir = tmp_path / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    (run_dir / "simulation_0001.inp").write_text("RANDOMIZ 1. 1.\n")
    result = queue_adapter.submit_run(
        backend_name="condor",
        config=_config("condor"),
        run_dir=run_dir,
        inp_filename="simulation_0001.inp",
        iteration=1,
        fluka_bin="/fake/fluka/bin",
        dry_run=True,
    )
    assert result.startswith("[dry run] condor_submit")
    assert (run_dir / "job_0001.sh").exists()
