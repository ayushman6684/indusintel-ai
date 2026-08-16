"""
Category-aware specification schema (Section 4 of the spec).

The base ProductIntelligenceSchema (see app/schemas.py) covers fields common
to most industrial products. Different categories care about different
*additional* technical specifications — a pump cares about flow_rate and
pressure_rating, a bearing cares about load ratings and bore diameter, a
sensor cares about accuracy and output signal type.

This registry doesn't change the schema shape (technical_specifications is
already a free-form dict on the base schema) — it tells the Structuring
Agent which extra fields to specifically look for per category, and lets
the UI/validation logic know which fields are "expected" for a given
category so it can flag them as missing rather than just unknown.
"""

CATEGORIES = [
    "Industrial Pumps",
    "Motors",
    "Valves",
    "Sensors",
    "Bearings",
    "Compressors",
    "Other",
]

# Extra technical_specifications keys the Structuring Agent should actively
# look for, per category. Kept intentionally small/readable — this is meant
# to steer extraction, not be an exhaustive industrial ontology.
CATEGORY_SPEC_FIELDS: dict[str, list[str]] = {
    "Industrial Pumps": [
        "flow_rate",
        "pressure_rating",
        "head",
        "impeller_material",
        "suction_size",
        "discharge_size",
        "efficiency",
    ],
    "Motors": [
        "voltage",
        "power",
        "rpm",
        "frame_size",
        "efficiency_class",
        "insulation_class",
        "duty_cycle",
    ],
    "Valves": [
        "valve_type",
        "pressure_rating",
        "flow_coefficient_cv",
        "actuation_type",
        "end_connection",
        "seat_material",
    ],
    "Sensors": [
        "measurement_range",
        "accuracy",
        "output_signal",
        "response_time",
        "voltage",
        "ingress_protection",
    ],
    "Bearings": [
        "bore_diameter",
        "outer_diameter",
        "width",
        "load_rating_dynamic",
        "load_rating_static",
        "max_rpm",
        "seal_type",
    ],
    "Compressors": [
        "flow_rate",
        "pressure_rating",
        "power",
        "compressor_type",
        "tank_capacity",
        "noise_level",
    ],
    "Other": [],
}


def expected_fields_for_category(category: str) -> list[str]:
    """Return the category-specific fields the pipeline expects, falling
    back to an empty list for unrecognized categories rather than raising —
    the schema must stay extensible to categories we haven't hardcoded."""
    return CATEGORY_SPEC_FIELDS.get(category, [])
