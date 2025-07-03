# Configuração dos MCPs para o Projeto Jurídico

## Status da Configuração

✅ **Concluído:**
- TypeScript instalado globalmente
- mcp-cerebra-legal-server compilado e funcionando
- Diretórios de dados criados
- Arquivo de configuração do Claude Desktop criado em `~/.config/Claude/claude_desktop_config.json`

⚠️ **Pendente:**
- Instalar Bun para o legal-context-ce (requer instalação manual)
- Configurar credenciais do Clio (se usar integração com Clio)

## MCPs Configurados

### 1. mcp-cerebra-legal-server ✅
- **Status**: Compilado e pronto
- **Funcionalidade**: Análise e raciocínio legal estruturado
- **Tool**: `legal_think` - para análise legal complexa

### 2. legal-context-ce ⚠️
- **Status**: Requer Bun para executar
- **Funcionalidade**: Integração com Clio e indexação de documentos
- **Instalação do Bun**: 
  ```bash
  curl -fsSL https://bun.sh/install | bash
  ```

### 3. filesystem ✅
- **Status**: Configurado
- **Diretório**: `/workspaces/jurisprubot/jurisprudencia-platform/data/documents`
- **Funcionalidade**: Acesso a documentos locais

### 4. sequential-thinking ✅
- **Status**: Configurado
- **Funcionalidade**: Raciocínio sequencial para problemas complexos

## Como Usar

1. **Reinicie o Claude Desktop** após a configuração

2. **Verifique os MCPs ativos** no Claude Desktop

3. **Para o legal-context-ce com Clio**, configure as variáveis:
   ```bash
   export CLIO_CLIENT_ID="seu_client_id"
   export CLIO_CLIENT_SECRET="seu_secret"
   export CLIO_REDIRECT_URI="http://localhost:3000/oauth/callback"
   ```

## Estrutura de Diretórios

```
/workspaces/jurisprubot/
├── jurisprudencia-platform/
│   └── data/
│       └── documents/
│           └── juridicos/   # Documentos jurídicos
├── data/
│   └── lancedb/            # Base vetorial do legal-context
├── mcp-cerebra-legal-server/
│   └── build/              # Servidor compilado
└── legal-context-ce/       # Requer Bun
```

## Solução de Problemas

1. **Erro "Bun not found"**: Instale o Bun seguindo as instruções acima
2. **MCPs não aparecem**: Reinicie o Claude Desktop
3. **Erro de permissão**: Verifique as permissões dos diretórios de dados