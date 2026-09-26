from fluka.queue.backends.base import QueueBackend
from fluka.queue.backends.htcondor import HTCondorBackend
from fluka.queue.backends.lsf import LSFBackend
from fluka.queue.backends.slurm import SlurmBackend
from fluka.queue.backends.ts import TSBackend

BACKEND_TYPES: dict[str, type[QueueBackend]] = {
    "ts": TSBackend,
    "slurm": SlurmBackend,
    "lsf": LSFBackend,
    "condor": HTCondorBackend,
}


def new_backends() -> dict[str, QueueBackend]:
    return {name: backend_type() for name, backend_type in BACKEND_TYPES.items()}
