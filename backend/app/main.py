"""EarthTrend FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from app.api.routers import (
    analysis,
    data,
    datasets,
    export,
    health,
    locations,
    variables,
)
from app.core.config import settings, REPO_ROOT
from app.core.errors import EarthTrendError
from app.core.logging import configure_logging, get_logger
from app.models.database import init_db

configure_logging(settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info(
        "EarthTrend API %s starting (environment=%s, demo_fallback=%s)",
        settings.app_version,
        settings.environment,
        settings.allow_demo_fallback,
    )
    yield
    logger.info("EarthTrend API shutting down")


DESCRIPTION = """
**EarthTrend** turns NASA Earth observation and Earth system model data into
scientifically meaningful, interactive environmental trend analysis.

* Discover supported environmental variables and their provenance.
* Retrieve real NASA POWER time series for any coordinate on Earth.
* Run ordinary least squares, Mann-Kendall, and Theil-Sen trend analyses.
* Assess data quality and statistical significance.
* Compare two regions descriptively.
* Export observations (CSV), results (JSON), and a full report (PDF).

EarthTrend is an independent educational project submitted to the NASA Space
Apps Challenge. It is **not** affiliated with or endorsed by NASA. All data is
attributed to its original provider, and no measurements, p-values, or findings
are ever fabricated.
"""


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=DESCRIPTION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={"name": "EarthTrend", "url": "https://github.com/earthtrend/earthtrend"},
        license_info={"name": "MIT"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # --- error handlers ---------------------------------------------------
    @app.exception_handler(EarthTrendError)
    async def earthtrend_error_handler(request: Request, exc: EarthTrendError) -> JSONResponse:
        logger.info("Handled %s: %s", exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_payload())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "The request payload failed validation.",
                    "details": {"errors": jsonable_encoder(exc.errors())},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:  # pragma: no cover
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected internal error occurred.",
                    "details": {},
                }
            },
        )

    # --- routes -----------------------------------------------------------
    for module in (health, variables, datasets, locations, data, analysis, export):
        app.include_router(module.router, prefix=settings.api_prefix)

    dist_index = settings.cache_dir.parent.parent / "frontend" / "dist" / "index.html"
    if not dist_index.exists():
        dist_index = REPO_ROOT / "frontend" / "dist" / "index.html"

    @app.get("/", tags=["meta"], summary="Service root or web dashboard")
    async def root(request: Request) -> Response:
        accept = request.headers.get("accept", "")
        if "text/html" in accept and dist_index.exists():
            return FileResponse(dist_index)
        return JSONResponse({
            "name": settings.app_name,
            "version": settings.app_version,
            "engine_version": settings.analysis_engine_version,
            "tagline": "Discover Earth's Changes. Understand Their Significance.",
            "docs": "/docs",
            "api_prefix": settings.api_prefix,
        })

    @app.get("/climate_power_monthly_2000-2025.csv", tags=["datasets"])
    async def download_csv():
        p = REPO_ROOT / "climate_power_monthly_2000-2025.csv"
        if not p.exists():
            p = REPO_ROOT / "data" / "climate_power_monthly_2000-2025.csv"
        if p.exists():
            return FileResponse(p, filename="climate_power_monthly_2000-2025.csv", media_type="text/csv")
        return JSONResponse(status_code=404, content={"message": "File not found"})

    @app.get("/climate_power_monthly_2000-2025.xlsx", tags=["datasets"])
    async def download_xlsx():
        p = REPO_ROOT / "climate_power_monthly_2000-2025.xlsx"
        if not p.exists():
            p = REPO_ROOT / "data" / "climate_power_monthly_2000-2025.xlsx"
        if p.exists():
            return FileResponse(p, filename="climate_power_monthly_2000-2025.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        return JSONResponse(status_code=404, content={"message": "File not found"})

    return app


app = create_app()
