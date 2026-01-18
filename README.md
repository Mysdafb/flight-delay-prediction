# Flight Delay Prediction API

A FastAPI-based machine learning service that predicts flight delays for departures and arrivals at Santiago International Airport (SCL) using a trained logistic regression model.

## Overview

This project operationalizes a data science model for delay prediction by:
- Providing a REST API endpoint (`/predict`) for batch predictions.
- Containerizing the app for easy deployment on cloud platforms (GCP Cloud Run).
- Implementing a complete CI/CD pipeline with tests and automated deployments on tag creation.
- Using environment variables to safely manage secrets and configuration.

## Tech Stack

- **Framework**: FastAPI
- **ML Model**: Scikit-learn LogisticRegression
- **Container**: Docker
- **Cloud**: Google Cloud (Cloud Run, Cloud Storage)
- **Testing**: pytest, mockito
- **Dependency Management**: uv (astral)
- **CI/CD**: GitHub Actions

## Project Structure

```
flight-delay-prediction/
├── challenge/
│   ├── api.py              # FastAPI app with /health and /predict endpoints
│   ├── model.py            # DelayModel and DataProcessor classes
│   └── __init__.py
├── tests/
│   ├── api/                # API integration tests
│   ├── model/              # Model unit tests
│   └── stress/             # Load/stress tests
├── .github/
│   └── workflows/
│       ├── ci.yml          # Continuous Integration pipeline
│       └── cd.yml          # Continuous Deployment (Cloud Run)
├── Dockerfile              # Container image definition
├── Makefile                # Development shortcuts
├── pyproject.toml          # Project metadata and uv config
├── uv.lock                 # Dependency lockfile
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Python 3.10+
- uv (astral) — for dependency management
- Docker (optional, for local container testing)
- GCP account (for cloud deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Mysdafb/flight-delay-prediction.git
   cd flight-delay-prediction
   ```

2. **Create and activate a virtual environment** (using `make`):
   ```bash
   make venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   make install
   ```
   Or manually:
   ```bash
   uv sync --group dev --group test
   ```

## Development

### Linting and Pre-commit

This project uses pre-commit hooks to ensure code quality. Install them:
```bash
pre-commit install
```

Run pre-commit on all files:
```bash
pre-commit run --all-files
```

### Running Locally

Start the development server:
```bash
uvicorn challenge.api:app --reload
```

The API will be available at `http://localhost:8000`.

Health check:
```bash
curl http://localhost:8000/health
# {"status":"OK"}
```

Test prediction:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"flights": [{"OPERA": "Airline name", "TIPOVUELO": "N", "MES": 3}]}'
```

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{"status": "OK"}
```

### `POST /predict`
Predict delay probability for a list of flights.

**Request:**
```json
{
  "flights": [
    {
      "OPERA": "Aerolineas Argentinas",
      "TIPOVUELO": "N",
      "MES": 3
    }
  ]
}
```

**Response:**
```json
{
  "predict": [0]
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid input (missing required fields, invalid data)

## Container & Deployment

### Building the Container Locally

```bash
docker build -t flight-delay-api:latest .
```

Run locally:
```bash
docker run -p 8080:8080 \
  -e GCP_BUCKET_NAME=your-bucket \
  -e GCP_MODEL_PATH=models/logreg.joblib \
  -e LOCAL_MODEL_PATH=/tmp/logreg.joblib \
  flight-delay-api:latest
