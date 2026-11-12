# RDCP - Team Commit Assignment Pack
**Repository:** https://github.com/akshitsinghal244/SE-JackFruit-Problem-
**Generated:** 28 Oct 2026 | **For:** Team Pacman (4 members)
**Sprints:** 2 (catch-up run: Wed 28 Oct → Fri 30 Oct) | **Total:** 30 stories, 88 SP

---

## 📦 QUICK START FOR EACH MEMBER

| Member | Your Stories | Your Paths | Reviewer |
|--------|--------------|------------|----------|
| **Aayushman** (PES1UG24AM006) | US-01,11,12,13,14,18,24,25,29,30 | `client/`, `.github/`, `docs/`, root | Akshit |
| **Arvind** (PES1UG24AM052) | US-08,09,10,17,19,20,21 | `gateway/`, `client/src/pages/History.jsx`, `client/src/pages/Admin.jsx` | Aayushman |
| **Akhil** (PES1UG24AM023) | US-04,05,06,15,22,23,28 | `services/`, `nginx/`, `loadtest/`, `scripts/` | Aayushman |
| **Akshit** (PES1UG24AM027) | US-02,03,07,16,26,27 | `services/qml_service/`, `.github/workflows/`, `docker-compose*.yml`, `k8s/`, `Dockerfile*` | Aayushman |

> **Rule:** Only `git add <your-files>`. Never `git add -A`. Your reviewer is a repo owner (Aayushman or Akshit) who is NOT you.

---

## 🔴 CRITICAL RULES (READ FIRST)

1. **Branch:** `feature/RDCP-<n>-<slug>` (e.g., `feature/RDCP-10-ci-pipeline`)
2. **Commit:** `RDCP-<n> US-xx.y <short description>` (e.g., `RDCP-10 US-02.1 Write ci.yml with matrix`)
3. **PR Title:** `RDCP-<n> <Story Title>` (e.g., `RDCP-10 CI pipeline with GitHub Actions`)
4. **Move Jira card** at each step: To Do → In Progress → In Review → Done (IMMEDIATELY on merge)
5. **Screenshot burndown** at every checkpoint (10 total)
6. **No secrets** in commits — use `.env.example` + GitHub Secrets
7. **Freeze main** at end: `gh api -X PUT repos/akshitsinghal244/SE-JackFruit-Problem-/branches/main/protection -f lock_branch=true`

---

## 📅 CHECKPOINT SCHEDULE (MANDATORY 10-min standups)

| Sprint | CP | Date/Time | Target Remaining SP |
|--------|----|-----------|---------------------|
| **S1** | CP1 | Wed 28 Oct 14:00 | 39 |
| **S1** | CP2 | Wed 28 Oct 19:00 | 25 |
| **S1** | CP3 | Wed 28 Oct 23:00 | 16 |
| **S1** | CP4 | Thu 29 Oct 08:00 | 6 |
| **S1** | CP5 | Thu 29 Oct 12:00 | **0** (complete S1, tag v0.1.0) |
| **S2** | CP1 | Thu 29 Oct 19:00 | 39 |
| **S2** | CP2 | Thu 29 Oct 23:00 | 28 |
| **S2** | CP3 | Fri 30 Oct 10:00 | 17 |
| **S2** | CP4 | Fri 30 Oct 14:00 | 8 |
| **S2** | CP5 | Fri 30 Oct 17:00 | **0** (tag v1.0.0, freeze main, complete S2) |

---

## 🔄 DAILY WORKFLOW (COPY-PASTE FOR EVERY STORY)

```bash
# 1. START STORY
git switch main && git pull --ff-only origin main
git switch -c feature/RDCP-<n>-<slug>
# Jira: To Do → In Progress

# 2. WORK + COMMIT PER SUB-TASK
git add <only-your-files>
git commit -m "RDCP-<n> US-xx.y <description>"
git push -u origin HEAD  # first push only
# Jira: Sub-task → Done

# 3. SYNC + LOCAL CHECKS
git fetch origin && git rebase origin/main
# Run lint + tests + docker build FOR YOUR COMPONENT ONLY
git push --force-with-lease

# 4. OPEN PR
gh pr create --base main --title "RDCP-<n> <Story Title>" --body-file .github/pull_request_template.md
# Jira: In Progress → In Review

# 5. REVIEW (assigned repo owner)
gh pr checkout <num>
gh pr checks <num> --watch  # wait for GREEN
gh pr review <num> --approve --body "AC checked"

# 6. MERGE
gh pr merge <num> --squash --delete-branch
# Jira: In Review → Done (IMMEDIATELY)
git switch main && git pull --ff-only

# 7. CHECK BURNDOWN
# Refresh Jira — should drop by story's points
```

---

## 👤 AAYUSHMAN SINGH (PES1UG24AM006) — @aayushman-gh
**Role:** Frontend, Jira/Scrum Admin, Release & Docs, CD | **Repo Owner** | **Reviews:** Akhil, Arvind, Akshit

### SPRINT 1 (10 SP)

