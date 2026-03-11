from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from ai_body_measurement.predictor import SinglePersonPredictor


REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / "models" / "best_model.keras"
WEB_DIR = REPO_ROOT / "web"
TEMPLATE_PATH = WEB_DIR / "template.html"
STATIC_DIR = WEB_DIR / "static"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = SinglePersonPredictor(model_path=str(MODEL_PATH))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


@app.post("/predict/")
async def predict(
    front_image: UploadFile = File(...),
    side_image: UploadFile = File(...),
    input_data: str = Form(...),
):
    try:
        try:
            input_dict = json.loads(input_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format in input_data"}

        if front_image.content_type not in ["image/jpeg", "image/png"]:
            return {"error": "Front image must be a JPEG or PNG file"}
        if side_image.content_type not in ["image/jpeg", "image/png"]:
            return {"error": "Side image must be a JPEG or PNG file"}

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as front_temp:
            shutil.copyfileobj(front_image.file, front_temp)
            front_temp_path = front_temp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as side_temp:
            shutil.copyfileobj(side_image.file, side_temp)
            side_temp_path = side_temp.name

        results = predictor.predict_measurements(
            front_img_path=front_temp_path,
            side_img_path=side_temp_path,
            gender=input_dict.get("gender"),
            height_cm=input_dict.get("height_cm"),
            weight_kg=input_dict.get("weight_kg"),
            apparel_type=input_dict.get("apparel_type"),
        )

        os.remove(front_temp_path)
        os.remove(side_temp_path)

        return {"results": results}
    except Exception as e:
        return {"error": str(e)}

