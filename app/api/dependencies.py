from functools import lru_cache

from app.core.config import get_settings
from app.services.glpi_forms_repository import GlpiFormsRepository
from app.services.glpi_client import GlpiClient


@lru_cache
def get_glpi_client() -> GlpiClient:
    return GlpiClient(get_settings())


@lru_cache
def get_glpi_forms_repository() -> GlpiFormsRepository:
    return GlpiFormsRepository(get_settings())