#### US-01 (RDCP-9, 2 SP) — Target: CP1 Wed 14:00 | Branch: `feature/RDCP-9-governance`
```bash
# US-01.1: Create repo + skeleton (run ONCE)
gh repo create akshitsinghal244/SE-JackFruit-Problem- --public --clone
cd SE-JackFruit-Problem-
mkdir -p client gateway services/ml services/dl services/qml k8s docs .github/workflows
touch client/.gitkeep gateway/.gitkeep services/ml/.gitkeep services/dl/.gitkeep services/qml/.gitkeep k8s/.gitkeep docs/.gitkeep .github/workflows/.gitkeep
cat > README.md << 'EOF'
# RDCP - Retail Demand Category Predictor
Three-tier system: web client (React) -> FastAPI gateway -> ML/DL/QML microservices
EOF
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.so
.env
.venv/
venv/
*.pkl
*.joblib
data/
certs/
# Node
node_modules/
dist/
build/
# OS
.DS_Store
Thumbs.db
# IDE
.vscode/
.idea/
EOF
git add README.md .gitignore client/.gitkeep gateway/.gitkeep services/ml/.gitkeep services/dl/.gitkeep services/qml/.gitkeep k8s/.gitkeep docs/.gitkeep .github/workflows/.gitkeep
git commit -m "RDCP-9 US-01.1 monorepo skeleton"
git push origin main

# US-01.2: Branch protection + PR template + CODEOWNERS
git switch -c feature/RDCP-9-governance
cat > .github/pull_request_template.md << 'EOF'
## Jira Key
RDCP-<n>

## What changed
-

## Test evidence
- [ ] Lint passes
- [ ] Tests pass
- [ ] Docker builds

## Checklist
- [ ] No secrets committed
- [ ] Branching convention followed
EOF
cat > .github/CODEOWNERS << 'EOF'
* @aayushman-gh @akshit-gh
EOF
git add .github/pull_request_template.md .github/CODEOWNERS
git commit -m "RDCP-9 US-01.2 branch protection PR template CODEOWNERS"
git push -u origin HEAD
gh pr create --base main --title "RDCP-9 Repo, branching & Jira-GitHub link" --body-file .github/pull_request_template.md
# Akshit reviews & merges

# US-01.3: CONTRIBUTING.md
git switch -c feature/RDCP-9-contributing
cat > CONTRIBUTING.md << 'EOF'
# Contributing to RDCP
## Branch naming: feature/RDCP-<n>-<slug>
## Commit message: RDCP-<n> US-xx.y <description>
## PR title: RDCP-<n> <Story Title>
## Review rule: PR raised by assignee, reviewed & merged by repo owner (Aayushman or Akshit)
EOF
git add CONTRIBUTING.md
git commit -m "RDCP-9 US-01.3 CONTRIBUTING.md"
git push -u origin HEAD
gh pr create --base main --title "RDCP-9 CONTRIBUTING.md" --body-file .github/pull_request_template.md
# Akshit reviews & merges

# US-01.4: GitHub for Jira link test
git switch -c feature/RDCP-9-jira-link-test
git commit --allow-empty -m "RDCP-9 test link"
git push -u origin HEAD
# Verify in Jira RDCP-9 Development panel (screenshot)
```

#### US-11 (RDCP-19, 3 SP) — Target: CP2 Wed 19:00 | Branch: `feature/RDCP-19-react-scaffold`
```bash
git switch -c feature/RDCP-19-react-scaffold
cd client
npm create vite@latest . -- --template react
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install recharts axios react-router-dom
# Edit: tailwind.config.js, src/index.css (@tailwind directives)
mkdir -p src/pages src/components src/context src/api
# Create: src/pages/Login.jsx, Predict.jsx, History.jsx, Models.jsx, Admin.jsx
# Create: src/components/Layout.jsx, src/context/auth.jsx, src/api.js
git add package.json package-lock.json tailwind.config.js postcss.config.js src/index.css src/main.jsx src/App.jsx src/pages/Login.jsx src/pages/Predict.jsx src/pages/History.jsx src/pages/Models.jsx src/pages/Admin.jsx src/components/Layout.jsx src/context/auth.jsx src/api.js
git commit -m "RDCP-19 US-11.1 US-11.2 US-11.3 US-11.4 React scaffold auth pages"
git push -u origin HEAD
gh pr create --base main --title "RDCP-19 React scaffold + login/register pages" --body-file ../.github/pull_request_template.md
# Akshit reviews & merges
```

#### US-12 (RDCP-20, 2 SP) — Target: CP4 Thu 08:00 | Branch: `feature/RDCP-20-input-form`
```bash
git switch -c feature/RDCP-20-input-form
cd client
# Edit: src/pages/Predict.jsx (form, validation, field errors, API wiring)
git add src/pages/Predict.jsx
git commit -m "RDCP-20 US-12.1 US-12.2 US-12.3 prediction form validation API wiring"
git push -u origin HEAD
gh pr create --base main --title "RDCP-20 Prediction input form with client-side validation" --body-file ../.github/pull_request_template.md
# Akshit reviews & merges
```

#### US-13 (RDCP-21, 2 SP) — Target: CP5 Thu 12:00 | Branch: `feature/RDCP-21-result-cards`
```bash
git switch -c feature/RDCP-21-result-cards
cd client
# Create: src/components/ModelCard.jsx, src/components/Charts.jsx
# Edit: src/pages/Predict.jsx (render results, consensus banner)
git add src/components/ModelCard.jsx src/components/Charts.jsx src/pages/Predict.jsx
git commit -m "RDCP-21 US-13.1 US-13.2 US-13.3 result cards badges error state"
git push -u origin HEAD
gh pr create --base main --title "RDCP-21 Result cards for ML DL QML" --body-file ../.github/pull_request_template.md
# Akshit reviews & merges
```

