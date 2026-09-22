from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_glpi_client
from app.core.security import require_api_key
from app.schemas.forms import FormUsageFilters, FormUsageResponse
from app.services.glpi_client import GlpiClient


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
        "Lista respostas registradas pelo plugin Formcreator, informando "
        "quando o formulario foi enviado e qual usuario o solicitou."
    ),
)
async def list_form_usage(
    form_id: Optional[int] = Query(default=None, gt=0, description="ID do formulario no Formcreator."),
    requester_id: Optional[int] = Query(default=None, gt=0, description="ID do usuario solicitante no GLPI."),
    date_from: Optional[date] = Query(default=None, description="Data inicial, no formato YYYY-MM-DD."),
    date_to: Optional[date] = Query(default=None, description="Data final, no formato YYYY-MM-DD."),
    limit: int = Query(default=100, ge=1, le=500),
    client: GlpiClient = Depends(get_glpi_client),
) -> FormUsageResponse:
    if date_from and date_to and date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to nao pode ser anterior a date_from.",
        )

    submissions = await client.list_form_usage(
        form_id=form_id,
        requester_id=requester_id,
        date_from=date_from,
        date_to=date_to,
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
        ),
        submissions=submissions,
    )
