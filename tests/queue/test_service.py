from pathlib import Path

import pytest

from fluka.queue.backends.base import JobInfo
from fluka.queue.core.config import SubmissionConfig
from fluka.queue.service import (
    PreparedJob,
    SubmissionBatchError,
    submit_prepared,
)


def test_submit_prepared_attempts_all_jobs_then_raises(tmp_path):
    class FakeBackend:
        def __init__(self):
            self.calls = 0

        def generate_script(self, job_info, job_dir, config):
            return str(Path(job_dir) / "job.sh")

        def submit(self, script_path, job_info, config):
            self.calls += 1
            if job_info.iteration == 2:
                raise RuntimeError("queue down")
            return f"job {job_info.iteration}"

    config = SubmissionConfig(backend="ts", input="sim.inp", njobs=3, dry_run=True)
    prepared = [
        PreparedJob(
            i,
            tmp_path / f"job_{i:04d}",
            JobInfo("sim.inp", i, "/fluka", None),
        )
        for i in (1, 2, 3)
    ]
    backend = FakeBackend()

    with pytest.raises(SubmissionBatchError) as exc:
        submit_prepared(config, prepared, backend)

    assert backend.calls == 3
    assert [failure.iteration for failure in exc.value.failures] == [2]


def test_submit_prepared_aggregates_oserror_and_attempts_later_jobs(tmp_path):
    class MissingSchedulerBackend:
        def __init__(self):
            self.attempted = []

        def generate_script(self, job_info, job_dir, config):
            return str(Path(job_dir) / "job.sh")

        def submit(self, script_path, job_info, config):
            self.attempted.append(job_info.iteration)
            if job_info.iteration == 2:
                raise FileNotFoundError("scheduler command missing")
            return f"job {job_info.iteration}"

    config = SubmissionConfig(backend="ts", input="sim.inp", njobs=3)
    prepared = [
        PreparedJob(i, tmp_path / f"job_{i:04d}", JobInfo("sim.inp", i, "/fluka", None))
        for i in (1, 2, 3)
    ]
    backend = MissingSchedulerBackend()

    with pytest.raises(SubmissionBatchError) as exc:
        submit_prepared(config, prepared, backend)

    assert backend.attempted == [1, 2, 3]
    assert [failure.iteration for failure in exc.value.failures] == [2]
    assert exc.value.summary.results == ((1, "job 1"), (3, "job 3"))
