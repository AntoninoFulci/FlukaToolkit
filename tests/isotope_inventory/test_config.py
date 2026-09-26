from pathlib import Path

import pytest

from fluka.isotope_inventory.config import AnalysisConfig, load_analysis_config
from fluka.run.simconfig import resolve


def _write_sim(tmp_path, body: str) -> Path:
    p = tmp_path / "sim.yaml"
    p.write_text(body)
    return p


def test_load_full_config(tmp_path):
    output_dir = tmp_path / "results"
    run_dir = output_dir / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    sim_path = _write_sim(
        tmp_path,
        """
general:
  input: example.inp
  backend: ts
  output: results/
  primaries: 1000
analysis:
  run: c1/run_0001
  units: [21, 22]
  executable: usrsuw
  volume: 1000
  isotopes:
    31: 70
    30: 69
  output: out.xlsx
""",
    )
    view = resolve(sim_path, "analysis")
    c = load_analysis_config(view)
    assert isinstance(c, AnalysisConfig)
    assert c.directory == run_dir
    assert c.units == [21, 22]
    assert c.executable == "usrsuw"
    assert c.volume == 1000.0
    assert c.isotopes == [(30, 69), (31, 70)]
    assert c.output == "out.xlsx"


def test_defaults_applied(tmp_path):
    output_dir = tmp_path / "results"
    run_dir = output_dir / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    sim_path = _write_sim(
        tmp_path,
        """
general:
  input: example.inp
  backend: ts
  output: results/
  primaries: 1000
analysis:
  run: c1/run_0001
  units: [21]
  volume: 500
  isotopes:
    27: 60
""",
    )
    view = resolve(sim_path, "analysis")
    c = load_analysis_config(view)
    assert c.executable == "usrsuw"
    assert c.output == "isotopes.xlsx"


def test_isotopes_list_valued_mass(tmp_path):
    output_dir = tmp_path / "results"
    run_dir = output_dir / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    sim_path = _write_sim(
        tmp_path,
        """
general:
  input: example.inp
  backend: ts
  output: results/
analysis:
  run: c1/run_0001
  units: [21]
  volume: 100
  isotopes:
    30: [69, 70]
    31: 71
""",
    )
    view = resolve(sim_path, "analysis")
    c = load_analysis_config(view)
    assert c.isotopes == [(30, 69), (30, 70), (31, 71)]


def test_missing_run_field_raises(tmp_path):
    output_dir = tmp_path / "results"
    output_dir.mkdir(parents=True)
    sim_path = _write_sim(
        tmp_path,
        """
general:
  input: example.inp
  backend: ts
  output: results/
analysis:
  units: [21]
  volume: 1
  isotopes:
    27: 60
""",
    )
    view = resolve(sim_path, "analysis")
    with pytest.raises(ValueError, match="run"):
        load_analysis_config(view)


def test_nonexistent_run_directory_raises(tmp_path):
    output_dir = tmp_path / "results"
    output_dir.mkdir(parents=True)
    sim_path = _write_sim(
        tmp_path,
        """
general:
  input: example.inp
  backend: ts
  output: results/
analysis:
  run: c1/run_0001
  units: [21]
  volume: 1
  isotopes:
    27: 60
""",
    )
    view = resolve(sim_path, "analysis")
    with pytest.raises(ValueError, match="does not exist"):
        load_analysis_config(view)


def test_empty_units_raises(tmp_path):
    output_dir = tmp_path / "results"
    run_dir = output_dir / "c1" / "run_0001"
    run_dir.mkdir(parents=True)
    sim_path = _write_sim(
        tmp_path,
        """
general:
  input: example.inp
  backend: ts
  output: results/
analysis:
  run: c1/run_0001
  units: []
  volume: 1
  isotopes:
    27: 60
""",
    )
    view = resolve(sim_path, "analysis")
    with pytest.raises(ValueError, match="units"):
        load_analysis_config(view)
