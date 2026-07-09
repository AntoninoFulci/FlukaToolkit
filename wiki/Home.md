# FlukaToolkit

FlukaToolkit is a toolkit for FLUKA Monte Carlo workflows — grid generation,
batch submission, isotope/activation inventory, and ROOT-format output — in
one installable package. It merges what used to be four separate projects
(`fluka-grid-search`, `FlukaQueueSub`, `FlukaIsotopeAnalysis`, and
`FlukaROOTOutput`) into a single `fluka` Python package plus a `root_output/`
build tree, all driven from one configuration file per simulation.

## Install

Requires Python ≥ 3.10 and FLUKA (`fluka-config` / `rfluka` on `PATH`).

```bash
pip install -e .
```

This registers five console commands and makes every component importable as
a library (`from fluka.isotope_inventory import analysis`, etc.).

## One config, many tools

A single `sim.yaml` describes an entire simulation. Each tool reads **only
its own section** and ignores the rest, so the whole run lives in one file:

```yaml
grid:      { ... }   # fluka-grid   reads this
submit:    { ... }   # fluka-submit reads this
analysis:  { ... }   # fluka-analysis reads this
root:      { ... }   # fluka-root   reads this
```

Every tool also still accepts its own **standalone** config file
(back-compat), so existing single-tool configs keep working. See
[sim.yaml reference](sim-yaml) for the full annotated example.

## Commands

| Command | Does | Page |
|---------|------|------|
| `fluka-grid <cfg>` | Expand a parameter grid over a `.inp` template, patch unique seeds, submit each run | [fluka-grid](fluka-grid) |
| `fluka-submit <cfg>` | Submit FLUKA inputs to a batch backend (SLURM / LSF / HTCondor / Task-Spooler). `--grid` first generates the grid | [fluka-submit](fluka-submit) |
| `fluka-analysis <cfg>` | Post-process `RESNUCLEi` output → per-isotope activity (Bq) / mass (µg) → Excel | [fluka-analysis](fluka-analysis) |
| `fluka-root <cfg>` | Compile FLUKA ROOT-output routines via `src/root_output/Makefile` | [fluka-root](fluka-root) |
| `fluka-run <phase> <cfg>` | Orchestrate a whole simulation from one file: `submit` (grid+submit) / `analyze` (collect+analysis) | [fluka-run](fluka-run) |

## Typical flow

```bash
# 1. (once) compile the ROOT-output routines if your template uses them
fluka-root sim.yaml

# 2. generate the grid and submit it to the farm
fluka-submit --grid sim.yaml        # or: fluka-run submit sim.yaml

# 3. ...wait for the farm jobs to finish (FlukaToolkit does not poll)...

# 4. collect results and run the isotope inventory
fluka-run analyze sim.yaml          # or: fluka-analysis sim.yaml
```

> **Async by design:** `fluka-run` is a thin sequencer — it does not track
> job completion across backends. You wait for the farm, then run the
> analyze phase yourself.

## Layout

```
src/fluka/
  grid/                # parameter-grid generation + seeding
  queue/               # batch submission backends + result collection
  isotope_inventory/   # RESNUCLEi → isotope activity/mass → Excel
  cli/                 # console-script entrypoints
  run/                 # sim.yaml loader + fluka-run orchestrator
src/root_output/        # C++/ROOT FLUKA routines (compiled, not pip-packaged)
```

The original per-project READMEs are preserved under `docs/legacy/` in the
repository for historical reference; this wiki is the maintained
documentation going forward.

## See also

- [fluka-grid](fluka-grid)
- [fluka-submit](fluka-submit)
- [fluka-analysis](fluka-analysis)
- [fluka-root](fluka-root)
- [fluka-run](fluka-run)
- [sim.yaml reference](sim-yaml)
