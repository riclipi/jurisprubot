"""
Exemplo de integração do MCP Client com Streamlit
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_client import JurisprudenciaMCPClient

def main():
    st.set_page_config(
        page_title="MCP Jurisprudência",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.title("⚖️ Sistema de Gestão de Documentos Jurídicos com MCP")
    st.markdown("---")
    
    # Inicializar cliente
    if 'mcp_client' not in st.session_state:
        st.session_state.mcp_client = JurisprudenciaMCPClient()
    
    client = st.session_state.mcp_client
    
    # Sidebar para upload
    with st.sidebar:
        st.header("📤 Upload de Documento")
        
        uploaded_file = st.file_uploader(
            "Escolha um arquivo jurídico",
            type=['txt', 'pdf'],
            help="Formatos suportados: TXT, PDF"
        )
        
        if uploaded_file is not None:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            filename = uploaded_file.name
            
            if st.button("💾 Salvar Documento"):
                filepath = client.save_document(content, filename)
                st.success(f"✅ Documento salvo: {filename}")
                st.experimental_rerun()
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["📁 Documentos", "🔍 Buscar", "📊 Análise"])
    
    with tab1:
        st.header("Documentos Disponíveis")
        
        docs = client.list_documents()
        
        if docs:
            # Grid de documentos
            cols = st.columns(3)
            for i, doc in enumerate(docs):
                with cols[i % 3]:
                    with st.container():
                        st.markdown(f"**📄 {doc}**")
                        
                        if st.button(f"Ver", key=f"view_{doc}"):
                            filepath = os.path.join(client.docs_path, doc)
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            st.text_area(
                                "Conteúdo",
                                value=content,
                                height=300,
                                key=f"content_{doc}"
                            )
                        
                        if st.button(f"Analisar", key=f"analyze_{doc}"):
                            filepath = os.path.join(client.docs_path, doc)
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            analysis = client.process_legal_document(content)
                            
                            st.info(f"**Tipo:** {analysis['document_type']}")
                            
                            with st.expander("Entidades"):
                                for entity in analysis['key_entities']:
                                    st.write(f"• {entity}")
                            
                            with st.expander("Conceitos Jurídicos"):
                                for concept in analysis['legal_concepts']:
                                    st.write(f"• {concept}")
        else:
            st.info("📭 Nenhum documento encontrado. Faça upload de um documento.")
    
    with tab2:
        st.header("Busca Semântica")
        
        search_query = st.text_input(
            "Digite sua busca",
            placeholder="Ex: dano moral, indenização, código de defesa..."
        )
        
        if st.button("🔍 Buscar") and search_query:
            with st.spinner("Buscando..."):
                results = client.search_documents(search_query)
            
            if results:
                st.success(f"Encontrados {len(results)} resultados")
                
                for result in results:
                    with st.expander(f"📄 {result['filename']} (Relevância: {result['relevance']:.2f})"):
                        st.text(result['content'])
            else:
                st.warning("Nenhum resultado encontrado")
    
    with tab3:
        st.header("Análise de Documento")
        
        # Seletor de documento
        docs = client.list_documents()
        if docs:
            selected_doc = st.selectbox("Selecione um documento", docs)
            
            if st.button("🔬 Analisar Documento"):
                filepath = os.path.join(client.docs_path, selected_doc)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                with st.spinner("Analisando..."):
                    analysis = client.process_legal_document(content)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Tipo de Documento", analysis['document_type'])
                    st.metric("Entidades Encontradas", len(analysis['key_entities']))
                    st.metric("Conceitos Jurídicos", len(analysis['legal_concepts']))
                
                with col2:
                    st.subheader("📋 Resumo")
                    st.write(analysis['summary'])
                
                st.markdown("---")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.subheader("🏷️ Entidades")
                    for entity in analysis['key_entities']:
                        st.write(f"• {entity}")
                
                with col4:
                    st.subheader("⚖️ Conceitos Jurídicos")
                    for concept in analysis['legal_concepts']:
                        st.write(f"• {concept}")
        else:
            st.info("📭 Faça upload de documentos para análise")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Desenvolvido com ❤️ usando MCP (Model Context Protocol)</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()