# fluka-run

`fluka-run <cfg>` is the whole-simulation orchestrator: a thin sequencer,
backed by `src/fluka/run/orchestrator.py`, that runs the other tools in the
right order from a single `sim.yaml`. It has two entry points: a bare,
one-shot invocation that launches a simulation, and an `analyze` subcommand
that collects and post-processes the results afterward.

```bash
fluka-run sim.yaml
fluka-run analyze sim.yaml
```

There is no `submit` subcommand — `fluka-run sim.yaml` (bare) is the launch
path; see below for exactly what it does.

## Bare `fluka-run <cfg>` (compile + grid/submit)

```python
def launch(sim_path) -> None:
    sim = Path(sim_path)
    data = load_sim(sim)
    exe = None
    if "custom_exe" in data:
        recompile = bool((data.get("general") or {}).get("recompile", False))
        exe = compile_exe(resolve(sim, "custom_exe"), force=recompile)
    grid = data.get("grid") or {}
    if grid.get("parameters"):
        _do_grid(sim, exe)
    else:
        _do_submit(sim, exe)
```

`fluka-run sim.yaml` does the following, in order:

1. **Compile, if `custom_exe:` is present.** If the config has a top-level
   `custom_exe:` section, `fluka-run` compiles it first (equivalent to
   [`fluka-compile sim.yaml`](fluka-compile)), reusing the cached executable
   at `exe_path` unless `general.recompile: true` forces a rebuild. If
   `custom_exe:` is absent, this step is skipped entirely — no executable is
   compiled, and `general.custom_executable` (if set by hand) is left as-is.
2. **Grid or submit, based on `grid.parameters`.** If the config has a
   `grid:` section with a non-empty `parameters:` map, `fluka-run` runs the
   grid phase (equivalent to [`fluka-grid sim.yaml`](fluka-grid), which
   generates the parameter grid **and** submits it). Otherwise it runs the
   plain submit phase (equivalent to [`fluka-submit sim.yaml`](fluka-submit)).
   Either way, if a `custom_exe:` section was compiled in step 1, the
   resulting executable path is passed straight through — as
   `FlukaConfig.custom_executable` for the grid path, or `Namespace.custom_exe`
   for the submit path — so the job is launched with `rfluka -e <exe_path>`
   without you having to also set `general.custom_executable` by hand.

So a single `fluka-run sim.yaml` call covers: compile (if needed) → grid
generation + submission, or plain submission — whichever the config calls
for.

## `analyze` subcommand (collect + analysis)

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
`fluka-run sim.yaml`, the jobs are handed off to SLURM/LSF/HTCondor/`ts` and
run independently on the farm; `fluka-run` returns immediately. `fluka-run`
itself has no built-in wait loop or status check — for that, use
[`fluka-status`](fluka-status): it reports each job's state
(PENDING/RUNNING/DONE/FAIL) and, with `--watch`, polls until every job is
terminal. `fluka-status --collect` combines the two: wait for all jobs to
finish, then run the same collect+analyze step as `fluka-run analyze`.

```bash
# 1. compile (if needed), generate the grid (if configured), and submit it
fluka-run sim.yaml

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
| `fluka-run sim.yaml`, with a `custom_exe:` section | `fluka-compile sim.yaml`, then `fluka-grid sim.yaml` (if `grid.parameters` set) or `fluka-submit sim.yaml`, with the compiled executable passed through as `-e <exe_path>` |
| `fluka-run sim.yaml`, no `custom_exe:`, with `grid.parameters` | `fluka-grid sim.yaml` (generates the grid **and** submits) |
| `fluka-run sim.yaml`, no `custom_exe:`, no `grid.parameters` | `fluka-submit sim.yaml` |
| `fluka-run analyze sim.yaml` | collect results, then `fluka-analysis sim.yaml` |

`fluka-run` always operates on a multi-section `sim.yaml` — see
[sim.yaml reference](sim-yaml) — and hands each phase's own section to the
corresponding tool.
