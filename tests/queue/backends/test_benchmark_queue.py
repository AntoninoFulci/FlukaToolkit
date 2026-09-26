from fluka.queue.backends.htcondor import HTCondorBackend
from fluka.queue.backends.lsf import LSFBackend
from fluka.queue.backends.slurm import SlurmBackend
from fluka.queue.backends.ts import TSBackend
from fluka.queue.core.config import SubmissionConfig


def _config(backend, queue=None):
    return SubmissionConfig(backend=backend, input="s.inp", njobs=1, queue=queue)


def test_slurm_set_priority_queue():
    backend = SlurmBackend()
    args = _config("slurm", "production")
    backend.set_priority_queue(args, "priority")
    assert args.queue == "priority"


def test_lsf_set_priority_queue():
    backend = LSFBackend()
    args = _config("lsf", "normal")
    backend.set_priority_queue(args, "fast")
    assert args.queue == "fast"


def test_htcondor_set_priority_queue_is_noop():
    backend = HTCondorBackend()
    args = _config("condor", "vanilla")
    backend.set_priority_queue(args, "priority")
    assert args.queue == "vanilla"


def test_ts_set_priority_queue_does_not_raise():
    backend = TSBackend()
    args = _config("ts")
    backend.set_priority_queue(args, "priority")  # must not raise
    assert args.queue is None