#### US-14 (RDCP-22, 1 SP) — Target: CP5 Thu 12:00 | Branch: `feature/RDCP-22-sprint1-demo`
```bash
git switch -c feature/RDCP-22-sprint1-demo
mkdir -p docs/demo
# Record ~1 min video → save as docs/demo/sprint1.mp4
git add docs/demo/sprint1.mp4
git commit -m "RDCP-22 US-14.1 US-14.2 sprint1 demo video"
git switch main && git pull --ff-only
git tag -a v0.1.0 -m "Sprint 1 demo"
git push origin v0.1.0

# US-14.3: deviations.md
cat > docs/deviations.md << 'EOF'
# Deviations from SRS/SAD/STP
D1: Using Jira instead of GitHub Projects (teacher approved)
D2: Compressed sprint dates (catch-up run Wed 28 Oct - Fri 30 Oct instead of Oct 19-30)
D3: STP file not provided - acceptance criteria from SRS/SAD
EOF
git add docs/deviations.md
git commit -m "RDCP-22 US-14.3 deviations.md"
git push origin main
# US-14.4: Sprint review + retro notes in Jira (manual)
```

### SPRINT 2 (13 SP)

#### US-18 (RDCP-26, 3 SP) — Target: CP2 Thu 23:00 | Branch: `feature/RDCP-26-consensus-charts`
```bash
git switch -c feature/RDCP-26-consensus-charts
# US-18.1: Consensus logic (with Arvind) - gateway/app/services.py
# US-18.2: /models/info endpoint (with Arvind) - gateway/app/routers/models.py
# US-18.3: Charts - client/src/components/Charts.jsx
# US-18.4: Consensus banner + info panel - client/src/pages/Predict.jsx, client/src/components/ModelCard.jsx
git add gateway/app/services.py gateway/app/routers/models.py client/src/components/Charts.jsx client/src/pages/Predict.jsx client/src/components/ModelCard.jsx
git commit -m "RDCP-26 US-18.1 US-18.2 US-18.3 US-18.4 consensus charts model-info panel"
git push -u origin HEAD
gh pr create --base main --title "RDCP-26 Consensus, comparison charts & model-info panel" --body-file .github/pull_request_template.md
# Akshit reviews & merges
```

#### US-24 (RDCP-32, 3 SP) — Target: CP4 Fri 14:00 | Branch: `feature/RDCP-32-responsive-ui`
```bash
git switch -c feature/RDCP-32-responsive-ui
cd client
# Edit: src/index.css (dark mode), src/components/Layout.jsx (theme toggle), src/pages/*.jsx (responsive grids)
# US-24.2: Screenshot browsers at 360px, 768px, 1920px → docs/img/
# US-24.3: Fill docs/usability.md (5-user trial, ≥4/5 within 60s)
git add src/index.css src/components/Layout.jsx src/pages/*.jsx src/components/*.jsx docs/usability.md docs/img/
git commit -m "RDCP-32 US-24.1 US-24.2 US-24.3 responsive dark mode browser usability trial"
git push -u origin HEAD
gh pr create --base main --title "RDCP-32 Responsive UI, dark mode & browser/usability checks" --body-file .github/pull_request_template.md
# Akshit reviews & merges
```

#### US-25 (RDCP-33, 2 SP) — Target: CP1 Thu 19:00 | Branch: `feature/RDCP-33-cd-dockerhub`
```bash
git switch -c feature/RDCP-33-cd-dockerhub
# US-25.1: Create DockerHub repos + token (manual)
# US-25.2: Add GitHub Secrets
gh secret set DOCKERHUB_USERNAME --body "<dockerhub-username>"
gh secret set DOCKERHUB_TOKEN --body "<dockerhub-token>"

# US-25.3: CD workflow
cat > .github/workflows/cd.yml << 'EOF'
name: CD
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]
  push:
    tags: ['v*']
jobs:
  build-and-push:
    if: ${{ github.event.workflow_run.conclusion == 'success' || github.event_name == 'push' }}
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [client, gateway, ml, dl, qml]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/rdcp-${{ matrix.service }}:${{ github.sha }}
            ${{ secrets.DOCKERHUB_USERNAME }}/rdcp-${{ matrix.service }}:latest
EOF
git add .github/workflows/cd.yml
git commit -m "RDCP-33 US-25.1 US-25.2 US-25.3 US-25.4 CD workflow DockerHub push verify"
git push -u origin HEAD
gh pr create --base main --title "RDCP-33 CD: build & push images to DockerHub" --body-file .github/pull_request_template.md
# Akshit reviews & merges
```

#### US-29 (RDCP-37, 3 SP) — Target: CP5 Fri 17:00 | Branch: `feature/RDCP-37-docs`
```bash
git switch -c feature/RDCP-37-docs
# US-29.1: Update README.md
# US-29.2: Export OpenAPI
curl -k https://localhost/api/v1/openapi.json > docs/openapi.json
# US-29.3: Update docs/deviations.md
# US-29.4: Architecture + accuracy table (docs/architecture.md, docs/models.md)
git add README.md docs/openapi.json docs/deviations.md docs/architecture.md docs/models.md
git commit -m "RDCP-37 US-29.1 US-29.2 US-29.3 US-29.4 README OpenAPI deviations architecture models"
git push -u origin HEAD
gh pr create --base main --title "RDCP-37 Documentation & deviation log" --body-file .github/pull_request_template.md
# Akshit reviews & merges
```

