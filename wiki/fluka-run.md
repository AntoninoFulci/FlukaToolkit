# fluka-run

`fluka-run <phase> <cfg>` is the whole-simulation orchestrator: a thin
sequencer, backed by `src/fluka/run/orchestrator.py`, that runs the other
tools in the right order from a single `sim.yaml`. It has two phases,
`submit` and `analyze`.

```bash
fluka-run submit sim.yaml
fluka-run analyze sim.yaml
```

## `submit` phase (grid + submit)

```python
def submit_phase(sim_path, *, do_grid: bool) -> None:
    sim = Path(sim_path)
    if do_grid:
        _run_grid(sim)      # fluka.cli.grid.run_sim(sim)
    _run_submit(sim)        # fluka.cli.submit.run_sim(sim)
```

By default `fluka-run submit sim.yaml` first runs the grid phase (equivalent
to [`fluka-grid sim.yaml`](fluka-grid)) and then submits
(equivalent to [`fluka-submit sim.yaml`](fluka-submit)). Pass `--no-grid` to
skip grid generation and submit an already-prepared set of inputs directly:

```bash
fluka-run submit --no-grid sim.yaml
```

This is exactly what `fluka-submit --grid sim.yaml` also does — the two
commands are equivalent entry points into the same code path.

## `analyze` phase (collect + analysis)

```python
def analyze_phase(sim_path) -> None:
    sim = Path(sim_path)
    _run_collect(sim)       # fluka.cli.submit.collect_sim(sim)
    _run_analysis(sim)      # fluka.cli.analysis.run_sim(sim)
```

`fluka-run analyze sim.yaml` first collects each submitted job's `.root`
output into a `root_files/` directory (the same behavior as
`fluka.queue.collect_results`, invoked over the current working directory),
then runs the isotope inventory over the `analysis:` section of `sim.yaml`
— equivalent to [`fluka-analysis sim.yaml`](fluka-analysis).

## Async by design

`fluka-run` does **not** poll job completion across batch backends. After
`fluka-run submit`, the jobs are handed off to SLURM/LSF/HTCondor/`ts` and
run independently on the farm; `fluka-run` returns immediately. `fluka-run`
itself has no built-in wait loop or status check — for that, use
[`fluka-status`](fluka-status): it reports each job's state
(PENDING/RUNNING/DONE/FAIL) and, with `--watch`, polls until every job is
terminal. `fluka-status --collect` combines the two: wait for all jobs to
finish, then run the same collect+analyze step as `fluka-run analyze`.

```bash
# 1. generate the grid and submit it
fluka-run submit sim.yaml

# 2. wait for the farm jobs to finish
fluka-status sim.yaml --watch

# 3. collect results and run the isotope inventory
fluka-run analyze sim.yaml
# ...or do steps 2+3 together:
fluka-status sim.yaml --collect
```

## Equivalence to standalone commands

| `fluka-run` invocation | Equivalent to |
|-------------------------|---------------|
| `fluka-run submit sim.yaml` | `fluka-grid sim.yaml` then `fluka-submit sim.yaml` (i.e. `fluka-submit --grid sim.yaml`) |
| `fluka-run submit --no-grid sim.yaml` | `fluka-submit sim.yaml` |
| `fluka-run analyze sim.yaml` | collect results, then `fluka-analysis sim.yaml` |

`fluka-run` always operates on a multi-section `sim.yaml` — see
[sim.yaml reference](sim-yaml) — and hands each phase's own section to the
corresponding tool.
