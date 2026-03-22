from .auth import router as auth_router
from .clienti import router as clienti_router
from .tipi_contratto import router as tipi_contratto_router
from .contratti import router as contratti_router
from .documenti import router as documenti_router
from .dashboard import router as dashboard_router
from .search import router as search_router
from .chat import router as chat_router

__all__ = [
    "auth_router",
    "clienti_router",
    "tipi_contratto_router",
    "contratti_router",
    "documenti_router",
    "dashboard_router",
    "search_router",
    "chat_router",
]