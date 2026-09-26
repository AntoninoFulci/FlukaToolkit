import pytest
import yaml
from fluka.run.simconfig import resolve


def make_yaml(tmp_path, content: dict) -> str:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(content))
    return str(path)


def _write_sim(tmp_path, **overrides):
    """Write the canonical v2 sim.yaml (general+submit), with overrides merged
    into the relevant top-level sections."""
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
    }
    for section, patch_ in overrides.items():
        data.setdefault(section, {})
        data[section].update(patch_)
    p = tmp_path / "sim.yaml"
    p.write_text(yaml.dump(data))
    return p


def test_load_ts_minimal(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"backend": "ts", "input": "sim.inp", "njobs": 5})
    args = load_yaml_config(path, backends)
    assert args.backend == "ts"
    assert args.input == "sim.inp"
    assert args.njobs == 5
    assert args.dry_run is False
    assert args.custom_exe is None
    assert args.output_dir is None


def test_load_lsf_uses_backend_defaults(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.lsf import LSFBackend
    backends = {"lsf": LSFBackend()}
    path = make_yaml(tmp_path, {"backend": "lsf", "input": "sim.inp", "njobs": 1})
    args = load_yaml_config(path, backends)
    assert args.queue == "normal"
    assert args.mem == "1500"
    assert args.ntasks == 1
    assert args.time == "1-00:00:00"


def test_load_lsf_overrides_defaults(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.lsf import LSFBackend
    backends = {"lsf": LSFBackend()}
    path = make_yaml(tmp_path, {
        "backend": "lsf", "input": "sim.inp", "njobs": 10,
        "queue": "priority", "mem": "3000", "ntasks": 4, "time": "2-00:00:00",
    })
    args = load_yaml_config(path, backends)
    assert args.queue == "priority"
    assert args.mem == "3000"
    assert args.ntasks == 4
    assert args.time == "2-00:00:00"


def test_load_slurm_defaults(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.slurm import SlurmBackend
    backends = {"slurm": SlurmBackend()}
    path = make_yaml(tmp_path, {"backend": "slurm", "input": "sim.inp", "njobs": 1})
    args = load_yaml_config(path, backends)
    assert args.queue == "production"
    assert args.nodes == 1
    assert args.ntasks == 1


def test_dry_run_parsed(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"backend": "ts", "input": "sim.inp", "njobs": 1, "dry_run": True})
    args = load_yaml_config(path, backends)
    assert args.dry_run is True


def test_custom_exe_parsed(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {
        "backend": "ts", "input": "sim.inp", "njobs": 1, "custom_exe": "/path/to/exe"
    })
    args = load_yaml_config(path, backends)
    assert args.custom_exe == "/path/to/exe"


def test_missing_backend_raises(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"input": "sim.inp", "njobs": 1})
    with pytest.raises(ValueError, match="backend"):
        load_yaml_config(path, backends)


def test_unknown_backend_raises(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"backend": "unknown", "input": "sim.inp", "njobs": 1})
    with pytest.raises(ValueError, match="unknown"):
        load_yaml_config(path, backends)


def test_missing_input_raises(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"backend": "ts", "njobs": 1})
    with pytest.raises(ValueError, match="input"):
        load_yaml_config(path, backends)


def test_missing_njobs_raises(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"backend": "ts", "input": "sim.inp"})
    with pytest.raises(ValueError, match="njobs"):
        load_yaml_config(path, backends)


def test_load_htcondor_defaults(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.htcondor import HTCondorBackend
    backends = {"condor": HTCondorBackend()}
    path = make_yaml(tmp_path, {"backend": "condor", "input": "sim.inp", "njobs": 1})
    args = load_yaml_config(path, backends)
    assert args.queue == "vanilla"
    assert args.mem == "1500"
    assert args.ncpu == 1
    assert args.disk == 100000
    assert args.time == 86400
    assert args.transfer_files == "yes"
    assert args.stdout == "job_$(Cluster)_$(Process).out"
    assert args.output_dir is None  # common arg, separate from scheduler stdout


def test_njobs_zero_raises(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"backend": "ts", "input": "sim.inp", "njobs": 0})
    with pytest.raises(ValueError, match="njobs"):
        load_yaml_config(path, backends)


def test_input_wrong_extension_raises(tmp_path):
    from fluka.queue.core.config import load_yaml_config
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    path = make_yaml(tmp_path, {"backend": "ts", "input": "sim.txt", "njobs": 1})
    with pytest.raises(ValueError, match=r"\.inp"):
        load_yaml_config(path, backends)


# ---------------------------------------------------------------------------
# build_submit_args: v2 merged view (general + submit) -> SubmissionConfig
# ---------------------------------------------------------------------------