#### US-30 (RDCP-38, 2 SP) — Target: CP5 Fri 17:00 | Branch: `feature/RDCP-38-release`
```bash
git switch -c feature/RDCP-38-release
mkdir -p docs/demo
# Record ~2 min video → docs/demo/sprint2.mp4
git add docs/demo/sprint2.mp4
git commit -m "RDCP-38 US-30.1 US-30.2 demo video"
git switch main && git pull --ff-only
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
gh release create v1.0.0 --title "RDCP v1.0.0" --notes "Final release"
gh api -X PUT repos/akshitsinghal244/SE-JackFruit-Problem-/branches/main/protection -f lock_branch=true
# US-30.4: Complete Sprint 2 in Jira (manual)
```

---

## 👤 ARVIND AJAY BHARADWAJ (PES1UG24AM052) — @arvind-gh
**Role:** Gateway (FastAPI), Auth, Security, History/Export | **Reviewed by:** Aayushman

### SPRINT 1 (11 SP)

#### US-08 (RDCP-16, 5 SP) — Target: CP2 Wed 19:00 | Branch: `feature/RDCP-16-gateway-skeleton`
```bash
git switch -c feature/RDCP-16-gateway-skeleton
cd gateway
mkdir -p app/routers
# Create/edit: app/main.py, app/config.py, app/models.py, app/schemas.py, app/db.py, app/deps.py, app/errors.py, app/__init__.py
# tests/test_api.py
git add app/main.py app/config.py app/models.py app/schemas.py app/db.py app/deps.py app/errors.py app/__init__.py tests/test_api.py
git commit -m "RDCP-16 US-08.1 US-08.2 US-08.3 US-08.4 US-08.5 gateway skeleton DB validation errors"
git push -u origin HEAD
gh pr create --base main --title "RDCP-16 Gateway skeleton DB models validation & error format" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-09 (RDCP-17, 3 SP) — Target: CP3 Wed 23:00 | Branch: `feature/RDCP-17-auth`
```bash
git switch -c feature/RDCP-17-auth
cd gateway
# Create/edit: app/security.py, app/routers/auth.py, tests/test_auth.py
git add app/security.py app/routers/auth.py tests/test_auth.py
git commit -m "RDCP-17 US-09.1 US-09.2 US-09.3 US-09.4 US-09.5 auth register login JWT bcrypt"
git push -u origin HEAD
gh pr create --base main --title "RDCP-17 Register & login (bcrypt, JWT 15 min)" --body-file ../.github/pull_request_template.md
# Akshit reviews & merges
```

#### US-10 (RDCP-18, 3 SP) — Target: CP5 Thu 12:00 | Branch: `feature/RDCP-18-orchestrator`
```bash
git switch -c feature/RDCP-18-orchestrator
cd gateway
# Create/edit: app/services.py, app/routers/predict.py, tests/test_orchestrator.py
git add app/services.py app/routers/predict.py tests/test_orchestrator.py
git commit -m "RDCP-18 US-10.1 US-10.2 US-10.3 US-10.4 US-10.5 orchestrator scatter-gather timeout"
git push -u origin HEAD
gh pr create --base main --title "RDCP-18 Prediction orchestrator (parallel calls, 8 s timeout)" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

### SPRINT 2 (12 SP)

#### US-17 (RDCP-25, 3 SP) — Target: CP1 Thu 19:00 | Branch: `feature/RDCP-25-resilience`
```bash
git switch -c feature/RDCP-25-resilience
cd gateway
# Edit: app/services.py (circuit breaker, failure classification, 207/502/504, history_saved)
# tests/test_resilience.py
git add app/services.py tests/test_resilience.py
git commit -m "RDCP-25 US-17.1 US-17.2 US-17.3 US-17.4 US-17.5 resilience circuit breaker partial results"
git push -u origin HEAD
gh pr create --base main --title "RDCP-25 Resilience: partial results, circuit breaker, all-down handling" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-19 (RDCP-27, 3 SP) — Target: CP3 Fri 10:00 | Branch: `feature/RDCP-27-history-export`
```bash
git switch -c feature/RDCP-27-history-export
cd gateway
# Edit: app/routers/predict.py (persist), app/routers/history.py (endpoints)
cd ../client
# Edit: src/pages/History.jsx (table + export button)
git add gateway/app/routers/predict.py gateway/app/routers/history.py gateway/tests/test_history.py client/src/pages/History.jsx
git commit -m "RDCP-27 US-19.1 US-19.2 US-19.3 US-19.4 US-19.5 history persist endpoint CSV export page"
git push -u origin HEAD
gh pr create --base main --title "RDCP-27 Prediction history (latest 50) & CSV export" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-20 (RDCP-28, 3 SP) — Target: CP2 Thu 23:00 | Branch: `feature/RDCP-28-auth-hardening`
```bash
git switch -c feature/RDCP-28-auth-hardening
cd gateway
# Edit: app/deps.py (RBAC), app/security.py (lockout), app/ratelimit.py (Redis rate limiter), app/main.py (middleware)
# tests/test_auth_hardening.py
git add app/deps.py app/security.py app/ratelimit.py app/main.py tests/test_auth_hardening.py
git commit -m "RDCP-28 US-20.1 US-20.2 US-20.3 US-20.4 RBAC lockout rate limit tests"
git push -u origin HEAD
gh pr create --base main --title "RDCP-28 Auth hardening: RBAC, lockout, rate limiting" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-21 (RDCP-29, 3 SP) — Target: CP4 Fri 14:00 | Branch: `feature/RDCP-29-audit-headers`
```bash
git switch -c feature/RDCP-29-audit-headers
cd gateway
# Edit: app/main.py (audit hooks, CORS, security headers, purge job), app/models.py (AuditLog)
# Edit: app/routers/auth.py, app/routers/predict.py, app/routers/history.py, app/routers/admin.py (audit calls)
# tests/test_audit_headers.py
git add app/main.py app/models.py app/routers/auth.py app/routers/predict.py app/routers/history.py app/routers/admin.py tests/test_audit_headers.py
git commit -m "RDCP-29 US-21.1 US-21.2 US-21.3 US-21.4 audit log CORS headers API key tests"
git push -u origin HEAD
gh pr create --base main --title "RDCP-29 Audit log, CORS/headers & service API key" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

