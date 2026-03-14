# NGO Fund Tracker

Streamlit UI → FastAPI backend → SQLite database.

## Setup

```bash
cd ngo-fund-tracker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

### 1) Start backend (FastAPI)

From `ngo-fund-tracker/`:

```bash
uvicorn backend.main:app --reload
```

If you get a file-watch/permissions error with `--reload`, run without it:

```bash
uvicorn backend.main:app
```

The API will create the SQLite DB at `database/ngo.db` on startup.

### 2) Start frontend (Streamlit)

In another terminal (still from `ngo-fund-tracker/`):

```bash
streamlit run frontend/app.py
```

If your backend is on a different host/port, set:

```bash
export BACKEND_URL="http://127.0.0.1:8000"
```

## API Endpoints

- `POST /donor`
- `GET /donors`
- `POST /donation`
- `GET /donations`
- `POST /project`
- `GET /projects`
- `POST /expense`
- `GET /expenses`
- `GET /dashboard`
