"""
Deterministic normalization rules (Stage 2 — Normalize).

Kept outside the LLM per the spec's rule: "Keep deterministic validation
rules outside the LLM wherever possible." Unit/value normalization is
exactly this kind of rule — it doesn't need judgment, just consistent
string handling, so it's cheaper and more reliable as plain code than as
an AI call.

`10 bar` and `10 Bar` should become the same normalized representation —
this module is what makes that happen.
"""
from __future__ import annotations

import re

# Canonical unit spellings, keyed by lowercased variant.
UNIT_ALIASES = {
    "bar": "bar",
    "bars": "bar",
    "kg": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
    "l/min": "L/min",
    "lpm": "L/min",
    "liters/min": "L/min",
    "litres/min": "L/min",
    "kw": "kW",
    "kilowatt": "kW",
    "kilowatts": "kW",
    "hp": "hp",
    "v": "V",
    "volt": "V",
    "volts": "V",
    "c": "°C",
    "°c": "°C",
    "celsius": "°C",
    "f": "°F",
    "°f": "°F",
    "fahrenheit": "°F",
    "psi": "psi",
    "rpm": "RPM",
}

# Matches a leading numeric value (int/float, optional sign) followed by an
# optional space and a unit token, e.g. "10 bar", "10bar", "-10.5 C".
VALUE_UNIT_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z/°]+)?\s*$")


def normalize_value(raw: str | None) -> tuple[str | None, str | None]:
    """Normalize a raw spec value string.

    Returns (normalized_value, unit). If the value doesn't look like a
    number + unit, normalized_value is just the trimmed/lowercased-unit-safe
    original string and unit is None.
    """
    if raw is None:
        return None, None

    text = str(raw).strip()
    if not text:
        return None, None

    match = VALUE_UNIT_RE.match(text)
    if not match:
        return text, None

    number, unit_raw = match.groups()
    if not unit_raw:
        return number, None

    unit_key = unit_raw.strip().lower()
    canonical_unit = UNIT_ALIASES.get(unit_key, unit_raw.strip())
    return f"{number} {canonical_unit}", canonical_unit


def normalize_category(raw: str | None, known_categories: list[str]) -> str:
    """Snap a free-text category to the closest known category (case-
    insensitive exact match), otherwise return the original text trimmed so
    new categories aren't silently dropped — the schema must stay
    extensible per the spec."""
    if not raw:
        return "Other"
    text = raw.strip()
    for known in known_categories:
        if text.lower() == known.lower():
            return known
    return text


def normalize_field_name(raw: str) -> str:
    """Normalize a technical_specifications key to snake_case for
    consistent storage/lookup (e.g. 'Pressure Rating' -> 'pressure_rating')."""
    text = raw.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")
