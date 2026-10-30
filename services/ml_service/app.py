"""Run:  MODEL_DIR=artifacts/ml SERVICE_API_KEY=dev-key uvicorn ml_service.app:app --port 8001"""
from ml_service.predictor import MLPredictor
from shared.service import create_app

app = create_app("ml", MLPredictor)
