from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.routes.health import router as health_router
from app.api.routes.forms import router as forms_router
from app.api.routes.tickets import router as tickets_router
from app.core.config import get_settings

settings = get_settings()
public_prefix = settings.app_public_prefix.rstrip("/")

app = FastAPI(
    title=settings.app_name,
    description=(
        "Backend para criar chamados, acompanhamentos e solucoes no GLPI. "
        "Use o header X-API-Key nos endpoints de chamados."
    ),
    version="1.0.0",
    docs_url=f"{public_prefix}/docs" if public_prefix else "/docs",
    redoc_url=f"{public_prefix}/redoc" if public_prefix else "/redoc",
    openapi_url=f"{public_prefix}/openapi.json" if public_prefix else "/openapi.json",
    servers=[{"url": public_prefix or "/", "description": "Servidor publico"}],
)

app.include_router(health_router)
app.include_router(forms_router)
app.include_router(tickets_router)
if public_prefix:
    app.include_router(health_router, prefix=public_prefix)
    app.include_router(forms_router, prefix=public_prefix)
    app.include_router(tickets_router, prefix=public_prefix)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["servers"] = [{"url": public_prefix or "/", "description": "Servidor publico"}]
    schema.setdefault("components", {}).setdefault("securitySchemes", {})["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
    }
    for path, methods in schema.get("paths", {}).items():
        if path.startswith(("/tickets", "/forms")):
            for operation in methods.values():
                operation.setdefault("security", [{"ApiKeyAuth": []}])

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
