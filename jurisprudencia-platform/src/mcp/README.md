# MCP Client para Jurisprudência

## Visão Geral

O `JurisprudenciaMCPClient` é um wrapper Python que facilita a integração entre seu projeto Streamlit e os servidores MCP (Model Context Protocol) configurados no Claude Desktop.

## Funcionalidades

### 1. Gestão de Documentos
- **Salvar documentos**: Armazena documentos jurídicos no sistema de arquivos
- **Listar documentos**: Lista todos os documentos disponíveis
- **Buscar documentos**: Busca semântica em documentos

### 2. Análise Jurídica
- **Extração de entidades**: Identifica números de processo, valores monetários
- **Conceitos jurídicos**: Identifica termos jurídicos relevantes
- **Processamento contextual**: Análise completa de documentos

## Instalação

```bash
# Já está incluído no projeto
# Basta importar:
from mcp.mcp_client import JurisprudenciaMCPClient
```

## Uso Básico

### Inicialização

```python
from mcp.mcp_client import JurisprudenciaMCPClient

# Criar instância do cliente
client = JurisprudenciaMCPClient()
```

### Salvar Documento

```python
# Salvar um acórdão
content = "ACÓRDÃO - Processo: 1234567-89.2023.8.26.0100..."
filepath = client.save_document(content, "acordao_001.txt")
print(f"Documento salvo em: {filepath}")
```

### Buscar Documentos

```python
# Buscar por termo
results = client.search_documents("dano moral")

for result in results:
    print(f"Arquivo: {result['filename']}")
    print(f"Relevância: {result['relevance']}")
    print(f"Preview: {result['content'][:100]}...")
```

### Análise de Documento

```python
# Processar documento jurídico
analysis = client.process_legal_document(content)

print(f"Tipo: {analysis['document_type']}")
print(f"Entidades: {analysis['key_entities']}")
print(f"Conceitos: {analysis['legal_concepts']}")
```

## Integração com Streamlit

### Exemplo Básico

```python
import streamlit as st
from mcp.mcp_client import JurisprudenciaMCPClient

# Inicializar cliente
if 'mcp_client' not in st.session_state:
    st.session_state.mcp_client = JurisprudenciaMCPClient()

client = st.session_state.mcp_client

# Upload de arquivo
uploaded_file = st.file_uploader("Escolha um documento")
if uploaded_file:
    content = uploaded_file.read().decode('utf-8')
    client.save_document(content, uploaded_file.name)
    st.success("Documento salvo!")

# Buscar documentos
query = st.text_input("Buscar")
if query:
    results = client.search_documents(query)
    for result in results:
        st.write(result['filename'])
```

### Aplicação Completa

Execute a aplicação de exemplo:

```bash
cd src/mcp
streamlit run streamlit_integration.py
```

## Estrutura de Dados

### Resultado de Busca

```python
{
    'filename': 'acordao_001.txt',
    'content': 'Preview do conteúdo...',
    'relevance': 0.8
}
```

### Análise de Documento

```python
{
    'document_type': 'acordao',
    'key_entities': ['Processo: 1234567-89.2023.8.26.0100', 'Valor: R$ 10.000,00'],
    'legal_concepts': ['dano moral', 'indenização'],
    'summary': 'Resumo do documento...'
}
```

## Extensões Futuras

### 1. Integração com Legal-Context MCP
```python
# TODO: Implementar busca vetorial com LanceDB
def vector_search(self, query: str, top_k: int = 5):
    # Usar embeddings para busca semântica
    pass
```

### 2. Integração com Cerebra Legal
```python
# TODO: Usar legal_think para análise avançada
def advanced_legal_analysis(self, content: str):
    # Chamar MCP cerebra-legal-server
    pass
```

### 3. Cache e Performance
```python
# TODO: Implementar cache de análises
@lru_cache(maxsize=100)
def cached_analysis(self, doc_hash: str):
    pass
```

## Testes

Execute os testes:

```bash
python test_mcp_client.py
```

## Solução de Problemas

### Erro: Diretório não encontrado
```python
# O cliente cria diretórios automaticamente
client = JurisprudenciaMCPClient()  # Diretórios criados aqui
```

### Erro: Encoding de arquivo
```python
# Use errors='ignore' ao ler arquivos
content = file.read().decode('utf-8', errors='ignore')
```

### Performance lenta em buscas
```python
# Para muitos documentos, considere implementar índice
# ou usar a integração com LanceDB do legal-context
```

## Contribuindo

1. Adicione novos extractors em `extract_entities()`
2. Expanda termos jurídicos em `extract_legal_concepts()`
3. Implemente integrações com MCPs externos