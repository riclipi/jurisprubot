"""Streamlit interface for the jurisprudence platform."""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ..scraper.tjsp_scraper import TJSPScraper
from ..processing.pdf_processor import PDFProcessor
from ..processing.text_chunker import TextChunker
from ..rag.embeddings import EmbeddingsManager
from ..rag.search_engine import JurisprudenceSearchEngine
from config.settings import STREAMLIT_CONFIG, RAW_PDF_DIR, PROCESSED_DIR

# Page configuration
st.set_page_config(
    page_title=STREAMLIT_CONFIG['page_title'],
    page_icon=STREAMLIT_CONFIG['page_icon'],
    layout=STREAMLIT_CONFIG['layout'],
    initial_sidebar_state=STREAMLIT_CONFIG['initial_sidebar_state']
)


class JurisprudenceApp:
    """Main Streamlit application for jurisprudence platform."""
    
    def __init__(self):
        """Initialize the application."""
        self.init_session_state()
        self.load_components()
    
    def init_session_state(self):
        """Initialize session state variables."""
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'processed_docs' not in st.session_state:
            st.session_state.processed_docs = []
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
    
    def load_components(self):
        """Load application components."""
        try:
            self.scraper = TJSPScraper()
            self.processor = PDFProcessor()
            self.chunker = TextChunker()
            self.embeddings_manager = EmbeddingsManager()
            self.search_engine = JurisprudenceSearchEngine()
        except Exception as e:
            st.error(f"Erro ao carregar componentes: {str(e)}")
    
    def run(self):
        """Run the main application."""
        st.title("⚖️ Plataforma de Jurisprudência")
        st.markdown("Sistema de busca e análise de jurisprudência do TJSP")
        
        # Sidebar
        with st.sidebar:
            st.header("Menu")
            page = st.radio(
                "Selecione uma página:",
                ["🔍 Buscar Jurisprudência", 
                 "📥 Coletar Documentos",
                 "📄 Processar PDFs",
                 "🗃️ Gerenciar Base de Dados",
                 "💬 Assistente Jurídico",
                 "📊 Estatísticas"]
            )
        
        # Route to appropriate page
        if page == "🔍 Buscar Jurisprudência":
            self.search_page()
        elif page == "📥 Coletar Documentos":
            self.scraper_page()
        elif page == "📄 Processar PDFs":
            self.processor_page()
        elif page == "🗃️ Gerenciar Base de Dados":
            self.database_page()
        elif page == "💬 Assistente Jurídico":
            self.assistant_page()
        elif page == "📊 Estatísticas":
            self.statistics_page()
    
    def search_page(self):
        """Search jurisprudence page."""
        st.header("🔍 Buscar Jurisprudência")
        
        # Search form
        with st.form("search_form"):
            query = st.text_input(
                "Digite sua consulta:",
                placeholder="Ex: contrato de compra e venda inadimplemento"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                num_results = st.slider("Número de resultados:", 1, 20, 5)
            with col2:
                search_type = st.selectbox(
                    "Tipo de busca:",
                    ["Semântica", "Por palavras-chave", "Híbrida"]
                )
            
            search_button = st.form_submit_button("🔍 Buscar")
        
        # Perform search
        if search_button and query:
            with st.spinner("Buscando..."):
                try:
                    results = self.search_engine.search(query, k=num_results)
                    st.session_state.search_results = results
                    
                    st.success(f"Encontrados {len(results)} resultados")
                    
                    # Display results
                    for i, result in enumerate(results):
                        with st.expander(f"Resultado {i+1} - Score: {result['similarity_score']:.3f}"):
                            st.write("**Conteúdo:**")
                            st.write(result['content'][:500] + "...")
                            
                            st.write("**Metadados:**")
                            st.json(result['metadata'])
                            
                            # Action buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("📄 Ver completo", key=f"view_{i}"):
                                    st.session_state.selected_doc = result
                            with col2:
                                if st.button("📊 Resumir", key=f"summary_{i}"):
                                    summary = self.search_engine.summarize_document(result['content'])
                                    st.write("**Resumo:**")
                                    st.write(summary)
                            with col3:
                                if st.button("💾 Salvar", key=f"save_{i}"):
                                    st.success("Documento salvo!")
                
                except Exception as e:
                    st.error(f"Erro na busca: {str(e)}")
    
    def scraper_page(self):
        """Document collection page."""
        st.header("📥 Coletar Documentos do TJSP")
        
        with st.form("scraper_form"):
            query = st.text_input(
                "Termo de busca:",
                placeholder="Ex: contrato de locação"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Data inicial (opcional)")
            with col2:
                end_date = st.date_input("Data final (opcional)")
            
            max_results = st.number_input(
                "Número máximo de documentos:",
                min_value=1,
                max_value=100,
                value=10
            )
            
            scrape_button = st.form_submit_button("🚀 Iniciar Coleta")
        
        if scrape_button and query:
            with st.spinner("Coletando documentos..."):
                try:
                    # Format dates
                    start_str = start_date.strftime("%d/%m/%Y") if start_date else None
                    end_str = end_date.strftime("%d/%m/%Y") if end_date else None
                    
                    # Scrape documents
                    results = self.scraper.scrape_and_download(
                        query=query,
                        start_date=start_str,
                        end_date=end_str,
                        max_results=max_results
                    )
                    
                    # Display results
                    st.success(f"Coletados {len(results)} documentos")
                    
                    # Create dataframe
                    df = pd.DataFrame(results)
                    st.dataframe(df[['case_number', 'judgment_date', 'court', 'local_path']])
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Baixar relatório CSV",
                        data=csv,
                        file_name=f"coleta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                except Exception as e:
                    st.error(f"Erro na coleta: {str(e)}")
    
    def processor_page(self):
        """PDF processing page."""
        st.header("📄 Processar PDFs")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Carregar PDFs",
            type=['pdf'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Save uploaded file
                pdf_path = RAW_PDF_DIR / uploaded_file.name
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Arquivo {uploaded_file.name} carregado")
        
        # Process existing PDFs
        st.subheader("Processar PDFs existentes")
        
        pdf_files = list(RAW_PDF_DIR.glob("*.pdf"))
        if pdf_files:
            st.write(f"Encontrados {len(pdf_files)} PDFs para processar")
            
            if st.button("🔄 Processar todos os PDFs"):
                with st.spinner("Processando..."):
                    progress_bar = st.progress(0)
                    
                    results = []
                    for i, pdf_file in enumerate(pdf_files):
                        result = self.processor.process_pdf(pdf_file)
                        if result:
                            results.append(result)
                        progress_bar.progress((i + 1) / len(pdf_files))
                    
                    st.success(f"Processados {len(results)} documentos")
                    st.session_state.processed_docs = results
                    
                    # Show sample
                    if results:
                        st.subheader("Amostra do processamento:")
                        st.json(results[0]['metadata'])
        else:
            st.info("Nenhum PDF encontrado para processar")
    
    def database_page(self):
        """Database management page."""
        st.header("🗃️ Gerenciar Base de Dados")
        
        # Get stats
        stats = self.embeddings_manager.get_collection_stats()
        
        # Display stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Documentos", stats['document_count'])
        with col2:
            st.metric("Modelo", stats['embedding_model'].split('/')[-1])
        with col3:
            st.metric("Dimensão", stats['vector_dimension'])
        
        st.subheader("Ações")
        
        # Index documents
        if st.button("📥 Indexar documentos processados"):
            processed_files = self.processor.get_processed_files()
            
            if processed_files:
                with st.spinner("Indexando documentos..."):
                    all_chunks = []
                    
                    for file_path in processed_files:
                        data = self.processor.load_processed_data(file_path)
                        chunks = self.chunker.chunk_text(
                            data['cleaned_text'],
                            data['metadata']
                        )
                        all_chunks.extend(chunks)
                    
                    # Add to vector store
                    ids = self.embeddings_manager.add_documents(all_chunks)
                    st.success(f"Indexados {len(ids)} chunks")
            else:
                st.warning("Nenhum documento processado encontrado")
        
        # Clear database
        if st.button("🗑️ Limpar base de dados", type="secondary"):
            if st.checkbox("Confirmo que desejo limpar toda a base"):
                self.embeddings_manager.delete_collection()
                st.success("Base de dados limpa")
                st.experimental_rerun()
    
    def assistant_page(self):
        """Legal assistant chat page."""
        st.header("💬 Assistente Jurídico")
        
        # Chat interface
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Input
        if prompt := st.chat_input("Digite sua pergunta jurídica..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.write(prompt)
            
            # Get response
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    try:
                        response = self.search_engine.answer_question(prompt)
                        
                        # Display answer
                        st.write(response['answer'])
                        
                        # Display sources
                        with st.expander("📚 Fontes consultadas"):
                            for source in response['sources']:
                                st.write(f"**{source['metadata'].get('case_number', 'N/A')}**")
                                st.write(source['content'])
                                st.divider()
                        
                        # Add to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response['answer']
                        })
                        
                    except Exception as e:
                        st.error(f"Erro ao gerar resposta: {str(e)}")
        
        # Clear chat button
        if st.button("🗑️ Limpar conversa"):
            st.session_state.chat_history = []
            st.experimental_rerun()
    
    def statistics_page(self):
        """Statistics and analytics page."""
        st.header("📊 Estatísticas")
        
        # Collection stats
        stats = self.embeddings_manager.get_collection_stats()
        
        st.subheader("Base de Dados")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de documentos", stats['document_count'])
        with col2:
            pdf_count = len(list(RAW_PDF_DIR.glob("*.pdf")))
            st.metric("PDFs coletados", pdf_count)
        
        # Processing stats
        st.subheader("Processamento")
        processed_count = len(list(PROCESSED_DIR.glob("*.json")))
        st.metric("Documentos processados", processed_count)
        
        # Search stats
        if st.session_state.search_results:
            st.subheader("Última busca")
            scores = [r['similarity_score'] for r in st.session_state.search_results]
            
            df = pd.DataFrame({
                'Resultado': range(1, len(scores) + 1),
                'Score': scores
            })
            
            st.bar_chart(df.set_index('Resultado'))
        
        # System info
        st.subheader("Informações do Sistema")
        st.json({
            "Modelo de embeddings": stats['embedding_model'],
            "Dimensão dos vetores": stats['vector_dimension'],
            "Coleção": stats['collection_name'],
            "Diretório de PDFs": str(RAW_PDF_DIR),
            "Diretório processado": str(PROCESSED_DIR)
        })


def main():
    """Main function to run the app."""
    app = JurisprudenceApp()
    app.run()


if __name__ == "__main__":
    main()