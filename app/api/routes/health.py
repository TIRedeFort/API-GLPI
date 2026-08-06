from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Sistema"])


@router.get("/health", response_model=HealthResponse, summary="Verifica se a API esta online")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, environment=settings.app_env)
