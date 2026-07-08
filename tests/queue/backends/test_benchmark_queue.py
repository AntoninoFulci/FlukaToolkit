from argparse import Namespace
from backends.slurm import SlurmBackend
from backends.lsf import LSFBackend
from backends.htcondor import HTCondorBackend
from backends.ts import TSBackend


def test_slurm_set_priority_queue():
    backend = SlurmBackend()
    args = Namespace(queue="production")
    backend.set_priority_queue(args, "priority")
    assert args.queue == "priority"


def test_lsf_set_priority_queue():
    backend = LSFBackend()
    args = Namespace(queue="normal")
    backend.set_priority_queue(args, "fast")
    assert args.queue == "fast"


def test_htcondor_set_priority_queue_is_noop():
    backend = HTCondorBackend()
    args = Namespace(queue="vanilla")
    backend.set_priority_queue(args, "priority")
    assert args.queue == "vanilla"


def test_ts_set_priority_queue_does_not_raise():
    backend = TSBackend()
    args = Namespace()
    backend.set_priority_queue(args, "priority")  # must not raise
    assert not hasattr(args, "queue")
