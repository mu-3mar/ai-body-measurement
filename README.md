# AI Body Measurement

> Estimate body measurements and basic clothing sizes from two photographs using
> computer vision and a multi-input Keras model.

AI Body Measurement is a local end-to-end demo that combines front and side
silhouette images with a person's gender, height, and weight. The model
estimates **14 body measurements in centimetres**, then the backend maps those
estimates to simple T-shirt and pants sizes.

This project is intended for learning, experimentation, and demonstration. It
is **not** a medical device, a replacement for a professional tailor, or a
production-grade sizing engine. The returned values are estimates and can
change with pose, clothing, camera angle, lighting, background-removal quality,
and differences between the training data and the submitted photo.

## Demo

The repository includes a screen recording at [`demo/demo.webm`](demo/demo.webm).
The web interface is a local frontend; images are sent to the local FastAPI
server for processing.

## What the project does

- Accepts one front-view and one side-view JPEG or PNG image.
- Removes the background from each image with `rembg`.
- Converts both images into 128 × 128 grayscale silhouettes.
- Uses gender, height, and weight as additional model inputs.
- Predicts 14 body measurements in centimetres.
- Returns all measurements, or only the measurements relevant to T-shirts or
  pants, depending on the selected apparel type.
- Calculates generic clothing sizes from built-in measurement charts.
- Provides a health endpoint that reports whether the model is loaded.
- Validates metadata, MIME types, and actual image contents before inference.
- Runs locally; uploaded images are written to temporary files and removed after
  the request finishes.

## Architecture

```text
┌──────────────────────┐
│ Browser frontend     │
│ HTML / CSS / JS      │
└──────────┬───────────┘
           │ POST /predict/
           ▼
┌──────────────────────┐
│ FastAPI backend      │
│ validation + API     │
└──────────┬───────────┘
           │
           ├─ rembg background removal
           ├─ silhouette preprocessing
           ├─ Keras inference
           └─ clothing-size heuristics
```

The frontend and backend are intentionally served separately:

- `http://localhost:5500` serves the web interface.
- `http://localhost:8000` serves the API.

Port `8000` is an API port, so opening it directly does not display the
frontend.

## Repository structure

```text
ai-body-measurement/
├── src/ai_body_measurement/
│   ├── api.py              # FastAPI app, health and prediction endpoints
│   ├── config.py           # Paths, ports, CORS and validation ranges
│   ├── predictor.py        # Keras model loading and inference
│   ├── preprocessing.py    # Background removal and silhouette preparation
│   ├── sizing.py           # Measurement mapping and clothing-size rules
│   └── validation.py       # JSON and request-field validation
├── frontend/
│   ├── index.html          # User interface
│   ├── app.js              # API requests and result rendering
│   ├── styles.css          # Interface styling
│   └── logo-animated.html  # Animated logo component
├── artifacts/models/
│   └── best_model.keras    # Keras checkpoint used by the demo
├── notebooks/
│   └── FinalModel.ipynb    # Dataset preparation, training and experiments
├── data/data.md            # Dataset description and availability notes
├── demo/demo.webm          # Demonstration recording
├── main.py                 # Local backend launcher
├── pyproject.toml          # Package metadata and dependencies
├── LICENSE                 # MIT license
└── README.md
```

Local environments, caches, build output, and private datasets are excluded
from version control through [`.gitignore`](.gitignore).

## Requirements

- Python 3.10, 3.11, or 3.12
- A modern browser
- The included compatible model at
  [`artifacts/models/best_model.keras`](artifacts/models/best_model.keras)
- TensorFlow and `rembg` for inference

Python 3.11 is recommended because TensorFlow and `rembg` support can vary
between Python releases.

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

The first prediction may take longer because `rembg` can download its
segmentation model into its local cache.

## Run the application

### 1. Start the backend

```bash
source .venv/bin/activate
python main.py
```

The API starts at `http://localhost:8000`.

### 2. Start the frontend

Open a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Then open `http://localhost:5500` in a browser. Upload matching front and side
views, enter the metadata, choose an apparel type, and select **Measure**.

