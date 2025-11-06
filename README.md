# RUE API
![Tests](https://github.com/kartoza/rue-api/actions/workflows/tests.yml/badge.svg?branch=main)
![Python](https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13-blue)
![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000?logo=ruff)
![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-2A6DB2)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Last commit](https://img.shields.io/github/last-commit/kartoza/rue-api)

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
cp .env.example .env

# 4) Run DB migrations
alembic revision --autogenerate -m "init"   # first time, if you have models
alembic upgrade head

# 5) Start the API
uvicorn app.main:app --reload
