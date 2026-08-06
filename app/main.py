from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.routes.health import router as health_router
from app.api.routes.tickets import router as tickets_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend para criar chamados, acompanhamentos e solucoes no GLPI. "
        "Use o header X-API-Key nos endpoints de chamados."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.include_router(health_router)
app.include_router(tickets_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    for path, methods in schema.get("paths", {}).items():
        if path.startswith("/tickets"):
            for operation in methods.values():
                operation.setdefault("security", [{"ApiKeyAuth": []}])

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