```

### Deploying to Cloud Run

**Prerequisites:**
- GCP project with Cloud Run, Cloud Build, Cloud Storage enabled.
- Service account with appropriate permissions.
- Model uploaded to GCS bucket.

**Step 1: Set up secrets in GitHub**

Go to your repository Settings → Secrets and add:
- `GCP_SA_KEY`: JSON key of your GCP service account.
- `GCP_PROJECT`: Your GCP project ID.
- `GCP_REGION`: e.g., `us-central1`.
- `CLOUD_RUN_SERVICE`: Name of the Cloud Run service, e.g., `flight-delay-api`.
- `GCP_BUCKET_NAME`: GCS bucket containing the model.
- `GCP_MODEL_PATH`: Path to the model in the bucket, e.g., `models/logreg.joblib`.
- `LOCAL_MODEL_PATH`: Local path for the model, e.g., `/tmp/logreg.joblib`.

**Step 2: Upload the model to GCS**

```bash
gsutil cp logreg.joblib gs://your-bucket/models/logreg.joblib
```

**Step 3: Create a tag to trigger the deployment**

```bash
git tag v1.0.0
git push origin v1.0.0
```

The GitHub Actions CD pipeline will automatically:
1. Build the Docker image.
2. Push it to Google Container Registry.
3. Deploy it to Cloud Run with the environment variables.

**Step 4: Test the deployment**

Retrieve the Cloud Run URL:
```bash
gcloud run services describe flight-delay-api --region us-central1
```

Test the deployed API:
```bash
curl https://flight-delay-api-xxxxx.run.app/health
```

### Service Account Permissions

The service account used for deployment should have (minimum):
- `roles/run.admin` (for Cloud Run deployments)
- `roles/cloudbuild.builds.editor` (for Cloud Build)
- `roles/storage.objectViewer` on the GCS bucket (for downloading the model)

### Manual Deploy (Local `gcloud` CLI)

```bash
gcloud run deploy flight-delay-api \
  --image gcr.io/PROJECT_ID/flight-delay-api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GCP_BUCKET_NAME=your-bucket,GCP_MODEL_PATH=models/logreg.joblib,LOCAL_MODEL_PATH=/tmp/logreg.joblib
```

## CI/CD Pipeline

### Continuous Integration (CI)

Triggered on every push and pull request. Runs:
1. **Pre-commit checks**: linting, formatting.
2. **Model tests**: unit tests for `DelayModel` and `DataProcessor`.
3. **API tests**: integration tests for the FastAPI endpoints (with mocked model).

See `.github/workflows/ci.yml` for details.

### Continuous Deployment (CD)

Triggered when a new **tag** is created. Builds and deploys to Cloud Run automatically.

See `.github/workflows/cd.yml` for details.

## Model Training & Data

The model is trained using a logistic regression classifier on flight data. Features include:
- **Temporal**: month, period of day (morning/afternoon/night), high season indicator.
- **Operational**: airline, flight type (international/national).

The training notebook and dataset are documented in `docs/challenge.md`.

### Model Details

- **Type**: Logistic Regression with class weighting.
- **Input**: 10 one-hot encoded features.
- **Output**: Binary classification (0: on-time, 1: delayed >15 min).
- **Serialization**: joblib format (`logreg.joblib`).

## Environment Variables

The API requires the following environment variables (provided at container runtime):

| Variable | Description | Example |
|----------|-------------|---------|
| `GCP_BUCKET_NAME` | GCS bucket name | `my-flight-models` |
| `GCP_MODEL_PATH` | Path inside bucket | `models/logreg.joblib` |
| `LOCAL_MODEL_PATH` | Local cache path | `/tmp/logreg.joblib` |

## Testing

### Unit Tests
```bash
make model-test
```

### Integration Tests (API)
```bash
make api-test
```

### Stress/Load Tests
```bash
make stress-test
```
(Requires the API to be running at the configured URL.)

## Troubleshooting

### Model fails to load
- Ensure `GCP_BUCKET_NAME`, `GCP_MODEL_PATH` are set correctly.
- Check that the Cloud Run service account has `storage.objectViewer` on the bucket.
- Verify the model file exists at the specified path in GCS.

### Cold starts are slow
- The first request to a Cloud Run instance downloads and loads the model. This is expected behavior.
- To reduce latency, keep a minimum instance count or embed the model in the image (trade-off: larger image, slower deployments).

### Permission denied when accessing GCS
- Verify the Cloud Run service account has at least `roles/storage.objectViewer` on the model bucket.
- Use `gcloud` to grant permissions:
  ```bash
  gsutil iam ch serviceAccount:SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com:objectViewer gs://BUCKET
  ```

## Contributing

1. Create a feature branch from `main`: `git checkout -b feature/my-feature`.
2. Implement changes and add tests.
3. Run tests locally: `make api-test && make model-test`.
4. Push to GitHub and create a pull request.
5. Once merged to `main`, create a release tag to trigger deployment.

## License

See [LICENSE](LICENSE) for details.