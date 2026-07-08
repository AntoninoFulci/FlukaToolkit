from __future__ import annotations
import math
from pathlib import Path
from typing import Optional

from .resnuclei import Resnuclei, unpack_array
from .physics import isotope_symbol, molar_mass, half_life, format_decay_time

_AVOGADRO = 6.02214076e23


def read_resnuclei_file(
    path: Path,
    requested_isotopes: dict[int, int],
    params: dict,
) -> Optional[dict]:
    if not path.exists():
        return None

    resn = Resnuclei(str(path))
    if not resn.detector:
        return None
    det = resn.detector[0]
    data = resn.read_data(0)
    stat = resn.read_stat(0)
    fdata = unpack_array(data)
    edata = unpack_array(stat[5]) if stat is not None else None

    zhigh = det.zhigh
    mhigh = det.mhigh
    nmzmin = det.nmzmin
    volume = det.volume
    amax = 2 * zhigh + mhigh + nmzmin

    lookup: dict[tuple[int, int], tuple[float, float]] = {}
    for a in range(1, amax + 1):
        for z in range(zhigh):
            z_actual = z + 1
            m = a - 2 * z - nmzmin - 3
            if m < 0 or m >= mhigh:
                lookup[(z_actual, a)] = (0.0, 0.0)
            else:
                pos = z + m * zhigh
                bq = fdata[pos] * volume
                bq_err = (edata[pos] * fdata[pos] * volume) if edata is not None else 0.0
                lookup[(z_actual, a)] = (bq, bq_err)

    tdecay_s = float(resn.tdecay)

    row: dict = {
        "_tdecay_s": tdecay_s,
        "CoolingTime": format_decay_time(tdecay_s),
        "Parameters": " ".join(f"{k}={v}" for k, v in params.items()),
    }
    for z, a in sorted(requested_isotopes.items()):
        sym = isotope_symbol(z, a)
        bq, bq_err = lookup.get((z, a), (0.0, 0.0))
        pct_err = (bq_err / bq * 100) if bq != 0 else 0.0
        hl = half_life(z, a)
        mm = molar_mass(z, a)
        ug = (bq * mm * hl) / (_AVOGADRO * math.log(2)) * 1e6 if (hl > 0 and mm > 0) else 0.0
        row[f"{sym} (Bq)"] = bq
        row[f"{sym} (% Error)"] = pct_err
        row[f"{sym} (µg)"] = ug
    return row
