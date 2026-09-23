from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings
from app.schemas.tickets import CreateTicketRequest


class GlpiClient:
    SEARCH_FIELD_CATEGORY = 7
    SEARCH_FIELD_ENTITY = 80
    SEARCH_FIELD_STATUS = 12
    CLOSED_STATUSES = {5, 6}
    SEARCH_PAGE_SIZE = 100
    SEARCH_MAX_PAGES = 20

    RELATED_TICKET_RESOURCES = {
        "requesters_and_actors": "Ticket_User",
        "assigned_groups": "Group_Ticket",
        "followups": "ITILFollowup",
        "tasks": "TicketTask",
        "solutions": "ITILSolution",
        "documents": "Document_Item",
    }

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

    async def update_ticket_status(self, ticket_id: int, new_status: int) -> Dict[str, Any]:
        session_token = await self.init_session()
        try:
            body = {"input": {"status": new_status}}
            return await self._request("PUT", f"/Ticket/{ticket_id}", json=body, session_token=session_token)
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

    async def get_ticket_full(self, ticket_id: int) -> Dict[str, Any]:
        session_token = await self.init_session()
        try:
            ticket = await self._request(
                "GET",
                f"/Ticket/{ticket_id}?expand_dropdowns=true&get_hateoas=false",
                session_token=session_token,
            )
            related: Dict[str, List[Dict[str, Any]]] = {}
            warnings: List[str] = []

            for name, resource in self.RELATED_TICKET_RESOURCES.items():
                try:
                    data = await self._request(
                        "GET",
                        f"/Ticket/{ticket_id}/{resource}?range=0-999&get_hateoas=false",
                        session_token=session_token,
                    )
                    related[name] = self._normalize_collection(data)
                except HTTPException as exc:
                    related[name] = []
                    warnings.append(f"{name}: {exc.detail}")

            return {
                "ticket": ticket if isinstance(ticket, dict) else {"data": ticket},
                "related": related,
                "warnings": warnings,
            }
        finally:
            await self.kill_session(session_token)

    async def list_tickets_by_category(self, category_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        return await self._search_tickets_by_field(self.SEARCH_FIELD_CATEGORY, category_id, limit)

    async def list_tickets_by_entity(self, entity_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        return await self._search_tickets_by_field(self.SEARCH_FIELD_ENTITY, entity_id, limit)

    async def _search_tickets_by_field(self, search_field: int, value: int, limit: int) -> List[Dict[str, Any]]:
        session_token = await self.init_session()
        try:
            tickets: List[Dict[str, Any]] = []
            start = 0
            total_count: int | None = None

            for _ in range(self.SEARCH_MAX_PAGES):
                page_size = min(self.SEARCH_PAGE_SIZE, max(limit * 2, self.SEARCH_PAGE_SIZE))
                end = start + page_size - 1
                params = {
                    "criteria[0][field]": search_field,
                    "criteria[0][searchtype]": "equals",
                    "criteria[0][value]": value,
                    "forcedisplay[0]": 2,
                    "forcedisplay[1]": 1,
                    "forcedisplay[2]": 7,
                    "forcedisplay[3]": 80,
                    "forcedisplay[4]": 12,
                    "range": f"{start}-{end}",
                    "rawdata": 1,
                }
                data = await self._request(
                    "GET",
                    f"/search/Ticket?{urlencode(params)}",
                    session_token=session_token,
                )
                if isinstance(data, dict):
                    total_count = self._safe_int(data.get("totalcount"))

                page_tickets = self._normalize_search_tickets(data)
                open_tickets = [
                    ticket
                    for ticket in page_tickets
                    if self._safe_int(ticket.get("status")) not in self.CLOSED_STATUSES
                ]
                tickets.extend(open_tickets)

                if len(tickets) >= limit or not page_tickets:
                    break
                start += page_size
                if total_count is not None and start >= total_count:
                    break

            return tickets[:limit]
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

    @staticmethod
    def _normalize_collection(data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            rows = data.get("data")
            if isinstance(rows, list):
                return [item for item in rows if isinstance(item, dict)]
            if data:
                return [data]
        return []

    @staticmethod
    def _normalize_search_tickets(data: Any) -> List[Dict[str, Any]]:
        if not isinstance(data, dict):
            return []

        rows = data.get("data")
        if not isinstance(rows, list):
            return []

        tickets: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            tickets.append(
                {
                    "id": row.get("2"),
                    "titulo": row.get("1"),
                    "categoria": row.get("7"),
                    "entidade": row.get("80"),
                    "status": row.get("12"),
                    "raw": row,
                }
            )
        return tickets

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    async def _request(
        self,
        method: str,
        path: str,
        json: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        session_token: str | None = None,
    ) -> Any:
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
