from .api_leads import router as api_router
from .api_telemetria import router as telemetria_router
from .views import router as views_router
from .api_ia import router as ia_router

__all__ = ["api_router", "telemetria_router", "views_router", "ia_router"]
