from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, health, interviews, resumes
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.llm import LLMNotConfiguredError


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, debug=settings.DEBUG)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(LLMNotConfiguredError)
    async def llm_not_configured_handler(
        request: Request, exc: LLMNotConfiguredError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(health.router, prefix=settings.API_PREFIX)
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(resumes.router, prefix=settings.API_PREFIX)
    app.include_router(interviews.router, prefix=settings.API_PREFIX)
    return app


app = create_app()
