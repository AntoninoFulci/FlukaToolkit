#!/usr/bin/env python3
"""Collect ROOT files from job subdirectories into root_files/."""

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from rich import box
from rich.console import Console
from rich.table import Table


@dataclass
class FileMove:
    parent_dir: Path
    job_dir: Path
    source: Path
    dest: Path
    size: int


@dataclass
class EmptyJob:
    parent_dir: Path
    job_dir: Path


@dataclass
class CollectionCollision:
    parent_dir: Path
    dest: Path
    sources: list[Path]
    destination_exists: bool = False


@dataclass
class MovePlan:
    moves: list[FileMove] = field(default_factory=list)
    empty_jobs: list[EmptyJob] = field(default_factory=list)
    collisions: list[CollectionCollision] = field(default_factory=list)


def scan_all(cwd: Path) -> MovePlan:
    plan = MovePlan()
    for parent_dir in sorted(p for p in cwd.iterdir() if p.is_dir()):
        root_files_dir = parent_dir / "root_files"
        job_dirs = sorted(
            p for p in parent_dir.iterdir() if p.is_dir() and p.name.startswith("job_")
        )
        parent_moves: list[FileMove] = []
        for job_dir in job_dirs:
            root_files = list(job_dir.glob("*.root"))
            if not root_files:
                plan.empty_jobs.append(EmptyJob(parent_dir=parent_dir, job_dir=job_dir))
                continue
            for f in root_files:
                parent_moves.append(
                    FileMove(
                        parent_dir=parent_dir,
                        job_dir=job_dir,
                        source=f,
                        dest=root_files_dir / f.name,
                        size=f.stat().st_size,
                    )
                )

        by_dest: dict[Path, list[FileMove]] = {}
        for move in parent_moves:
            by_dest.setdefault(move.dest, []).append(move)

        parent_collisions = [
            CollectionCollision(
                parent_dir=parent_dir,
                dest=dest,
                sources=[move.source for move in moves],
                destination_exists=dest.exists(),
            )
            for dest, moves in sorted(by_dest.items())
            if len(moves) > 1 or dest.exists()
        ]
        if parent_collisions:
            plan.collisions.extend(parent_collisions)
        else:
            plan.moves.extend(parent_moves)
    return plan


def _format_size(size: int) -> str:
    s = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if s < 1024 or unit == "TB":
            return f"{s:.0f} {unit}"
        s /= 1024
    return f"{s:.0f} B"  # unreachable


def display_plan(plan: MovePlan, console: Console | None = None) -> None:
    if console is None:
        console = Console()

    for collision in plan.collisions:
        sources = ", ".join(str(source) for source in collision.sources)
        reason = "destination exists" if collision.destination_exists else "duplicate filename"
        console.print(f"[red]COLLISION[/red] {collision.dest} ({reason}); sources: {sources}")

    if not plan.moves and not plan.empty_jobs:
        return

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
    table.add_column("Parent Dir", style="dim")
    table.add_column("Job")
    table.add_column("File")
    table.add_column("Size", justify="right")
    table.add_column("Destination", style="dim")

    parent_names = sorted(
        {m.parent_dir.name for m in plan.moves} | {e.parent_dir.name for e in plan.empty_jobs}
    )
    colors = ["white", "bright_white"]
    color_map = {name: colors[i % 2] for i, name in enumerate(parent_names)}

    rows: list[FileMove | EmptyJob] = [*plan.moves, *plan.empty_jobs]
    rows.sort(
        key=lambda r: (
            r.parent_dir.name,
            r.job_dir.name,
            r.source.name if isinstance(r, FileMove) else "",
        )
    )

    for item in rows:
        if isinstance(item, FileMove):
            table.add_row(
                item.parent_dir.name,
                item.job_dir.name,
                item.source.name,
                _format_size(item.size),
                f"root_files/{item.source.name}",
                style=color_map[item.parent_dir.name],
            )
        else:
            table.add_row(
                item.parent_dir.name,
                item.job_dir.name,
                "[red]no .root files[/red]",
                "—",
                "—",
                style="red",
            )

    console.print(table)
    n_parents = len({m.parent_dir for m in plan.moves} | {e.parent_dir for e in plan.empty_jobs})
    n_jobs = len({m.job_dir for m in plan.moves} | {e.job_dir for e in plan.empty_jobs})
    console.print(
        f"[bold]{len(plan.moves)} files[/bold] across {n_jobs} job dirs in {n_parents} parent dirs"
    )


def execute_plan(plan: MovePlan) -> int:
    parents: dict[Path, list[FileMove]] = {}
    for m in plan.moves:
        parents.setdefault(m.parent_dir, []).append(m)

    exit_code = 1 if plan.collisions else 0
    for parent_dir, moves in sorted(parents.items()):
        dest_dir = parent_dir / "root_files"
        try:
            dest_dir.mkdir(exist_ok=True)
        except OSError as e:
            print(f"ERROR: {parent_dir.name}: cannot create root_files/: {e}", file=sys.stderr)
            exit_code = 1
            continue

        created_destinations: list[tuple[Path, tuple[int, int]]] = []
        parent_failed = False
        for m in moves:
            try:
                os.link(m.source, m.dest)
                stat = m.dest.stat()
                created_destinations.append((m.dest, (stat.st_dev, stat.st_ino)))
            except OSError as e:
                print(f"ERROR: {parent_dir.name}/{m.source.name}: {e}", file=sys.stderr)
                parent_failed = True
                exit_code = 1
                break

        if parent_failed:
            for dest, identity in reversed(created_destinations):
                try:
                    stat = dest.stat()
                    if (stat.st_dev, stat.st_ino) == identity:
                        dest.unlink()
                except OSError as e:
                    print(
                        f"ERROR: {parent_dir.name}/{dest.name}: cannot roll back: {e}",
                        file=sys.stderr,
                    )
            print(f"{parent_dir.name}: moved 0 files, deleted 0 job dirs")
            continue

        job_dirs_all = {m.job_dir for m in moves}
        deleted_job_dirs = 0
        for job_dir in job_dirs_all:
            try:
                shutil.rmtree(job_dir)
                deleted_job_dirs += 1
            except OSError as e:
                print(f"ERROR: {parent_dir.name}/{job_dir.name}: {e}", file=sys.stderr)
                exit_code = 1

        print(
            f"{parent_dir.name}: moved {len(created_destinations)} files, "
            f"deleted {deleted_job_dirs} job dirs"
        )
    return exit_code


def main(cwd: Path | None = None) -> int:
    cwd = Path.cwd() if cwd is None else Path(cwd)
    plan = scan_all(cwd)

    if not plan.moves and not plan.empty_jobs and not plan.collisions:
        print("ERROR: no job_* directories found under any subdirectory", file=sys.stderr)
        return 1

    display_plan(plan)

    if not plan.moves:
        return 1 if plan.collisions else 0

    answer = input("Proceed? [y/N]: ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return 0

    return execute_plan(plan)


if __name__ == "__main__":
    sys.exit(main())
