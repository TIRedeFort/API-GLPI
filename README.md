# API GLPI

Backend profissional para criar chamados, acompanhamentos e solucoes no GLPI.

O projeto usa FastAPI e gera documentacao Swagger automaticamente em:

```text
/docs
```

## O que esta API faz

- Testa autenticacao na API REST legada do GLPI.
- Cria chamados.
- Consulta chamado completo.
- Lista chamados por categoria.
- Lista chamados por entidade.
- Adiciona acompanhamentos.
- Adiciona solucao e marca chamado como solucionado.
- Protege os endpoints com `X-API-Key`.

## URLs

API local:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Healthcheck:

```text
http://localhost:8000/health
```

## Configuracao

Copie `.env.example` para `.env` e ajuste os tokens:

```env
API_KEY=uma_chave_forte
APP_PUBLIC_PREFIX=/api-glpi
GLPI_API_URL=https://fortsupermercados.com.br/suporte/apirest.php
GLPI_APP_TOKEN=...
GLPI_USER_TOKEN=...
```

Os padroes atuais foram mapeados do chamado `2608060012`:

```env
GLPI_DEFAULT_ENTITY_ID=4
GLPI_DEFAULT_CATEGORY_ID=287
GLPI_DEFAULT_REQUESTER_ID=114
GLPI_DEFAULT_TICKET_TYPE=1
GLPI_DEFAULT_REQUEST_TYPE_ID=1
GLPI_DEFAULT_URGENCY=3
GLPI_DEFAULT_IMPACT=3
GLPI_DEFAULT_PRIORITY=3
```

## Rodar localmente

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Depois abra:

```text
http://localhost:8000/docs
```

No Swagger, clique em `Authorize` e informe a chave configurada em `API_KEY`.

## Rodar com Docker

```bash
docker build -t api-glpi .
docker run --env-file .env -p 8000:8000 api-glpi
```

Ou:

```bash
docker compose up -d --build
```

## Easypanel

Crie um novo projeto usando este repositorio/pasta.

Configure:

- Build: Dockerfile
- Porta interna: `8000`
- Healthcheck: `/health`
- Variaveis de ambiente: copie o conteudo do `.env`
- Para publicar em `/api-glpi`, configure `APP_PUBLIC_PREFIX=/api-glpi`

Sugestao de URL:

```text
https://app.fortsupermercados.com.br/api-glpi
```

Com `APP_PUBLIC_PREFIX=/api-glpi`, o Swagger fica em:

```text
https://app.fortsupermercados.com.br/api-glpi/docs
```

A API tambem continua respondendo `/health` sem prefixo para healthcheck interno
do container.

## Criar chamado

Endpoint:

```http
POST /tickets
X-API-Key: sua_chave
Content-Type: application/json
```

Exemplo:

```json
{
  "titulo": "CHAMADO VIA API",
  "descricao": "Chamado criado para teste de integracao via API."
}
```

Como os defaults ja estao no `.env`, esse payload cria o chamado usando:

- entidade `4`;
- categoria `287`;
- requerente `114` (`RPA`);
- tipo `1`;
- origem `1`;
- urgencia/impacto/prioridade `3`.

Tambem e possivel sobrescrever:

```json
{
  "titulo": "Outro chamado",
  "descricao": "Descricao completa",
  "entities_id": 4,
  "category_id": 287,
  "requester_id": 114,
  "assign_user_id": 10,
  "assign_group_id": 20,
  "urgency": 3,
  "impact": 3,
  "priority": 3
}
```

## Consultar chamado completo

```http
GET /tickets/{ticket_id}/full
```

Retorna os dados principais do chamado e relacionamentos comuns:

- requerentes e atores;
- grupos atribuidos;
- acompanhamentos;
- tarefas;
- solucoes;
- documentos.

## Listar por categoria

```http
GET /tickets/by-category/{category_id}?limit=100
```

Exemplo:

```http
GET /tickets/by-category/287?limit=100
```

## Listar por entidade

```http
GET /tickets/by-entity/{entity_id}?limit=100
```

Exemplo:

```http
GET /tickets/by-entity/4?limit=100
```

O parametro `limit` define quantos chamados serao retornados pela busca do GLPI. O filtro de categoria/entidade e feito diretamente na busca do GLPI.

## Alterar status do chamado

```http
PATCH /tickets/{ticket_id}/status
```

```json
{
  "status": 2
}
```

Status GLPI:

- `1`: Novo
- `2`: Processando atribuido
- `3`: Processando planejado
- `4`: Pendente
- `5`: Solucionado
- `6`: Fechado

## Adicionar acompanhamento

```http
POST /tickets/{ticket_id}/followups
```

```json
{
  "descricao": "Atualizacao feita via API."
}
```

## Solucionar chamado

```http
POST /tickets/{ticket_id}/solve
```

```json
{
  "descricao": "Tarefa feita com sucesso"
}
```

## Segurança

- Nao publique a API sem `API_KEY`.
- Nao compartilhe `GLPI_APP_TOKEN` e `GLPI_USER_TOKEN`.
- Como os tokens atuais foram exibidos durante a configuracao, o ideal e
  regenerar os tokens no GLPI depois dos testes e atualizar o `.env`.
