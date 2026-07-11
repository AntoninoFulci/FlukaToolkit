import sys
import pytest
from unittest.mock import patch
from fluka.isotope_inventory import run as run_analysis


def test_main_loads_config_and_runs(tmp_path):
    output_dir = tmp_path / "results"
    run_dir = output_dir / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    cfg = tmp_path / "sim.yaml"
    cfg.write_text(f"""
general:
  input: example.inp
  backend: ts
  output: results/
analysis:
  run: c1/run_0001
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
    assert passed_cfg.directory == run_dir
    assert passed_cfg.units == [21]


def test_main_requires_config_arg():
    with patch.object(sys, "argv", ["run_analysis.py"]):
        with pytest.raises(SystemExit):
            run_analysis.main()
