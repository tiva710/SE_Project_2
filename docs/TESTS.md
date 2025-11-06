# 🧪 Testing & Continuous Integration

[![Frontend CI](https://github.com/tiva710/SE_Project_2/actions/workflows/frontend-tests.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/frontend-tests.yml)
[![Backend CI](https://github.com/tiva710/SE_Project_2/actions/workflows/main.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/main.yml)
[![Lint & Style Check](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml/badge.svg)](https://github.com/tiva710/SE_Project_2/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🧭 Overview

This project employs **GitHub Actions** for automated testing, linting, and build verification across both the **frontend** (React) and **backend** (FastAPI).  
All checks are designed to ensure code quality, consistent formatting, and proper dependency resolution.

At present, there are **no manual test suites** (such as Jest or Pytest), but all CI workflows function as automated quality gates for each commit and pull request.

---

## ⚙️ GitHub Actions Test Suites

| Workflow | Description | Location | Trigger |
|-----------|--------------|-----------|----------|
| **Frontend CI** | Installs dependencies, , runs `npm test`, and ensures the React app builds successfully. | [`.github/workflows/frontend.yml`](.github/workflows/frontend.yml) | On push and pull request |
| **Backend CI** | Runs all backend unit tests via `pytest` and uploads coverage reports to Codecov. | [`.github/workflows/backend.yml`](.github/workflows/backend.yml) | On push and pull request |
| **Lint & Style Check** | Enforces strict code standards using ESLint and Stylelint with `--max-warnings=0`. | [`.github/workflows/lint.yml`](.github/workflows/lint.yml) | On push and pull request |


---

## 💻 Running Tests Locally

Although GitHub Actions runs automatically on push or PR, you can also verify locally before committing.

### Manually running Frontend tests

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run linter
npm run lint

#Run formatter (prettier)
npm run format

# Run build check
npm run build

#Run tests w/coverage
npm test
```
- This will output a /coverage directory (ignored via .gitignore)
### Manually running Backend tests
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run backend test suite with coverage
pytest --cov=. --cov-report html --cov-report term
```
- A coverage report will be generated in: /backend/htmlcov/
- You can open ```htmlcov/index.html``` in your browser to view detailed test coverage.

### Code Coverage Reporting (Codecov) 
[![codecov](https://codecov.io/gh/tiva710/SE_Project_2/branch/main/graph/badge.svg)](https://app.codecov.io/gh/tiva710/SE_Project_2)

Backend coverage reports are automatically uploaded to [Codecov]("https://app.codecov.io/gh/tiva710/SE_Project_2/new") through GitHub Actions.

The upload step is defined in the backend workflow: 
```bash
- name: Upload coverage report to Codecov
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: backend/coverage.xml
    fail_ci_if_error: true
```
### Manual CI Execution
Although CI triggers on each push and PR, you can also manually run workflows from the GitHub Actions tab: 
1. Go to Actions → Backend CI / Frontend CI / Lint & Style Check
2. Click “Run workflow”
3. Select the branch you wish to test
4. Press Run workflow

This is useful for re-running tests after dependency updates or environment changes without creating a new commit.

