from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["API GLPI"])
    environment: str = Field(examples=["production"])


class SessionTestResponse(BaseModel):
    ok: bool = Field(examples=[True])
    message: str = Field(examples=["Sessao GLPI criada com sucesso."])
