import dataclasses
import os

import fastapi
import pandas as pd
from pydantic import BaseModel
from google.cloud import storage

from .model import DelayModel


@dataclasses.dataclass(frozen=True)
class EnvironmentVariables:
    local_model_path: str
    gcp_bucket_name: str
    gcp_model_path: str


class Flight(BaseModel):
    OPERA: str
    TIPOVUELO: str
    MES: int


class PredictRequest(BaseModel):
    flights: list[Flight]


class PredictResponse(BaseModel):
    predict: list[int]


def load_environment_variables() -> EnvironmentVariables:
    """loads the environment variables needed for the application."""
    gcp_model_path = os.getenv("GCP_MODEL_PATH")
    gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
    local_model_path = os.getenv("LOCAL_MODEL_PATH", "logreg.joblib")
    if gcp_model_path is None or gcp_bucket_name is None:
        raise RuntimeError("GCP_BUCKET_NAME and GCP_MODEL_PATH must be set.")

    return EnvironmentVariables(
        local_model_path=local_model_path,
        gcp_bucket_name=gcp_bucket_name,
        gcp_model_path=gcp_model_path,
    )


def download_model_from_gcp(env_vars: EnvironmentVariables) -> None:
    """Downloads the model from GCP Storage to a local path."""
    if not os.path.exists(env_vars.local_model_path):
        client = storage.Client()
        bucket = client.bucket(env_vars.gcp_bucket_name)
        blob = bucket.blob(env_vars.gcp_model_path)

        if not blob.exists():
            raise FileNotFoundError(
                f"Model not found: gs://{env_vars.gcp_bucket_name}/{env_vars.gcp_model_path}"
            )

        blob.download_to_filename(env_vars.local_model_path)


app = fastapi.FastAPI()


@app.get("/health", status_code=200)
async def get_health() -> dict:
    """Health check endpoint."""
    return {"status": "OK"}


@app.post("/predict", response_model=PredictResponse, status_code=200)
async def post_predict(request: PredictRequest) -> PredictResponse:
    """Predicts flight delay class for a list of flights."""
    try:
        raw_data = pd.DataFrame([flight.model_dump() for flight in request.flights])
        env_vars = load_environment_variables()
        download_model_from_gcp(env_vars)
        model = DelayModel()
        model.load(env_vars.local_model_path)
        input_data = model.preprocess(raw_data)
        preds = model.predict(input_data)

        return PredictResponse(predict=preds)

    except Exception as e:
        raise fastapi.HTTPException(status_code=400, detail=str(e))
