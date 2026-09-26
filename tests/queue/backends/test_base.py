import pytest

from fluka.queue.backends.base import JobInfo, QueueBackend
from fluka.queue.backends.registry import BACKEND_TYPES, new_backends
from fluka.queue.core.config import SubmissionConfig


class ConcreteBackend(QueueBackend):
    def add_args(self, parser):
        pass

    def validate(self, args):
        pass

    def generate_script(self, job_info, job_dir, args):
        return "/tmp/job.sh"

    def submit(self, script_path, job_info, args):
        return "submitted"

    def table_rows(self, args, fluka_path, fluka_folder):
        return []

    def set_priority_queue(self, args, queue_name):
        pass


def test_jobinfo_fields():
    ji = JobInfo(input_file="sim_0001.inp", iteration=1, fluka_path="/usr/bin", custom_exe=None)
    assert ji == JobInfo(
        input_file="sim_0001.inp", iteration=1, fluka_path="/usr/bin", custom_exe=None
    )


def test_cannot_instantiate_abstract_backend():
    with pytest.raises(TypeError):
        QueueBackend()


def test_concrete_backend_instantiates():
    b = ConcreteBackend()
    config = SubmissionConfig(backend="ts", input="f.inp", njobs=1)
    assert b.submit(None, JobInfo("f", 1, "/p", None), config) == "submitted"


def test_registry_exposes_all_supported_backends():
    assert set(BACKEND_TYPES) == {"ts", "slurm", "lsf", "condor"}
    instances = new_backends()
    assert set(instances) == set(BACKEND_TYPES)
    assert all(
        isinstance(instances[name], backend_type) for name, backend_type in BACKEND_TYPES.items()
    )
