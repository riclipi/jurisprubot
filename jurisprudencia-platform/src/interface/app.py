"""
Interface Web SIMPLES para busca de jurisprudência
Usando Streamlit
"""

import streamlit as st
import sys
import os
sys.path.append('.')
from src.rag.simple_search import SimpleSearchEngine

# Configuração da página
st.set_page_config(
    page_title='Busca de Jurisprudência TJSP',
    page_icon='⚖️',
    layout='wide'
)

# Carregar sistema apenas uma vez (cache)
@st.cache_resource
def load_search_engine():
    """Carrega o sistema de busca (cached)"""
    with st.spinner('🚀 Carregando sistema de busca...'):
        return SimpleSearchEngine()

def display_results(results):
    """
    Exibe os resultados da busca de forma organizada
    
    Args:
        results: Lista de resultados da busca
    """
    if not results:
        st.warning("❌ Nenhum resultado encontrado para sua consulta.")
        st.info("💡 **Dicas:**\n- Tente palavras-chave diferentes\n- Use termos jurídicos como 'dano moral', 'indenização', 'negativação'\n- Seja mais específico ou mais geral")
        return
    
    st.success(f"✅ Encontrados **{len(results)}** resultados relevantes")
    
    # Exibir cada resultado
    for i, result in enumerate(results):
        with st.container():
            # Header do resultado
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### 📄 Resultado #{result['rank']}")
                st.markdown(f"**📁 Arquivo:** `{result['metadata']['file']}`")
            
            with col2:
                # Score com cor baseada na relevância
                score = result['score']
                if score > 0.7:
                    score_color = "🟢"
                elif score > 0.5:
                    score_color = "🟡"
                else:
                    score_color = "🟠"
                
                st.markdown(f"**Relevância:** {score_color} {score:.3f}")
            
            # Conteúdo do resultado
            st.markdown("**📝 Trecho encontrado:**")
            st.markdown(f"> {result['text']}")
            
            # Separador visual
            if i < len(results) - 1:
                st.divider()

def main():
    """Interface principal"""
    
    # Header bonito
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>⚖️ Busca de Jurisprudência TJSP</h1>
        <h3>Sistema de Busca Semântica em Acórdãos sobre Negativação Indevida</h3>
        <p style='color: #666; font-size: 16px;'>
            Encontre rapidamente trechos relevantes em 10 acórdãos do Tribunal de Justiça de São Paulo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Seção de busca
    st.markdown("## 🔍 Faça sua consulta")
    
    # Campo de entrada principal
    col1, col2 = st.columns([4, 1])
    
    with col1:
        query = st.text_input(
            "Digite sua pergunta:",
            placeholder="Ex: negativação indevida banco, dano moral indenização, valor da condenação...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_button = st.button("🔍 Buscar", type="primary", use_container_width=True)
    
    # Botões de exemplo
    st.markdown("**💡 Ou teste com estas consultas de exemplo:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    example_queries = [
        "negativação indevida banco",
        "dano moral indenização",
        "serasa spc nome",
        "valor da condenação"
    ]
    
    selected_example = None
    
    with col1:
        if st.button("🏦 Negativação Indevida", use_container_width=True):
            selected_example = example_queries[0]
    
    with col2:
        if st.button("💰 Dano Moral", use_container_width=True):
            selected_example = example_queries[1]
    
    with col3:
        if st.button("📋 Serasa/SPC", use_container_width=True):
            selected_example = example_queries[2]
    
    with col4:
        if st.button("⚖️ Condenação", use_container_width=True):
            selected_example = example_queries[3]
    
    # Usar query selecionada se houver
    if selected_example:
        query = selected_example
        st.rerun()
    
    # Executar busca
    if search_button or selected_example:
        if not query.strip():
            st.error("❌ Por favor, digite uma consulta!")
            return
        
        try:
            # Carregar sistema de busca
            search_engine = load_search_engine()
            
            # Executar busca
            with st.spinner(f'🔍 Buscando por: "{query}"...'):
                results = search_engine.search(query, top_k=5)
            
            # Exibir resultados
            st.divider()
            st.markdown("## 📊 Resultados da Busca")
            display_results(results)
            
        except Exception as e:
            st.error(f"❌ Erro ao realizar busca: {str(e)}")
    
    # Sidebar com informações
    with st.sidebar:
        st.markdown("## ℹ️ Sobre o Sistema")
        
        st.markdown("""
        **📚 Base de Dados:**
        - 10 acórdãos do TJSP
        - Tema: Negativação Indevida
        - 209 trechos indexados
        
        **🔧 Tecnologia:**
        - Busca semântica
        - Sentence Transformers
        - Embeddings de 384 dimensões
        
        **🎯 Como usar:**
        1. Digite sua pergunta
        2. Clique em "Buscar"
        3. Analise os resultados por relevância
        
        **💡 Dicas:**
        - Use termos jurídicos específicos
        - Combine palavras-chave
        - Scores >0.5 são mais relevantes
        """)
        
        st.divider()
        
        st.markdown("## 📈 Estatísticas")
        try:
            search_engine = load_search_engine()
            st.metric("Documentos", "10")
            st.metric("Chunks", len(search_engine.chunks))
            st.metric("Modelo", "all-MiniLM-L6-v2")
        except:
            st.info("Sistema carregando...")

if __name__ == "__main__":
    main()