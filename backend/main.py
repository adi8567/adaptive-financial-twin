from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.v1.endpoints import router as api_v1_router
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.services.demo_seed import seed_demo_data

# Create tables
Base.metadata.create_all(bind=engine)

# Auto-seed demo persona Alex on startup
db = SessionLocal()
try:
    seed_demo_data(db)
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Stateful Adaptive Financial Digital Twin with Multi-Regime Monte Carlo, Behavioral Economics, Constrained RL, and Grounded AI Copilot."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permissive for monorepo development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "is_demo_mode": True
    }
