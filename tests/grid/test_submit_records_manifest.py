from types import SimpleNamespace
from pathlib import Path
import fluka.grid.run as R
from fluka.run.manifest import load_manifest, manifest_path_for


def test_submit_combo_records_jobs(tmp_path, monkeypatch):
    # stub the actual submission to return a fake backend stdout
    monkeypatch.setattr(R.queue_adapter, "submit_run",
                        lambda **kw: "Submitted batch job 4242")
    ex = SimpleNamespace(backend="slurm", queue=None, mem="1500", ntasks=1, nodes=1,
                         time="1-00:00:00", gres="disk:1G", ncpu=1, disk=100000,
                         condor_max_runtime=86400, max_parallel=4, farm_out="/farm_out")
    fluka = SimpleNamespace(input=tmp_path / "t.inp", primaries=None,
                            custom_executable=None, use_dpm=False)
    grid = SimpleNamespace(parameters={"beame": [0.1]}, runs_per_combo=2)
    config = SimpleNamespace(execution=ex, fluka=fluka, grid=grid, output_dir=tmp_path)
    (tmp_path / "t.inp").write_text("#define beame 0\nRANDOMIZ\nSTART\n")

    args = SimpleNamespace(dry_run=False, reset=False, config=fluka.input)
    R._submit_combo({"beame": 0.1}, config, Path("/f/rfluka"), args)

    jobs = load_manifest(manifest_path_for(tmp_path))
    assert len(jobs) == 2
    assert all(j.job_id == "4242" and j.backend == "slurm" for j in jobs)
    assert jobs[0].extra.get("farm_out") == "/farm_out"


def test_submit_combo_dry_run_records_no_manifest(tmp_path, monkeypatch):
    # dry-run submissions must not pollute the manifest with phantom job rows
    monkeypatch.setattr(R.queue_adapter, "submit_run",
                        lambda **kw: "[dry run] sbatch --partition=production job.sh")
    ex = SimpleNamespace(backend="slurm", queue=None, mem="1500", ntasks=1, nodes=1,
                         time="1-00:00:00", gres="disk:1G", ncpu=1, disk=100000,
                         condor_max_runtime=86400, max_parallel=4, farm_out="/farm_out")
    fluka = SimpleNamespace(input=tmp_path / "t.inp", primaries=None,
                            custom_executable=None, use_dpm=False)
    grid = SimpleNamespace(parameters={"beame": [0.1]}, runs_per_combo=2)
    config = SimpleNamespace(execution=ex, fluka=fluka, grid=grid, output_dir=tmp_path)
    (tmp_path / "t.inp").write_text("#define beame 0\nRANDOMIZ\nSTART\n")

    args = SimpleNamespace(dry_run=True, reset=False, config=fluka.input)
    R._submit_combo({"beame": 0.1}, config, Path("/f/rfluka"), args)

    jobs = load_manifest(manifest_path_for(tmp_path))
    assert jobs == []
