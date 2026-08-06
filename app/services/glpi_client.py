from typing import Any, Dict

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.schemas.tickets import CreateTicketRequest


class GlpiClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = str(settings.glpi_api_url).rstrip("/")

    async def init_session(self) -> str:
        headers = {
            "App-Token": self.settings.glpi_app_token,
            "Authorization": f"user_token {self.settings.glpi_user_token}",
        }
        data = await self._request("GET", "/initSession", headers=headers)
        token = data.get("session_token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "GLPI nao retornou session_token.", "response": data},
            )
        return str(token)

    async def kill_session(self, session_token: str) -> None:
        if not self.settings.glpi_kill_session:
            return
        try:
            await self._request("GET", "/killSession", session_token=session_token)
        except HTTPException:
            return

    async def create_ticket(self, payload: CreateTicketRequest) -> Dict[str, Any]:
        session_token = await self.init_session()
        try:
            body = {"input": self._build_ticket_input(payload)}
            return await self._request("POST", "/Ticket", json=body, session_token=session_token)
        finally:
            await self.kill_session(session_token)

    async def add_followup(self, ticket_id: int, content: str) -> Dict[str, Any]:
        session_token = await self.init_session()
        try:
            body = {
                "input": {
                    "items_id": ticket_id,
                    "itemtype": "Ticket",
                    "content": content,
                }
            }
            return await self._request("POST", "/ITILFollowup", json=body, session_token=session_token)
        finally:
            await self.kill_session(session_token)

    async def solve_ticket(self, ticket_id: int, content: str) -> Dict[str, Any]:
        session_token = await self.init_session()
        try:
            body = {
                "input": {
                    "items_id": ticket_id,
                    "itemtype": "Ticket",
                    "content": content,
                }
            }
            result = await self._request("POST", "/ITILSolution", json=body, session_token=session_token)
            await self._request("PUT", f"/Ticket/{ticket_id}", json={"input": {"status": 5}}, session_token=session_token)
            return result
        finally:
            await self.kill_session(session_token)

    def _build_ticket_input(self, payload: CreateTicketRequest) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": payload.titulo,
            "content": payload.descricao,
            "type": payload.type or self.settings.glpi_default_ticket_type,
        }

        optional_fields = {
            "entities_id": payload.entities_id or self.settings.glpi_default_entity_id,
            "itilcategories_id": payload.itilcategories_id or payload.category_id or self.settings.glpi_default_category_id,
            "_users_id_requester": payload.requester_id or self.settings.glpi_default_requester_id,
            "_users_id_assign": payload.assign_user_id or self.settings.glpi_default_assign_user_id,
            "_groups_id_assign": payload.assign_group_id or self.settings.glpi_default_assign_group_id,
            "requesttypes_id": payload.requesttypes_id or self.settings.glpi_default_request_type_id,
            "urgency": payload.urgency or self.settings.glpi_default_urgency,
            "impact": payload.impact or self.settings.glpi_default_impact,
            "priority": payload.priority or self.settings.glpi_default_priority,
        }
        for key, value in optional_fields.items():
            if value is not None:
                data[key] = value

        data.update(payload.glpi_fields)
        return data

    async def _request(
        self,
        method: str,
        path: str,
        json: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        session_token: str | None = None,
    ) -> Dict[str, Any]:
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "App-Token": self.settings.glpi_app_token,
        }
        if session_token:
            request_headers["Session-Token"] = session_token
        if headers:
            request_headers.update(headers)

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    json=json,
                    headers=request_headers,
                )
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Falha ao conectar no GLPI: {exc}",
                ) from exc

        if response.is_error:
            try:
                detail: Any = response.json()
            except ValueError:
                detail = response.text
            raise HTTPException(
                status_code=response.status_code,
                detail={"message": "Erro retornado pelo GLPI.", "response": detail},
            )

        if not response.content:
            return {}
        return response.json()
