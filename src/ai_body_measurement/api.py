"""FastAPI application: web demo and prediction endpoint."""

from __future__ import annotations

import io
import logging
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from ai_body_measurement.config import ALLOWED_IMAGE_TYPES, FRONTEND_ORIGINS, MODEL_PATH
from ai_body_measurement.validation import InputValidationError, parse_prediction_input

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def _validate_upload(upload: UploadFile, label: str) -> str | None:
    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        return f"{label} image must be a JPEG or PNG file"

    try:
        contents = await upload.read()
        with Image.open(io.BytesIO(contents)) as image:
            image.verify()
            if image.format not in {"JPEG", "PNG"}:
                return f"{label} image is not a valid JPEG or PNG file"
    except (UnidentifiedImageError, OSError):
        return f"{label} image is not a valid JPEG or PNG file"
    finally:
        await upload.seek(0)

    return None


def _load_predictor():
    from ai_body_measurement.predictor import SinglePersonPredictor

    return SinglePersonPredictor(model_path=MODEL_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.predictor = None
    app.state.model_error = None
    try:
        app.state.predictor = _load_predictor()
        logger.info("Predictor ready")
    except Exception as exc:
        app.state.model_error = str(exc)
        logger.warning("Predictor unavailable: %s", exc)
    yield


app = FastAPI(
    title="AI Body Measurement",
    description="Estimate body measurements and clothing sizes from front and side photos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(FRONTEND_ORIGINS),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict[str, object]:
    predictor = getattr(app.state, "predictor", None)
    error = getattr(app.state, "model_error", None)
    return {
        "status": "ok" if predictor is not None else "degraded",
        "model_loaded": predictor is not None,
        "model_path": str(MODEL_PATH),
        "error": error,
    }


@app.post("/predict/")
async def predict(
    front_image: UploadFile = File(...),
    side_image: UploadFile = File(...),
    input_data: str = Form(...),
):
    predictor = getattr(app.state, "predictor", None)
    if predictor is None:
        message = getattr(app.state, "model_error", None) or "Model is not loaded."
        return JSONResponse(status_code=503, content={"error": message})

    try:
        payload = parse_prediction_input(input_data)
    except InputValidationError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    for image, label in ((front_image, "Front"), (side_image, "Side")):
        image_error = await _validate_upload(image, label)
        if image_error:
            return JSONResponse(status_code=400, content={"error": image_error})

    front_temp_path = None
    side_temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as front_temp:
            shutil.copyfileobj(front_image.file, front_temp)
            front_temp_path = front_temp.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as side_temp:
            shutil.copyfileobj(side_image.file, side_temp)
            side_temp_path = side_temp.name

        results = predictor.predict_measurements(
            front_img_path=front_temp_path,
            side_img_path=side_temp_path,
            gender=payload.gender,
            height_cm=payload.height_cm,
            weight_kg=payload.weight_kg,
            apparel_type=payload.apparel_type,
        )
        return {"results": results}
    except Exception as exc:
        logger.exception("Prediction request failed")
        return JSONResponse(status_code=500, content={"error": str(exc)})
    finally:
        for path in (front_temp_path, side_temp_path):
            if path:
                Path(path).unlink(missing_ok=True)
