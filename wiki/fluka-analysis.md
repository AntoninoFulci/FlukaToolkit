# fluka-analysis

`fluka-analysis <cfg>` post-processes FLUKA `RESNUCLEi` output for a single
simulation directory: it reads raw `RESNUCLEi` binaries (`fort.21`, …)
and/or already-processed `.rnc` files (e.g. from FLAIR), computes
per-isotope activity (Bq), error, and mass (µg), and writes the result to an
Excel workbook. It is backed by the `fluka.isotope_inventory` package
(`src/fluka/isotope_inventory/`), the successor to the standalone
FlukaIsotopeAnalysis project.

`<cfg>` may be a standalone `analysis.yaml` or a multi-section `sim.yaml`
containing an `analysis:` section — see [sim.yaml reference](sim-yaml).

## The `analysis:` config section

From `examples/sim.yaml` (lines 31-38):

```yaml
analysis:
  directory: results/c1/run_0001
  units: [21, 22, 23]
  volume: 1000                 # cm³
  isotopes:                    # Z: A
    31: 70
    30: 69
  output: isotopes.xlsx
```

Field reference (`fluka.isotope_inventory.config.AnalysisConfig`):

| Field | Required | Meaning |
|-------|----------|---------|
| `directory` | yes | Path to the simulation directory containing `fort.<unit>`/`*.rnc` output. Must exist. |
| `units` | yes | List of FLUKA RESNUCLEi unit numbers to read (e.g. `[21, 22, 23]`). |
| `volume` | yes | Scoring volume in cm³, used to convert to activity/mass. |
| `isotopes` | yes | Map of atomic number `Z` to mass number(s) `A` to report — either a single `A` (`31: 70`) or a list of masses for the same `Z` (`31: [69, 70]`). |
| `executable` | no (default `usrsuw`) | FLUKA merge tool used to convert raw units into `.rnc` files. |
| `output` | no (default `isotopes.xlsx`) | Excel filename written into `directory`. |

For each `units` entry: an existing `*<unit>*.rnc` file is used as-is;
otherwise the raw `*.<unit>`/`fort.<unit>` files are processed with
`executable` into `merged_<unit>.rnc`. The output workbook has an
`Activity` sheet with one row per cooling time.

## Running it

```bash
# standalone analysis config
fluka-analysis analysis.yaml

# or driving a multi-section sim.yaml (reads only the analysis: section)
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
