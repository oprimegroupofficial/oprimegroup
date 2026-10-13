"""Minimal ORTEC .Spc writer (same layout the reader parses) - used to build test files."""

from __future__ import annotations

import struct
from datetime import datetime

import numpy as np

RECORD = 128
HEADER_RECORDS = 25


def spc_bytes(counts, live_time: float, real_time: float, name: str = "TEST",
              start: datetime | None = None, cal=(0.0, 0.5, 0.0), description: str = "TEST DSPEC-50") -> bytes:
    counts = np.asarray(counts, dtype="<i4")
    n = counts.size
    data_records = -(-4 * n // RECORD)
    total = HEADER_RECORDS + data_records
    buf = bytearray(total * RECORD)
    struct.pack_into("<H", buf, 54, total)
    struct.pack_into("<H", buf, 60, HEADER_RECORDS + 1)
    struct.pack_into("<H", buf, 62, RECORD)
    struct.pack_into("<i", buf, 64, n)
    struct.pack_into("<f", buf, 90, real_time)
    struct.pack_into("<f", buf, 94, live_time)
    start = start or datetime(2026, 10, 13, 8, 0, 0)
    mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][start.month - 1]
    stamp = f"{start.day:02d}-{mon}-{start.year % 100:02d}{1 if start.year >= 2000 else 0}  {start:%H:%M:%S}"
    buf[256:256 + 16] = name[:12].upper().ljust(16).encode("latin-1")
    buf[272:272 + len(stamp)] = stamp.encode("latin-1")
    buf[512:512 + len(description)] = description.encode("latin-1")
    long = (name + ".Spc").encode("latin-1")
    buf[768:768 + len(long)] = long
    struct.pack_into("<3f", buf, 660, *cal)
    struct.pack_into("<2H", buf, 2816, 0xFFFE, 0xFFFF)
    off = HEADER_RECORDS * RECORD
    buf[off:off + 4 * n] = counts.tobytes()
    return bytes(buf)
