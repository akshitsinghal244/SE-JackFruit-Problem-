"""Load test for US-28 / NFR-P1, NFR-P2:  20 concurrent users for 10 minutes, error rate < 1 %,
p95 <= 10 s for /predict with QML (<= 3 s when only ML+DL are queried).

  pip install locust
  locust -f loadtest/locustfile.py --headless -u 20 -r 5 -t 10m --host https://localhost --csv docs/perf/run --html docs/perf/run.html
(self-signed certificate: the script disables TLS verification)
Each simulated user registers once, logs in, then mixes predictions (80 %), history (15 %) and model info (5 %).
Think time 2-4 s keeps every user well under the 60 requests/min rate limit (SEC-07)."""
import random
import uuid

from locust import HttpUser, between, task


class Analyst(HttpUser):
    wait_time = between(2, 4)

    def on_start(self):
        self.client.verify = False
        tag = uuid.uuid4().hex[:10]
        self.email, self.pw = f"load_{tag}@example.com", "LoadTest123"
        r = self.client.post("/api/v1/auth/register", json={"username": f"load_{tag}", "email": self.email, "password": self.pw}, name="register")
        if r.status_code != 201:
            r.failure("register failed")
            return
        r = self.client.post("/api/v1/auth/login", json={"email": self.email, "password": self.pw}, name="login")
        self.headers = {"Authorization": f"Bearer {r.json()['access_token']}"} if r.ok else {}

    @task(8)
    def predict(self):
        body = {"store_id": random.randint(1, 10), "item_id": random.randint(1, 50), "date": "2017-10-%02d" % random.randint(1, 28),
                "prev_sales": [random.randint(10, 90) for _ in range(7)]}
        with self.client.post("/api/v1/predict", json=body, headers=self.headers, name="predict", catch_response=True) as r:
            if r.status_code in (200, 207):          # 207 = partial result: the system still worked as designed (FR-14)
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}")

    @task(2)
    def history(self):
        self.client.get("/api/v1/history", headers=self.headers, name="history")

    @task(1)
    def models(self):
        self.client.get("/api/v1/models/info", headers=self.headers, name="models/info")
