"""Convert photos into the silhouette tensors expected by the trained model."""

from __future__ import annotations

import io
import logging
from typing import Tuple

import numpy as np
from PIL import Image
from rembg import new_session, remove

from ai_body_measurement.config import IMAGE_SIZE

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Remove the background and produce a 128x128 grayscale silhouette."""

    def __init__(self, img_size: Tuple[int, int] = IMAGE_SIZE) -> None:
        self.img_size = img_size
        self.session = new_session()
        logger.info("Image processor initialized.")

    def process_single_person(self, front_path: str, side_path: str) -> Tuple[np.ndarray, np.ndarray]:
        return self._process_image(front_path), self._process_image(side_path)

    def _process_image(self, image_path: str) -> np.ndarray:
        try:
            with open(image_path, "rb") as handle:
                img_bytes = handle.read()

            bg_removed = Image.open(io.BytesIO(remove(img_bytes, session=self.session)))
            white_person = Image.new("RGBA", bg_removed.size, (255, 255, 255, 255))
            white_person.putalpha(bg_removed.getchannel("A"))
            silhouette = Image.alpha_composite(
                Image.new("RGBA", white_person.size, (0, 0, 0, 255)),
                white_person,
            )
            return self._prepare_image(silhouette)
        except Exception:
            logger.exception("Failed to process %s", image_path)
            raise

    def _prepare_image(self, image: Image.Image) -> np.ndarray:
        grayscale = image.convert("L").resize(self.img_size)
        array = np.asarray(grayscale, dtype=np.float32) / 255.0
        return np.expand_dims(array, axis=-1)
