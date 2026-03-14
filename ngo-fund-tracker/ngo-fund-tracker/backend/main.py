from __future__ import annotations

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from .database import init_db
from .routes import donors, donations, expenses, projects
from .schemas import DashboardOut
from . import crud

# Create FastAPI app
app = FastAPI(title="NGO Fund Tracker API")

# OAuth2 authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Enable CORS (for frontend connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def _startup() -> None:
    init_db()

# Login endpoint (for Swagger authentication)
@app.post("/login", tags=["auth"])
def login():
    return {
        "access_token": "demo_token_123",
        "token_type": "bearer"
    }

# Protected dashboard endpoint
@app.get("/dashboard", response_model=DashboardOut, tags=["dashboard"])
def dashboard(token: str = Depends(oauth2_scheme)) -> DashboardOut:
    return DashboardOut(**crud.get_dashboard())

# Include API routers
app.include_router(donors.router)
app.include_router(donations.router)
app.include_router(projects.router)
app.include_router(expenses.router)