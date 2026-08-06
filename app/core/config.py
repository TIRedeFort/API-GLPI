from functools import lru_cache
from typing import Optional

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "API GLPI"
    app_env: str = "development"
    app_port: int = 8000
    app_public_prefix: str = ""

    api_key: str = Field(min_length=12)

    glpi_api_url: HttpUrl
    glpi_app_token: str = Field(min_length=10)
    glpi_user_token: str = Field(min_length=10)

    glpi_default_entity_id: Optional[int] = None
    glpi_default_category_id: Optional[int] = None
    glpi_default_requester_id: Optional[int] = None
    glpi_default_ticket_type: int = 1
    glpi_default_request_type_id: Optional[int] = None
    glpi_default_urgency: Optional[int] = None
    glpi_default_impact: Optional[int] = None
    glpi_default_priority: Optional[int] = None
    glpi_default_assign_user_id: Optional[int] = None
    glpi_default_assign_group_id: Optional[int] = None
    glpi_kill_session: bool = True

    @field_validator(
        "glpi_default_entity_id",
        "glpi_default_category_id",
        "glpi_default_requester_id",
        "glpi_default_request_type_id",
        "glpi_default_urgency",
        "glpi_default_impact",
        "glpi_default_priority",
        "glpi_default_assign_user_id",
        "glpi_default_assign_group_id",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