---

## 👤 AKHIL MANGIPUDI (PES1UG24AM023) — @akhil-gh
**Role:** Data + ML/DL Services, Admin, TLS, Testing/Perf | **Reviewed by:** Aayushman

### SPRINT 1 (9 SP)

#### US-04 (RDCP-12, 3 SP) — Target: CP2 Wed 19:00 | Branch: `feature/RDCP-12-dataset-labels`
```bash
git switch -c feature/RDCP-12-dataset-labels
mkdir -p services/scripts services/common/data services/tests
# US-04.1: Download script
cat > services/scripts/download_data.py << 'EOF'
import os, kaggle
os.makedirs("data", exist_ok=True)
kaggle.api.authenticate()
kaggle.api.competition_download_files("demand-forecasting-kernels-only", path="data", unzip=True)
EOF
# US-04.2: Labels + thresholds
cat > services/common/data/labels.py << 'EOF'
# Load train.csv, compute 33rd/66th percentile per store-item on training data only, save thresholds.json
EOF
# US-04.3: Time split (last 3 months = test)
# US-04.4: Features + tests
cat > services/common/features.py << 'EOF'
def build_features(df): ...
def make_tabular_row(store_id, item_id, date, prev_sales): ...
EOF
cat > services/tests/test_features.py << 'EOF'
import pytest
from common.features import make_tabular_row
def test_features_shape(): ...
EOF
git add services/scripts/download_data.py services/common/data/labels.py services/common/features.py services/tests/test_features.py
git commit -m "RDCP-12 US-04.1 US-04.2 US-04.3 US-04.4 dataset labels thresholds features tests"
git push -u origin HEAD
gh pr create --base main --title "RDCP-12 Dataset preparation & demand-category labels" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-05 (RDCP-13, 3 SP) — Target: CP3 Wed 23:00 | Branch: `feature/RDCP-13-ml-service`
```bash
git switch -c feature/RDCP-13-ml-service
cd services/ml_service
# Create/edit: train.py, predictor.py, app.py, Dockerfile, tests/test_ml_contract.py
# Train: python train.py --data ../../data/train.csv --out ../../services/artifacts/ml
git add train.py predictor.py app.py Dockerfile tests/test_ml_contract.py
git commit -m "RDCP-13 US-05.1 US-05.2 US-05.3 US-05.4 ML service train FastAPI contract tests"
git push -u origin HEAD
gh pr create --base main --title "RDCP-13 ML microservice (Random Forest / XGBoost)" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-06 (RDCP-14, 3 SP) — Target: CP4 Thu 08:00 | Branch: `feature/RDCP-14-dl-service`
```bash
git switch -c feature/RDCP-14-dl-service
cd services/dl_service
# Create/edit: train.py, predictor.py, app.py, Dockerfile, tests/test_dl_contract.py
# Train: python train.py --data ../../data/train.csv --out ../../services/artifacts/dl --arch mlp
git add train.py predictor.py app.py Dockerfile tests/test_dl_contract.py
git commit -m "RDCP-14 US-06.1 US-06.2 US-06.3 US-06.4 DL service MLP FastAPI contract tests"
git push -u origin HEAD
gh pr create --base main --title "RDCP-14 DL microservice (MLP, LSTM stretch)" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

### SPRINT 2 (11 SP)

#### US-15 (RDCP-23, 3 SP) — Target: CP1 Thu 19:00 | Branch: `feature/RDCP-23-ml-dl-eval`
```bash
git switch -c feature/RDCP-23-ml-dl-eval
# US-15.1: Tune ML
cd services/ml_service
python train.py --tune --data ../../data/train.csv --out ../../services/artifacts/ml
# US-15.1: Tune DL
cd ../dl_service
python train.py --tune --data ../../data/train.csv --out ../../services/artifacts/dl
# US-15.2: Evaluate on held-out (record accuracy + macro-F1)
# US-15.3: Update metadata (artifacts/ml/metadata.json, artifacts/dl/metadata.json)
# US-15.4: Generate docs/models.md
python scripts/make_models_md.py
git add services/ml_service/train.py services/dl_service/train.py services/artifacts/ml/metadata.json services/artifacts/dl/metadata.json docs/models.md
git commit -m "RDCP-23 US-15.1 US-15.2 US-15.3 US-15.4 ML DL tuning evaluation metadata models.md"
git push -u origin HEAD
gh pr create --base main --title "RDCP-23 ML & DL evaluation, tuning and model metadata" --body-file ../.github/pull_request_template.md
# Akshit reviews & merges
```

#### US-22 (RDCP-30, 3 SP) — Target: CP3 Fri 10:00 | Branch: `feature/RDCP-30-admin`
```bash
git switch -c feature/RDCP-30-admin
cd gateway
# Edit: app/services.py (health_loop), app/routers/admin.py (health + users endpoints)
cd ../client
# Edit: src/pages/Admin.jsx (Health + Users pages)
git add gateway/app/services.py gateway/app/routers/admin.py gateway/tests/test_admin.py client/src/pages/Admin.jsx
git commit -m "RDCP-30 US-22.1 US-22.2 US-22.3 US-22.4 admin health poller user management tests"
git push -u origin HEAD
gh pr create --base main --title "RDCP-30 Admin: service health & user management" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-23 (RDCP-31, 2 SP) — Target: CP2 Thu 23:00 | Branch: `feature/RDCP-31-nginx-tls`
```bash
git switch -c feature/RDCP-31-nginx-tls
mkdir -p certs nginx
# US-23.1: Generate cert
./scripts/gen-cert.sh  # Creates certs/rdcp.crt, certs/rdcp.key (gitignored)
# US-23.2: nginx.conf
cat > nginx/edge.conf << 'EOF'
server { listen 80; return 301 https://$host$request_uri; }
server {
    listen 443 ssl http2;
    ssl_certificate /certs/rdcp.crt;
    ssl_certificate_key /certs/rdcp.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    add_header Strict-Transport-Security "max-age=31536000" always;
    location / { proxy_pass http://client:8080; }
    location /api/ { proxy_pass http://gateway:8000; }
}
EOF
# US-23.3: Add nginx to docker-compose.yml (public network)
git add nginx/edge.conf docker-compose.yml
git commit -m "RDCP-31 US-23.1 US-23.2 US-23.3 US-23.4 nginx TLS cert HSTS proxy smoke test"
git push -u origin HEAD
gh pr create --base main --title "RDCP-31 Nginx TLS termination & HTTPS" --body-file ../.github/pull_request_template.md
# Arvind reviews & merges
```

