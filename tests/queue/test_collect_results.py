import subprocess
import sys
from io import StringIO
from pathlib import Path

from fluka.queue.collect_results import (
    display_plan,
    execute_plan,
    scan_all,
)

SCRIPT = Path(__file__).resolve().parent.parent / "collect_results.py"


# ── helpers ────────────────────────────────────────────────────────────────────


def make_tree(tmp_path, structure):
    """Build a directory tree from a dict.

    structure: { "parent_name": { "job_name": ["file1.root", ...], ... }, ... }
    """
    for parent_name, jobs in structure.items():
        parent = tmp_path / parent_name
        parent.mkdir()
        for job_name, files in jobs.items():
            job_dir = parent / job_name
            job_dir.mkdir()
            for fname in files:
                f = job_dir / fname
                f.write_bytes(b"x" * 100)
    return tmp_path


# ── scan_all ───────────────────────────────────────────────────────────────────


def test_scan_finds_root_files_in_all_subdirs(tmp_path):
    make_tree(
        tmp_path,
        {
            "SimLead": {"job_0001": ["lead.root"]},
            "SimMercury": {"job_0001": ["mercury.root"]},
        },
    )
    plan = scan_all(tmp_path)
    sources = {m.source.name for m in plan.moves}
    assert sources == {"lead.root", "mercury.root"}


def test_scan_ignores_non_job_dirs(tmp_path):
    make_tree(
        tmp_path,
        {
            "SimLead": {
                "job_0001": ["a.root"],
                "configs": ["config.yaml"],
            }
        },
    )
    plan = scan_all(tmp_path)
    assert len(plan.moves) == 1
    assert plan.moves[0].source.name == "a.root"


def test_scan_ignores_non_root_files(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root", "b.inp", "c.sh"]}})
    plan = scan_all(tmp_path)
    assert len(plan.moves) == 1
    assert plan.moves[0].source.name == "a.root"


def test_scan_destination_is_root_files_subdir(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    plan = scan_all(tmp_path)
    assert plan.moves[0].dest == tmp_path / "SimLead" / "root_files" / "a.root"


def test_scan_records_file_size(tmp_path):
    parent = tmp_path / "SimLead"
    parent.mkdir()
    job = parent / "job_0001"
    job.mkdir()
    f = job / "a.root"
    f.write_bytes(b"x" * 512)
    plan = scan_all(tmp_path)
    assert plan.moves[0].size == 512


def test_scan_records_collision_with_existing_root_file(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    root_files_dir = tmp_path / "SimLead" / "root_files"
    root_files_dir.mkdir()
    (root_files_dir / "a.root").touch()

    plan = scan_all(tmp_path)
    assert len(plan.moves) == 0
    assert len(plan.collisions) == 1
    assert plan.collisions[0].dest == root_files_dir / "a.root"
    assert plan.collisions[0].destination_exists is True


def test_scan_proceeds_if_root_files_dir_is_empty(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    (tmp_path / "SimLead" / "root_files").mkdir()
    plan = scan_all(tmp_path)
    assert len(plan.moves) == 1


def test_scan_records_empty_job_dirs(tmp_path):
    make_tree(
        tmp_path,
        {
            "SimLead": {
                "job_0001": [],
                "job_0002": ["a.root"],
            }
        },
    )
    plan = scan_all(tmp_path)
    assert len(plan.empty_jobs) == 1
    assert plan.empty_jobs[0].job_dir.name == "job_0001"


def test_scan_moves_sorted_by_parent_then_job(tmp_path):
    make_tree(
        tmp_path,
        {
            "SimB": {"job_0002": ["b.root"], "job_0001": ["a.root"]},
            "SimA": {"job_0001": ["c.root"]},
        },
    )
    plan = scan_all(tmp_path)
    parents = [m.parent_dir.name for m in plan.moves]
    assert parents[0] == "SimA"
    assert parents[1] == "SimB"
    assert parents[2] == "SimB"
    jobs_in_simb = [m.job_dir.name for m in plan.moves if m.parent_dir.name == "SimB"]
    assert jobs_in_simb == ["job_0001", "job_0002"]


def test_scan_empty_cwd_returns_empty_plan(tmp_path):
    plan = scan_all(tmp_path)
    assert plan.moves == []
    assert plan.empty_jobs == []
    assert plan.collisions == []


def test_duplicate_destination_aborts_parent_without_moving(tmp_path):
    make_tree(
        tmp_path,
        {
            "SimLead": {
                "job_0001": ["dump.root"],
                "job_0002": ["dump.root"],
            }
        },
    )
    plan = scan_all(tmp_path)

    assert [c.dest.name for c in plan.collisions] == ["dump.root"]
    assert execute_plan(plan) == 1
    assert (tmp_path / "SimLead" / "job_0001" / "dump.root").exists()
    assert (tmp_path / "SimLead" / "job_0002" / "dump.root").exists()
    assert not (tmp_path / "SimLead" / "root_files" / "dump.root").exists()


def test_existing_destination_is_never_overwritten(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["dump.root"]}})
    dest_dir = tmp_path / "SimLead" / "root_files"
    dest_dir.mkdir()
    dest = dest_dir / "dump.root"
    dest.write_bytes(b"original")

    plan = scan_all(tmp_path)

    assert execute_plan(plan) == 1
    assert dest.read_bytes() == b"original"
    assert (tmp_path / "SimLead" / "job_0001" / "dump.root").exists()


def test_destination_created_after_scan_is_never_overwritten(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["dump.root"]}})
    plan = scan_all(tmp_path)
    dest = tmp_path / "SimLead" / "root_files" / "dump.root"
    dest.parent.mkdir()
    dest.write_bytes(b"created-after-scan")

    assert execute_plan(plan) == 1
    assert dest.read_bytes() == b"created-after-scan"
    assert (tmp_path / "SimLead" / "job_0001" / "dump.root").exists()


