from pathlib import Path
from types import SimpleNamespace

import pytest

import fluka.run.orchestrator as O
import fluka.run.orchestrator as orch
from fluka.queue.service import SubmissionBatchError, SubmissionFailure, SubmissionSummary

SIM_YAML = """
general:
  input: example.inp
  backend: ts
  output: results/
  primaries: 1000
submit:
  njobs: 2
grid:
  parameters: { beame: [0.1] }
  runs_per_combo: 2
analysis:
  units: [21]
"""


def test_analyze_phase_runs_collect_then_analysis(tmp_path, monkeypatch):
    p = tmp_path / "sim.yaml"
    p.write_text(SIM_YAML)
    calls = []
    monkeypatch.setattr(orch, "_run_collect", lambda sim: calls.append("collect"))
    monkeypatch.setattr(orch, "_run_analysis", lambda sim: calls.append("analysis"))
    orch.analyze_phase(p)
    assert calls == ["collect", "analysis"]


def test_analyze_phase_stops_when_collection_fails(monkeypatch):
    analyzed = []
    monkeypatch.setattr(
        "fluka.cli.submit.collect_sim",
        lambda sim: (_ for _ in ()).throw(RuntimeError("collection failed")),
    )
    monkeypatch.setattr("fluka.cli.analysis.run_sim", lambda sim: analyzed.append(sim))

    with pytest.raises(RuntimeError, match="collection failed"):
        orch.analyze_phase(Path("sim.yaml"))

    assert analyzed == []


def test_collect_sim_scans_results_relative_to_sim_config(tmp_path, monkeypatch):
    """Analysis must collect simulation output, not whichever directory invoked CLI."""
    from fluka.cli import submit

    sim = tmp_path / "sim.yaml"
    sim.write_text("general:\n  output: results/\n")
    seen = {}

    def collect(cwd=None):
        seen["cwd"] = cwd
        return 0

    monkeypatch.setattr("fluka.queue.collect_results.main", collect)
    submit.collect_sim(sim)
    assert seen["cwd"] == tmp_path / "results"


def _sim(tmp_path, *, custom_exe=True, grid=True):
    lines = [
        "general:",
        "  input: x.inp",
        "  backend: ts",
        "  output: out/",
        "  recompile: true",
        "submit:",
        "  njobs: 2",
    ]
    if grid:
        lines += ["grid:", "  parameters: { beame: [0.1] }", "  runs_per_combo: 1"]
    if custom_exe:
        lines += ["custom_exe:", "  routines: [mgdraw.f]"]
    p = tmp_path / "sim.yaml"
    p.write_text("\n".join(lines) + "\n")
    return p


