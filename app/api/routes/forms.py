from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_glpi_forms_repository
from app.core.security import require_api_key
from app.schemas.forms import FormUsageFilters, FormUsageResponse
from app.services.glpi_forms_repository import GlpiFormsRepository


router = APIRouter(
    prefix="/forms",
    tags=["Formularios"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "/usage",
    response_model=FormUsageResponse,
    summary="Consulta uso dos formularios",
    description=(
        "Lista envios dos formularios nativos do GLPI 11, incluindo solicitante "
        "e respostas quando solicitado. Requer acesso de banco somente leitura."
    ),
)
async def list_form_usage(
    form_id: Optional[int] = Query(default=None, gt=0, description="ID do formulario nativo no GLPI."),
    requester_id: Optional[int] = Query(default=None, gt=0, description="ID do usuario solicitante no GLPI."),
    date_from: Optional[date] = Query(default=None, description="Data inicial, no formato YYYY-MM-DD."),
    date_to: Optional[date] = Query(default=None, description="Data final, no formato YYYY-MM-DD."),
    include_answers: bool = Query(default=True, description="Inclui perguntas e respostas preenchidas."),
    limit: int = Query(default=100, ge=1, le=500),
    repository: GlpiFormsRepository = Depends(get_glpi_forms_repository),
) -> FormUsageResponse:
    if date_from and date_to and date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to nao pode ser anterior a date_from.",
        )

    submissions = await repository.list_form_usage(
        form_id=form_id,
        requester_id=requester_id,
        date_from=date_from,
        date_to=date_to,
        include_answers=include_answers,
        limit=limit,
    )

    return FormUsageResponse(
        ok=True,
        count=len(submissions),
        filters=FormUsageFilters(
            form_id=form_id,
            requester_id=requester_id,
            date_from=date_from,
            date_to=date_to,
            include_answers=include_answers,
        ),
        submissions=submissions,
    )