#### US-28 (RDCP-36, 3 SP) — Target: CP5 Fri 17:00 | Branch: `feature/RDCP-36-coverage-loadtest`
```bash
git switch -c feature/RDCP-36-coverage-loadtest
# US-28.1: Update CI for coverage (edit .github/workflows/ci.yml)
# US-28.2: Locust script
cat > loadtest/locustfile.py << 'EOF'
from locust import HttpUser, task, between
class RDCPUser(HttpUser):
    wait_time = between(1, 3)
    def on_start(self):
        self.client.post("/api/v1/auth/register", json={"username":"u","email":"u@test.com","password":"Pass123"})
        r = self.client.post("/api/v1/auth/login", json={"email":"u@test.com","password":"Pass123"})
        self.token = r.json()["access_token"]
    @task
    def predict(self):
        self.client.post("/api/v1/predict", json={"store_id":3,"item_id":12,"date":"2017-09-15","prev_sales":[41,38,45,50,47,39,44]}, headers={"Authorization":f"Bearer {self.token}"})
EOF
# US-28.3: Run load test (manual, results to docs/perf/)
# US-28.4: Fix hot spots or add deviation
git add .github/workflows/ci.yml loadtest/locustfile.py docs/perf/
git commit -m "RDCP-36 US-28.1 US-28.2 US-28.3 US-28.4 coverage 70% locust loadtest perf results"
git push -u origin HEAD
gh pr create --base main --title "RDCP-36 Test coverage >= 70% & load test (20 users)" --body-file ../.github/pull_request_template.md
# Arvind reviews & merges
```

---

## 👤 AKSHIT SINGHAL (PES1UG24AM027) — @akshit-gh
**Role:** QML Service, CI/CD, Docker, Kubernetes | **Repo Owner** | **Reviews:** Aayushman, Arvind

### SPRINT 1 (11 SP)

