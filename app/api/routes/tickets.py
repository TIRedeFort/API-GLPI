from fastapi import APIRouter, Depends, Path, status

from app.api.dependencies import get_glpi_client
from app.core.security import require_api_key
from app.schemas.common import SessionTestResponse
from app.schemas.tickets import (
    CreateTicketRequest,
    FollowupRequest,
    FollowupResponse,
    SolutionRequest,
    SolutionResponse,
    TicketResponse,
)
from app.services.glpi_client import GlpiClient

router = APIRouter(
    prefix="/tickets",
    tags=["Chamados"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "/session-test",
    response_model=SessionTestResponse,
    summary="Testa autenticacao no GLPI",
    description="Cria uma sessao na API REST legada do GLPI e encerra em seguida.",
)
async def session_test(client: GlpiClient = Depends(get_glpi_client)) -> SessionTestResponse:
    token = await client.init_session()
    await client.kill_session(token)
    return SessionTestResponse(ok=True, message="Sessao GLPI criada com sucesso.")


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um chamado no GLPI",
    description="Cria um chamado usando os padroes do .env quando entidade, categoria ou requerente nao forem enviados.",
)
async def create_ticket(payload: CreateTicketRequest, client: GlpiClient = Depends(get_glpi_client)) -> TicketResponse:
    result = await client.create_ticket(payload)
    return TicketResponse(ok=True, ticket=result)


@router.post(
    "/{ticket_id}/followups",
    response_model=FollowupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona acompanhamento ao chamado",
)
async def add_followup(
    payload: FollowupRequest,
    ticket_id: int = Path(gt=0),
    client: GlpiClient = Depends(get_glpi_client),
) -> FollowupResponse:
    result = await client.add_followup(ticket_id, payload.descricao)
    return FollowupResponse(ok=True, followup=result)


@router.post(
    "/{ticket_id}/solve",
    response_model=SolutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona solucao e marca o chamado como solucionado",
)
async def solve_ticket(
    payload: SolutionRequest,
    ticket_id: int = Path(gt=0),
    client: GlpiClient = Depends(get_glpi_client),
) -> SolutionResponse:
    result = await client.solve_ticket(ticket_id, payload.descricao)
    return SolutionResponse(ok=True, solution=result)
