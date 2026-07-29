# fluka-analysis

`fluka-analysis <cfg>` post-processes FLUKA `RESNUCLEi` output for a single
simulation directory: it reads raw `RESNUCLEi` binaries (`fort.21`, …)
and/or already-processed `.rnc` files (e.g. from FLAIR), computes
per-isotope activity (Bq), error, and mass (µg), and writes the result to an
Excel workbook. It is backed by the `fluka.isotope_inventory` package
(`src/fluka/isotope_inventory/`), the successor to the standalone
FlukaIsotopeAnalysis project.

`<cfg>` is a `sim.yaml` with a top-level `general:` section plus an
`analysis:` section — a standalone `analysis.yaml` works too, as long as it
still carries its own `general:` section (the top-level `general` section
is always required — see [sim.yaml reference](sim-yaml)). Unlike the other
tools, `analysis` does **not** inherit `general.output` directly as its own
`output` field — `general.output` is the shared results directory and
`analysis.run` is resolved relative to it, while `analysis.output` is the
Excel filename (the loader keeps the two from colliding).

## The `general:` + `analysis:` config sections

From `examples/simple/example.yaml`:

```yaml
general:
  output: results/          # shared results directory

analysis:
  run: c1/run_0001          # relative to general.output -> results/c1/run_0001
  units: [21, 22]
  volume: 1000               # cm³
  isotopes:                  # Z: A
    31: 70
    30: 69
  output: isotopes.xlsx
```

Field reference (`fluka.isotope_inventory.config.AnalysisConfig`):

| Section | Field | Required | Meaning |
|---------|-------|----------|---------|
| `general` | `output` | yes | Shared results directory; `analysis.run` is resolved relative to it. |
| `analysis` | `run` | yes | Run subdirectory, relative to `general.output` (e.g. `c1/run_0001` → `results/c1/run_0001`). Must exist. |
| `analysis` | `units` | yes | List of FLUKA RESNUCLEi unit numbers to read (e.g. `[21, 22, 23]`). |
| `analysis` | `volume` | yes | Scoring volume in cm³, used to convert to activity/mass. |
| `analysis` | `isotopes` | yes | Map of atomic number `Z` to mass number(s) `A` to report — either a single `A` (`31: 70`) or a list of masses for the same `Z` (`31: [69, 70]`). |
| `analysis` | `executable` | no (default `usrsuw`) | FLUKA merge tool used to convert raw units into `.rnc` files. |
| `analysis` | `output` | no (default `isotopes.xlsx`) | Excel filename written into the run directory. |

For each `units` entry: an existing `*<unit>*.rnc` file is used as-is;
otherwise the raw `*.<unit>`/`fort.<unit>` files are processed with
`executable` into `merged_<unit>.rnc`. The output workbook has an
`Activity` sheet with one row per cooling time.

## Running it

```bash
# standalone analysis config (still needs its own general: section)
fluka-analysis analysis.yaml

# or driving a full sim.yaml (reads general + only the analysis: section)
fluka-analysis sim.yaml
```

## Library use

The underlying modules are importable directly:

```python
from fluka.isotope_inventory.reader import read_resnuclei_file
from fluka.isotope_inventory.physics import isotope_symbol, half_life
```

See `docs/legacy/isotope-README.md` for the original FlukaIsotopeAnalysis
documentation.
