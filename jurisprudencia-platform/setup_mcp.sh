#!/bin/bash

echo "🚀 Configuração Simples dos MCPs"
echo "================================"
echo ""

# 1. Criar estrutura de pastas
echo "📁 Criando pastas..."
mkdir -p data/documents/juridicos
mkdir -p data/lancedb
mkdir -p mcp_config
echo "✅ Pastas criadas!"
echo ""

# 2. Verificar documentos
echo "📄 Documentos disponíveis:"
ls -la data/documents/juridicos/ | grep -E "\.(txt|pdf)$" | wc -l
echo ""

# 3. Criar arquivo de configuração simples
echo "⚙️ Criando configuração..."
cat > mcp_config/config.json << 'EOF'
{
  "mcp_servers": {
    "filesystem": {
      "description": "Acesso aos documentos jurídicos",
      "path": "data/documents/juridicos"
    },
    "cerebra_legal": {
      "description": "Análise jurídica avançada",
      "path": "/workspaces/jurisprubot/mcp-cerebra-legal-server/build/index.js"
    }
  }
}
EOF
echo "✅ Configuração criada!"
echo ""

# 4. Instruções finais
echo "📋 PRÓXIMOS PASSOS:"
echo "==================="
echo ""
echo "1. Para testar o sistema:"
echo "   streamlit run simple_mcp_integration.py"
echo ""
echo "2. Para usar o Filesystem MCP:"
echo "   npx -y @modelcontextprotocol/server-filesystem \$(pwd)/data/documents/juridicos"
echo ""
echo "3. Para instalar o Bun (necessário para legal-context):"
echo "   curl -fsSL https://bun.sh/install | bash"
echo ""
echo "✅ Configuração concluída!"