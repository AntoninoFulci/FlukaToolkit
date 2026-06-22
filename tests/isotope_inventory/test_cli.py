import sys
import pytest
from unittest.mock import patch
import run_analysis


def test_main_loads_config_and_runs(tmp_path):
    sim = tmp_path / "sim"
    sim.mkdir()
    cfg = tmp_path / "analysis.yaml"
    cfg.write_text(f"""
analysis:
  directory: {sim}
  units: [21]
  volume: 1000
  isotopes:
    27: 60
""")
    with patch.object(run_analysis, "run_analysis") as mock_run:
        with patch.object(sys, "argv", ["run_analysis.py", str(cfg)]):
            run_analysis.main()
    mock_run.assert_called_once()
    passed_cfg = mock_run.call_args.args[0]
    assert passed_cfg.directory == sim
    assert passed_cfg.units == [21]


def test_main_requires_config_arg():
    with patch.object(sys, "argv", ["run_analysis.py"]):
        with pytest.raises(SystemExit):
            run_analysis.main()
