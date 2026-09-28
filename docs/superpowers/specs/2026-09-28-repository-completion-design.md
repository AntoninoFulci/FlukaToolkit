# FlukaToolkit Repository Completion Design

**Date:** 2026-09-28

## Objective

Finish repository-hardening follow-up work without expanding scope into new runtime
features. Align public submission documentation with implemented guarantees, extend
mypy coverage to `fluka.isotope_inventory`, record deferred behavioral policies, and
leave repository ready for an explicit publication decision.

The project remains without an explicit license. No license file or package license
metadata will be added.

## Current State

- `main` is clean and 12 commits ahead of `origin/main`.
- Collision-safe collection, failed-collection retention, and per-job submission
  failure aggregation already exist in code and tests but are not fully described in
  `wiki/fluka-submit.md`.
- Mypy checks `fluka.queue`, `fluka.run`, and `fluka.cli`; it skips
  `fluka.isotope_inventory`.
- Direct mypy analysis of `fluka.isotope_inventory` reports 11 errors across binary
  file handling and inconsistent isotope collection annotations.

## Scope

### Submission wiki

Update `wiki/fluka-submit.md` to state these existing guarantees:

1. Collection rejects duplicate destination filenames and destinations already
   present under `root_files/` before moving files for the affected parent run.
2. Any planning or execution failure preserves source `job_*` directories. A failed
   parent is not partially collected; destinations created during a failed execution
   are rolled back when they can be identified safely.
3. Submission attempts all independently prepared jobs, reports each failed job, and
   returns a non-zero CLI result when any job fails. Successful submissions remain
   successful and are included in the summary.

Documentation must describe behavior, not internal implementation names.

### Isotope typing

Include `src/fluka/isotope_inventory` in the configured mypy target and remove its
`follow_imports = "skip"` override.

Use `list[tuple[int, int]]` consistently for requested isotope `(Z, A)` pairs across
configuration, analysis, reader, and workbook generation. Add focused aliases only
where they clarify heterogeneous analysis rows or binary statistics records.

Type binary readers explicitly. Internal open-file state must be represented as
optional and checked before use, or eliminated in favor of locally scoped file
handles. Missing required detector data must raise an explicit `OSError` instead of
passing `None` into `struct.unpack`.

Typing changes must preserve current output values, workbook columns, file parsing,
and CLI behavior. Do not silence errors with `type: ignore`, broad `Any` annotations,
or a replacement mypy exclusion.

### Deferred policies

Record these decisions as future requirements. Do not implement them in this change.

#### Grid submission failures

- Continue submitting independent prepared runs and parameter combinations after one
  scheduler submission fails.
- Record manifest entries only for successful submissions.
- Aggregate failures with combo, run, and scheduler error context.
- Exit non-zero after all independent submissions have been attempted.

#### Scheduler paths, quoting, and resources

- Resolve user-configured paths relative to the configuration file before passing
  them into scheduler adapters.
- Quote every value interpolated into a shell command; prefer argument vectors when
  no shell syntax is required.
- Keep resource validation in the backend that owns each resource and reject invalid
  values before submission.
- Preserve accepted cross-backend configuration keys so one `sim.yaml` remains
  portable; unused resource keys do not affect other backends.

#### Cancellation and empty results

- Declining confirmation before work starts is a successful no-op with exit status 0.
- Interrupting active work stops new submissions, preserves already created files and
  recorded successful submissions, performs no implicit scheduler cancellation, and
  exits with status 130.
- Commands whose purpose is to produce or collect results return non-zero when no
  result exists, state the empty condition explicitly, and delete nothing.
- Adding explicit scheduler cancellation remains a separate feature requiring backend
  contracts and tests.

Store deferred policies in this design document. They guide future issues but create
no compatibility promise until implemented and documented in user-facing pages.

## Files and Ownership

- `wiki/fluka-submit.md`: user-facing description of current submission and collection
  guarantees.
- `src/fluka/isotope_inventory/config.py`: canonical isotope pair type at configuration
  boundary.
- `src/fluka/isotope_inventory/analysis.py`: typed analysis orchestration.
- `src/fluka/isotope_inventory/reader.py`: typed detector-data extraction and missing
  data failure.
- `src/fluka/isotope_inventory/excel.py`: typed workbook input.
- `src/fluka/isotope_inventory/resnuclei.py`: binary stream and statistics record
  typing.
- `pyproject.toml`: mypy target expansion and exclusion removal.
- `tests/isotope_inventory/`: regression tests for any newly explicit failure path.

No production queue or grid code changes belong in this completion pass.

## Verification

Run focused isotope tests and mypy first, then repository-wide gates:

```bash
python3 -m pytest tests/isotope_inventory -q
python3 -m mypy src/fluka/isotope_inventory
python3 -m ruff check src tests
python3 -m ruff format --check src tests
python3 -m mypy
python3 -m pytest --cov=fluka --cov-report=term-missing
python3 -m build
```

Confirm generated distributions contain required package assets using existing wheel
tests. Finish with `git status --short --branch` and
`git rev-list --left-right --count origin/main...main`.

## Publication Boundary

Publishing is a separate, explicit step after all verification passes. This work does
not push, create a remote branch, or open a pull request. At handoff, choose either:

- direct push of clean local `main`; or
- publication through a feature branch and pull request.

## Non-Goals

- No implementation of deferred grid, scheduler, cancellation, or empty-result
  policies.
- No scheduler backend additions or interface redesign.
- No output-format or CLI-schema changes.
- No new runtime dependencies.
- No license selection or license metadata.
- No push or pull request during implementation.
