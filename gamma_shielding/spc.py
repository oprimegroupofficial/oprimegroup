"""Reader for ORTEC/MAESTRO ``.Spc`` binary spectrum files (DSPEC family).

The format is organised in 128-byte records.  Layout verified on DSPEC-50
files (4096 channels, int32 counts):

========  ======  =====================================================
offset    type    content
========  ======  =====================================================
54        u16     total number of records in the file
60        u16     first record of the spectrum data (1-based)
62        u16     record size in bytes (128)
64        i32     number of channels
90        f32     real time [s]
94        f32     live time [s]
256       text    8.3 file name, acquisition date, time, live/real time
512       text    description (PC name, spectrometer, serial number)
660       3xf32   energy calibration c0, c1, c2 (E = c0 + c1*ch + c2*ch^2)
768       text    original (long) file name
2816      u16[]   0xFFFE marker, ROI channel pairs stored by MAESTRO, 0xFFFF terminator
2432      text    "Detector State Of Health" block (voltages, HV, temp)
========  ======  =====================================================
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

RECORD = 128


class SpcFormatError(ValueError):
    """Raised when a file does not look like an ORTEC ``.Spc`` spectrum."""


@dataclass
class Spectrum:
    name: str
    counts: np.ndarray
    live_time: float
    real_time: float
    start: datetime | None = None
    header_calibration: tuple[float, float, float] = (0.0, 1.0, 0.0)
    header_rois: list[tuple[int, int]] = field(default_factory=list)
    description: str = ""
    source_file: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def n_channels(self) -> int:
        return int(self.counts.size)

    @property
    def total_counts(self) -> int:
        return int(self.counts.sum())

    @property
    def dead_time_fraction(self) -> float:
        if self.real_time <= 0:
            return float("nan")
        return 1.0 - self.live_time / self.real_time

    def header_energy(self, ch):
        c0, c1, c2 = self.header_calibration
        ch = np.asarray(ch, dtype=float)
        return c0 + c1 * ch + c2 * ch**2


def _text(buf: bytes, start: int, length: int) -> str:
    return buf[start:start + length].decode("latin-1", errors="replace").replace("\x00", " ").strip()


_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


def _parse_datetime(date_txt: str, time_txt: str, century_digit: str) -> datetime | None:
    """``13-Oct-26`` + century digit (``1`` = 2000s, ``0`` = 1900s) + ``14:56:57``."""
    m = re.match(r"(\d{1,2})-([A-Za-z]{3})-(\d{2})", date_txt)
    t = re.match(r"(\d{1,2}):(\d{2}):(\d{2})", time_txt)
    if not m or not t or m.group(2).title() not in _MONTHS:
        return None
    year = int(m.group(3)) + (2000 if century_digit == "1" else 1900)
    try:
        return datetime(year, _MONTHS[m.group(2).title()], int(m.group(1)),
                        int(t.group(1)), int(t.group(2)), int(t.group(3)))
    except ValueError:
        return None


def read_spc(path: str | Path) -> Spectrum:
    path = Path(path)
    buf = path.read_bytes()
    if len(buf) < 4 * RECORD:
        raise SpcFormatError(f"{path.name}: file too small for an .Spc spectrum")

    rec_size = struct.unpack_from("<H", buf, 62)[0]
    first_rec = struct.unpack_from("<H", buf, 60)[0]
    n_ch = struct.unpack_from("<i", buf, 64)[0]
    if rec_size != RECORD or not (16 <= n_ch <= 65536) or first_rec < 2:
        raise SpcFormatError(
            f"{path.name}: unexpected header (record size {rec_size}, channels {n_ch}, "
            f"data record {first_rec}); is this an ORTEC .Spc file?")
    offset = (first_rec - 1) * RECORD
    if offset + 4 * n_ch > len(buf):
        raise SpcFormatError(f"{path.name}: file is shorter than the declared {n_ch} channels")

    counts = np.frombuffer(buf, dtype="<i4", count=n_ch, offset=offset).astype(np.int64)
    if counts.min() < 0:
        raise SpcFormatError(f"{path.name}: negative counts found - wrong data offset?")

    real_time = struct.unpack_from("<f", buf, 90)[0]
    live_time = struct.unpack_from("<f", buf, 94)[0]
    c0, c1, c2 = struct.unpack_from("<3f", buf, 660)

    # acquisition stamp (record 3): name(16) date(9) century(1) 2 blanks time(8)
    date_txt, century, time_txt = _text(buf, 272, 9), _text(buf, 281, 1), _text(buf, 284, 8)
    start = _parse_datetime(date_txt, time_txt, century)

    rois: list[tuple[int, int]] = []
    words = struct.unpack_from("<64H", buf, 2816)
    vals = []
    for w in words[1:] if words[0] == 0xFFFE else words:   # 0xFFFE = list marker, 0xFFFF = end
        if w == 0xFFFF:
            break
        vals.append(w)
    for i in range(0, len(vals) - 1, 2):
        rois.append((vals[i], vals[i + 1]))

    health = _text(buf, 2432, 256)
    long_name = _text(buf, 768, 40)
    stem = Path(long_name).stem if long_name else path.stem
    meta = {
        "short_name": _text(buf, 256, 16),
        "long_name": long_name,
        "detector_health": re.sub(r"\s+", " ", health),
        "records": struct.unpack_from("<H", buf, 54)[0],
    }
    return Spectrum(
        name=stem, counts=counts, live_time=float(live_time), real_time=float(real_time),
        start=start, header_calibration=(c0, c1, c2), header_rois=rois,
        description=_text(buf, 512, 80), source_file=str(path), meta=meta)