def test_launch_compiles_then_grid(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(O, "compile_exe", lambda section, force: Path("/E"))
    monkeypatch.setattr(O, "_do_grid", lambda cfg, exe: seen.update(grid=exe))
    monkeypatch.setattr(O, "_do_submit", lambda cfg, exe: seen.update(submit=exe))
    O.launch(_sim(tmp_path, custom_exe=True, grid=True))
    assert seen.get("grid") == Path("/E") and "submit" not in seen


def test_launch_no_custom_exe_submit(tmp_path, monkeypatch):
    called = {"compile": False}
    monkeypatch.setattr(O, "compile_exe", lambda *a, **k: called.__setitem__("compile", True))
    monkeypatch.setattr(O, "_do_grid", lambda cfg, exe: None)
    monkeypatch.setattr(O, "_do_submit", lambda cfg, exe: called.__setitem__("submit_exe", exe))
    O.launch(_sim(tmp_path, custom_exe=False, grid=False))
    assert called["compile"] is False and called["submit_exe"] is None


# --- injection seams: _do_grid / _do_submit set custom_executable / custom_exe
# directly on the config/args object they build. `_do_grid` and `_do_submit`
# import load_config/validate_config/run_config and build_submit_args/run_submission
# *locally* (inside the function body), so they must be monkeypatched at their
# defining module, not as `orch.<name>` (orchestrator never binds those names
# at module scope).


def test_do_grid_injects_custom_executable(tmp_path, monkeypatch):
    fake_cfg = SimpleNamespace(fluka=SimpleNamespace(custom_executable=None, use_dpm=False))
    captured = {}
    monkeypatch.setattr("fluka.grid.config.load_config", lambda view: fake_cfg)
    monkeypatch.setattr(
        "fluka.grid.config.validate_config",
        lambda cfg: captured.setdefault("validated", cfg),
    )
    monkeypatch.setattr("fluka.grid.run.run_config", lambda cfg: captured.setdefault("ran", cfg))
    sim = _sim(tmp_path, custom_exe=False, grid=True)
    O._do_grid(sim, Path("/E"))
    assert fake_cfg.fluka.custom_executable == "/E"
    assert captured["validated"] is fake_cfg
    assert captured["ran"] is fake_cfg


def test_do_grid_raises_when_use_dpm_and_custom_exe(tmp_path, monkeypatch):
    fake_cfg = SimpleNamespace(fluka=SimpleNamespace(custom_executable=None, use_dpm=True))

    def fake_validate(cfg):
        # mirrors the real fluka.grid.config.validate_config guard
        if cfg.fluka.use_dpm and cfg.fluka.custom_executable:
            raise ValueError(
                "fluka.use_dpm and fluka.custom_executable are mutually exclusive; set only one."
            )

    monkeypatch.setattr("fluka.grid.config.load_config", lambda view: fake_cfg)
    monkeypatch.setattr("fluka.grid.config.validate_config", fake_validate)
    monkeypatch.setattr(
        "fluka.grid.run.run_config",
        lambda cfg: pytest.fail("run_config should not be reached"),
    )
    sim = _sim(tmp_path, custom_exe=False, grid=True)
    with pytest.raises(ValueError, match="mutually exclusive"):
        O._do_grid(sim, Path("/E"))


def test_do_submit_injects_custom_exe(tmp_path, monkeypatch):
    fake_args = SimpleNamespace(custom_exe=None, use_dpm=False)
    captured = {}
    monkeypatch.setattr(
        "fluka.queue.core.config.build_submit_args", lambda view, backends: fake_args
    )
    monkeypatch.setattr(
        "fluka.queue.launch_jobs.run_submission",
        lambda args: captured.setdefault("ran", args),
    )
    sim = _sim(tmp_path, custom_exe=False, grid=False)
    O._do_submit(sim, Path("/E"))
    assert fake_args.custom_exe == "/E"
    assert captured["ran"] is fake_args


def test_do_submit_raises_when_use_dpm_and_custom_exe(tmp_path, monkeypatch):
    fake_args = SimpleNamespace(custom_exe=None, use_dpm=True)
    monkeypatch.setattr(
        "fluka.queue.core.config.build_submit_args", lambda view, backends: fake_args
    )
    monkeypatch.setattr(
        "fluka.queue.launch_jobs.run_submission",
        lambda args: pytest.fail("run_submission should not be reached"),
    )
    sim = _sim(tmp_path, custom_exe=False, grid=False)
    with pytest.raises(ValueError, match="mutually exclusive"):
        O._do_submit(sim, Path("/E"))


def test_main_bare_argv_dispatches_to_launch(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(O, "launch", lambda sim: seen.update(launch=sim))
    monkeypatch.setattr(O, "analyze_phase", lambda sim: seen.update(analyze=sim))
    monkeypatch.setattr("sys.argv", ["fluka-run", "cfg.yaml"])
    O.main()
    assert seen == {"launch": Path("cfg.yaml")}


def test_main_analyze_argv_dispatches_to_analyze_phase(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(O, "launch", lambda sim: seen.update(launch=sim))
    monkeypatch.setattr(O, "analyze_phase", lambda sim: seen.update(analyze=sim))
    monkeypatch.setattr("sys.argv", ["fluka-run", "analyze", "cfg.yaml"])
    O.main()
    assert seen == {"analyze": Path("cfg.yaml")}


def test_main_translates_expected_launch_error_to_exit_one(monkeypatch):
    monkeypatch.setattr(O, "launch", lambda sim: (_ for _ in ()).throw(ValueError("bad config")))
    monkeypatch.setattr("sys.argv", ["fluka-run", "cfg.yaml"])
    with pytest.raises(SystemExit) as exc:
        O.main()
    assert exc.value.code == 1


def test_main_does_not_hide_unexpected_launch_error(monkeypatch):
    monkeypatch.setattr(
        O,
        "launch",
        lambda sim: (_ for _ in ()).throw(AssertionError("programming defect")),
    )
    monkeypatch.setattr("sys.argv", ["fluka-run", "cfg.yaml"])
    with pytest.raises(AssertionError, match="programming defect"):
        O.main()


def test_main_configures_logging_and_reports_submission_batch(monkeypatch, caplog):
    configured = []
    summary = SubmissionSummary(
        results=((1, "job 101"),),
        failures=(SubmissionFailure(2, RuntimeError("queue down")),),
    )
    monkeypatch.setattr(O, "configure_logging", lambda: configured.append(True), raising=False)
    monkeypatch.setattr(
        O,
        "launch",
        lambda sim: (_ for _ in ()).throw(SubmissionBatchError(summary)),
    )
    monkeypatch.setattr("sys.argv", ["fluka-run", "sim.yaml"])

    with caplog.at_level("INFO"), pytest.raises(SystemExit) as exc:
        O.main()

    assert exc.value.code == 1
    assert configured == [True]
    assert "Job 1: job 101" in caplog.text
    assert "Job 2 fallito: queue down" in caplog.text
