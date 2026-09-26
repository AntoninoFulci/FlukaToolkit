import getpass
from types import SimpleNamespace
from fluka.grid.backends.queue_adapter import _build_submission_config, manifest_extra


def _config(backend="slurm", farm_out="/myfarm"):
    ex = SimpleNamespace(backend=backend, queue=None, mem="1500", ntasks=1, nodes=1,
                         time="1-00:00:00", gres="disk:1G", ncpu=1, disk=100000,
                         condor_max_runtime=86400, max_parallel=4, farm_out=farm_out)
    fluka = SimpleNamespace(custom_executable=None, use_dpm=False, input="s.inp")
    return SimpleNamespace(execution=ex, fluka=fluka)

def test_slurm_submission_config_has_farm_out():
    config = _build_submission_config("slurm", _config(), dry_run=True)
    assert config.farm_out == "/myfarm"

def test_manifest_extra_slurm():
    extra = manifest_extra("slurm", _config(), run_dir="/o/c1/run_0001", input_file="s.inp")
    assert extra["farm_out"] == "/myfarm"
    assert extra["job_name"] == "s.inp"
    assert extra["user"] == getpass.getuser()

def test_manifest_extra_ts_empty():
    assert manifest_extra("ts", _config(backend="ts"), run_dir="/o/c1/run_0001",
                          input_file="s.inp") == {}

def test_manifest_extra_lsf_job_dir():
    extra = manifest_extra("lsf", _config(backend="lsf"), run_dir="/o/c1/run_0001",
                           input_file="s.inp")
    assert extra["job_dir"] == "/o/c1/run_0001"