#### US-02 (RDCP-10, 3 SP) — Target: CP2 Wed 19:00 | Branch: `feature/RDCP-10-ci-pipeline`
```bash
git switch -c feature/RDCP-10-ci-pipeline
# US-02.1: CI workflow with matrix
cat > .github/workflows/ci.yml << 'EOF'
name: CI
on: { pull_request: {}, push: { branches: [main] } }
jobs:
  gateway:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: ./gateway } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5 { with: { python-version: "3.11" } }
      - run: pip install -r requirements-dev.txt
      - run: ruff check .
      - run: pytest --cov=app --cov-fail-under=70
  ml:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: ./services/ml_service } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5 { with: { python-version: "3.11" } }
      - run: pip install -r ../../requirements/dev.txt
      - run: ruff check .
      - run: pytest --cov=. --cov-fail-under=70
  dl:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: ./services/dl_service } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5 { with: { python-version: "3.11" } }
      - run: pip install -r ../../requirements/dev.txt
      - run: ruff check .
      - run: pytest --cov=. --cov-fail-under=70
  qml:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: ./services/qml_service } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5 { with: { python-version: "3.11" } }
      - run: pip install -r ../../requirements/dev.txt
      - run: ruff check .
      - run: pytest --cov=. --cov-fail-under=70
  client:
    runs-on: ubuntu-latest
    if: hashFiles('client/package.json') != ''
    defaults: { run: { working-directory: ./client } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4 { with: { node-version: "20" } }
      - run: npm ci && npm run lint && npm run build
  docker:
    runs-on: ubuntu-latest
    needs: [gateway, ml, dl, qml, client]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with: { context: ./gateway, push: false, tags: rdcp-gateway:test, cache-from: type=gha, cache-to: type=gha,mode=max }
      - uses: docker/build-push-action@v5
        with: { context: ./client, push: false, tags: rdcp-client:test, cache-from: type=gha, cache-to: type=gha,mode=max }
      - uses: docker/build-push-action@v5
        with: { context: ./services/ml_service, push: false, tags: rdcp-ml:test, cache-from: type=gha, cache-to: type=gha,mode=max }
      - uses: docker/build-push-action@v5
        with: { context: ./services/dl_service, push: false, tags: rdcp-dl:test, cache-from: type=gha, cache-to: type=gha,mode=max }
      - uses: docker/build-push-action@v5
        with: { context: ./services/qml_service, push: false, tags: rdcp-qml:test, cache-from: type=gha, cache-to: type=gha,mode=max }
EOF
# US-02.5: Mark checks required (after merge)
# gh api -X PUT repos/akshitsinghal244/SE-JackFruit-Problem-/branches/main/protection --input protection.json
git add .github/workflows/ci.yml
git commit -m "RDCP-10 US-02.1 US-02.2 US-02.3 US-02.4 US-02.5 CI pipeline matrix lint test docker buildx"
git push -u origin HEAD
gh pr create --base main --title "RDCP-10 CI pipeline with GitHub Actions" --body-file .github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-03 (RDCP-11, 3 SP) — Target: CP3 Wed 23:00 | Branch: `feature/RDCP-11-dockerise`
```bash
git switch -c feature/RDCP-11-dockerise
# US-03.1: Dockerfiles
# client/Dockerfile, gateway/Dockerfile, services/ml_service/Dockerfile, services/dl_service/Dockerfile, services/qml_service/Dockerfile
# US-03.2: docker-compose.yml
# US-03.3: Postgres service + volume
# US-03.4: .env.example + README run section
cat > .env.example << 'EOF'
POSTGRES_PASSWORD=changeme
JWT_SECRET=changeme-min-32-chars
SERVICE_API_KEY=changeme
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=AdminPass123
CORS_ORIGINS=https://localhost
EOF
git add client/Dockerfile gateway/Dockerfile services/ml_service/Dockerfile services/dl_service/Dockerfile services/qml_service/Dockerfile docker-compose.yml .env.example README.md
git commit -m "RDCP-11 US-03.1 US-03.2 US-03.3 US-03.4 Dockerfiles compose postgres env README"
git push -u origin HEAD
gh pr create --base main --title "RDCP-11 Dockerise all components + docker compose" --body-file .github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-07 (RDCP-15, 5 SP) — Target: CP4 Thu 08:00 | Branch: `feature/RDCP-15-qml-service`
```bash
git switch -c feature/RDCP-15-qml-service
cd services/qml_service
# Create/edit: train.py, predictor.py, app.py, Dockerfile, tests/test_qml_contract.py
# Train: python train.py --data ../../data/train.csv --out ../../services/artifacts/qml --qubits 4
git add train.py predictor.py app.py Dockerfile tests/test_qml_contract.py
git commit -m "RDCP-15 US-07.1 US-07.2 US-07.3 US-07.4 US-07.5 QML service VQC PennyLane FastAPI latency"
git push -u origin HEAD
gh pr create --base main --title "RDCP-15 QML microservice v1 (VQC/QNN on simulator)" --body-file ../.github/pull_request_template.md
# Aayushman/Akshit reviews & merges
```

### SPRINT 2 (11 SP)

#### US-16 (RDCP-24, 3 SP) — Target: CP2 Thu 23:00 | Branch: `feature/RDCP-24-qml-tuning`
```bash
git switch -c feature/RDCP-24-qml-tuning
cd services/qml_service
# US-16.1: Tune (run sweeps manually)
# python train.py --qubits 4 --ansatz-depth 2 ...
# US-16.2: Evaluate on held-out (target ≥60%)
# US-16.3: Measure p95 latency
# US-16.4: Update metadata + docs/models.md
git add train.py predictor.py services/artifacts/qml/metadata.json docs/models.md
git commit -m "RDCP-24 US-16.1 US-16.2 US-16.3 US-16.4 QML tuning ansatz latency metadata models.md"
git push -u origin HEAD
gh pr create --base main --title "RDCP-24 QML tuning, accuracy and latency" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-26 (RDCP-34, 5 SP) — Target: CP3 Fri 10:00 | Branch: `feature/RDCP-34-k8s-manifests`
```bash
git switch -c feature/RDCP-34-k8s-manifests
mkdir -p k8s/base k8s/overlays/mock
# US-26.1: Namespace, ConfigMap, Secret template
cat > k8s/base/namespace.yaml << 'EOF'
apiVersion: v1
kind: Namespace
metadata: { name: rdcp }
EOF
cat > k8s/base/config.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata: { name: rdcp-config, namespace: rdcp }
data: {}
EOF
cat > k8s/secret.example.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata: { name: rdcp-secrets, namespace: rdcp }
type: Opaque
stringData:
  POSTGRES_PASSWORD: ""
  JWT_SECRET: ""
  SERVICE_API_KEY: ""
  ADMIN_EMAIL: ""
  ADMIN_PASSWORD: ""
