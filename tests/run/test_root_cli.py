from fluka.cli.root import build_commands

def test_rntuple_file_sets_use_rntuple_1():
    cmds = build_commands({"files": ["FluLibRNTuple.cpp"]}, root_dir="/x/root_output")
    assert len(cmds) == 1
    c = cmds[0]
    assert c[0] == "make" and "-C" in c and "/x/root_output" in c
    assert "USE_RNTUPLE=1" in c

def test_default_file_sets_use_rntuple_0():
    cmds = build_commands({"files": ["FluLib.cpp"]}, root_dir="/x")
    assert "USE_RNTUPLE=0" in cmds[0]

def test_format_used_when_no_files():
    cmds = build_commands({"format": "rntuple"}, root_dir="/x")
    assert len(cmds) == 1 and "USE_RNTUPLE=1" in cmds[0]

def test_empty_section_builds_nothing():
    assert build_commands({}, root_dir="/x") == []
