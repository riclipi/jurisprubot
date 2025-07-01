# 🚀 Como Ativar as Funções Reais do Sistema

## 1. Para BUSCA REAL funcionar:

O sistema já está pronto! Basta executar:
```bash
python teste_completo.py
```

Isso vai:
- Abrir o Chrome
- Navegar no TJSP
- Buscar jurisprudências de verdade

## 2. Para o botão VER ÍNTEGRA funcionar:

Precisamos conectar a interface com o sistema de busca. Isso já está programado no arquivo original `src/interface/streamlit_app.py`.

## 3. Para o ASSISTENTE com IA funcionar:

### Opção A - Usar OpenAI (ChatGPT):
1. Vá em https://platform.openai.com/api-keys
2. Crie uma conta e gere uma API key
3. Adicione no arquivo .env:
   ```
   OPENAI_API_KEY=sua_chave_aqui
   ```

### Opção B - Usar Google (Gratuito):
1. Vá em https://makersuite.google.com/app/apikey
2. Gere uma API key gratuita
3. Adicione no arquivo .env:
   ```
   GOOGLE_API_KEY=sua_chave_aqui
   ```

## 4. Para ativar TUDO de uma vez:

```bash
# Instalar o que falta
pip install langchain chromadb sentence-transformers openai google-generativeai

# Executar o sistema completo
python -m streamlit run src/interface/streamlit_app.py
```

## 💡 Dica:

A versão simplificada (app_simples.py) é ótima para:
- Mostrar para investidores
- Demonstrar o conceito
- Testar a interface

A versão completa (src/interface/streamlit_app.py) é para:
- Uso real
- Produção
- Quando tiver as APIs configuradas