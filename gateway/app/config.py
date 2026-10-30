"""All settings come from environment variables (12-factor); same image runs in compose and Kubernetes."""
import os


class Settings:
    def __init__(self) -> None:
        e = os.environ.get
        self.database_url = e("DATABASE_URL", "sqlite:///./rdcp.db")
        self.jwt_secret = e("JWT_SECRET", "")
        self.jwt_minutes = int(e("JWT_MINUTES", "15"))                       # SEC-02
        self.service_api_key = e("SERVICE_API_KEY", "dev-key")               # SEC-05
        self.service_urls = {
            "ml": e("ML_URL", "http://localhost:8001"),
            "dl": e("DL_URL", "http://localhost:8002"),
            "qml": e("QML_URL", "http://localhost:8003"),
        }
        self.timeout = float(e("SERVICE_TIMEOUT", "8"))                      # FR-05
        self.cors = [o.strip() for o in e("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]  # SEC-10
        self.admin_email = e("ADMIN_EMAIL", "")
        self.admin_password = e("ADMIN_PASSWORD", "")
        self.redis_url = e("REDIS_URL", "")                                  # shared rate-limit across pods
        self.rate_limit = int(e("RATE_LIMIT_PER_MIN", "60"))                 # SEC-07
        self.bcrypt_cost = int(e("BCRYPT_COST", "12"))                       # SEC-01
        self.lock_after = 5                                                  # SEC-08
        self.lock_minutes = 15
        self.health_interval = int(e("HEALTH_INTERVAL", "30"))               # FR-12
        self.breaker_failures = 3
        self.breaker_cooldown = 30
        self.dev = e("RDCP_DEV") == "1"


settings = Settings()
