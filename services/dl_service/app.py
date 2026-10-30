"""Run:  MODEL_DIR=artifacts/dl SERVICE_API_KEY=dev-key uvicorn dl_service.app:app --port 8002"""
from dl_service.predictor import DLPredictor
from shared.service import create_app

app = create_app("dl", DLPredictor)
