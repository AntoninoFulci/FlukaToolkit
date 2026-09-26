import os
import pytest
from unittest.mock import patch
from fluka.queue.backends.slurm import SlurmBackend
from fluka.queue.backends.base import JobInfo
from fluka.queue.core.config import SubmissionConfig

BACKEND = SlurmBackend()

def make_args(**kwargs):
    defaults = dict(backend="slurm", input="sim.inp", njobs=1,
                    queue="production", mem="1500", ntasks=1, nodes=1,
                    time="1-00:00:00", gres="disk:1G", dry_run=False, custom_exe=None,
                    farm_out="/farm_out")
    defaults.update(kwargs)
    return SubmissionConfig(**defaults)

def test_validate_accepts_valid_time():
    BACKEND.validate(make_args(time="2-00:00:00"))

def test_validate_rejects_time_over_max():
    with pytest.raises(ValueError):
        BACKEND.validate(make_args(time="5-00:00:00"))

def test_generate_script_creates_sh_file(tmp_path):
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    script = BACKEND.generate_script(job_info, str(tmp_path), make_args())
    assert os.path.isfile(script)
    assert script.endswith("job_0001.sh")

def test_generate_script_contains_sbatch_directives(tmp_path):
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    args = make_args(mem="3000", ntasks=4, nodes=2)
    content = open(BACKEND.generate_script(job_info, str(tmp_path), args)).read()
    assert "#SBATCH" in content
    assert "3000" in content


def test_generate_script_propagates_fluka_exit_status(tmp_path):
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    content = open(BACKEND.generate_script(job_info, str(tmp_path), make_args())).read()
    assert "rc=$?" in content
    assert "FLUKA_STATUS rc=$rc" in content
    assert 'exit "$rc"' in content

def test_submit_dry_run(tmp_path):
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    result = BACKEND.submit("/tmp/job_0001.sh", job_info, make_args(dry_run=True, queue="mypartition"))
    assert "dry run" in result.lower()
    assert "sbatch" in result
    assert "mypartition" in result

def test_submit_calls_sbatch():
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Submitted batch job 99"
        result = BACKEND.submit("/tmp/job.sh", job_info, make_args(dry_run=False, queue="prod"))
    assert "99" in result
    called_cmd = mock_run.call_args[0][0]
    assert called_cmd == ["sbatch", "--partition=prod", "/tmp/job.sh"]

def test_submit_raises_on_failure():
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Partition not found"
        with pytest.raises(RuntimeError, match="Partition not found"):
            BACKEND.submit("/tmp/job.sh", job_info, make_args(dry_run=False))

def test_submit_raises_if_script_path_is_none():
    job_info = JobInfo("sim_0001.inp", 1, "/usr/local/fluka/bin", None)
    with pytest.raises(RuntimeError, match="script_path"):
        BACKEND.submit(None, job_info, make_args(dry_run=False))
