from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, jobs
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=f"{settings.app_name} API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api = APIRouter(prefix="/api")
    api.include_router(auth.router)
    api.include_router(jobs.router)

    @api.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "ai_provider": settings.resolved_ai_provider or "rules"}

    app.include_router(api)
    return app


app = create_app()