EOF
# US-26.2: Deployments + Services (client, gateway, ml, dl, qml)
# US-26.3: Postgres StatefulSet + PVC
# US-26.4: Ingress + NetworkPolicy
# US-26.5: CI dry-run step (add to .github/workflows/ci.yml)
git add k8s/base/namespace.yaml k8s/base/config.yaml k8s/secret.example.yaml k8s/base/*.yaml .github/workflows/ci.yml
git commit -m "RDCP-34 US-26.1 US-26.2 US-26.3 US-26.4 US-26.5 K8s manifests namespace deployments postgres ingress networkpolicy dry-run"
git push -u origin HEAD
gh pr create --base main --title "RDCP-34 Kubernetes manifests" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

#### US-27 (RDCP-35, 3 SP) — Target: CP4 Fri 14:00 | Branch: `feature/RDCP-35-k8s-deploy`
```bash
git switch -c feature/RDCP-35-k8s-deploy
# US-27.1: Deploy (manual, record in README)
# kind create cluster --name rdcp --config k8s/kind-cluster.yaml
# Install ingress-nginx
# kubectl apply -f k8s/base/namespace.yaml
# Create secret from secret.example.yaml
# kubectl apply -f k8s/
# US-27.2: Verify pods + E2E prediction
# US-27.3: Self-heal + scale demo
# US-27.4: Update README with K8s commands
git add README.md
git commit -m "RDCP-35 US-27.1 US-27.2 US-27.3 US-27.4 K8s deploy kind ingress self-heal scale README"
git push -u origin HEAD
gh pr create --base main --title "RDCP-35 Deploy to local cluster from DockerHub & smoke test" --body-file ../.github/pull_request_template.md
# Aayushman reviews & merges
```

---

## 📋 REVIEW ASSIGNMENTS

| Story | Author | Reviewer (Repo Owner) |
|-------|--------|----------------------|
| RDCP-9, 10, 11, 15 | Akshit | **Aayushman** |
| RDCP-16, 17, 18, 25, 27, 28, 29 | Arvind | **Aayushman** |
| RDCP-12, 13, 14, 23, 30, 31, 36 | Akhil | **Aayushman** |
| RDCP-19, 20, 21, 22, 24, 26, 32, 33, 34, 35, 37, 38 | Aayushman | **Akshit** |

---

## ✅ EVIDENCE CHECKLIST (FOR DEMO)

- [ ] Jira: Backlog with epics, both sprints (41 SP, 47 SP), issue links
- [ ] Jira: Sprint 1 & 2 board mid-sprint, final burndown, sprint report, velocity chart
- [ ] Jira: One issue with Development panel showing branch, PR, build
- [ ] GitHub: PR list (author ≠ reviewer), branch protection page, Actions runs (CI + CD, one red-then-green)
- [ ] DockerHub: Five `rdcp-*` repos with `:latest` and sha tags
- [ ] Terminal: `docker compose up`, `kubectl get pods,svc`, pod self-heal demo
- [ ] Repo: `docs/demo/sprint1.*`, `docs/demo/sprint2.*`, `docs/deviations.md` (with D2), tags `v0.1.0`, `v1.0.0`

---

## 📌 ALL BRANCHES QUICK REFERENCE

| Story | Key | Branch | Owner |
|-------|-----|--------|-------|
| US-01 | RDCP-9 | feature/RDCP-9-governance | Aayushman |
| US-02 | RDCP-10 | feature/RDCP-10-ci-pipeline | Akshit |
| US-03 | RDCP-11 | feature/RDCP-11-dockerise | Akshit |
| US-04 | RDCP-12 | feature/RDCP-12-dataset-labels | Akhil |
| US-05 | RDCP-13 | feature/RDCP-13-ml-service | Akhil |
| US-06 | RDCP-14 | feature/RDCP-14-dl-service | Akhil |
| US-07 | RDCP-15 | feature/RDCP-15-qml-service | Akshit |
| US-08 | RDCP-16 | feature/RDCP-16-gateway-skeleton | Arvind |
| US-09 | RDCP-17 | feature/RDCP-17-auth | Arvind |
| US-10 | RDCP-18 | feature/RDCP-18-orchestrator | Arvind |
| US-11 | RDCP-19 | feature/RDCP-19-react-scaffold | Aayushman |
| US-12 | RDCP-20 | feature/RDCP-20-input-form | Aayushman |
| US-13 | RDCP-21 | feature/RDCP-21-result-cards | Aayushman |
| US-14 | RDCP-22 | feature/RDCP-22-sprint1-demo | Aayushman |
| US-15 | RDCP-23 | feature/RDCP-23-ml-dl-eval | Akhil |
| US-16 | RDCP-24 | feature/RDCP-24-qml-tuning | Akshit |
| US-17 | RDCP-25 | feature/RDCP-25-resilience | Arvind |
| US-18 | RDCP-26 | feature/RDCP-26-consensus-charts | Aayushman |
| US-19 | RDCP-27 | feature/RDCP-27-history-export | Arvind |
| US-20 | RDCP-28 | feature/RDCP-28-auth-hardening | Arvind |
| US-21 | RDCP-29 | feature/RDCP-29-audit-headers | Arvind |
| US-22 | RDCP-30 | feature/RDCP-30-admin | Akhil |
| US-23 | RDCP-31 | feature/RDCP-31-nginx-tls | Akhil |
| US-24 | RDCP-32 | feature/RDCP-32-responsive-ui | Aayushman |
| US-25 | RDCP-33 | feature/RDCP-33-cd-dockerhub | Aayushman |
| US-26 | RDCP-34 | feature/RDCP-34-k8s-manifests | Akshit |
| US-27 | RDCP-35 | feature/RDCP-35-k8s-deploy | Akshit |
| US-28 | RDCP-36 | feature/RDCP-36-coverage-loadtest | Akhil |
| US-29 | RDCP-37 | feature/RDCP-37-docs | Aayushman |
| US-30 | RDCP-38 | feature/RDCP-38-release | Aayushman |

---

**File location:** `C:\Users\Lenovo\rdcp\TEAM_COMMIT_ASSIGNMENTS.md`  
**Share this file** with your team — each member extracts their section and follows the daily workflow.