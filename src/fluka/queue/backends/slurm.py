import os
import subprocess
from argparse import ArgumentParser
from string import Template
from typing import TYPE_CHECKING

from fluka.queue.backends.base import JobInfo, QueueBackend
from fluka.queue.core.display import COLORS
from fluka.queue.core.utils import parse_time_to_seconds

if TYPE_CHECKING:
    from fluka.queue.core.config import SubmissionConfig

_DEFAULT_QUEUE = "production"
_MAX_TIME = "4-00:00:00"

_MAX_TIME_SECONDS = parse_time_to_seconds(_MAX_TIME)

_SCRIPT_TEMPLATE = Template("""\
#!/bin/bash

#SBATCH --job-name=$input
#SBATCH --nodes=$nodes
#SBATCH --mem=$mem
#SBATCH --ntasks=$ntasks
#SBATCH --time=$time
#SBATCH --gres=$gres
#SBATCH --output=$farm_out/%u/%x-%j-%N.out
#SBATCH --error=$farm_out/%u/%x-%j-%N.err

cd /scratch/slurm/$$SLURM_JOB_ID

# copia il .err di FLUKA ogni 30 secondi
while true; do
    cp fluka_*/*.err $farm_out/$$USER/$$SLURM_JOB_NAME-$$SLURM_JOB_ID-live.err 2>/dev/null
    sleep 30
done &
WATCHER_PID=$$!

echo
echo Launching FLUKA run...
$fluka_command $job_dir/$input
rc=$$?
echo "FLUKA_STATUS rc=$$rc" > $farm_out/$$USER/$$SLURM_JOB_NAME-$$SLURM_JOB_ID.fluka_status

kill $$WATCHER_PID 2>/dev/null

echo
echo Job completed. Transferring files to $job_dir

mv ./*.root $job_dir
exit "$$rc"
""")


class SlurmBackend(QueueBackend):
    def add_args(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-q",
            "--queue",
            type=str,
            default=_DEFAULT_QUEUE,
            help=f"Partizione SLURM su cui inviare i job (default: {_DEFAULT_QUEUE})",
        )
        parser.add_argument(
            "-m",
            "--mem",
            type=str,
            default="1500",
            help="Memoria richiesta per nodo in MB (default: 1500)",
        )
        parser.add_argument(
            "-t",
            "--ntasks",
            type=int,
            default=1,
            help="Numero di task SLURM per job, corrisponde a --ntasks (default: 1)",
        )
        parser.add_argument(
            "-o",
            "--nodes",
            type=int,
            default=1,
            help="Numero di nodi richiesti per job, corrisponde a --nodes (default: 1)",
        )
        parser.add_argument(
            "-T",
            "--time",
            type=str,
            default="1-00:00:00",
            help="Limite di tempo massimo nel formato D-HH:MM:SS, max 4-00:00:00 "
            "(default: 1-00:00:00)",
        )
        parser.add_argument(
            "-g",
            "--gres",
            type=str,
            default="disk:1G",
            help="Risorse generiche SLURM (--gres), es. disk:2G o gpu:1 (default: disk:1G)",
        )
        parser.add_argument(
            "--farm-out",
            dest="farm_out",
            type=str,
            default="/farm_out",
            help="Directory accessibile dove finiscono out/err/sentinel (default: /farm_out)",
        )

    def validate(self, args: "SubmissionConfig") -> None:
        if not isinstance(args.time, str):
            raise ValueError("Il time limit SLURM deve usare il formato D-HH:MM:SS")
        if parse_time_to_seconds(args.time) > _MAX_TIME_SECONDS:
            raise ValueError(f"Il time limit non puo' superare {_MAX_TIME}")

    def generate_script(self, job_info: JobInfo, job_dir: str, args: "SubmissionConfig") -> str:
        fluka_cmd = f"{job_info.fluka_path}/rfluka -M 1"
        if job_info.use_dpm:
            fluka_cmd += " -d"
        elif job_info.custom_exe is not None:
            fluka_cmd += f" -e {job_info.custom_exe}"

        content = _SCRIPT_TEMPLATE.substitute(
            input=job_info.input_file,
            fluka_command=fluka_cmd,
            job_dir=job_dir,
            mem=args.mem,
            ntasks=args.ntasks,
            nodes=args.nodes,
            time=args.time,
            gres=args.gres,
            farm_out=args.farm_out,
        )
        script_path = os.path.join(job_dir, f"job_{job_info.iteration:04d}.sh")
        with open(script_path, "w") as f:
            f.write(content)
        os.chmod(script_path, 0o755)
        return script_path

    def submit(self, script_path: str | None, job_info: JobInfo, args: "SubmissionConfig") -> str:
        if script_path is None:
            raise RuntimeError("SlurmBackend requires a script file (script_path cannot be None)")
        if args.dry_run:
            return f"[dry run] sbatch --partition={args.queue} {script_path}"
        result = subprocess.run(
            ["sbatch", f"--partition={args.queue}", script_path], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()

    def table_rows(
        self, args: "SubmissionConfig", fluka_path: str, fluka_folder: str
    ) -> list[list[str]]:
        C = COLORS
        return [
            ["-q", f"{C['M']}Partizione{C['RE']}", f"{C['M']}{args.queue}{C['RE']}"],
            ["-m", f"{C['C']}Memoria (MB){C['RE']}", f"{C['C']}{args.mem}{C['RE']}"],
            ["-t", f"{C['C']}N. task{C['RE']}", f"{C['C']}{args.ntasks}{C['RE']}"],
            ["-o", f"{C['C']}N. nodi{C['RE']}", f"{C['C']}{args.nodes}{C['RE']}"],
            ["-T", f"{C['C']}Time limit{C['RE']}", f"{C['C']}{args.time}{C['RE']}"],
            ["-g", f"{C['C']}GRES{C['RE']}", f"{C['C']}{args.gres}{C['RE']}"],
            [" ", f"{C['B']}FLUKA bin{C['RE']}", f"{C['B']}{fluka_path}{C['RE']}"],
            [" ", f"{C['B']}FLUKA folder{C['RE']}", f"{C['B']}{fluka_folder}{C['RE']}"],
        ]

    def set_priority_queue(self, args: "SubmissionConfig", queue_name: str) -> None:
        args.queue = queue_name

    def _sentinel_path(self, job):
        from pathlib import Path

        e = job.extra
        return Path(e["farm_out"]) / e["user"] / f"{e['job_name']}-{job.job_id}.fluka_status"

    def _queue_state(self, job):
        from fluka.run.status import PENDING, RUNNING

        try:
            r = subprocess.run(
                ["squeue", "-j", job.job_id, "-h", "-o", "%t"], capture_output=True, text=True
            )
        except (FileNotFoundError, OSError):
            # squeue not installed on this host; fall back to sentinel-based state.
            return None
        if r.returncode != 0:
            return None
        code = r.stdout.strip()
        if not code:
            return None
        if code == "PD":
            return PENDING
        return RUNNING
