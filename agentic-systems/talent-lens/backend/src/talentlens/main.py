import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talentlens.api.routes import assessments, candidates, dashboard, health, rubrics, webhooks
from talentlens.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TalentLens starting (env=%s)", settings.env)
    yield
    logger.info("TalentLens shutting down")


_docs_url = "/docs" if settings.env == "development" else None
_redoc_url = "/redoc" if settings.env == "development" else None

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url="/openapi.json" if settings.env == "development" else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(assessments.router, prefix="/api")
app.include_router(rubrics.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
