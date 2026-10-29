const API_BASE = window.BODY_MEASURE_API_URL || "http://localhost:8000";
const form = document.querySelector("#prediction-form");
const errorBox = document.querySelector("#error-message");
const submitButton = document.querySelector("#submit-button");
const apiStatus = document.querySelector("#api-status");
const apiPill = document.querySelector(".api-pill");
const resultTitle = document.querySelector("#result-title");
const resultSummary = document.querySelector("#result-summary");
const resultSymbol = document.querySelector(".result-symbol");
const sizeRow = document.querySelector("#size-row");
const measureGrid = document.querySelector("#measure-grid");
const progressBlock = document.querySelector("#progress-block");

async function checkApi() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error("API unavailable");
    const data = await response.json();
    if (data.model_loaded) {
      apiStatus.textContent = "Model ready";
      apiPill.classList.add("connected");
      apiPill.classList.remove("offline");
    } else {
      apiStatus.textContent = "API up, model missing";
      apiPill.classList.add("offline");
      apiPill.classList.remove("connected");
    }
  } catch {
    apiStatus.textContent = "API offline";
    apiPill.classList.add("offline");
    apiPill.classList.remove("connected");
  }
}

function previewImage(input, previewId) {
  const preview = document.getElementById(previewId);
  if (!preview) return;
  const file = input.files && input.files[0];
  if (!file) {
    preview.src = "";
    preview.classList.remove("is-visible");
    return;
  }
  const reader = new FileReader();
  reader.onload = (event) => {
    preview.src = event.target.result;
    preview.classList.add("is-visible");
  };
  reader.readAsDataURL(file);
}

function showError(message) {
  errorBox.hidden = false;
  errorBox.textContent = message;
  resultSymbol.textContent = "!";
  resultSymbol.style.color = "var(--error)";
}

function clearResult() {
  errorBox.hidden = true;
  errorBox.textContent = "";
  sizeRow.hidden = true;
  sizeRow.innerHTML = "";
  measureGrid.hidden = true;
  measureGrid.innerHTML = "";
  progressBlock.hidden = true;
  resultTitle.textContent = "Measurement estimates will appear here.";
  resultSummary.textContent = "Upload both views, enter your details, then select “Measure”.";
  resultSymbol.textContent = "↗";
  resultSymbol.style.color = "var(--accent)";
}

function labelize(key) {
  return key.replace(/-/g, " ");
}

function renderSizes(results) {
  const chips = [];
  if (results.tshirt_size) {
    chips.push(`<div class="size-chip"><span>T-shirt</span><strong>${results.tshirt_size}</strong></div>`);
  }
  if (results.pants_size !== undefined && results.pants_size !== null) {
    chips.push(`<div class="size-chip"><span>Pants</span><strong>${results.pants_size}</strong></div>`);
  }
  sizeRow.innerHTML = chips.join("");
  sizeRow.hidden = chips.length === 0;
}

function renderMeasurements(results) {
  const source =
    results.body_measurements ||
    results.upper_body_measurements ||
    results.lower_body_measurements ||
    {};
  const items = Object.entries(source).map(
    ([key, value]) =>
      `<div class="measure-item"><span>${labelize(key)}</span><strong>${value} cm</strong></div>`
  );
  measureGrid.innerHTML = items.join("");
  measureGrid.hidden = items.length === 0;
}

document.querySelector("#front_image").addEventListener("change", (event) => {
  previewImage(event.target, "frontPreview");
});
document.querySelector("#side_image").addEventListener("change", (event) => {
  previewImage(event.target, "sidePreview");
});

document.querySelector("#reset-form").addEventListener("click", () => {
  form.reset();
  document.querySelectorAll(".preview-image").forEach((image) => {
    image.src = "";
    image.classList.remove("is-visible");
  });
  clearResult();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  sizeRow.hidden = true;
  measureGrid.hidden = true;
  progressBlock.hidden = false;
  submitButton.disabled = true;
  resultTitle.textContent = "Working on your photos…";
  resultSummary.textContent = "Background removal can take a few seconds on the first run.";
  resultSymbol.textContent = "…";
  resultSymbol.style.color = "var(--accent)";

  const formData = new FormData(form);
  const inputData = {
    gender: parseInt(formData.get("gender"), 10),
    height_cm: parseFloat(formData.get("height_cm")),
    weight_kg: parseFloat(formData.get("weight_kg")),
    apparel_type: formData.get("apparel_type"),
  };
  formData.append("input_data", JSON.stringify(inputData));

  try {
    const response = await fetch(`${API_BASE}/predict/`, {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok || payload.error) {
      showError(payload.error || "Prediction failed.");
      resultTitle.textContent = "Could not complete the measurement.";
      resultSummary.textContent = "Check the photos and form values, then try again.";
      return;
    }

    const results = payload.results;
    resultSymbol.textContent = "✓";
    resultSymbol.style.color = "var(--success)";
    resultTitle.textContent = "Estimated measurements are ready.";
    resultSummary.textContent = "Values are in centimetres. Clothing sizes use the built-in charts.";
    renderSizes(results);
    renderMeasurements(results);
  } catch {
    showError("Failed to connect to the server. Please try again.");
    resultTitle.textContent = "Could not reach the API.";
    resultSummary.textContent = "Confirm the local server is running, then retry.";
  } finally {
    progressBlock.hidden = true;
    submitButton.disabled = false;
  }
});

checkApi();