def test_scan_cwd_with_no_job_dirs_returns_empty_plan(tmp_path):
    (tmp_path / "SimLead").mkdir()
    plan = scan_all(tmp_path)
    assert plan.moves == []
    assert plan.empty_jobs == []


# ── execute_plan ───────────────────────────────────────────────────────────────


def test_execute_moves_root_files(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root", "b.root"]}})
    plan = scan_all(tmp_path)
    execute_plan(plan)
    assert (tmp_path / "SimLead" / "root_files" / "a.root").exists()
    assert (tmp_path / "SimLead" / "root_files" / "b.root").exists()


def test_execute_deletes_job_dirs(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"], "job_0002": ["b.root"]}})
    plan = scan_all(tmp_path)
    execute_plan(plan)
    assert not (tmp_path / "SimLead" / "job_0001").exists()
    assert not (tmp_path / "SimLead" / "job_0002").exists()


def test_execute_creates_root_files_dir(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    plan = scan_all(tmp_path)
    execute_plan(plan)
    assert (tmp_path / "SimLead" / "root_files").is_dir()


def test_execute_leaves_non_job_dirs_intact(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    (tmp_path / "SimLead" / "configs").mkdir()
    plan = scan_all(tmp_path)
    execute_plan(plan)
    assert (tmp_path / "SimLead" / "configs").exists()


def test_execute_returns_0_on_success(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    plan = scan_all(tmp_path)
    assert execute_plan(plan) == 0


def test_execute_skips_empty_jobs(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": [], "job_0002": ["a.root"]}})
    plan = scan_all(tmp_path)
    execute_plan(plan)
    assert (tmp_path / "SimLead" / "job_0001").exists()
    assert not (tmp_path / "SimLead" / "job_0002").exists()


def test_execute_multiple_parents(tmp_path):
    make_tree(
        tmp_path,
        {
            "SimA": {"job_0001": ["a.root"]},
            "SimB": {"job_0001": ["b.root"]},
        },
    )
    plan = scan_all(tmp_path)
    execute_plan(plan)
    assert (tmp_path / "SimA" / "root_files" / "a.root").exists()
    assert (tmp_path / "SimB" / "root_files" / "b.root").exists()


def test_execute_move_failure_preserves_all_sibling_job_dirs(tmp_path):
    make_tree(
        tmp_path,
        {"SimLead": {"job_0001": ["a.root"], "job_0002": ["b.root"]}},
    )
    plan = scan_all(tmp_path)
    (tmp_path / "SimLead" / "job_0002" / "b.root").unlink()

    assert execute_plan(plan) == 1
    assert (tmp_path / "SimLead" / "job_0001" / "a.root").exists()
    assert (tmp_path / "SimLead" / "job_0002").is_dir()
    assert not (tmp_path / "SimLead" / "root_files" / "a.root").exists()


# ── display_plan ───────────────────────────────────────────────────────────────


def test_display_plan_runs_without_error(tmp_path):
    from rich.console import Console

    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    plan = scan_all(tmp_path)
    console = Console(file=StringIO(), highlight=False)
    display_plan(plan, console=console)  # must not raise


def test_display_plan_shows_empty_job_warning(tmp_path):
    from rich.console import Console

    make_tree(tmp_path, {"SimLead": {"job_0001": []}})
    plan = scan_all(tmp_path)
    buf = StringIO()
    console = Console(file=buf, highlight=False, no_color=True)
    display_plan(plan, console=console)
    assert "no .root" in buf.getvalue()


def test_display_plan_shows_existing_destination_collision(tmp_path):
    from rich.console import Console

    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    root_files_dir = tmp_path / "SimLead" / "root_files"
    root_files_dir.mkdir()
    (root_files_dir / "a.root").touch()
    plan = scan_all(tmp_path)
    buf = StringIO()
    console = Console(file=buf, highlight=False, no_color=True)
    display_plan(plan, console=console)
    assert "COLLISION" in buf.getvalue()
    assert "a.root" in buf.getvalue()
    assert "destination" in buf.getvalue()
    assert "exists" in buf.getvalue()


# ── integration (subprocess) ───────────────────────────────────────────────────


def test_main_executes_on_y(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    result = subprocess.run(
        [sys.executable, "-m", "fluka.queue.collect_results"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input="y\n",
    )
    assert result.returncode == 0
    assert (tmp_path / "SimLead" / "root_files" / "a.root").exists()


def test_main_aborts_on_n(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    result = subprocess.run(
        [sys.executable, "-m", "fluka.queue.collect_results"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input="n\n",
    )
    assert result.returncode == 0
    assert not (tmp_path / "SimLead" / "root_files").exists()
    assert (tmp_path / "SimLead" / "job_0001").exists()


def test_main_aborts_on_empty_input(tmp_path):
    make_tree(tmp_path, {"SimLead": {"job_0001": ["a.root"]}})
    result = subprocess.run(
        [sys.executable, "-m", "fluka.queue.collect_results"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input="\n",
    )
    assert result.returncode == 0
    assert not (tmp_path / "SimLead" / "root_files").exists()


def test_main_exits_1_when_no_job_dirs_found(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "fluka.queue.collect_results"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input="\n",
    )
    assert result.returncode == 1
    assert "no job_" in result.stderr


def test_main_processes_multiple_parents(tmp_path):
    make_tree(
        tmp_path,
        {
            "SimLead": {"job_0001": ["lead.root"]},
            "SimMercury": {"job_0001": ["mercury.root"]},
        },
    )
    result = subprocess.run(
        [sys.executable, "-m", "fluka.queue.collect_results"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        input="y\n",
    )
    assert result.returncode == 0
    assert (tmp_path / "SimLead" / "root_files" / "lead.root").exists()
    assert (tmp_path / "SimMercury" / "root_files" / "mercury.root").exists()
