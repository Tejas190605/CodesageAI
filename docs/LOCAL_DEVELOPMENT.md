# CodeSage AI — Local Development Guide

This guide provides step-by-step instructions for configuring and running **CodeSage AI** locally on Windows PowerShell and POSIX environments.

---

## System Requirements

- **Python**: 3.10+ (Recommended: 3.14)
- **Node.js**: 18.0+ (Recommended: 20.x or 22.x)
- **PostgreSQL**: 15+ (With `pgvector` extension enabled for vector search)
- **Redis**: 6.0+ (For background queue processing)
- **PowerShell**: 7.0+ or Windows PowerShell 5.1

---

## 1. Local Environment Setup

Clone the repository and enter the project directory:

```powershell
cd c:\Users\tejas\codesage-ai
```

### Backend Setup (PowerShell)

```powershell
cd backend

# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment
.\venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Copy Environment Files

```powershell
# In project root
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env.local
```

Edit `backend/.env` to configure your database connection and API keys:

```env
DATABASE_URL=sqlite:///./codesage.db
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
```

---

## 2. Database Migrations

Apply Alembic migrations to initialize the database schema:

```powershell
cd backend
.\venv\Scripts\python.exe -m alembic upgrade head
```

Verify current head:

```powershell
.\venv\Scripts\python.exe -m alembic heads
# Expected Output: 007_phase_5d_analytics_audit (head)
```

---

## 3. Running Applications Locally

### Start FastAPI Backend

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

FastAPI interactive documentation will be available at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Start Frontend Next.js Dashboard

Open a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Next.js Developer Dashboard will be available at `http://localhost:3000`.

---

## 4. Docker Compose Alternative

If Docker Desktop is running locally, you can start the entire stack via Docker Compose:

```powershell
docker compose up -d --build
```

Services exposed:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

---

## 5. Running Quality Gates & Test Suites

### Backend Unit & Integration Tests

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m compileall app
```

Expected result: **142 tests PASSED**.

### Frontend ESLint & Production Build

```powershell
cd frontend
npm run lint
npm run build
```

Expected result: **0 errors, 0 warnings**, static page generation successful across 15 routes.
