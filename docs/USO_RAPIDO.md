# Uso rapido

## 1. Abrir Swagger

```text
http://localhost:8000/docs
```

Clique em `Authorize` e informe:

```text
X-API-Key = valor da variavel API_KEY
```

## 2. Testar GLPI

Use o endpoint:

```text
GET /tickets/session-test
```

Se retornar `ok: true`, os tokens do GLPI estao corretos.

## 3. Criar chamado

Use:

```text
POST /tickets
```

Exemplo minimo:

```json
{
  "titulo": "CHAMADO VIA API",
  "descricao": "Chamado criado para teste de integracao via API."
}
```

Os campos de entidade, categoria e requerente ja vem do `.env`.

## 4. Consultar chamado completo

```text
GET /tickets/{ticket_id}/full
```

## 5. Listar chamados por categoria

```text
GET /tickets/by-category/{category_id}?limit=100
```

## 6. Listar chamados por entidade

```text
GET /tickets/by-entity/{entity_id}?limit=100
```

## 7. Responder chamado

```text
POST /tickets/{ticket_id}/followups
```

```json
{
  "descricao": "Atualizacao do chamado."
}
```

## 8. Solucionar chamado

```text
POST /tickets/{ticket_id}/solve
```

```json
{
  "descricao": "Tarefa feita com sucesso"
}
```
