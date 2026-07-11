import sys
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fluka.grid import run as run_grid
from fluka.grid.seeds import scan_used_seeds


def make_project(tmp_path, backend="ts", runs_per_combo=2, params=None):
    inp = tmp_path / "example.inp"
    inp.write_text("#define beame 0.5\n#define mat GALLIUM\nRANDOMIZ         1.0\nSTOP\n")
    cfg = {
        "general": {
            "input": str(inp),
            "backend": backend,
            "output": str(tmp_path / "results"),
            "rfluka_path": "/fluka/bin",
        },
        "submit": {"max_parallel": 4},
        "grid": {
            "parameters": params or {"beame": [0.05, 0.1], "mat": ["GALLIUM"]},
            "runs_per_combo": runs_per_combo,
        },
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(cfg))
    return cfg_path


def run_main(argv):
    with patch.object(sys, "argv", ["run_grid.py"] + argv):
        run_grid.main()
    return run_grid


# --- main() end-to-end (submission delegated to queue_adapter) -----------------

def test_dry_run_passes_dry_flag_and_skips_confirm(tmp_path):
    cfg_path = make_project(tmp_path)
    with patch("fluka.grid.backends.queue_adapter.submit_run", return_value="[dry run]") as m, \
         patch("subprocess.run") as mock_sub:
        run_main([str(cfg_path), "--dry-run"])
    # 2 combos × 2 runs = 4 submissions, all dry
    assert m.call_count == 4
    assert all(c.kwargs["dry_run"] is True for c in m.call_args_list)
    # ts slot-setting (`ts -S`) must NOT run in dry-run mode
    assert not any(call.args and call.args[0][:2] == ["ts", "-S"] for call in mock_sub.call_args_list)


def test_submits_correct_number_of_jobs(tmp_path):
    cfg_path = make_project(tmp_path)
    with patch("builtins.input", return_value="yes"), \
         patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="1\n")), \
         patch("fluka.grid.backends.queue_adapter.submit_run", return_value="job") as m:
        run_main([str(cfg_path)])
    # 2 combos × 2 runs = 4 submissions
    assert m.call_count == 4


def test_ts_slots_set_before_submit(tmp_path):
    cfg_path = make_project(tmp_path, backend="ts")
    with patch("builtins.input", return_value="yes"), \
         patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="")) as mock_sub, \
         patch("fluka.grid.backends.queue_adapter.submit_run", return_value="job"):
        run_main([str(cfg_path)])
    assert any(
        call.args and call.args[0][:2] == ["ts", "-S"] for call in mock_sub.call_args_list
    )


def test_reset_deletes_output_dir(tmp_path, monkeypatch):
    cfg_path = make_project(tmp_path)
    results = tmp_path / "results"
    results.mkdir()
    marker = results / "old.txt"
    marker.write_text("stale")

    monkeypatch.setattr("builtins.input", lambda _: "yes")
    with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="")), \
         patch("fluka.grid.backends.queue_adapter.submit_run", return_value="job"):
        run_main([str(cfg_path), "--reset"])

    assert not marker.exists()      # output dir was wiped
    assert results.exists()         # and recreated for fresh submission


def test_reset_aborts_on_no(tmp_path, monkeypatch, capsys):
    cfg_path = make_project(tmp_path)
    results = tmp_path / "results"
    results.mkdir()
    marker = results / "keep_me.txt"
    marker.write_text("important")

    monkeypatch.setattr("builtins.input", lambda _: "no")
    with pytest.raises(SystemExit):
        run_main([str(cfg_path), "--reset"])

    assert marker.exists()
    assert "Aborted" in capsys.readouterr().out


