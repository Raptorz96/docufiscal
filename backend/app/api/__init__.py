from .auth import router as auth_router
from .clienti import router as clienti_router
from .tipi_contratto import router as tipi_contratto_router
from .contratti import router as contratti_router

__all__ = ["auth_router", "clienti_router", "tipi_contratto_router", "contratti_router"]