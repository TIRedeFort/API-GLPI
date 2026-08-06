from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateTicketRequest(BaseModel):
    titulo: str = Field(min_length=1, max_length=255, examples=["CHAMADO VIA API"])
    descricao: str = Field(min_length=1, examples=["Chamado criado para teste de integracao via API."])

    entities_id: Optional[int] = Field(default=None, description="Entidade GLPI. Se vazio, usa GLPI_DEFAULT_ENTITY_ID.")
    category_id: Optional[int] = Field(default=None, description="Categoria GLPI. Alias de itilcategories_id.")
    itilcategories_id: Optional[int] = Field(default=None, description="Categoria GLPI.")
    requester_id: Optional[int] = Field(default=None, description="Usuario requerente.")
    assign_user_id: Optional[int] = Field(default=None, description="Tecnico atribuido.")
    assign_group_id: Optional[int] = Field(default=None, description="Grupo tecnico atribuido.")
    type: Optional[int] = Field(default=None, description="1 = incidente, 2 = requisicao.")
    requesttypes_id: Optional[int] = Field(default=None, description="Origem da requisicao.")
    urgency: Optional[int] = Field(default=None, ge=1, le=5)
    impact: Optional[int] = Field(default=None, ge=1, le=5)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    glpi_fields: Dict[str, Any] = Field(default_factory=dict, description="Campos extras enviados diretamente ao GLPI.")


class TicketResponse(BaseModel):
    ok: bool
    ticket: Dict[str, Any]


class TicketFullResponse(BaseModel):
    ok: bool
    ticket: Dict[str, Any]
    related: Dict[str, List[Dict[str, Any]]]
    warnings: List[str] = Field(default_factory=list)


class TicketListResponse(BaseModel):
    ok: bool
    count: int
    tickets: List[Dict[str, Any]]


class FollowupRequest(BaseModel):
    descricao: str = Field(min_length=1, examples=["Atualizacao do chamado via API."])


class FollowupResponse(BaseModel):
    ok: bool
    followup: Dict[str, Any]


class SolutionRequest(BaseModel):
    descricao: str = Field(default="Tarefa feita com sucesso", min_length=1)


class SolutionResponse(BaseModel):
    ok: bool
    solution: Dict[str, Any]
