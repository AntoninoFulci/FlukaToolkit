from argparse import Namespace
from pathlib import Path
import subprocess
from fluka.queue.backends.htcondor import HTCondorBackend
from fluka.queue.backends.base import JobInfo
from fluka.run.manifest import Job
from fluka.run import status as S


def _args():
    return Namespace(dry_run=True, queue="vanilla", mem="1500", ncpu=1, disk=100000,
                     time=86400, transfer_files="yes",
                     output="job.out", error="job.err", log="job.log")

def _job(run_dir="/o/c1/run_0001", output="job.out"):
    return Job(combo="c1", run_idx=1, run_name="run_0001", run_dir=run_dir,
               backend="condor", job_id="90", input_file="s.inp", submitted_at="t",
               extra={"output": output, "error": "job.err", "log": "job.log"})

def test_script_echoes_sentinel(tmp_path):
    ji = JobInfo(input_file="s.inp", iteration=1, fluka_path="/f", custom_exe=None)
    content = Path(HTCondorBackend().generate_script(ji, str(tmp_path), _args())).read_text()
    assert "FLUKA_STATUS rc=$?" in content

def test_sentinel_path_joins_run_dir(tmp_path):
    (tmp_path / "job.out").write_text("FLUKA_STATUS rc=0")
    p = Path(HTCondorBackend()._sentinel_path(_job(run_dir=tmp_path, output="job.out")))
    assert p == Path(tmp_path) / "job.out"

def test_queue_state_running(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="R\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert HTCondorBackend()._queue_state(_job()) == S.RUNNING

def test_queue_state_idle(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="I\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert HTCondorBackend()._queue_state(_job()) == S.PENDING

def test_queue_state_absent(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert HTCondorBackend()._queue_state(_job()) is None
