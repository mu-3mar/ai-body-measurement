# AI Body Measurement

AI Body Measurement is a local computer-vision application that estimates body
measurements and simple clothing sizes from:

- one front-view photograph,
- one side-view photograph,
- gender,
- height in centimetres, and
- weight in kilograms.

The project is intended for experimentation and demonstration. It is not a
medical device, a tailoring replacement, or a production-grade sizing system.
Predictions can be affected by pose, clothing, lighting, camera angle,
background removal quality, and the training data.

## Project layout

The repository is intentionally divided into four clear areas:

```text
ai-body-measurement/
├── src/
│   └── ai_body_measurement/    # Backend Python source
│       ├── api.py              # FastAPI application and REST endpoints
│       ├── config.py           # Paths and runtime configuration
│       ├── predictor.py        # Keras model loading and inference
│       ├── preprocessing.py    # Background removal and image preparation
│       ├── sizing.py            # Measurement names and clothing size rules
│       └── validation.py       # Request parsing and validation
├── frontend/
│   ├── index.html              # User interface
│   ├── app.js                  # API calls and result rendering
│   ├── styles.css              # User interface styles
│   └── logo-animated.html      # Logo component
├── artifacts/
│   └── models/
│       └── best_model.keras    # Trained Keras model used by the backend
├── notebooks/
│   └── FinalModel.ipynb        # Training and experimentation notebook
├── demo/
│   └── demo.webm               # Project demonstration recording
├── main.py                     # Backend launcher
├── pyproject.toml              # Python package and dependency definition
├── README.md
├── LICENSE
└── .gitignore
```

Generated files such as `.venv`, `__pycache__`, `.pytest_cache`, build
directories, and local datasets are excluded from version control.

## Architecture

The frontend and backend are independent:

```text
Browser
  │
  │  http://localhost:5500
  ▼
Frontend static server
  │
  │  POST http://localhost:8000/predict/
  ▼
FastAPI backend
  │
  ├── validates metadata and uploaded images
  ├── removes image backgrounds with rembg
  ├── creates 128 × 128 grayscale silhouette tensors
  ├── runs the Keras model
  └── maps measurements to clothing sizes
```

The backend does not serve the frontend. The frontend is opened from its own
static server and calls the backend through the configured API URL.

## Requirements

- Python 3.10, 3.11, or 3.12
- A local copy of `artifacts/models/best_model.keras`
- TensorFlow
- rembg
- A modern web browser

TensorFlow and rembg may not support every newer Python release. Python 3.11
is a practical choice for the inference environment.

## Installation

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[inference]"
```

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[inference]"
```

The first prediction may take longer because rembg can download its
segmentation model into its local cache.

## Running the application

Start the backend from the repository root:

```bash
source .venv/bin/activate
python main.py
```

The backend listens on:

```text
http://localhost:8000
```

Open a second terminal and start the frontend:

```bash
cd frontend
python -m http.server 5500
```

Open the application at:

```text
http://localhost:5500
```

Do not open port 8000 expecting the web page. Port 8000 is the API only.

## Configuration

Runtime configuration is read from environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `MODEL_PATH` | `artifacts/models/best_model.keras` | Path to a compatible Keras model |
| `HOST` | `0.0.0.0` | Backend bind address |
| `PORT` | `8000` | Backend port |
| `FRONTEND_ORIGINS` | `http://localhost:5500,http://127.0.0.1:5500` | Allowed browser origins |

Example:

```bash
MODEL_PATH=/absolute/path/to/model.keras PORT=8001 python main.py
```

If the backend port is changed, update `API_BASE` in
`frontend/app.js` before opening the frontend.

## Backend API

### `GET /health`

