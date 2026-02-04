from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import SessionLocal
import os
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(
    title="Diploma FastAPI",
    description="FastAPI backend for Diploma Project",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------- CORS ---------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------

@app.get("/")
async def root():
    return {
        "message": "FastAPI backend is running",
        "docs": "/docs",
        "environment": os.getenv("ENVIRONMENT")
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


#if __name__ == "__main__":
#    uvicorn.run("main:app", host="0.0.0.0", port=8001)