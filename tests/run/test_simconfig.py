from pathlib import Path
import pytest
from fluka.run.simconfig import load_sim, resolve, GENERAL_KEYS


def _write(tmp_path, text):
    p = tmp_path / "sim.yaml"; p.write_text(text); return p

BASE = """
general:
  input: example.inp
  backend: ts
  output: results/
  primaries: 1000
submit:
  njobs: 2
  mem: "1500"
grid:
  parameters: { beame: [0.1] }
  runs_per_combo: 2
"""

def test_load_sim_requires_general(tmp_path):
    p = _write(tmp_path, "submit: {njobs: 1}\n")
    with pytest.raises(Exception):
        load_sim(p)

def test_resolve_merges_general_into_tool(tmp_path):
    p = _write(tmp_path, BASE)
    g = resolve(p, "grid")
    assert g["backend"] == "ts"                 # from general
    assert g["primaries"] == 1000               # from general
    assert g["parameters"] == {"beame": [0.1]}  # from grid
    assert g["runs_per_combo"] == 2

def test_resolve_tool_overrides_general(tmp_path):
    p = _write(tmp_path, BASE + "\nsubmit:\n  backend: slurm\n  njobs: 2\n")
    s = resolve(p, "submit")
    assert s["backend"] == "slurm"              # submit overrides general.ts

def test_resolve_paths_relative_to_config_dir(tmp_path):
    p = _write(tmp_path, BASE)
    g = resolve(p, "grid")
    assert Path(g["input"]).is_absolute()
    assert Path(g["input"]) == (tmp_path / "example.inp")
    assert Path(g["output"]) == (tmp_path / "results")

def test_resolve_missing_tool_section(tmp_path):
    p = _write(tmp_path, BASE)
    # analysis section absent -> resolve still returns general-only view (no crash);
    # required-field errors are raised by the tool loader, not resolve.
    a = resolve(p, "analysis")
    assert a["backend"] == "ts"
