# Build from the repo root:  docker build -f dl_service/Dockerfile -t rdcp-dl .
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MODEL_DIR=/models
WORKDIR /app
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/dl.txt
COPY shared/ shared/
COPY dl_service/ dl_service/
# Run as a non-root user (least privilege).
RUN useradd --create-home --uid 10001 rdcp
USER rdcp
EXPOSE 8000
# Model artifacts are NOT baked into the image; mount them read-only at /models.
CMD ["uvicorn", "dl_service.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
