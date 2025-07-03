# 📚 DOCUMENTAÇÃO COMPLETA DA API

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Autenticação](#autenticação)
3. [Endpoints](#endpoints)
4. [Rate Limiting](#rate-limiting)
5. [Erros](#erros)
6. [Webhooks](#webhooks)
7. [SDKs](#sdks)
8. [Exemplos](#exemplos)

## 🎯 Visão Geral

A API da Plataforma de Jurisprudência fornece acesso programático completo aos recursos do sistema.

### Base URL
```
https://api.jurisprudencia.com/v1
```

### Formato de Resposta
Todas as respostas são retornadas em JSON com a seguinte estrutura:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## 🔐 Autenticação

### OAuth 2.0 / JWT

A API usa tokens JWT para autenticação. 

#### Obter Token

```http
POST /auth/token
Content-Type: application/json

{
  "username": "usuario@example.com",
  "password": "senha_segura"
}
```

**Resposta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### Usar Token

```http
GET /api/processos
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Renovar Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### API Keys

Para integrações servidor-a-servidor:

```http
GET /api/processos
X-API-Key: your-api-key-here
```

## 📍 Endpoints

### Processos

#### Listar Processos

```http
GET /api/processos
```

**Parâmetros Query:**
- `limit` (int): Número de resultados (padrão: 20, máx: 100)
- `offset` (int): Offset para paginação
- `tribunal` (string): Filtrar por tribunal
- `status` (string): Filtrar por status
- `data_inicio` (date): Data inicial
- `data_fim` (date): Data final

**Exemplo:**
```bash
curl -X GET "https://api.jurisprudencia.com/v1/api/processos?limit=10&tribunal=TJSP" \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "numero_cnj": "0000001-23.2024.8.26.0100",
        "titulo": "Ação de Indenização",
        "tribunal": "TJSP",
        "status": "ativo",
        "valor_causa": 50000.00,
        "data_distribuicao": "2024-01-15",
        "partes": {
          "autor": ["João Silva"],
          "reu": ["Empresa XYZ Ltda"]
        }
      }
    ],
    "total": 150,
    "limit": 10,
    "offset": 0
  }
}
```

#### Obter Processo

```http
GET /api/processos/{processo_id}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "numero_cnj": "0000001-23.2024.8.26.0100",
    "titulo": "Ação de Indenização",
    "descricao": "Ação de indenização por danos morais...",
    "tribunal": "TJSP",
    "vara": "1ª Vara Cível",
    "comarca": "São Paulo",
    "status": "ativo",
    "fase_atual": "instrução",
    "valor_causa": 50000.00,
    "data_distribuicao": "2024-01-15",
    "partes": {
      "autor": [
        {
          "nome": "João Silva",
          "cpf": "***.456.789-**",
          "tipo": "pessoa_fisica"
        }
      ],
      "reu": [
        {
          "nome": "Empresa XYZ Ltda",
          "cnpj": "**.345.678/0001-**",
          "tipo": "pessoa_juridica"
        }
      ]
    },
    "movimentacoes": [
      {
        "data": "2024-01-20",
        "descricao": "Petição inicial protocolada",
        "tipo": "peticao"
      }
    ],
    "documentos": [
      {
        "id": "doc-123",
        "nome": "Petição Inicial.pdf",
        "tipo": "peticao_inicial",
        "data_upload": "2024-01-15",
        "tamanho_bytes": 245760
      }
    ]
  }
}
```

#### Criar Processo

```http
POST /api/processos
Content-Type: application/json

{
  "numero_cnj": "0000001-23.2024.8.26.0100",
  "titulo": "Ação de Cobrança",
  "descricao": "Cobrança de valores devidos...",
  "tribunal": "TJSP",
  "vara": "2ª Vara Cível",
  "comarca": "São Paulo",
  "valor_causa": 75000.00,
  "partes": {
    "autor": ["Maria Santos"],
    "reu": ["José Oliveira"]
  }
}
```

#### Atualizar Processo

```http
PUT /api/processos/{processo_id}
Content-Type: application/json

{
  "status": "arquivado",
  "fase_atual": "sentenca",
  "observacoes": "Processo julgado procedente"
}
```

#### Buscar Processos

```http
POST /api/processos/search
Content-Type: application/json

{
  "query": "indenização danos morais",
  "filters": {
    "tribunal": ["TJSP", "TJRJ"],
    "data_inicio": "2024-01-01",
    "valor_min": 10000,
    "valor_max": 100000
  },
  "sort": "relevancia",
  "limit": 20
}
```

### Documentos

#### Upload de Documento

```http
POST /api/documentos/upload
Content-Type: multipart/form-data

processo_id=123e4567-e89b-12d3-a456-426614174000
tipo=peticao
file=@documento.pdf
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "id": "doc-456",
    "nome": "documento.pdf",
    "tipo": "peticao",
    "processo_id": "123e4567-e89b-12d3-a456-426614174000",
    "url": "https://api.jurisprudencia.com/v1/api/documentos/doc-456/download",
    "hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4",
    "tamanho_bytes": 512000,
    "data_upload": "2024-01-20T14:30:00Z"
  }
}
```

#### Download de Documento

```http
GET /api/documentos/{documento_id}/download
```

#### Análise de Documento com IA

```http
POST /api/documentos/{documento_id}/analyze
Content-Type: application/json

