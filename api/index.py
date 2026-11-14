"""Vercel Serverless Function entrypoint for EarthTrend FastAPI."""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app
