# Task 4 report: writable executable default and wheel asset coverage

## Completed changes

- Changed the implicit compiled executable destination to
  `<sim.yaml directory>/.fluka/fluka_custom_exe`, using the `_config_dir`
  metadata already attached by `resolve()`.
- Preserved an explicit `custom_exe.exe_path` as the higher-priority
  destination.
- Expanded the wheel regression test to assert the Makefile, all three default
  Fortran routines, both C++ sources, and `scripts/compilerf.sh` in both the
  wheel archive and the installed package.
- Made the installed-wheel check import and call the production
  `fluka.cli.compile._root_output_dir()` helper.
- Removed the invalid source-checkout routine override from the simple example
  and compiler guide; both now explain that packaged routines are the default.
- Updated the compiler guide with the project-local executable destination.

## TDD evidence

- RED:
  `PYTHONPATH=src pytest -q tests/run/test_compile_cli.py tests/test_wheel_package.py`
  failed because `_exe_path()` returned
  `src/fluka/root_output/fluka_custom_exe` instead of the config-local
  `.fluka/fluka_custom_exe`.
- GREEN:
  `PYTHONPATH=src pytest -q tests/run/test_compile_cli.py tests/test_wheel_package.py`
  — 13 passed.
- Full suite:
  `PYTHONPATH=src pytest -q` — 328 passed.
- `git diff --check` — clean.

The smoke-test virtual environment uses `--system-site-packages` only to make
the test runner's installed dependencies (notably PyYAML) available after the
wheel itself is deliberately installed with `--no-deps --no-index`. Isolation
from the source checkout remains enforced by `-I`, an empty `PYTHONPATH`, and a
temporary working directory.

## Commit

`fix: use project-local compiler executable`

## Integration note

`wiki/sim-yaml.md` still describes the prior package-directory executable
default. It was not modified because it is outside Task 4's assigned file list;
the coordinating agent was notified.
