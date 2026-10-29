"""Clothing size heuristics derived from predicted measurements."""

from __future__ import annotations

from typing import Any

MEASUREMENT_INDICES: dict[str, int] = {
    "ankle": 0,
    "arm-length": 1,
    "bicep": 2,
    "calf": 3,
    "chest": 4,
    "forearm": 5,
    "height": 6,
    "hip": 7,
    "leg-length": 8,
    "shoulder-breadth": 9,
    "shoulder-to-crotch": 10,
    "thigh": 11,
    "waist": 12,
    "wrist": 13,
}

UPPER_BODY_KEYS = (
    "chest",
    "shoulder-breadth",
    "bicep",
    "forearm",
    "wrist",
    "arm-length",
    "shoulder-to-crotch",
)

LOWER_BODY_KEYS = (
    "waist",
    "hip",
    "thigh",
    "calf",
    "ankle",
    "leg-length",
)

SIZE_CHARTS: dict[str, dict[str, list[tuple[float, float, Any]]]] = {
    "male": {
        "tshirt": [
            (97, 42, "S"),
            (104, 45, "M"),
            (112, 48, "L"),
            (120, 51, "XL"),
            (128, 54, "XXL"),
            (136, 57, "XXXL"),
        ],
        "pants": [
            (76, 102, 30),
            (81, 107, 32),
            (86, 112, 34),
            (91, 117, 36),
            (97, 122, 38),
            (102, 127, 40),
            (107, 132, 42),
        ],
    },
    "female": {
        "tshirt": [
            (89, 38, "S"),
            (96, 41, "M"),
            (104, 44, "L"),
            (112, 47, "XL"),
            (120, 50, "XXL"),
            (128, 53, "XXXL"),
        ],
        "pants": [
            (66, 92, 26),
            (71, 97, 28),
            (76, 102, 30),
            (81, 107, 32),
            (86, 112, 34),
            (91, 117, 36),
            (97, 122, 38),
        ],
    },
}


def gender_label(gender: int) -> str:
    return "male" if gender == 0 else "female"


def measurements_from_vector(prediction: list[float] | tuple[float, ...]) -> dict[str, float]:
    return {
        name: round(float(prediction[idx]), 2)
        for name, idx in MEASUREMENT_INDICES.items()
    }


def calculate_tshirt_size(gender: int, measurements: dict[str, float], weight: float) -> str:
    """Map chest and shoulder breadth onto a t-shirt size chart."""
    chart = SIZE_CHARTS[gender_label(gender)]["tshirt"]
    chest = measurements["chest"]
    shoulder_breadth = measurements["shoulder-breadth"]

    base_size = next(
        (
            size
            for max_chest, max_shoulder, size in chart
            if chest <= max_chest and shoulder_breadth <= max_shoulder
        ),
        "XXXL",
    )

    if (weight > 95 and gender == 0) or (weight > 80 and gender == 1):
        base_size = "XXL"

    if measurements["height"] > 180:
        base_size = f"Tall {base_size}"

    return base_size


def calculate_pants_size(gender: int, measurements: dict[str, float], weight: float) -> int:
    """Map waist and hip onto a numeric pants size. Weight is unused but kept for API compatibility."""
    del weight
    chart = SIZE_CHARTS[gender_label(gender)]["pants"]
    waist = measurements["waist"]
    hip = measurements["hip"]

    base_size = next(
        (
            size
            for max_waist, max_hip, size in chart
            if waist <= max_waist and hip <= max_hip
        ),
        chart[-1][2],
    )

    if measurements["height"] > 180 and gender == 0:
        if base_size < 40:
            base_size += 2

    return int(base_size)


def assemble_result(
    apparel_type: str,
    measurements: dict[str, float],
    gender: int,
    weight_kg: float,
) -> dict[str, Any]:
    """Build the API payload for a given apparel selection."""
    if apparel_type == "tshirt":
        return {
            "tshirt_size": calculate_tshirt_size(gender, measurements, weight_kg),
            "upper_body_measurements": {
                key: measurements[key] for key in UPPER_BODY_KEYS if key in measurements
            },
        }

    if apparel_type == "pants":
        return {
            "pants_size": calculate_pants_size(gender, measurements, weight_kg),
            "lower_body_measurements": {
                key: measurements[key] for key in LOWER_BODY_KEYS if key in measurements
            },
        }

    return {
        "body_measurements": measurements,
        "tshirt_size": calculate_tshirt_size(gender, measurements, weight_kg),
        "pants_size": calculate_pants_size(gender, measurements, weight_kg),
    }
