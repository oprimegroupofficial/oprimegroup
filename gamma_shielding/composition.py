"""Free-text composition input -> element weight fractions.

Accepted entries (separated by ';', new line or ', '):
    Ni 0.7497          element, weight fraction (or percent)
    Dy2O3 5            compound formula (parentheses allowed), weight %
    SiO2=60; B2O3=30   '=' or ':' also work
mode "wt": numbers are weights (fractions or %), mode "mol": numbers are mole amounts (mol %).
Decimal comma is accepted ("0,7497").  The result is normalised to sum to 1.
"""

from __future__ import annotations

import re

from .xsec import ELEMENTS

_ENTRY = re.compile(r"^\s*([A-Za-z0-9().\[\]]+?)\s*(?:[=:]|\s)\s*([0-9]+(?:\.[0-9]+)?)\s*%?\s*$")
_TOKEN = re.compile(r"([A-Z][a-z]?)|(\()|(\))|([0-9]*\.?[0-9]+)")


class CompositionError(ValueError):
    pass


def parse_formula(formula: str) -> dict[str, float]:
    """'Dy2O3' -> {'Dy': 2, 'O': 3};  'Ca(OH)2' -> {'Ca': 1, 'O': 2, 'H': 2}."""
    s = formula.replace("[", "(").replace("]", ")")
    pos, stack = 0, [{}]
    tokens = []
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            raise CompositionError(f"formül okunamadı: '{formula}'")
        tokens.append(m)
        pos = m.end()
    i = 0
    while i < len(tokens):
        m = tokens[i]
        if m.group(1):
            el = m.group(1)
            if el not in ELEMENTS:
                raise CompositionError(f"bilinmeyen element '{el}' ('{formula}')")
            n = 1.0
            if i + 1 < len(tokens) and tokens[i + 1].group(4):
                n = float(tokens[i + 1].group(4))
                i += 1
            stack[-1][el] = stack[-1].get(el, 0.0) + n
        elif m.group(2):
            stack.append({})
        elif m.group(3):
            if len(stack) < 2:
                raise CompositionError(f"parantez hatası: '{formula}'")
            inner = stack.pop()
            n = 1.0
            if i + 1 < len(tokens) and tokens[i + 1].group(4):
                n = float(tokens[i + 1].group(4))
                i += 1
            for el, c in inner.items():
                stack[-1][el] = stack[-1].get(el, 0.0) + c * n
        else:
            raise CompositionError(f"formül okunamadı: '{formula}'")
        i += 1
    if len(stack) != 1 or not stack[0]:
        raise CompositionError(f"parantez hatası: '{formula}'")
    return stack[0]


def molar_mass(counts: dict[str, float]) -> float:
    return sum(n * ELEMENTS[el][1] for el, n in counts.items())


def split_entries(text: str) -> list[str]:
    t = re.sub(r"(?<=\d),(?=\d)", ".", text.replace("\r", "\n"))     # decimal comma
    parts = re.split(r";|\n|,", t)
    return [p.strip() for p in parts if p.strip()]


def parse_composition(text: str, mode: str = "wt") -> dict[str, float]:
    """Return element weight fractions (sum = 1)."""
    if mode not in ("wt", "mol"):
        raise ValueError("mode 'wt' veya 'mol' olmalı")
    entries = split_entries(text)
    if not entries:
        raise CompositionError("bileşim boş")
    mass: dict[str, float] = {}
    for e in entries:
        m = _ENTRY.match(e)
        if not m:
            raise CompositionError(f"'{e}' okunamadı (örnek: 'Ni 0.75' veya 'Dy2O3 5')")
        counts = parse_formula(m.group(1))
        val = float(m.group(2))
        M = molar_mass(counts)
        total_mass = val if mode == "wt" else val * M
        for el, n in counts.items():
            mass[el] = mass.get(el, 0.0) + total_mass * n * ELEMENTS[el][1] / M
    tot = sum(mass.values())
    if tot <= 0:
        raise CompositionError("bileşim toplamı sıfır")
    return {el: v / tot for el, v in mass.items() if v > 0}
