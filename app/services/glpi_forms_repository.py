import json
import logging
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional

import pymysql
from fastapi import HTTPException, status
from pymysql.cursors import DictCursor
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.schemas.forms import FormFieldAnswer, FormUsageRecord


logger = logging.getLogger(__name__)


class GlpiFormsRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def list_form_usage(
        self,
        form_id: Optional[int] = None,
        requester_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        include_answers: bool = True,
        limit: int = 100,
    ) -> List[FormUsageRecord]:
        if not self.settings.glpi_db_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Leitura dos formularios nativos nao configurada. Defina "
                    "GLPI_DB_HOST, GLPI_DB_NAME, GLPI_DB_USER e GLPI_DB_PASSWORD "
                    "com uma conta de banco somente leitura."
                ),
            )

        return await run_in_threadpool(
            self._list_form_usage,
            form_id,
            requester_id,
            date_from,
            date_to,
            include_answers,
            limit,
        )

    def _list_form_usage(
        self,
        form_id: Optional[int],
        requester_id: Optional[int],
        date_from: Optional[date],
        date_to: Optional[date],
        include_answers: bool,
        limit: int,
    ) -> List[FormUsageRecord]:
        prefix = self.settings.glpi_db_table_prefix
        answer_json = "a.answers" if include_answers else "NULL"
        query = f"""
            SELECT
                a.id AS answer_id,
                a.forms_forms_id AS form_id,
                f.name AS form_name,
                a.users_id AS requester_id,
                COALESCE(
                    NULLIF(TRIM(CONCAT_WS(' ', NULLIF(u.firstname, ''), NULLIF(u.realname, ''))), ''),
                    NULLIF(u.name, '')
                ) AS requester_name,
                a.date_creation AS used_at,
                {answer_json} AS answer_json
            FROM `{prefix}forms_answerssets` AS a
            INNER JOIN `{prefix}forms_forms` AS f ON f.id = a.forms_forms_id
            LEFT JOIN `{prefix}users` AS u ON u.id = a.users_id
            WHERE 1 = 1
        """
        params: List[Any] = []

        if form_id is not None:
            query += " AND a.forms_forms_id = %s"
            params.append(form_id)
        if requester_id is not None:
            query += " AND a.users_id = %s"
            params.append(requester_id)
        if date_from is not None:
            query += " AND a.date_creation >= %s"
            params.append(datetime.combine(date_from, time.min))
        if date_to is not None:
            query += " AND a.date_creation < %s"
            params.append(datetime.combine(date_to + timedelta(days=1), time.min))

        query += " ORDER BY a.date_creation DESC, a.id DESC LIMIT %s"
        params.append(limit)

        connection = None
        try:
            connection = pymysql.connect(
                host=self.settings.glpi_db_host,
                port=self.settings.glpi_db_port,
                user=self.settings.glpi_db_user,
                password=self.settings.glpi_db_password,
                database=self.settings.glpi_db_name,
                charset="utf8mb4",
                cursorclass=DictCursor,
                connect_timeout=10,
                read_timeout=30,
                autocommit=True,
            )
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        except pymysql.MySQLError as exc:
            error_code = exc.args[0] if exc.args else "unknown"
            logger.error("Consulta ao banco do GLPI falhou (codigo %s).", error_code)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Falha ao consultar os envios nativos do GLPI.",
            ) from exc
        finally:
            if connection is not None:
                connection.close()

        return [self._to_record(row, include_answers) for row in rows]

    @classmethod
    def _to_record(cls, row: Dict[str, Any], include_answers: bool) -> FormUsageRecord:
        used_at = row.get("used_at")
        if isinstance(used_at, (date, datetime)):
            used_at = used_at.isoformat(sep=" ") if isinstance(used_at, datetime) else used_at.isoformat()
        elif used_at is not None:
            used_at = str(used_at)

        answers = cls._decode_answers(row.get("answer_json")) if include_answers else []
        return FormUsageRecord(
            answer_id=int(row["answer_id"]),
            form_id=cls._safe_int(row.get("form_id")),
            form_name=row.get("form_name"),
            requester_id=cls._safe_int(row.get("requester_id")),
            requester_name=row.get("requester_name"),
            used_at=used_at,
            status=None,
            answers=answers,
        )

    @staticmethod
    def _decode_answers(value: Any) -> List[FormFieldAnswer]:
        if value is None:
            return []
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="O GLPI retornou respostas de formulario em formato invalido.",
                ) from exc
        if not isinstance(value, list):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="O GLPI retornou respostas de formulario em formato inesperado.",
            )

        answers: List[FormFieldAnswer] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            answers.append(
                FormFieldAnswer(
                    question_id=GlpiFormsRepository._safe_int(item.get("question_id")),
                    question=item.get("question_label"),
                    field_type=item.get("raw_question_type"),
                    answer=item.get("raw_answer"),
                )
            )
        return answers

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None
