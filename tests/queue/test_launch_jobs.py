import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml as _yaml


def test_no_subcommand_exits(capsys):
    sys.argv = ["launch_jobs.py"]
    import importlib

    from fluka.queue import launch_jobs

    importlib.reload(launch_jobs)
    with pytest.raises(SystemExit):
        launch_jobs.main()


def test_invalid_extension_exits():
    sys.argv = ["launch_jobs.py", "ts", "-f", "input.txt", "-n", "1"]
    import importlib

    from fluka.queue import launch_jobs

    importlib.reload(launch_jobs)
    with pytest.raises(SystemExit) as exc:
        launch_jobs.main()
    assert exc.value.code == 1


def test_run_submission_raises_validation_error_instead_of_system_exit():
    from fluka.queue.core.config import SubmissionConfig
    from fluka.queue.launch_jobs import run_submission

    config = SubmissionConfig(backend="ts", input="not-an-input.txt", njobs=1)
    with pytest.raises(ValueError, match="must end with .inp"):
        run_submission(config)


def test_main_translates_submission_error_to_exit_one(monkeypatch):
    from fluka.queue import launch_jobs

    def fail(config):
        raise ValueError("invalid submission")

    monkeypatch.setattr(launch_jobs, "run_submission", fail, raising=False)
    monkeypatch.setattr("sys.argv", ["launch_jobs.py", "ts", "-f", "input.inp", "-n", "1"])
    with pytest.raises(SystemExit) as exc:
        launch_jobs.main()
    assert exc.value.code == 1


def test_main_does_not_hide_unexpected_submission_errors(monkeypatch):
    from fluka.queue import launch_jobs

    def fail(config):
        raise AssertionError("programming defect")

    monkeypatch.setattr(launch_jobs, "run_submission", fail, raising=False)
    monkeypatch.setattr("sys.argv", ["launch_jobs.py", "ts", "-f", "input.inp", "-n", "1"])
    with pytest.raises(AssertionError, match="programming defect"):
        launch_jobs.main()


