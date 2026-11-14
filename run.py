"""EarthTrend Application Server Runner.

Starts the EarthTrend full-stack application (FastAPI backend + integrated
interactive web dashboard) on http://localhost:8000.

Usage:
    py run.py
"""

import sys
from pathlib import Path

# Add backend directory to python path
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("  EarthTrend — Earth Intelligence & Environmental Analytics")
    print("  NASA Space Apps Challenge 2026")
    print("=" * 70)
    print("  Web Dashboard: http://localhost:8000")
    print("  API Docs:      http://localhost:8000/docs")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
