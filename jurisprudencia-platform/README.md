# Plataforma de Jurisprudência

Sistema completo para coleta, processamento e busca semântica de jurisprudência do Tribunal de Justiça de São Paulo (TJSP) utilizando técnicas de RAG (Retrieval-Augmented Generation).

## 📋 Descrição do Projeto

Esta plataforma oferece uma solução integrada para:
- Coleta automatizada de documentos jurídicos do TJSP
- Processamento e extração de texto de PDFs
- Indexação vetorial para busca semântica
- Interface web intuitiva com assistente jurídico
- Análise e comparação de jurisprudências

## 🚀 Funcionalidades

### 1. Coleta de Documentos (Web Scraping)
- Busca automatizada no portal do TJSP
- Download de PDFs de acórdãos e decisões
- Extração de metadados (número do processo, data, relator, etc.)

### 2. Processamento de Documentos
- Extração de texto de PDFs
- Limpeza e normalização de texto
- Chunking inteligente preservando contexto
- Extração automática de informações-chave

### 3. Busca Semântica (RAG)
- Embeddings com Sentence Transformers
- Armazenamento vetorial com ChromaDB
- Busca por similaridade semântica
- Reranking para melhor relevância

### 4. Assistente Jurídico
- Respostas baseadas em documentos reais
- Citação de fontes
- Resumo de documentos
- Comparação entre casos

### 5. Interface Web
- Dashboard interativo com Streamlit
- Visualização de resultados
- Chat com assistente
- Estatísticas e métricas

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **LangChain** - Framework para aplicações LLM
- **ChromaDB** - Banco de dados vetorial
- **Sentence Transformers** - Modelos de embedding
- **Streamlit** - Interface web
- **Selenium** - Web scraping
- **BeautifulSoup4** - Parsing HTML
- **PyPDF2** - Processamento de PDFs
- **OpenAI/Google Gemini** - LLMs para geração de respostas

## 📦 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/jurisprudencia-platform.git
cd jurisprudencia-platform
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione suas chaves de API:
```
OPENAI_API_KEY=sua_chave_openai
GOOGLE_API_KEY=sua_chave_google
TJSP_BASE_URL=https://esaj.tjsp.jus.br
```

### 5. Instale o ChromeDriver
Para o web scraping funcionar, você precisa do ChromeDriver instalado:
- Baixe de: https://chromedriver.chromium.org/
- Adicione ao PATH do sistema

## 🎯 Como Usar

### 1. Iniciar a aplicação
```bash
streamlit run src/interface/streamlit_app.py
```

### 2. Coletar documentos
1. Acesse a aba "📥 Coletar Documentos"
2. Digite os termos de busca
3. Configure datas e quantidade
4. Clique em "Iniciar Coleta"

### 3. Processar PDFs
1. Acesse a aba "📄 Processar PDFs"
2. Faça upload ou processe PDFs existentes
3. Aguarde o processamento

### 4. Indexar documentos
1. Acesse "🗃️ Gerenciar Base de Dados"
2. Clique em "Indexar documentos processados"

### 5. Buscar jurisprudência
1. Acesse "🔍 Buscar Jurisprudência"
2. Digite sua consulta
3. Analise os resultados

### 6. Usar o assistente
1. Acesse "💬 Assistente Jurídico"
2. Faça perguntas sobre jurisprudência
3. Receba respostas com fontes citadas

## 📁 Estrutura do Projeto

```
jurisprudencia-platform/
├── data/                    # Dados locais
│   ├── raw_pdfs/           # PDFs baixados
│   ├── processed/          # Documentos processados
│   └── vectorstore/        # Base vetorial
├── src/                    # Código fonte
│   ├── scraper/           # Módulo de coleta
│   ├── processing/        # Processamento de texto
│   ├── rag/              # Busca e geração
│   └── interface/        # Interface web
├── notebooks/             # Jupyter notebooks
├── config/               # Configurações
├── tests/               # Testes
└── requirements.txt     # Dependências
```

## 🔧 Configuração Avançada

### Parâmetros de Chunking
Edite `config/settings.py`:
```python
CHUNK_CONFIG = {
    "chunk_size": 1000,      # Tamanho dos chunks
    "chunk_overlap": 200,    # Sobreposição
}
```

### Modelos de Embedding
```python
EMBEDDING_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "device": "cpu",  # ou "cuda" para GPU
}
```

### Configurações do LLM
```python
LLM_CONFIG = {
    "openai": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.2,
    }
}
```

## 📊 Exemplos de Uso

### Busca semântica
```python
from src.rag.search_engine import JurisprudenceSearchEngine

engine = JurisprudenceSearchEngine()
results = engine.search("contrato inadimplemento danos morais", k=5)
```

### Processamento de PDF
```python
from src.processing.pdf_processor import PDFProcessor

processor = PDFProcessor()
result = processor.process_pdf(Path("documento.pdf"))
```

### Web scraping
```python
from src.scraper.tjsp_scraper import TJSPScraper

scraper = TJSPScraper()
docs = scraper.scrape_and_download("ação rescisória", max_results=10)
```

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Crie um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## ⚠️ Avisos Legais

- Este projeto é apenas para fins educacionais e de pesquisa
- Respeite os termos de uso do TJSP
- Não faça requisições excessivas ao site
- Os documentos coletados são públicos

## 🐛 Problemas Conhecidos

- O scraping pode falhar se o site do TJSP mudar sua estrutura
- Documentos muito grandes podem demorar para processar
- Requer boa quantidade de memória RAM para grandes bases

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no GitHub.