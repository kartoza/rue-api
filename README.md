# RUE API

FastAPI backend for the Rapid Urbanism Explorer (RUE).

---

## Quickstart

```bash
# 1) Create & activate venv (optional)
python -m venv .venv
source .venv/bin/activate

# 2) Install deps
pip install -U pip
pip install -e .

# 3) Create a .env
cp .env.example .env   # or see “Environment” below

# 4) Run DB migrations
alembic revision --autogenerate -m "init"   # first time, if you have models
alembic upgrade head

# 5) Start the API
uvicorn app.main:app --reload
