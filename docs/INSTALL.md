# INSTALLATION GUIDE 

This document provides step-by-step instructions to install, configure, run, and verify **ReqTrace** (backend + frontend). Follow the sections below for local development on macOS / Linux or Windows.

---

## Prerequisites 

- Git (for cloning the repo)
- Python 3.11
- pip
- Node.js (>=18) and npm
- Optional: Docker (if you prefer containerized deployment)
- Recommended: an isolated Python virtual environment (venv)

  Ports used by default:
  - Backend (uvicorn/FastAPI): **8000**
  - Frontend (React + Vite): **5173**
 
---

## Project layout (important paths)

```bash
  /SE_Project_2
  /backend #Python API & services
  /frontend #React app
  /docs
  README.md
  .github/
```
  ---

## 1. Clone the repository

```bash
  git clone https://github.com/tiva710/SE_Project_2.git
  cd SE_Project_2
```

---

## 2. Backend - Local devolpment 
  Activate a virtual environment first to keep dependencies isolated. 

### MacOS/Linux
1. Create & activate virtual environment

```bash
  cd backend
  conda create -n se_project python=3.11 faiss-cpu -c conda-forge
  conda activate se_project
  pip install openai-whisper     
```

2. Install Python dependencies

```bash
  pip install --upgrade pip
  pip install -r requirements.txt
```

3. Update Neo4j credentials
- Navigate to /backend/app/services/neo4j_service.py

- Replace "URI" & "pwd" with correct credentials
```bash
  NEO4J_URI = "URI"
  NEO4J_USER = "neo4j" 
  NEO4J_PASS = "pwd"
```

4. Run the development server
```bash
  uvicorn app.main:app --reload
```

### Windows (Powershell) 
```bash
  cd backend
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1

  pip install
  pip install -r requirements.txt

  #Update Neo4j credentials in backend\app\services

  uvicorn main:app --reload 
```
---
## 3. Frontend - Local development 

### macOS/Linux/Windows (same commands) 
1. Install dependencies
```bash
  cd frontend
  npm install
```

2. Start development server
```bash
  npm run dev 
```
---

## 4. Running tests & generating coverage reports 
We recommend running tests locally before pushing. Do refer to [TESTS.md](TESTS.md) for instructions and information on coverage report generation. 

## 5. Common Troubleshooting 
Do refer to [SUPPORT.md](SUPPORT.md) for common errors (including installation errors), symptoms, solutions, and more on support resources :) 

## 6. Where to find more information 
- Full usage examples: [USAGE.md](USAGE.md)
- API reference: [API.md](API.md)
- Full documentation files in repository's Wiki
