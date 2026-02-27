from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_router

app = FastAPI(
    title="DocuFiscal API",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}