For best results, use a full-body image with the person standing straight,
clearly visible, and photographed from the requested view. Similar framing and
lighting for both images are preferable.

## Configuration

Runtime settings can be provided through environment variables or a local
`.env` file:

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

If the backend port changes, set `BODY_MEASURE_API_URL` before opening the
frontend, or update the default `API_BASE` in
[`frontend/app.js`](frontend/app.js):

```bash
BODY_MEASURE_API_URL=http://localhost:8001
```

## API reference

### `GET /health`

Returns the current backend and model status:

```json
{
  "status": "ok",
  "model_loaded": true,
  "model_path": ".../artifacts/models/best_model.keras",
  "error": null
}
```

If TensorFlow, `rembg`, or the model cannot be loaded, the endpoint remains
available with `"status": "degraded"` and prediction requests return HTTP 503.

### `POST /predict/`

The endpoint accepts `multipart/form-data` with:

| Field | Type | Description |
| --- | --- | --- |
| `front_image` | file | Front-view JPEG or PNG |
| `side_image` | file | Side-view JPEG or PNG |
| `input_data` | JSON string | Gender, height, weight, and apparel type |

Example `input_data`:

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
- `height_cm`: `100` to `250`
- `weight_kg`: `30` to `300`
- `apparel_type`: `all`, `tshirt`, or `pants`

Typical response:

```json
{
  "results": {
    "body_measurements": {
      "ankle": 22.1,
      "arm-length": 59.4,
      "bicep": 31.7,
      "calf": 37.2,
      "chest": 98.6,
      "forearm": 26.4,
      "height": 174.8,
      "hip": 96.2,
      "leg-length": 82.4,
      "shoulder-breadth": 44.1,
      "shoulder-to-crotch": 73.5,
      "thigh": 54.0,
      "waist": 84.3,
      "wrist": 17.1
    },
    "tshirt_size": "M",
    "pants_size": 34
  }
}
```

The numeric values above are response-shape examples, not a benchmark
prediction.

HTTP behavior:

- `200`: prediction completed.
- `400`: invalid JSON, metadata, MIME type, or image content.
- `503`: the model is unavailable.
- `500`: an unexpected inference failure.

## Inference pipeline

The Keras model receives three inputs:

1. Front silhouette: `(128, 128, 1)`
2. Side silhouette: `(128, 128, 1)`
3. Metadata vector: `[gender, height_cm, weight_kg]`

For every uploaded image, the backend:

1. reads the image and verifies that it is a valid JPEG or PNG;
2. removes the background with `rembg`;
3. composites the person as a white silhouette on a black background;
4. converts the result to grayscale;
5. resizes it to 128 × 128 pixels; and
6. scales pixel values to `[0, 1]`.

The model output is mapped to these 14 measurements:

```text
ankle, arm-length, bicep, calf, chest, forearm, height,
hip, leg-length, shoulder-breadth, shoulder-to-crotch,
thigh, waist, wrist
```

## Clothing-size logic

The size result is a transparent heuristic, not a learned size classifier:

- T-shirt size uses predicted chest and shoulder breadth.
- Pants size uses predicted waist and hip.
- High-weight rules can increase the T-shirt result.
- Predicted height above 180 cm adds a `Tall` prefix to T-shirt sizes.
- Tall male pants results below size 40 receive a two-size increase.

The charts are generic and are not tied to a specific brand, country, or
retailer. Users should always check the target brand's own size chart.

## Dataset

The training work used a BodyM-style dataset originally hosted on AWS. The
dataset description reports:

- **2,505 subjects**
- **8,978 silhouette images**
- front and lateral/side views
- height, weight, and gender metadata
- 14 target measurements in centimetres

The dataset contains personal body information and images of real people, so
the original files are not included in this repository and cannot be
redistributed here. See [`data/data.md`](data/data.md) for the documented
dataset details and the original AWS reference:
<https://registry.opendata.aws/bodym/>.

Training is optional for running the demo. The notebook expects a local copy
of the training data and is not part of the inference installation.

## Training setup and experiments