def test_build_submit_args_from_v2_view(tmp_path):
    from fluka.queue.core.config import SubmissionConfig, build_submit_args
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    p = _write_sim(tmp_path)
    view = resolve(p, "submit")

    args = build_submit_args(view, backends)

    assert isinstance(args, SubmissionConfig)
    assert args.backend == "ts"
    assert args.input.endswith("example.inp")
    assert args.njobs == 2
    assert args.dry_run is False
    assert args.output_dir.endswith("results")
    assert args.custom_exe is None
    assert args.use_dpm is False
    assert args.nprim == 1000


def test_build_submit_args_backend_resource_fields(tmp_path):
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.backends.slurm import SlurmBackend
    backends = {"slurm": SlurmBackend()}
    p = _write_sim(tmp_path, general={"backend": "slurm"}, submit={"queue": "production"})
    view = resolve(p, "submit")

    args = build_submit_args(view, backends)

    assert args.backend == "slurm"
    assert args.queue == "production"
    assert args.mem == "1500"
    assert args.time == "1-00:00:00"
    assert args.ntasks == 1
    assert args.nodes == 1
    assert args.gres == "disk:1G"
    assert args.farm_out == "/farm_out"


def test_build_submit_args_njobs_from_submit_section(tmp_path):
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    p = _write_sim(tmp_path, submit={"njobs": 7})
    view = resolve(p, "submit")

    args = build_submit_args(view, backends)
    assert args.njobs == 7


def test_build_submit_args_missing_backend_raises(tmp_path):
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    p = _write_sim(tmp_path)
    raw = yaml.safe_load(p.read_text())
    del raw["general"]["backend"]
    p.write_text(yaml.dump(raw))
    view = resolve(p, "submit")
    with pytest.raises(ValueError, match="backend"):
        build_submit_args(view, backends)


def test_build_submit_args_missing_njobs_raises(tmp_path):
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    p = _write_sim(tmp_path)
    raw = yaml.safe_load(p.read_text())
    del raw["submit"]["njobs"]
    p.write_text(yaml.dump(raw))
    view = resolve(p, "submit")
    with pytest.raises(ValueError, match="njobs"):
        build_submit_args(view, backends)


def test_build_submit_args_input_wrong_extension_raises(tmp_path):
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    p = _write_sim(tmp_path, general={"input": "example.txt"})
    view = resolve(p, "submit")
    with pytest.raises(ValueError, match=r"\.inp"):
        build_submit_args(view, backends)


def test_build_submit_args_use_dpm_and_custom_exe_raises(tmp_path):
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.backends.ts import TSBackend
    backends = {"ts": TSBackend()}
    p = _write_sim(tmp_path, general={"use_dpm": True, "custom_executable": "/custom/fluka"})
    view = resolve(p, "submit")
    with pytest.raises(ValueError, match="mutually exclusive"):
        build_submit_args(view, backends)


def test_build_submit_args_condor_output_not_clobbered(tmp_path):
    """general.output (the results dir) must not overwrite HTCondor's own
    --output arg (the job stdout filename pattern) -- both happen to be
    called 'output' but mean different things."""
    from fluka.queue.core.config import build_submit_args
    from fluka.queue.backends.htcondor import HTCondorBackend
    backends = {"condor": HTCondorBackend()}
    p = _write_sim(tmp_path, general={"backend": "condor"})
    view = resolve(p, "submit")

    args = build_submit_args(view, backends)

    assert args.output_dir.endswith("results")
    assert args.stdout == "job_$(Cluster)_$(Process).out"


def test_legacy_and_merged_view_build_equivalent_typed_configs(tmp_path):
    from fluka.queue.backends.registry import new_backends
    from fluka.queue.core.config import (
        SubmissionConfig,
        load_submission_config,
        submission_config_from_view,
    )

    backends = new_backends()
    input_path = str(tmp_path / "sim.inp")
    legacy_path = make_yaml(tmp_path, {
        "backend": "slurm",
        "input": input_path,
        "njobs": 3,
        "mem": "2400",
        "time": "2-00:00:00",
    })
    legacy = load_submission_config(legacy_path, backends)

    sim_path = _write_sim(
        tmp_path,
        general={"backend": "slurm", "input": input_path},
        submit={"njobs": 3, "mem": "2400", "time": "2-00:00:00"},
    )
    merged = submission_config_from_view(resolve(sim_path, "submit"), backends)

    assert isinstance(legacy, SubmissionConfig)
    assert isinstance(merged, SubmissionConfig)
    assert legacy.backend == merged.backend == "slurm"
    assert legacy.input == merged.input
    assert legacy.njobs == merged.njobs == 3
    assert legacy.mem == merged.mem == "2400"
    assert legacy.time == merged.time == "2-00:00:00"
    assert legacy.dry_run is False and merged.dry_run is False
