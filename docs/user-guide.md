# User guide (SRS 2.6)

1. **Open** `https://localhost` (compose) or the cluster address. The certificate is self-signed: accept the browser warning.
2. **Register** with a username, email and a password (8+ characters, 1 digit, 1 uppercase letter), then sign in.
3. **Predict:** choose Store (1-10), Item (1-50), the target date, and the units sold on each of the 7 days before it (oldest first; the last box is yesterday). **Use sample** fills an example. Press **Predict demand**.
4. **Read the result:** each model card shows the predicted class (Low / Medium / High), confidence, the model's test accuracy and its latency. The banner shows the majority vote, or *No consensus* when all three disagree. High/Low means above/below what this item normally sells at this store - a restocking signal.
5. If a card shows an error, that model is temporarily unavailable; the other results are still valid.
6. **History** lists your last 50 predictions; **Export CSV** downloads them. **Models** shows algorithm, version, accuracy and macro-F1 of each model.
7. **Admins** also see **Admin**: service health (refreshes every 30 s), enable/disable users, recent audit events.

_Screenshots: add them to `docs/img/` and reference them here (US-29.1)._
API reference: `docs/openapi.json` (also served at `/api/v1/docs`).