def test_ts_dry_run_creates_job_dirs(tmp_path, monkeypatch):
    inp = tmp_path / "myinput.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")

    sys.argv = ["launch_jobs.py", "ts", "-f", str(inp), "-n", "3", "-w"]
    monkeypatch.chdir(tmp_path)

    with (
        patch(
            "fluka.queue.core.fluka.detect_fluka_path",
            return_value=("/usr/local/bin", "/usr/local/fluka"),
        ),
        patch("fluka.queue.core.display.confirm", return_value=True),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        launch_jobs.main()

    output_dir = tmp_path / "myinput"
    assert output_dir.is_dir()
    assert len(list(output_dir.iterdir())) == 3


def test_lsf_dry_run_creates_sh_files(tmp_path, monkeypatch):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")

    sys.argv = ["launch_jobs.py", "lsf", "-f", str(inp), "-n", "2", "-w"]
    monkeypatch.chdir(tmp_path)

    with (
        patch(
            "fluka.queue.core.fluka.detect_fluka_path",
            return_value=("/usr/local/bin", "/usr/local/fluka"),
        ),
        patch("fluka.queue.core.display.confirm", return_value=True),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        launch_jobs.main()

    output_dir = tmp_path / "sim"
    sh_files = list(output_dir.rglob("*.sh"))
    assert len(sh_files) == 2


def test_yaml_mode_ts_dry_run(tmp_path, monkeypatch):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")

    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({"backend": "ts", "input": str(inp), "njobs": 2, "dry_run": True}))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", str(cfg)]

    with (
        patch(
            "fluka.queue.core.fluka.detect_fluka_path",
            return_value=("/usr/local/bin", "/usr/local/fluka"),
        ),
        patch("fluka.queue.core.display.confirm", return_value=True),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        launch_jobs.main()

    output_dir = tmp_path / "sim"
    assert output_dir.is_dir()
    assert len(list(output_dir.iterdir())) == 2


def test_yaml_mode_lsf_dry_run(tmp_path, monkeypatch):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")

    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({"backend": "lsf", "input": str(inp), "njobs": 2, "dry_run": True}))

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", str(cfg)]

    with (
        patch(
            "fluka.queue.core.fluka.detect_fluka_path",
            return_value=("/usr/local/bin", "/usr/local/fluka"),
        ),
        patch("fluka.queue.core.display.confirm", return_value=True),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        launch_jobs.main()

    sh_files = list((tmp_path / "sim").rglob("*.sh"))
    assert len(sh_files) == 2


def test_yaml_mode_invalid_input_extension_exits(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({"backend": "ts", "input": "sim.txt", "njobs": 1}))

    sys.argv = ["launch_jobs.py", str(cfg)]

    with patch(
        "fluka.queue.core.fluka.detect_fluka_path",
        return_value=("/usr/local/bin", "/usr/local/fluka"),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        with pytest.raises(SystemExit):
            launch_jobs.main()


def test_yaml_mode_missing_backend_exits(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(_yaml.dump({"input": "sim.inp", "njobs": 1}))  # no backend key

    sys.argv = ["launch_jobs.py", str(cfg)]

    import importlib

    from fluka.queue import launch_jobs

    importlib.reload(launch_jobs)
    with pytest.raises(SystemExit):
        launch_jobs.main()


def test_folder_mode_runs_all_yamls(tmp_path, monkeypatch):
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    for stem in ["sim_a", "sim_b"]:
        inp = tmp_path / f"{stem}.inp"
        inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")
        (configs_dir / f"{stem}.yaml").write_text(
            _yaml.dump(
                {
                    "backend": "ts",
                    "input": str(inp),
                    "njobs": 1,
                    "dry_run": True,
                }
            )
        )

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", str(configs_dir)]

    with (
        patch(
            "fluka.queue.core.fluka.detect_fluka_path",
            return_value=("/usr/local/bin", "/usr/local/fluka"),
        ),
        patch("fluka.queue.core.display.confirm", return_value=True),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        launch_jobs.main()

    # Two YAMLs with the same input create two output dirs (sim/ and sim_1/)
    output_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name != "configs"]
    assert len(output_dirs) == 2


def test_folder_mode_empty_dir_warns(tmp_path, caplog):
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()

    sys.argv = ["launch_jobs.py", str(configs_dir)]

    import importlib

    from fluka.queue import launch_jobs

    importlib.reload(launch_jobs)

    import logging

    with caplog.at_level(logging.WARNING):
        launch_jobs.main()

    assert "Nessun file YAML" in caplog.text


def test_folder_mode_skips_invalid_continues_valid(tmp_path, monkeypatch, caplog):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")

    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "bad.yaml").write_text(
        _yaml.dump({"backend": "nonexistent", "input": str(inp), "njobs": 1})
    )
    (configs_dir / "good.yaml").write_text(
        _yaml.dump({"backend": "ts", "input": str(inp), "njobs": 1, "dry_run": True})
    )

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", str(configs_dir)]

    with (
        patch(
            "fluka.queue.core.fluka.detect_fluka_path",
            return_value=("/usr/local/bin", "/usr/local/fluka"),
        ),
        patch("fluka.queue.core.display.confirm", return_value=True),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        import logging

        with caplog.at_level(logging.ERROR):
            launch_jobs.main()

    assert "non valido" in caplog.text
    output_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name != "configs"]
    assert len(output_dirs) == 1  # only good.yaml creates a dir


def test_folder_mode_cancelled_by_user(tmp_path, monkeypatch, caplog):
    inp = tmp_path / "sim.inp"
    inp.write_text("RANDOMIZ          1.  12345678\nSTOP\n")

    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "a.yaml").write_text(
        _yaml.dump({"backend": "ts", "input": str(inp), "njobs": 1, "dry_run": True})
    )

    monkeypatch.chdir(tmp_path)
    sys.argv = ["launch_jobs.py", str(configs_dir)]

    import logging

    with (
        patch(
            "fluka.queue.core.fluka.detect_fluka_path",
            return_value=("/usr/local/bin", "/usr/local/fluka"),
        ),
        patch("fluka.queue.core.display.confirm", return_value=False),
        caplog.at_level(logging.INFO),
    ):
        import importlib

        from fluka.queue import launch_jobs

        importlib.reload(launch_jobs)
        launch_jobs.main()

    assert "Lancio annullato" in caplog.text
    output_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name != "configs"]
    assert len(output_dirs) == 0  # no jobs executed


def test_submit_jobs_aborts_on_duplicate_seeds(tmp_path, monkeypatch):
    from fluka.queue import service
    from fluka.queue.core.config import SubmissionConfig

    submitted = []

    class StubBackend:
        def generate_script(self, job_info, job_dir, args):
            return None

        def submit(self, script_path, job_info, args):
            submitted.append(job_info)
            return "ok"

    backends = {"stub": StubBackend()}
    # Force the on-disk verification to report a duplicate.
    monkeypatch.setattr(
        service.fluka,
        "find_duplicate_seeds",
        lambda output_dir: {
            123: [tmp_path / "job_0001" / "a.inp", tmp_path / "job_0002" / "b.inp"]
        },
    )

    src = tmp_path / "sim.inp"
    src.write_text("RANDOMIZ          1.  1\n")
    args = SubmissionConfig(
        backend="stub",
        input=str(src),
        njobs=2,
        custom_exe=None,
        output_dir=str(tmp_path / "out"),
        nprim=None,
    )
    with pytest.raises(RuntimeError, match="Seed RANDOMIZ duplicati"):
        service.submit_jobs(args, fluka_path="/fake/fluka", backends=backends)
    assert submitted == []  # aborted before any submission


def test_prepare_jobs_gives_ts_an_absolute_input_path(tmp_path, monkeypatch):
    """TS backend must know job directory; relative input is absent from caller cwd."""
    from fluka.queue.core.config import SubmissionConfig
    from fluka.queue.service import prepare_jobs

    src = tmp_path / "sim.inp"
    src.write_text("RANDOMIZ          1.  1\n")
    args = SubmissionConfig(
        backend="ts",
        input=str(src),
        njobs=1,
        custom_exe=None,
        output_dir=str(tmp_path / "out"),
        nprim=None,
        dry_run=True,
        use_dpm=False,
    )
    prepared = prepare_jobs(args, fluka_path="/fake/fluka")
    submitted_input = Path(prepared[0].job_info.input_file)
    assert submitted_input.is_absolute()
    assert submitted_input.parent.name == "job_0001"
