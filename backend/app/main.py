from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_analysis, routes_cr, routes_effort, routes_feedback, routes_settings
from app.db import init_db

app = FastAPI(title="ChangePilot AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_cr.router)
app.include_router(routes_analysis.router)
app.include_router(routes_feedback.router)
app.include_router(routes_settings.router)
app.include_router(routes_effort.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