Returns the backend and model status:

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_path": ".../artifacts/models/best_model.keras",
  "error": null
}
```

When TensorFlow, rembg, or the model cannot be loaded, the endpoint remains
available and reports `"status": "degraded"` with `"model_loaded": false`.
Prediction requests return HTTP 503 until the model is available.

### `POST /predict/`

The endpoint accepts multipart form data:

- `front_image`: JPEG or PNG front-view image
- `side_image`: JPEG or PNG side-view image
- `input_data`: JSON string containing metadata

Example:

```json
{
  "gender": 0,
  "height_cm": 175,
  "weight_kg": 70,
  "apparel_type": "all"
}
```

Accepted values:

- `gender`: `0` for male or `1` for female
- `height_cm`: 100 to 250
- `weight_kg`: 30 to 300
- `apparel_type`: `all`, `tshirt`, or `pants`

The API validates both the declared MIME type and the actual image content.
Invalid metadata or images return HTTP 400. Model failures return HTTP 503,
and unexpected inference failures return HTTP 500.

## Model and preprocessing

The shipped model expects three inputs:

1. Front silhouette: `(128, 128, 1)`
2. Side silhouette: `(128, 128, 1)`
3. Metadata vector: `[gender, height_cm, weight_kg]`

For each uploaded image, the backend:

1. reads the image,
2. removes the background with rembg,
3. composites the foreground as a white silhouette on a black background,
4. converts the result to grayscale,
5. resizes it to 128 by 128 pixels, and
6. scales pixel values to the range `[0, 1]`.

The model produces fourteen predicted measurements in centimetres:

```text
ankle
arm-length
bicep
calf
chest
forearm
height
hip
leg-length
shoulder-breadth
shoulder-to-crotch
thigh
waist
wrist
```

## Clothing-size rules

The backend maps predictions to simple built-in charts:

- T-shirt size uses chest and shoulder breadth.
- Pants size uses waist and hip.
- High-weight rules can increase the T-shirt result.
- Predicted height above 180 cm adds a `Tall` prefix to T-shirt sizes.
- Tall male pants results below size 40 receive a two-size increase.

These are generic heuristics, not brand-specific size charts.

## Training metrics and evaluation status

The training run recorded in `notebooks/FinalModel.ipynb` ran for a maximum of
60 epochs and stopped early at epoch 22. The run used `ReduceLROnPlateau` and
`EarlyStopping`, then restored the weights from epoch 17 because the stopping
callback monitored `val_loss`.

The available validation metrics from that run are:

| Metric | Value | Epoch | Meaning |
| --- | ---: | ---: | --- |
| Best recorded validation loss | 40.7038 | 17 | Mean squared error on the validation split |
| Lowest recorded validation MAE | 2.8598 cm | 22 | Mean absolute error across the 14 outputs on the validation split |
| Restored checkpoint | Epoch 17 | 17 | Weights selected by the `val_loss` monitor |
| Final learning rate before stopping | 1.25e-05 | 21-22 | Learning rate after plateau reductions |

The validation MAE of **2.8598 cm** is a useful result from this specific
training run, but it is not a complete accuracy claim. It is an aggregate
validation metric, not a per-measurement report, and it does not establish
performance on new subjects, different poses, different clothing, or real
production images. The value also does not necessarily describe the restored
epoch-17 checkpoint because the lowest MAE and the lowest validation loss
occurred at different epochs.

The project currently has no verified independent test-set report with
per-measurement MAE, RMSE, R², confidence intervals, or subject-disjoint
evaluation. Training and validation metrics must not be presented as general
real-world accuracy. A proper evaluation should use a subject-disjoint
held-out test set and report at least:

- mean absolute error in centimetres for every measurement,
- median absolute error,
- root mean squared error,
- R² where appropriate,
- results grouped by gender and measurement,
- the number of test subjects, and
- the exact preprocessing and model checkpoint used.

Until that evaluation is completed, the application should be described as a
demonstration that produces estimates, not as a system with a claimed
measurement accuracy.

## Data and training sources

The training notebook expects a local BodyM-style dataset containing metadata,
measurements, front masks, and side masks. Training data is not required to
run the inference demo and is not included as a runtime dependency.

The notebook is stored under `notebooks/` so that training material is kept
separate from backend and frontend runtime code. The trained checkpoint
used by the application is stored under `artifacts/models/`.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).
