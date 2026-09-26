from pathlib import Path

from fluka.grid.seeds import find_duplicate_seeds, next_seed, scan_used_seeds


def _write_inp(path: Path, seed: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"* test input\nRANDOMIZ          1.{seed:>10d}\nSTART        1000.\nSTOP\n")


def test_scan_used_seeds_reads_combo_run_tree(tmp_path):
    _write_inp(tmp_path / "beame0.1_matGALLIUM" / "run_0001" / "simulation_0001.inp", 111)
    _write_inp(tmp_path / "beame0.1_matGALLIUM" / "run_0002" / "simulation_0002.inp", 222)
    _write_inp(tmp_path / "beame0.5_matTUNGSTEN" / "run_0001" / "simulation_0001.inp", 333)
    assert scan_used_seeds(tmp_path) == {111, 222, 333}


def test_scan_used_seeds_empty_when_dir_missing(tmp_path):
    assert scan_used_seeds(tmp_path / "nope") == set()


def test_next_seed_never_returns_used(tmp_path):
    used = {1, 2, 3}
    s = next_seed(used)
    assert s not in {1, 2, 3}
    assert s in used  # allocate_seed records it


def test_find_duplicate_seeds_flags_only_shared(tmp_path):
    _write_inp(tmp_path / "c1" / "run_0001" / "simulation_0001.inp", 555)
    _write_inp(tmp_path / "c2" / "run_0001" / "simulation_0001.inp", 555)
    _write_inp(tmp_path / "c3" / "run_0001" / "simulation_0001.inp", 777)
    dups = find_duplicate_seeds(tmp_path)
    assert set(dups.keys()) == {555}
    assert len(dups[555]) == 2


def test_find_duplicate_seeds_ignores_non_generated_inp(tmp_path):
    # only generated simulation_*.inp count; stray .inp files (e.g. produced on the
    # farm) must not trigger false duplicates
    _write_inp(tmp_path / "c1" / "run_0001" / "simulation_0001.inp", 555)
    _write_inp(tmp_path / "c1" / "run_0001" / "copy.inp", 555)
    assert find_duplicate_seeds(tmp_path) == {}