{
  "tipo_analise": "extracao_completa",
  "incluir_embeddings": true
}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "tipo_documento": "sentenca",
    "partes": {
      "autor": ["João Silva"],
      "reu": ["Empresa ABC"]
    },
    "pedidos": [
      "Indenização por danos morais",
      "Lucros cessantes"
    ],
    "decisao": "procedente_parcial",
    "valor_condenacao": 25000.00,
    "fundamentos": [
      "Art. 186 do Código Civil",
      "Súmula 227 do STJ"
    ],
    "embeddings": {
      "modelo": "text-embedding-3-large",
      "vetor": [0.123, -0.456, ...],
      "dimensoes": 1536
    }
  }
}
```

### Jurisprudência

#### Buscar Jurisprudência

```http
POST /api/jurisprudencia/search
Content-Type: application/json

{
  "query": "dano moral consumidor",
  "tribunais": ["STJ", "STF"],
  "data_inicio": "2020-01-01",
  "tipo_decisao": ["acordao", "sumula"],
  "usar_ia": true,
  "limit": 50
}
```

#### Análise de Precedentes

```http
POST /api/jurisprudencia/analyze
Content-Type: application/json

{
  "processo_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipos_analise": ["precedentes_favoraveis", "teses_contrarias", "evolucao_entendimento"]
}
```

### Inteligência Artificial

#### Gerar Petição

```http
POST /api/ia/gerar-peticao
Content-Type: application/json

{
  "tipo": "contestacao",
  "processo_id": "123e4567-e89b-12d3-a456-426614174000",
  "argumentos": [
    "Inexistência de dano moral",
    "Culpa exclusiva da vítima"
  ],
  "tom": "formal",
  "incluir_jurisprudencia": true
}
```

#### Resumir Processo

```http
POST /api/ia/resumir-processo
Content-Type: application/json

{
  "processo_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipo_resumo": "executivo",
  "max_palavras": 500
}
```

#### Prever Resultado

```http
POST /api/ia/prever-resultado
Content-Type: application/json

{
  "processo_id": "123e4567-e89b-12d3-a456-426614174000",
  "incluir_analise": true
}
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "predicao": {
      "resultado": "procedente_parcial",
      "confianca": 0.78,
      "valor_estimado": {
        "min": 15000,
        "max": 35000,
        "provavel": 25000
      }
    },
    "analise": {
      "fatores_favoraveis": [
        "Jurisprudência consolidada",
        "Provas documentais robustas"
      ],
      "fatores_desfavoraveis": [
        "Ausência de dano material comprovado"
      ],
      "precedentes_similares": [
        {
          "numero": "REsp 1.234.567/SP",
          "similaridade": 0.89,
          "resultado": "procedente_parcial",
          "valor": 20000
        }
      ]
    }
  }
}
```

### Estatísticas e Analytics

#### Dashboard Geral

```http
GET /api/stats/dashboard
```

**Resposta:**
```json
{
  "success": true,
  "data": {
    "resumo": {
      "total_processos": 15420,
      "processos_ativos": 8750,
      "processos_mes": 320,
      "taxa_sucesso": 0.67
    },
    "por_tribunal": {
      "TJSP": 5420,
      "TJRJ": 3200,
      "STJ": 890
    },
    "por_tipo": {
      "civel": 8900,
      "trabalhista": 4200,
      "criminal": 2320
    },
    "evolucao_mensal": [
      {"mes": "2024-01", "total": 280},
      {"mes": "2024-02", "total": 320}
    ]
  }
}
```

#### Relatórios Customizados

```http
POST /api/stats/relatorio
Content-Type: application/json

{
  "tipo": "desempenho_advogado",
  "periodo": {
    "inicio": "2024-01-01",
    "fim": "2024-12-31"
  },
  "metricas": ["taxa_sucesso", "tempo_medio", "valor_recuperado"],
  "formato": "pdf"
}
```

### Webhooks

#### Registrar Webhook

```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://seu-sistema.com/webhook",
  "eventos": ["processo.atualizado", "documento.adicionado", "sentenca.publicada"],
  "secret": "seu-secret-aqui"
}
```

#### Eventos Disponíveis

- `processo.criado`
- `processo.atualizado`
- `processo.arquivado`
- `documento.adicionado`
- `documento.assinado`
- `movimentacao.nova`
- `sentenca.publicada`
- `prazo.proximo`
- `audiencia.marcada`

#### Payload do Webhook

```json
{
  "evento": "processo.atualizado",
  "timestamp": "2024-01-20T14:30:00Z",
  "data": {
    "processo_id": "123e4567-e89b-12d3-a456-426614174000",
    "alteracoes": {
      "status": {
        "anterior": "ativo",
        "novo": "sentenciado"
      }
    }
  },
  "assinatura": "sha256=abcdef123456..."
}
```

## ⚡ Rate Limiting

### Limites

| Tipo de Conta | Requisições/Hora | Burst |
|---------------|------------------|-------|
| Free          | 100              | 10    |
| Basic         | 1.000            | 50    |
| Professional  | 10.000           | 200   |
| Enterprise    | Ilimitado        | 1000  |

### Headers de Rate Limit

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642680000
```

