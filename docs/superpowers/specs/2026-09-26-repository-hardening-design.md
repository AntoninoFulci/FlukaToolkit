# FlukaToolkit Repository Hardening Design

**Date:** 2026-09-26

## Objective

Harden FlukaToolkit against data loss and false-success states, clean repository artifacts and documentation, consolidate submission infrastructure, and add automated quality gates.

Compatibility is required for the six console commands and the existing `sim.yaml` schema. Internal Python APIs may change. The project remains without an explicit license.

## Current Strengths

- `src/` package layout with six installed console commands.
- Clear domain split between grid generation, queue submission, run orchestration, isotope analysis, and ROOT compiler assets.
- Broad automated suite: 335 tests currently pass.
- Wheel test verifies packaged compiler assets.

## Correctness Requirements

### ROOT result collection

Collection must never overwrite a destination file. Planning must detect duplicate destination names across job directories and files already present in `root_files/` before moving any source. Any collision aborts that parent directory without deleting job directories.

Collection returns a non-zero result on planning or execution failure. `collect_sim()` converts that result into an exception so `fluka-run analyze` and `fluka-status --collect` cannot start analysis after failed collection.

### Submission failures

Batch submission continues attempting independent prepared jobs, records every failure, then reports failure to the caller. CLI entrypoints exit non-zero when one or more submissions fail. Folder and benchmark modes include those failures in their existing failure counts.

### Scheduler status

All generated runner scripts capture FLUKA's exit code, write `FLUKA_STATUS rc=N`, complete required output transfer or cleanup, then exit with the captured code.

HTCondor status resolves the transferred `run_dir/.fluka_status` file instead of searching its stdout file. Slurm keeps its farm-visible sentinel path; LSF and Task Spooler keep run-directory sentinels.

### Process state

Task Spooler submission must not call process-global `os.chdir()`. Absolute input paths and the backend's command-local `cd` provide the required working directory.

Importing library modules must not configure root logging. Logging configuration belongs to CLI entrypoints.

## Architecture

### Backend registry

Create one registry module under `fluka.queue.backends`. It owns canonical backend names, backend classes, and factory functions for class or instance mappings. Grid submission, legacy submission, status, and configuration all consume this registry.

Backend implementations remain separate because scheduler behavior genuinely differs. Shared behavior is limited to small helpers for FLUKA command construction, executable script writing, and sentinel handling where this removes real duplication.

### Typed submission configuration

Replace core dependence on `argparse.Namespace` with a `SubmissionConfig` dataclass. Direct CLI parsing, legacy YAML, and merged `sim.yaml` views all create this type.

The dataclass contains common submission values plus scheduler resource values required by current backends. Backend validation consumes the typed object. `Namespace` exists only while parsing command-line arguments.

No compatibility promise applies to `load_yaml_config()`, `build_submit_args()`, `run_from_args()`, `_execute_jobs()`, or module-level `BACKENDS` imports. Tests and internal callers migrate to the new interfaces.

### Submission service

Move job preparation and submission out of `launch_jobs.py` into a focused service module. The service:

1. validates executable and input assumptions;
2. creates output and job directories;
3. allocates and verifies unique seeds;
4. submits prepared jobs;
5. returns a structured summary or raises a structured submission error.

`launch_jobs.py` retains CLI parsing, confirmation, folder mode, and benchmark presentation. CLI code translates domain exceptions into messages and exit codes.

### Error boundary

Core functions raise typed exceptions or return explicit result objects. Only console entrypoints raise `SystemExit`. Expected validation and scheduler failures are caught narrowly; unexpected exceptions retain tracebacks instead of being swallowed by broad `except Exception` blocks.

## Repository Cleanup

- Add `graphify-out/` to `.gitignore`; keep generated graph locally.
- Remove generated `.DS_Store`, `__pycache__`, `.pyc`, `.pytest_cache`, `build/`, and `*.egg-info` artifacts from the working tree.
- Keep `docs/legacy/` local and ignored. Remove README and wiki claims that it is present in public repository.
- Track `scripts/sync-wiki.sh`. Allow `FLUKATOOLKIT_WIKI_REMOTE` override and otherwise derive wiki URL from Git `origin` when possible.
- Add package `readme` and project URLs to `pyproject.toml`. Do not add license metadata or a `LICENSE` file.

## Quality Gates

Development dependencies include Ruff, mypy, pytest-cov, pytest, and build. Configuration lives in `pyproject.toml`.

- Ruff checks Python sources and tests and enforces formatting.
- Mypy starts with refactored queue, run, and CLI modules; missing third-party stubs do not block adoption.
- Pytest coverage reports missing lines without initially imposing an arbitrary percentage threshold.
- GitHub Actions runs lint, type checks, tests, and wheel build on supported Python versions.
- Existing wheel/package-data test remains authoritative for compiler assets.

## Testing Strategy

Every behavioral change follows red-green-refactor:

- duplicate ROOT filenames and existing destination collisions;
- failed collection preventing analysis;
- one failed scheduler submission causing overall failure;
- HTCondor sentinel path after queue disappearance;
- generated scripts preserving FLUKA exit status;
- Task Spooler submission leaving process working directory unchanged;
- registry parity across grid, status, and direct submission;
- CLI/YAML creation of equivalent typed configurations;
- unchanged command registration and `sim.yaml` resolution behavior.

Full `pytest` runs after each cohesive task. Final verification includes Ruff, mypy, coverage-enabled pytest, wheel build, installed-wheel asset smoke test, and a clean Git status review.

## Documentation and Migration

README and wiki keep public CLI usage unchanged. Internal Python API migrations require no compatibility shim unless needed temporarily inside one refactor step. Behavioral changes to exit codes and collision handling are documented as correctness fixes.

No data migration is required. Existing manifests and `sim.yaml` files remain readable.

## Explicit Non-Goals

- No new scheduler backend.
- No plugin framework or dynamic backend discovery.
- No replacement CLI framework.
- No new runtime dependency for configuration.
- No automatic deletion of simulation results.
- No license selection.
