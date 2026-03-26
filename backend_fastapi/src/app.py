from asgiref.sync import sync_to_async
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import json
from contextlib import asynccontextmanager
from typing import Dict, List

# Initializing Django
from . import django_settings

# Import routers
from .routers.testing import router as test_router
from .routers.results import router as results_router

# 1. Define lifespan (Keep it purely for startup/shutdown tasks like DB connections if needed)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("FastAPI Testing System starting...")
    yield
    # Shutdown
    print("FastAPI Testing System shutting down...")

# 2. Create app with lifespan
app = FastAPI(title="ORT Testing System", lifespan=lifespan)

# 3. Instrument and expose Prometheus metrics globally (OUTSIDE the lifespan)
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# ------- CORS ---------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------

app.include_router(test_router)
app.include_router(results_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Django database connection
        # Wrapper for the DB check
        def db_check():
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

        await sync_to_async(db_check)()

        return {
            "status": "healthy",
            "service": "testing_api",
            "database": "connected",
            "django": "initialized"
        }
    except Exception as e:
        print(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)