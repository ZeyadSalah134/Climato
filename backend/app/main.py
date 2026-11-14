"""EarthTrend FastAPI application entrypoint."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure backend directory is in sys.path so 'app.*' imports work when imported as backend.app.main (Vercel)
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

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
## 🌍 🚀 **[CLICK HERE TO OPEN THE INTERACTIVE MAP DASHBOARD](/)**

### **EarthTrend — Earth Intelligence & Environmental Analytics**
Turns NASA Earth observation and Earth system model data into scientifically meaningful, interactive environmental trend analysis.

* 🗺️ **[Launch Web Dashboard & Interactive Map](/)**
* 📊 Discover supported environmental variables and verified NASA datasets.
* 📈 Run Ordinary Least Squares, Mann-Kendall, and Theil-Sen statistical trend tests.
* 🔬 Assess data quality and 95% confidence intervals on 28,080 observations (2000–2025).
* ⚖️ Compare two regions descriptively.
* 📄 Export observations (CSV), results (JSON), and official PDF reports.

*NASA Space Apps Challenge 2026 Submission.*
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
        app.include_router(module.router, prefix="/api/v1")
        app.include_router(module.router, prefix="/api")

    search_indexes = [
        Path(__file__).resolve().parent / "static" / "index.html",
        Path("/var/task/backend/app/static/index.html"),
        REPO_ROOT / "public" / "index.html",
        REPO_ROOT / "frontend" / "dist" / "index.html",
        Path("/var/task/public/index.html"),
        Path("/var/task/frontend/dist/index.html"),
    ]
    dist_index = next((p for p in search_indexes if p.exists()), Path(__file__).resolve().parent / "static" / "index.html")

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
            "dashboard": "/dashboard",
            "api_prefix": settings.api_prefix,
        })

    @app.get("/dashboard", tags=["meta"], summary="Direct web dashboard")
    @app.get("/map", tags=["meta"], summary="Direct interactive map view")
    async def web_dashboard():
        if dist_index.exists():
            return FileResponse(dist_index)
        return JSONResponse(status_code=404, content={"message": "Web dashboard not built"})

    @app.get("/climate_power_monthly_2000-2025.csv", tags=["datasets"])
    async def download_csv():
        csv_paths = [
            Path(__file__).resolve().parent / "static" / "climate_power_monthly_2000-2025.csv",
            Path("/var/task/backend/app/static/climate_power_monthly_2000-2025.csv"),
            REPO_ROOT / "climate_power_monthly_2000-2025.csv",
            REPO_ROOT / "data" / "climate_power_monthly_2000-2025.csv",
        ]
        p = next((x for x in csv_paths if x.exists()), None)
        if p:
            return FileResponse(p, filename="climate_power_monthly_2000-2025.csv", media_type="text/csv")
        return JSONResponse(status_code=404, content={"message": "File not found"})

    @app.get("/climate_power_monthly_2000-2025.xlsx", tags=["datasets"])
    async def download_xlsx():
        xlsx_paths = [
            Path(__file__).resolve().parent / "static" / "climate_power_monthly_2000-2025.xlsx",
            REPO_ROOT / "climate_power_monthly_2000-2025.xlsx",
            REPO_ROOT / "data" / "climate_power_monthly_2000-2025.xlsx",
        ]
        p = next((x for x in xlsx_paths if x.exists()), None)
        if p:
            return FileResponse(p, filename="climate_power_monthly_2000-2025.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        return JSONResponse(status_code=404, content={"message": "File not found"})

    return app


app = create_app()
