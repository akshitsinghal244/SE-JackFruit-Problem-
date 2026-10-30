"""Run:  MODEL_DIR=artifacts/qml SERVICE_API_KEY=dev-key uvicorn qml_service.app:app --port 8003"""
from qml_service.predictor import QMLPredictor
from shared.service import create_app

app = create_app("qml", QMLPredictor)
