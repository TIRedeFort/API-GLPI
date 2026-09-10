from fastapi import APIRouter, Depends, Path, Query, status

from app.api.dependencies import get_glpi_client
from app.core.security import require_api_key
from app.schemas.common import SessionTestResponse
from app.schemas.tickets import (
    CreateTicketRequest,
    FollowupRequest,
    FollowupResponse,
    SolutionRequest,
    SolutionResponse,
    TicketFullResponse,
    TicketListResponse,
    TicketResponse,
    TicketStatusRequest,
    TicketStatusResponse,
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


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketStatusResponse,
    summary="Altera o status do chamado",
    description="Atualiza apenas o campo status do chamado no GLPI. Use 1=Novo, 2=Processando atribuido, 3=Processando planejado, 4=Pendente, 5=Solucionado, 6=Fechado.",
)
async def update_ticket_status(
    payload: TicketStatusRequest,
    ticket_id: int = Path(gt=0),
    client: GlpiClient = Depends(get_glpi_client),
) -> TicketStatusResponse:
    result = await client.update_ticket_status(ticket_id, payload.status)
    return TicketStatusResponse(ok=True, ticket=result)


@router.get(
    "/by-category/{category_id}",
    response_model=TicketListResponse,
    summary="Lista chamados por categoria",
    description="Busca os chamados mais recentes dentro do limite informado e retorna apenas os da categoria GLPI enviada.",
)
async def list_tickets_by_category(
    category_id: int = Path(gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    client: GlpiClient = Depends(get_glpi_client),
) -> TicketListResponse:
    tickets = await client.list_tickets_by_category(category_id, limit)
    return TicketListResponse(ok=True, count=len(tickets), tickets=tickets)


@router.get(
    "/by-entity/{entity_id}",
    response_model=TicketListResponse,
    summary="Lista chamados por entidade",
    description="Busca os chamados mais recentes dentro do limite informado e retorna apenas os da entidade GLPI enviada.",
)
async def list_tickets_by_entity(
    entity_id: int = Path(ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    client: GlpiClient = Depends(get_glpi_client),
) -> TicketListResponse:
    tickets = await client.list_tickets_by_entity(entity_id, limit)
    return TicketListResponse(ok=True, count=len(tickets), tickets=tickets)


@router.get(
    "/{ticket_id}/full",
    response_model=TicketFullResponse,
    summary="Consulta completa do chamado",
    description="Retorna dados principais do chamado e relacionamentos comuns, como requerentes, grupos, acompanhamentos, tarefas, solucoes e documentos.",
)
async def get_ticket_full(
    ticket_id: int = Path(gt=0),
    client: GlpiClient = Depends(get_glpi_client),
) -> TicketFullResponse:
    result = await client.get_ticket_full(ticket_id)
    return TicketFullResponse(ok=True, **result)


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
