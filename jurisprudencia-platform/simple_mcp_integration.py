"""
Integração Simples dos MCPs com Streamlit
Sem complexidade - apenas o essencial
"""

import os
import streamlit as st
from pathlib import Path

# Configuração da pasta de documentos
DOCS_PATH = Path("data/documents/juridicos")
DOCS_PATH.mkdir(parents=True, exist_ok=True)

def main():
    st.set_page_config(page_title="Sistema Jurídico Simples", page_icon="⚖️")
    
    st.title("⚖️ Sistema Jurídico com MCP")
    st.markdown("---")
    
    # Menu lateral
    with st.sidebar:
        st.header("📁 Gerenciar Documentos")
        
        # Upload simples
        uploaded_file = st.file_uploader("Enviar documento", type=['txt', 'pdf'])
        
        if uploaded_file and st.button("💾 Salvar"):
            # Salvar arquivo
            file_path = DOCS_PATH / uploaded_file.name
            
            if uploaded_file.type == "application/pdf":
                # Salvar PDF
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"PDF salvo: {uploaded_file.name}")
            else:
                # Salvar TXT
                content = uploaded_file.read().decode('utf-8', errors='ignore')
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(content)
                st.success(f"Documento salvo: {uploaded_file.name}")
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📚 Documentos", "🔍 Buscar", "📊 Análise Rápida"])
    
    with tab1:
        st.header("Documentos Disponíveis")
        
        # Listar arquivos
        files = list(DOCS_PATH.glob("*"))
        
        if files:
            for file in sorted(files):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.text(f"📄 {file.name}")
                
                with col2:
                    if st.button("Ver", key=f"view_{file.name}"):
                        if file.suffix == '.txt':
                            content = file.read_text(encoding='utf-8', errors='ignore')
                            st.text_area("Conteúdo", content, height=300)
                        else:
                            st.info("Visualização de PDF não implementada")
        else:
            st.info("Nenhum documento encontrado. Faça upload na barra lateral.")
    
    with tab2:
        st.header("Busca Simples")
        
        # Campo de busca
        search_term = st.text_input("Digite o termo de busca")
        
        if search_term and st.button("🔍 Buscar"):
            results = []
            
            # Busca simples em arquivos TXT
            for file in DOCS_PATH.glob("*.txt"):
                content = file.read_text(encoding='utf-8', errors='ignore')
                if search_term.lower() in content.lower():
                    # Encontrar contexto
                    pos = content.lower().find(search_term.lower())
                    start = max(0, pos - 100)
                    end = min(len(content), pos + 100)
                    context = content[start:end]
                    
                    results.append({
                        'file': file.name,
                        'context': f"...{context}..."
                    })
            
            # Mostrar resultados
            if results:
                st.success(f"Encontrados {len(results)} resultados")
                for result in results:
                    with st.expander(f"📄 {result['file']}"):
                        st.text(result['context'])
            else:
                st.warning("Nenhum resultado encontrado")
    
    with tab3:
        st.header("Análise Rápida")
        
        # Selecionar arquivo
        files = list(DOCS_PATH.glob("*.txt"))
        
        if files:
            selected_file = st.selectbox(
                "Escolha um documento",
                [f.name for f in files]
            )
            
            if st.button("📊 Analisar"):
                # Carregar arquivo
                file_path = DOCS_PATH / selected_file
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Análise básica
                st.subheader("📈 Estatísticas")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Caracteres", len(content))
                
                with col2:
                    st.metric("Palavras", len(content.split()))
                
                with col3:
                    st.metric("Linhas", len(content.splitlines()))
                
                # Termos jurídicos comuns
                st.subheader("⚖️ Termos Jurídicos Encontrados")
                
                termos = [
                    "acórdão", "sentença", "recurso", "apelação",
                    "dano moral", "indenização", "responsabilidade civil",
                    "código de defesa do consumidor", "juros", "correção monetária"
                ]
                
                encontrados = []
                for termo in termos:
                    if termo.lower() in content.lower():
                        count = content.lower().count(termo.lower())
                        encontrados.append(f"• {termo}: {count} ocorrência(s)")
                
                if encontrados:
                    for item in encontrados:
                        st.text(item)
                else:
                    st.info("Nenhum termo jurídico comum encontrado")
                
                # Valores monetários
                st.subheader("💰 Valores Encontrados")
                
                import re
                valores = re.findall(r'R\$\s?[\d.,]+', content)
                
                if valores:
                    for valor in set(valores):
                        st.text(f"• {valor}")
                else:
                    st.info("Nenhum valor monetário encontrado")
        else:
            st.info("Nenhum documento disponível para análise")
    
    # Rodapé
    st.markdown("---")
    st.markdown("Sistema simples de gestão de documentos jurídicos com MCP")

if __name__ == "__main__":
    main()