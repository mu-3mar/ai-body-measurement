"""Input validation for the prediction API."""

from __future__ import annotations

import json
from dataclasses import dataclass

from ai_body_measurement.config import (
    APPAREL_TYPES,
    HEIGHT_CM_RANGE,
    WEIGHT_KG_RANGE,
)


class InputValidationError(ValueError):
    """Raised when request fields are missing or out of range."""


@dataclass(frozen=True)
class PredictionInput:
    gender: int
    height_cm: float
    weight_kg: float
    apparel_type: str


def parse_prediction_input(raw_json: str) -> PredictionInput:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise InputValidationError("Invalid JSON format in input_data") from exc

    if not isinstance(payload, dict):
        raise InputValidationError("input_data must be a JSON object")

    try:
        gender = int(payload["gender"])
        height_cm = float(payload["height_cm"])
        weight_kg = float(payload["weight_kg"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InputValidationError(
            "input_data must include numeric gender, height_cm, and weight_kg"
        ) from exc

    apparel_type = str(payload.get("apparel_type", "all")).strip().lower()
    validate_prediction_fields(gender, height_cm, weight_kg, apparel_type)
    return PredictionInput(gender, height_cm, weight_kg, apparel_type)


def validate_prediction_fields(
    gender: int,
    height_cm: float,
    weight_kg: float,
    apparel_type: str,
) -> None:
    if gender not in (0, 1):
        raise InputValidationError("Gender must be 0 (male) or 1 (female).")
    if not HEIGHT_CM_RANGE[0] <= height_cm <= HEIGHT_CM_RANGE[1]:
        raise InputValidationError("Height must be between 100-250 cm.")
    if not WEIGHT_KG_RANGE[0] <= weight_kg <= WEIGHT_KG_RANGE[1]:
        raise InputValidationError("Weight must be between 30-300 kg.")
    if apparel_type not in APPAREL_TYPES:
        raise InputValidationError("Apparel type must be 'tshirt', 'pants', or 'all'.")
