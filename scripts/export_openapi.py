"""Write docs/openapi.json from the FastAPI app (no running server needed).  Run from the repo root:
   python scripts/export_openapi.py"""
import json
import os
import sys

os.environ.setdefault("RDCP_DEV", "1")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gateway"))
from app.main import create_app  # noqa: E402

with open(os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.json"), "w") as f:
    json.dump(create_app().openapi(), f, indent=2)
print("docs/openapi.json written")
