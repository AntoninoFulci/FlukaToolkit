from pathlib import Path
import pytest
from fluka.run.config import load_sim, section, extract, SECTIONS

SIM = """
grid: {template: my.inp, params: {thickness: [1, 2]}}
submit: {backend: slurm}
analysis: {units: [21], isotopes: {31: 70}}
root: {files: [FluLibRNTuple.cpp], format: rntuple}
"""

def _write(tmp_path) -> Path:
    p = tmp_path / "sim.yaml"; p.write_text(SIM); return p

def test_each_tool_gets_its_own_section(tmp_path):
    p = _write(tmp_path)
    assert extract(p, "grid")["template"] == "my.inp"
    assert extract(p, "submit")["backend"] == "slurm"
    assert extract(p, "analysis")["units"] == [21]
    assert extract(p, "root")["format"] == "rntuple"

def test_missing_section_raises_keyerror(tmp_path):
    p = tmp_path / "s.yaml"; p.write_text("grid: {}\n")
    with pytest.raises(KeyError, match="analysis"):
        extract(p, "analysis")

def test_sections_constant_covers_all_tools():
    assert set(SECTIONS) == {"grid", "submit", "analysis", "root"}
