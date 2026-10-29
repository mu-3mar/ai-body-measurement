"""Load the Keras model and run a single-person measurement prediction."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import tensorflow as tf

from ai_body_measurement.config import MODEL_PATH
from ai_body_measurement.preprocessing import ImagePreprocessor
from ai_body_measurement.sizing import assemble_result, measurements_from_vector
from ai_body_measurement.validation import validate_prediction_fields

logger = logging.getLogger(__name__)


class SinglePersonPredictor:
    """Predict body measurements from front/side photos plus metadata."""

    def __init__(self, model_path: str | Path | None = None) -> None:
        path = Path(model_path) if model_path is not None else MODEL_PATH
        if not path.is_file():
            raise FileNotFoundError(
                f"Trained model not found at {path}. See README.md for how to obtain it."
            )
        self.model = tf.keras.models.load_model(path)
        self.preprocessor = ImagePreprocessor()
        logger.info("Model loaded from %s", path)

    def predict_measurements(
        self,
        front_img_path: str,
        side_img_path: str,
        gender: int,
        height_cm: float,
        weight_kg: float,
        apparel_type: str = "all",
    ) -> dict[str, Any]:
        validate_prediction_fields(gender, height_cm, weight_kg, apparel_type)

        try:
            front_arr, side_arr = self.preprocessor.process_single_person(
                front_img_path, side_img_path
            )
            meta_arr = np.array([[gender, height_cm, weight_kg]], dtype=np.float32)
            prediction = self.model.predict(
                [
                    np.expand_dims(front_arr, axis=0),
                    np.expand_dims(side_arr, axis=0),
                    meta_arr,
                ],
                verbose=0,
            )
            measurements = measurements_from_vector(prediction[0])
            return assemble_result(apparel_type, measurements, gender, weight_kg)
        except Exception:
            logger.exception("Prediction failed")
            raise
