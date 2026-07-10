# FlukaToolkit

A toolkit for FLUKA Monte Carlo workflows — grid generation, batch
submission, isotope/activation inventory, and ROOT-format output — in one
installable package.

## Install

Requires Python ≥ 3.10 and FLUKA (`fluka-config` / `rfluka` on `PATH`).

```bash
pip install -e .
```

This registers five console commands and makes every component importable as a
library (`from fluka.isotope_inventory import analysis`, etc.).

## Commands

| Command | Does | Backed by |
|---------|------|-----------|
| `fluka-grid <cfg>` | Expand a parameter grid over a `.inp` template, patch unique seeds, submit each run | `fluka.grid` |
| `fluka-submit <cfg>` | Submit FLUKA inputs to a batch backend (SLURM / LSF / HTCondor / Task-Spooler). `--grid` first generates the grid | `fluka.queue` |
| `fluka-analysis <cfg>` | Post-process `RESNUCLEi` output → per-isotope activity (Bq) / mass (µg) → Excel | `fluka.isotope_inventory` |
| `fluka-root <cfg>` | Compile FLUKA ROOT-output routines via `src/root_output/Makefile` | `src/root_output/` |
| `fluka-run <phase> <cfg>` | Orchestrate a whole simulation from one file: `submit` (grid+submit) / `analyze` (collect+analysis) | `fluka.run` |
| `fluka-status <cfg>` | Report per-job state (PENDING/RUNNING/DONE/FAIL), `--watch`, `--collect` | `fluka.cli.status` |

## One config, many tools

A single `sim.yaml` describes an entire simulation. Each tool reads **only its
own section** and ignores the rest, so the whole run lives in one file:

```yaml
grid:      { ... }   # fluka-grid   reads this
submit:    { ... }   # fluka-submit reads this
analysis:  { ... }   # fluka-analysis reads this
root:      { ... }   # fluka-root   reads this
```

See [`examples/sim.yaml`](examples/sim.yaml) for a fully annotated example.
Every tool also still accepts its own **standalone** config file (back-compat),
so existing single-tool configs keep working.

### Typical flow

```bash
# 1. (once) compile the ROOT-output routines if your template uses them
fluka-root sim.yaml

# 2. generate the grid and submit it to the farm
fluka-submit --grid sim.yaml        # or: fluka-run submit sim.yaml

# 3. ...wait for the farm jobs to finish (FlukaToolkit does not poll)...

# 4. collect results and run the isotope inventory
fluka-run analyze sim.yaml          # or: fluka-analysis sim.yaml
```

> **Async by design:** `fluka-run` is a thin sequencer — it does not track job
> completion across backends. You wait for the farm, then run the analyze
> phase yourself.

## Documentation

Full per-utility docs live in the [project wiki](https://github.com/AntoninoFulci/FlukaToolkit/wiki):

- [fluka-grid](https://github.com/AntoninoFulci/FlukaToolkit/wiki/fluka-grid) — parameter-grid generation + seeding
- [fluka-submit](https://github.com/AntoninoFulci/FlukaToolkit/wiki/fluka-submit) — batch submission backends
- [fluka-analysis](https://github.com/AntoninoFulci/FlukaToolkit/wiki/fluka-analysis) — RESNUCLEi → isotope activity/mass → Excel
- [fluka-root](https://github.com/AntoninoFulci/FlukaToolkit/wiki/fluka-root) — compile FLUKA ROOT-output routines
- [fluka-run](https://github.com/AntoninoFulci/FlukaToolkit/wiki/fluka-run) — one-file orchestrator
- [fluka-status](https://github.com/AntoninoFulci/FlukaToolkit/wiki/fluka-status) — job monitoring + auto-collect
- [sim.yaml reference](https://github.com/AntoninoFulci/FlukaToolkit/wiki/sim-yaml) — full config reference

## Layout

```
src/
  fluka/
    grid/                # parameter-grid generation + seeding
    queue/               # batch submission backends + result collection
    isotope_inventory/   # RESNUCLEi → isotope activity/mass → Excel
    cli/                 # console-script entrypoints
    run/                 # sim.yaml loader + fluka-run orchestrator
  root_output/           # C++/ROOT FLUKA routines (compiled, not pip-packaged)
```

The original per-project READMEs are preserved under
[`docs/legacy/`](docs/legacy/).

## Development

```bash
pip install -e ".[dev]"
pytest                 # runs the merged grid + queue + isotope_inventory + run suites
```

The `htcondor` Python bindings are an optional extra: `pip install -e ".[htcondor]"`.
