import subprocess
import shlex
from argparse import ArgumentParser, Namespace
from pathlib import Path

from fluka.queue.backends.base import JobInfo, QueueBackend
from fluka.queue.core.display import COLORS


class TSBackend(QueueBackend):

    def add_args(self, parser: ArgumentParser) -> None:
        pass

    def validate(self, args: Namespace) -> None:
        pass

    def generate_script(self, job_info: JobInfo, job_dir: str, args: Namespace) -> None:
        return None

    def submit(self, script_path, job_info, args) -> str:
        fluka_parts = ["rfluka", "-M", "1"]
        if job_info.use_dpm:
            fluka_parts.append("-d")
        elif job_info.custom_exe is not None:
            fluka_parts.extend(["-e", job_info.custom_exe])
        input_path = Path(job_info.input_file)
        fluka_parts.append(input_path.name if input_path.is_absolute() else job_info.input_file)
        fluka_cmd = shlex.join(fluka_parts)
        if input_path.is_absolute():
            fluka_cmd = f"cd {shlex.quote(str(input_path.parent))} && {fluka_cmd}"
        wrapped = f'{fluka_cmd}; echo "FLUKA_STATUS rc=$?" > ./.fluka_status'
        cmd_list = ["ts", "bash", "-c", wrapped]

        if args.dry_run:
            return f"[dry run] {' '.join(cmd_list)}"
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()

    def _sentinel_path(self, job):
        from pathlib import Path
        return Path(job.run_dir) / ".fluka_status"

    def _queue_state(self, job):
        from fluka.run.status import RUNNING
        try:
            r = subprocess.run(["tsp", "-s", job.job_id], capture_output=True, text=True)
        except (FileNotFoundError, OSError):
            # task-spooler not installed on this host; fall back to sentinel-based state.
            return None
        if r.returncode != 0:
            return None
        out = (r.stdout + r.stderr).lower()
        if "running" in out or "queued" in out or "allocating" in out:
            return RUNNING
        return None

    def table_rows(self, args: Namespace, fluka_path: str, fluka_folder: str) -> list[list[str]]:
        C = COLORS
        return [
            [" ", f"{C['B']}FLUKA bin{C['RE']}",    f"{C['B']}{fluka_path}{C['RE']}"],
            [" ", f"{C['B']}FLUKA folder{C['RE']}", f"{C['B']}{fluka_folder}{C['RE']}"],
        ]

    def set_priority_queue(self, args: Namespace, queue_name: str) -> None:
        # Task Spooler non ha concetto di coda/partizione; l'override viene ignorato.
        import logging as _logging
        _logging.warning("TSBackend: benchmark_priority_queue ignorato (nessun concetto di coda).")