The reproducible training material is in
[`notebooks/FinalModel.ipynb`](notebooks/FinalModel.ipynb). The recorded run
used:

- 128 × 128 grayscale front and side inputs
- batch size `8`
- a `10%` validation split
- `random_state=15` for the split
- two convolutional silhouette branches with global average pooling
- metadata concatenation with the image features
- dense layers with dropout and L2 regularization
- maximum of `60` epochs
- `ReduceLROnPlateau`
- `EarlyStopping` with `restore_best_weights=True`
- `ModelCheckpoint` monitored by `val_loss`

The application checkpoint is
[`artifacts/models/best_model.keras`](artifacts/models/best_model.keras).

## Accuracy and evaluation status

The notebook contains one recorded training/validation run. Its reported
aggregate metrics are:

| Metric | Value | Epoch | Interpretation |
| --- | ---: | ---: | --- |
| Best recorded validation loss | `40.7038` | 17 | Mean squared error on the validation split |
| Lowest recorded validation MAE | `2.8598 cm` | 22 | Average absolute error across the 14 outputs |
| Maximum configured epochs | `60` | — | Training stopped before the limit |
| Early-stopping point | 22 | — | The run stopped after validation loss plateaued |
| Restored checkpoint | 17 | — | Selected by the `val_loss` monitor |
| Final recorded learning rate | `1.25e-05` | 21–22 | After plateau reductions |

### How to interpret `2.8598 cm`

`2.8598 cm` is the lowest aggregate **validation MAE recorded in that
specific run**. It is not a universal accuracy percentage, and it should not
be presented as guaranteed real-world accuracy. In particular:

- it is averaged across 14 different measurements;
- it is a validation result, not an independently verified test result;
- the lowest MAE occurred at epoch 22, while the checkpoint restored by the
  `val_loss` monitor came from epoch 17;
- there is no per-measurement MAE/RMSE/R² report in the repository;
- performance may differ for new subjects, poses, clothing, cameras, and
  backgrounds.

At the current project stage, the honest claim is:

> The recorded validation run reached an aggregate MAE of 2.8598 cm on its
> validation split. Independent real-world measurement accuracy has not been
> established.

### Evaluation still needed

A stronger accuracy report should use a subject-disjoint held-out test set and
publish:

- MAE, median absolute error, and RMSE for every measurement;
- R² where it is meaningful;
- results grouped by gender and measurement;
- the number of unique test subjects;
- the exact preprocessing configuration and checkpoint;
- error ranges or confidence intervals; and
- qualitative results on photographs outside the training distribution.

## What has been tried

The project has progressed from notebook experimentation to a runnable local
product flow:

1. A multi-input model was trained using front and side silhouettes plus
   metadata.
2. The training run was monitored with validation loss and MAE, learning-rate
   reduction, early stopping, and checkpoint saving.
3. The trained checkpoint was integrated into a Python inference service.
4. Background removal and silhouette normalization were added before inference.
5. Input validation was added for gender, height, weight, apparel type, file
   MIME type, and actual image format.
6. Generic T-shirt and pants size charts were added on top of the predicted
   measurements.
7. A browser frontend was connected to the API with image previews, API-health
   status, progress feedback, result rendering, and error messages.
8. A local demo recording was included in [`demo/demo.webm`](demo/demo.webm).

The current result is a complete local demonstration pipeline, not a
production-certified measurement or retail-sizing service.

## Limitations and responsible use

- Background removal can fail on cluttered scenes, poor contrast, or multiple
  people.
- A non-standard pose, loose clothing, cropped body, or inconsistent camera
  angle can reduce quality.
- Two-dimensional silhouettes cannot capture every three-dimensional body
  characteristic.
- Clothing sizes differ by brand and region; the built-in charts are only
  generic approximations.
- The model has no calibrated confidence score.
- The dataset is not shipped with the repository and independent test
  performance is not currently reported.
- Do not use the output for medical decisions, manufacturing, safety-critical
  applications, or irreversible purchases without independent measurement.

## License

This project is distributed under the MIT License. See [`LICENSE`](LICENSE).
