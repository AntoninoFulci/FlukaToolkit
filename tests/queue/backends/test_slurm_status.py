from argparse import Namespace
from pathlib import Path
import subprocess
from fluka.queue.backends.slurm import SlurmBackend
from fluka.queue.backends.base import JobInfo
from fluka.run.manifest import Job
from fluka.run import status as S


def _args(**kw):
    base = dict(dry_run=True, queue="production", mem="1500", ntasks=1, nodes=1,
                time="1-00:00:00", gres="disk:1G", farm_out="/myfarm")
    base.update(kw); return Namespace(**base)

def test_template_uses_farm_out(tmp_path):
    ji = JobInfo(input_file="s.inp", iteration=1, fluka_path="/f", custom_exe=None)
    path = SlurmBackend().generate_script(ji, str(tmp_path), _args())
    content = Path(path).read_text()
    assert "/myfarm" in content and "/farm_out" not in content
    assert "FLUKA_STATUS rc=$?" in content

def test_sentinel_path_from_extra():
    j = Job(combo="c1", run_idx=1, run_name="run_0001", run_dir="/o/c1/run_0001",
            backend="slurm", job_id="321", input_file="s.inp", submitted_at="t",
            extra={"farm_out": "/myfarm", "user": "me", "job_name": "s.inp"})
    p = Path(SlurmBackend()._sentinel_path(j))
    assert p == Path("/myfarm/me/s.inp-321.fluka_status")

def test_queue_state_running(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="R\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    j = Job(combo="c", run_idx=1, run_name="r", run_dir="/x", backend="slurm",
            job_id="1", input_file="s", submitted_at="t", extra={})
    assert SlurmBackend()._queue_state(j) == S.RUNNING

def test_queue_state_pending(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="PD\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    j = Job(combo="c", run_idx=1, run_name="r", run_dir="/x", backend="slurm",
            job_id="1", input_file="s", submitted_at="t", extra={})
    assert SlurmBackend()._queue_state(j) == S.PENDING

def test_queue_state_absent(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    j = Job(combo="c", run_idx=1, run_name="r", run_dir="/x", backend="slurm",
            job_id="1", input_file="s", submitted_at="t", extra={})
    assert SlurmBackend()._queue_state(j) is None

def test_queue_state_missing_binary(monkeypatch):
    def fake_run(cmd, **kw):
        raise FileNotFoundError("squeue not found")
    monkeypatch.setattr(subprocess, "run", fake_run)
    j = Job(combo="c", run_idx=1, run_name="r", run_dir="/x", backend="slurm",
            job_id="1", input_file="s", submitted_at="t", extra={})
    assert SlurmBackend()._queue_state(j) is None
