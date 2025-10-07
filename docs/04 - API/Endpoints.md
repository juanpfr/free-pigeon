# 🔗 Documentação da API REST

## Endpoints Principais
| Método | Endpoint | Descrição |
|--------|-----------|-----------|
| GET | /api/products/ | Lista todos os produtos |
| POST | /api/products/ | Cadastra novo produto |
| GET | /api/orders/ | Lista pedidos do usuário |
| POST | /api/payments/ | Processa pagamento via Stripe |

## Autenticação
A API utiliza **JWT** (JSON Web Token) para autenticação.

## Exemplo de Requisição
```bash
curl -X POST http://localhost:8000/api/token/      -d "username=admin&password=123456"
```
