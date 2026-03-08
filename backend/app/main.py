from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth_router, clienti_router, tipi_contratto_router, contratti_router, documenti_router, dashboard_router, search_router, chat_router

app = FastAPI(
    title="DocuFiscal API",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(clienti_router, prefix="/api/v1")
app.include_router(tipi_contratto_router, prefix="/api/v1")
app.include_router(contratti_router, prefix="/api/v1")
app.include_router(documenti_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}