def test_check_seeds_reports_duplicates(tmp_path, monkeypatch, capsys):
    out = tmp_path / "out"
    (out / "c1" / "run_0001").mkdir(parents=True)
    (out / "c2" / "run_0001").mkdir(parents=True)
    (out / "c1" / "run_0001" / "simulation_0001.inp").write_text("RANDOMIZ          1.       999\n")
    (out / "c2" / "run_0001" / "simulation_0001.inp").write_text("RANDOMIZ          1.       999\n")

    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "general:\n  input: sim.inp\n  rfluka_path: /fake/bin\n"
        "  output: %s\n"
        "submit:\n  max_parallel: 4\n"
        "grid:\n  parameters:\n    beame: [0.1]\n  runs_per_combo: 1\n" % out
    )
    (tmp_path / "sim.inp").write_text("#define beame 0.1\nRANDOMIZ 1. 1.\nSTART 1000.\nSTOP\n")

    monkeypatch.setattr(sys, "argv", ["run_grid.py", str(cfg_file), "--check-seeds"])
    with pytest.raises(SystemExit) as exc:
        run_grid.main()
    assert exc.value.code != 0
    assert "999" in capsys.readouterr().out


# --- _submit_combo unit tests --------------------------------------------------

def _make_cfg(tmp_path, backend="slurm", runs_per_combo=2):
    template = tmp_path / "sim.inp"
    template.write_text("#define beame 0.1\nRANDOMIZ          1.        1.\nSTART 1000.\nSTOP\n")

    class _F:
        input = template
        primaries = None
        use_dpm = False
        custom_executable = None

    class _G:
        pass

    class _E:
        def __init__(self, backend):
            self.backend = backend
            self.farm_out = "/farm_out"

    cfg = MagicMock()
    cfg.fluka = _F()
    cfg.grid = _G()
    cfg.grid.runs_per_combo = runs_per_combo
    cfg.output_dir = tmp_path / "out"
    cfg.execution = _E(backend)
    cfg.output_dir.mkdir()
    return cfg


def test_submit_combo_calls_adapter_per_run(tmp_path):
    cfg = _make_cfg(tmp_path, backend="slurm", runs_per_combo=2)
    args = MagicMock(dry_run=False)
    with patch.object(run_grid.queue_adapter, "submit_run", return_value="12345") as m:
        run_grid._submit_combo({"beame": 0.1}, cfg, Path("/fake/bin"), args)
    assert m.call_count == 2
    assert all(c.kwargs["backend_name"] == "slurm" for c in m.call_args_list)


def test_submit_combo_allocates_unique_seeds(tmp_path):
    cfg = _make_cfg(tmp_path, backend="ts", runs_per_combo=3)
    args = MagicMock(dry_run=False)
    with patch.object(run_grid.queue_adapter, "submit_run", return_value="job"):
        run_grid._submit_combo({"beame": 0.1}, cfg, Path("/fake/bin"), args)
    seeds = scan_used_seeds(cfg.output_dir)
    assert len(seeds) == 3  # three distinct seeds, no collisions


def test_submit_combo_dry_run_passes_flag(tmp_path):
    cfg = _make_cfg(tmp_path, backend="slurm", runs_per_combo=1)
    args = MagicMock(dry_run=True)
    with patch.object(run_grid.queue_adapter, "submit_run", return_value="[dry run]") as m:
        run_grid._submit_combo({"beame": 0.1}, cfg, Path("/fake/bin"), args)
    assert m.call_count == 1
    assert m.call_args.kwargs["dry_run"] is True


def test_submit_combo_repairs_duplicate_without_abort(tmp_path):
    from fluka.grid.seeds import find_duplicate_seeds

    cfg = _make_cfg(tmp_path, backend="slurm", runs_per_combo=1)
    out = cfg.output_dir
    # two pre-existing inputs (other combos) sharing the same seed
    for combo in ("c1", "c2"):
        d = out / combo / "run_0001"
        d.mkdir(parents=True)
        (d / "simulation_0001.inp").write_text("RANDOMIZ          1.       999\nSTART 1.\nSTOP\n")
    assert set(find_duplicate_seeds(out)) == {999}

    args = MagicMock(dry_run=False)
    with patch.object(run_grid.queue_adapter, "submit_run", return_value="job"):
        # must NOT raise SystemExit; repairs the duplicate and proceeds to submit
        run_grid._submit_combo({"beame": 0.1}, cfg, Path("/fake/bin"), args)

    assert find_duplicate_seeds(out) == {}  # duplicate was regenerated away
