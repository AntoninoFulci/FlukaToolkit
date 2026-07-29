# FlukaToolkit

FlukaToolkit is a toolkit for FLUKA Monte Carlo workflows — grid generation,
batch submission, isotope/activation inventory, and ROOT-format output — in
one installable package. It merges what used to be four separate projects
(`fluka-grid-search`, `FlukaQueueSub`, `FlukaIsotopeAnalysis`, and
`FlukaROOTOutput`) into a single `fluka` Python package plus packaged compiler
build tree, all driven from one configuration file per simulation.

## Install

Requires Python ≥ 3.10 and FLUKA (`fluka-config` / `rfluka` on `PATH`).

```bash
pip install -e .
```

This registers six console commands and makes every component importable as
a library (`from fluka.isotope_inventory import analysis`, etc.).

## One config, many tools

A single `sim.yaml` describes an entire simulation: a shared **`general`**
section plus one section per tool. Every tool merges `general` with its own
section — `general` provides the defaults, the tool section overrides — and
ignores everything else, so the whole run lives in one file:

```yaml
general:
  input: example.inp        # FLUKA .inp (one #define per grid key + RANDOMIZ/START)
  backend: ts                # ts | slurm | lsf | condor  (used by grid + submit)
  output: results/           # per-combo run dirs are created under here
  primaries: 1000

submit:                      # batch resources — used by submit AND grid
  njobs: 2
  max_parallel: 10
  mem: "1500"
  time: "1-00:00:00"

grid:                        # fluka-grid reads this (+ submit, for resources)
  parameters:
    irrtime: [86400, 172800]
    mat: [COPPER, TUNGSTEN]
  runs_per_combo: 2

custom_exe:                  # fluka-compile reads this (optional section)
  rntuple: false
  # packaged usrini/usrout/mgdraw defaults are used when routines is omitted

analysis:                    # fluka-analysis reads this
  run: c1/run_0001            # relative to general.output
  units: [21, 22]
  volume: 1000
  isotopes:
    31: 70
  output: isotopes.xlsx
```

A top-level `general:` section is always required — there is no standalone,
`general`-less config in schema v2. See [sim.yaml reference](sim-yaml) for
the full annotated example.

## Commands

| Command | Does | Page |
|---------|------|------|
| `fluka-grid <cfg>` | Expand a parameter grid over a `.inp` template, patch unique seeds, submit each run | [fluka-grid](fluka-grid) |
| `fluka-submit <cfg>` | Submit one FLUKA input to a batch backend. `--grid` generates and submits every grid run | [fluka-submit](fluka-submit) |
| `fluka-analysis <cfg>` | Post-process `RESNUCLEi` output → per-isotope activity (Bq) / mass (µg) → Excel | [fluka-analysis](fluka-analysis) |
| `fluka-compile <cfg>` | Compile a custom FLUKA ROOT-output executable from packaged compiler assets | [fluka-compile](fluka-compile) |
| `fluka-run <cfg>` | Orchestrate a whole simulation from one file: bare invocation compiles (if `custom_exe:` is set) then grid/submit; `analyze` collects+analyzes | [fluka-run](fluka-run) |
| `fluka-status <cfg>` | Report per-job state (PENDING/RUNNING/DONE/FAIL), `--watch`, `--collect` | [fluka-status](fluka-status) |

## Typical flow

```bash
# 1. compile (if the config has a custom_exe: section), generate the grid,
#    and submit it to the farm — all in one call
fluka-run sim.yaml

# ...or drive the same steps by hand:
fluka-compile sim.yaml              # (once) compile the ROOT-output executable
fluka-submit --grid sim.yaml        # generate and submit every grid run

# 2. ...wait for the farm jobs to finish (FlukaToolkit does not poll)...

# 3. collect results and run the isotope inventory
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
src/fluka/root_output/  # packaged C++/ROOT FLUKA compiler assets
```

The original per-project READMEs are preserved under `docs/legacy/` in the
repository for historical reference; this wiki is the maintained
documentation going forward.

## See also

- [fluka-grid](fluka-grid)
- [fluka-submit](fluka-submit)
- [fluka-analysis](fluka-analysis)
- [fluka-compile](fluka-compile)
- [fluka-run](fluka-run)
- [fluka-status](fluka-status)
- [sim.yaml reference](sim-yaml)