### Resposta de Rate Limit Excedido

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Limite de requisições excedido",
    "retry_after": 3600
  }
}
```

## ❌ Erros

### Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400    | Bad Request - Requisição inválida |
| 401    | Unauthorized - Token inválido ou expirado |
| 403    | Forbidden - Sem permissão |
| 404    | Not Found - Recurso não encontrado |
| 422    | Unprocessable Entity - Validação falhou |
| 429    | Too Many Requests - Rate limit excedido |
| 500    | Internal Server Error - Erro no servidor |

### Formato de Erro

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Erro de validação",
    "details": [
      {
        "field": "numero_cnj",
        "message": "Formato inválido"
      }
    ]
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## 🛠️ SDKs

### Python SDK

```python
from jurisprudencia_sdk import JurisprudenciaClient

# Inicializar cliente
client = JurisprudenciaClient(api_key="sua-api-key")

# Buscar processos
processos = client.processos.listar(tribunal="TJSP", limit=10)

# Criar processo
novo_processo = client.processos.criar({
    "numero_cnj": "0000001-23.2024.8.26.0100",
    "titulo": "Ação de Cobrança"
})

# Upload de documento
with open("peticao.pdf", "rb") as f:
    doc = client.documentos.upload(
        processo_id=novo_processo.id,
        arquivo=f,
        tipo="peticao"
    )
```

### JavaScript/TypeScript SDK

```typescript
import { JurisprudenciaClient } from '@jurisprudencia/sdk';

// Inicializar cliente
const client = new JurisprudenciaClient({
  apiKey: 'sua-api-key'
});

// Buscar processos
const processos = await client.processos.listar({
  tribunal: 'TJSP',
  limit: 10
});

// Webhook handler
app.post('/webhook', (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  
  if (client.webhooks.verify(signature, req.body)) {
    const event = req.body;
    
    switch (event.evento) {
      case 'processo.atualizado':
        console.log('Processo atualizado:', event.data);
        break;
    }
    
    res.status(200).send('OK');
  } else {
    res.status(401).send('Invalid signature');
  }
});
```

## 📝 Exemplos

### Fluxo Completo de Processo

```python
import asyncio
from jurisprudencia_sdk import JurisprudenciaClient

async def criar_processo_completo():
    client = JurisprudenciaClient(api_key="sua-api-key")
    
    # 1. Criar processo
    processo = await client.processos.criar({
        "numero_cnj": "0000001-23.2024.8.26.0100",
        "titulo": "Ação de Indenização",
        "descricao": "Ação de indenização por danos morais",
        "tribunal": "TJSP",
        "valor_causa": 50000
    })
    
    # 2. Upload de documentos
    with open("peticao_inicial.pdf", "rb") as f:
        doc_peticao = await client.documentos.upload(
            processo_id=processo.id,
            arquivo=f,
            tipo="peticao_inicial"
        )
    
    # 3. Análise com IA
    analise = await client.ia.analisar_documento(
        documento_id=doc_peticao.id,
        tipo_analise="extracao_completa"
    )
    
    # 4. Buscar jurisprudência
    jurisprudencia = await client.jurisprudencia.buscar({
        "query": analise.data.pedidos[0],
        "tribunais": ["STJ"],
        "limit": 10
    })
    
    # 5. Prever resultado
    predicao = await client.ia.prever_resultado(
        processo_id=processo.id
    )
    
    print(f"Processo criado: {processo.numero_cnj}")
    print(f"Chance de sucesso: {predicao.confianca:.0%}")
    print(f"Valor estimado: R$ {predicao.valor_provavel:,.2f}")

# Executar
asyncio.run(criar_processo_completo())
```

### Monitoramento em Tempo Real

```javascript
const { JurisprudenciaClient } = require('@jurisprudencia/sdk');
const EventSource = require('eventsource');

const client = new JurisprudenciaClient({
  apiKey: 'sua-api-key'
});

// SSE para atualizações em tempo real
const eventSource = new EventSource(
  'https://api.jurisprudencia.com/v1/stream/processos',
  {
    headers: {
      'Authorization': `Bearer ${client.apiKey}`
    }
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Atualização:', data);
  
  // Processar atualização
  if (data.tipo === 'nova_movimentacao') {
    notificarUsuario(data.processo_id, data.movimentacao);
  }
};

eventSource.onerror = (error) => {
  console.error('Erro SSE:', error);
};
```

---

**Última atualização**: Janeiro 2025