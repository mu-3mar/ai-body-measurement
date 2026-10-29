"""Portable paths and runtime settings."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv(REPO_ROOT / ".env")

MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", REPO_ROOT / "artifacts" / "models" / "best_model.keras")
).expanduser()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
FRONTEND_ORIGINS = tuple(
    origin.strip()
    for origin in os.environ.get(
        "FRONTEND_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
    ).split(",")
    if origin.strip()
)

IMAGE_SIZE = (128, 128)
ALLOWED_IMAGE_TYPES = frozenset(
    {"image/jpeg", "image/jpg", "image/pjpeg", "image/png"}
)

HEIGHT_CM_RANGE = (100.0, 250.0)
WEIGHT_KG_RANGE = (30.0, 300.0)
APPAREL_TYPES = frozenset({"tshirt", "pants", "all"})
