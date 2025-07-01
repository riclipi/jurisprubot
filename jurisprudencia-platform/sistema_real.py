"""
🚀 SISTEMA REAL DE JURISPRUDÊNCIA
=================================

Interface completa conectada com todos os módulos funcionais!
"""

import streamlit as st
import pandas as pd
import json
import time
import os
from datetime import datetime
from pathlib import Path
import sys

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

# Imports do sistema
try:
    from src.scraper.tjsp_scraper import TJSPScraper
    from src.processing.pdf_processor import PDFProcessor
    from src.processing.text_chunker import TextChunker
    from src.rag.embeddings import EmbeddingsManager
    from src.rag.search_engine import JurisprudenceSearchEngine
    SISTEMA_COMPLETO = True
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    SISTEMA_COMPLETO = False

# Configuração da página
st.set_page_config(
    page_title="⚖️ Sistema Real de Jurisprudência",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main { padding-top: 1rem; }
    .stButton>button {
        background-color: #1f77b4;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #0d47a1;
        transform: translateY(-2px);
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'scraper_results' not in st.session_state:
    st.session_state.scraper_results = []
if 'processed_docs' not in st.session_state:
    st.session_state.processed_docs = []
if 'embeddings_ready' not in st.session_state:
    st.session_state.embeddings_ready = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Título
st.title("⚖️ Sistema Real de Jurisprudência TJSP")
st.markdown("**Sistema FUNCIONAL com busca real, IA e processamento completo**")

# Verificar se sistema está completo
if not SISTEMA_COMPLETO:
    st.error("❌ Sistema incompleto. Execute: python configurar_sistema.py")
    st.stop()

# Status do sistema
with st.expander("🔧 Status do Sistema", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📄 PDFs Coletados", len(list(Path("data/raw_pdfs").glob("*.pdf"))))
    with col2:
        st.metric("📝 Processados", len(list(Path("data/processed").glob("*.json"))))
    with col3:
        try:
            embeddings_manager = EmbeddingsManager()
            stats = embeddings_manager.get_collection_stats()
            st.metric("🎯 Indexados", stats.get('document_count', 0))
        except:
            st.metric("🎯 Indexados", "Erro")

# Sidebar
with st.sidebar:
    st.header("📋 Menu")
    page = st.radio(
        "Páginas:",
        ["🔍 Busca Real", "📥 Coletar PDFs", "📄 Processar", "🎯 Indexar", "💬 IA Chat"]
    )
    
    # Configurações
    st.markdown("---")
    st.subheader("⚙️ Configurações")
    
    # Verificar APIs
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            env_content = f.read()
            has_openai = "OPENAI_API_KEY=" in env_content and len(env_content.split("OPENAI_API_KEY=")[1].split("\n")[0].strip()) > 0
            has_google = "GOOGLE_API_KEY=" in env_content and len(env_content.split("GOOGLE_API_KEY=")[1].split("\n")[0].strip()) > 0
    else:
        has_openai = has_google = False
    
    st.write("🤖 **APIs Configuradas:**")
    st.write(f"• OpenAI: {'✅' if has_openai else '❌'}")
    st.write(f"• Google: {'✅' if has_google else '❌'}")
    
    if not (has_openai or has_google):
        st.warning("⚠️ Configure pelo menos uma API no arquivo .env para usar a IA")

# PÁGINA 1: BUSCA REAL
if page == "🔍 Busca Real":
    st.header("🔍 Busca Real no TJSP")
    st.markdown("**Esta página faz busca REAL no site oficial do TJSP!**")
    
    with st.form("real_search_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            termo = st.text_input(
                "Termo de busca:",
                placeholder="Ex: dano moral, contrato inadimplemento, consumidor..."
            )
        
        with col2:
            max_results = st.number_input("Máx resultados:", 1, 10, 3)
        
        # Opções avançadas
        headless = st.checkbox("Modo headless (sem mostrar navegador)", value=True)
        
        buscar_clicked = st.form_submit_button("🚀 Buscar no TJSP", type="primary")
    
    if buscar_clicked and termo:
        st.markdown("---")
        
        # Executar busca real
        with st.spinner(f"🤖 Buscando '{termo}' no site do TJSP..."):
            try:
                # Inicializar scraper
                scraper = TJSPScraper(headless=headless)
                
                # Mostrar progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🌐 Conectando com o TJSP...")
                progress_bar.progress(20)
                time.sleep(1)
                
                status_text.text("🔍 Realizando busca...")
                progress_bar.progress(50)
                
                # Busca real
                resultados = scraper.search_acordaos(termo, max_results)
                
                status_text.text("📄 Processando resultados...")
                progress_bar.progress(80)
                time.sleep(1)
                
                progress_bar.progress(100)
                status_text.text("✅ Busca concluída!")
                
                # Salvar resultados
                st.session_state.scraper_results = resultados
                
                # Mostrar resultados
                if resultados:
                    st.success(f"🎉 Encontrados {len(resultados)} acórdãos!")
                    
                    for i, resultado in enumerate(resultados):
                        with st.expander(f"📄 Acórdão {i+1}: {resultado.get('numero_acordao', 'N/A')}"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**📅 Data:** {resultado.get('data_julgamento', 'N/A')}")
                                st.write(f"**👨‍⚖️ Relator:** {resultado.get('relator', 'N/A')}")
                                st.write(f"**🏛️ Comarca:** {resultado.get('comarca', 'N/A')}")
                                st.write(f"**⚖️ Órgão:** {resultado.get('orgao_julgador', 'N/A')}")
                                
                                if resultado.get('ementa'):
                                    st.write("**📝 Ementa:**")
                                    ementa = resultado['ementa'][:300] + "..." if len(resultado['ementa']) > 300 else resultado['ementa']
                                    st.write(ementa)
                            
                            with col2:
                                if resultado.get('pdf_url'):
                                    st.write("📎 **PDF Disponível**")
                                    if st.button(f"📥 Baixar PDF", key=f"download_{i}"):
                                        with st.spinner("Baixando..."):
                                            success, path = scraper.download_pdf(
                                                resultado['pdf_url'],
                                                resultado.get('filename', f"documento_{i}.pdf")
                                            )
                                            if success:
                                                st.success(f"✅ Salvo em: {path}")
                                            else:
                                                st.error(f"❌ Erro: {path}")
                                else:
                                    st.write("📎 PDF não disponível")
                
                else:
                    st.warning("⚠️ Nenhum resultado encontrado. Tente outro termo.")
                
            except Exception as e:
                st.error(f"❌ Erro durante a busca: {str(e)}")
                st.info("💡 Isso pode acontecer se o site do TJSP estiver lento ou bloqueando requests automáticos.")

# PÁGINA 2: COLETAR PDFs
elif page == "📥 Coletar PDFs":
    st.header("📥 Coleta Automática de PDFs")
    st.markdown("**Coleta em lote de documentos do TJSP**")
    
    with st.form("batch_collection"):
        termo = st.text_input("Termo para busca em lote:", placeholder="Ex: negativação indevida")
        max_docs = st.number_input("Quantidade de documentos:", 1, 50, 10)
        
        coletar_clicked = st.form_submit_button("🚀 Iniciar Coleta em Lote", type="primary")
    
    if coletar_clicked and termo:
        st.markdown("---")
        
        with st.spinner("🤖 Executando coleta automática..."):
            try:
                scraper = TJSPScraper(headless=True)
                
                # Usar o método run_scraping que já baixa os PDFs
                resultados = scraper.run_scraping(termo, max_docs)
                
                st.success(f"✅ Coleta concluída!")
                
                # Mostrar estatísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Encontrados", len(resultados.get('acordaos', [])))
                with col2:
                    st.metric("📥 Baixados", resultados.get('downloads', {}).get('successful', 0))
                with col3:
                    st.metric("❌ Falhas", resultados.get('downloads', {}).get('failed', 0))
                
                # Mostrar tempo
                st.info(f"⏱️ Tempo total: {resultados.get('total_time', 0):.1f} segundos")
                
                # Salvar no session state
                st.session_state.scraper_results.extend(resultados.get('acordaos', []))
                
            except Exception as e:
                st.error(f"❌ Erro na coleta: {str(e)}")

# PÁGINA 3: PROCESSAR
elif page == "📄 Processar":
    st.header("📄 Processamento de PDFs")
    st.markdown("**Extrai texto e metadados dos PDFs coletados**")
    
    # Listar PDFs disponíveis
    pdf_files = list(Path("data/raw_pdfs").glob("*.pdf"))
    
    if pdf_files:
        st.write(f"📁 **PDFs encontrados:** {len(pdf_files)}")
        
        # Mostrar alguns arquivos
        with st.expander("📋 Lista de PDFs"):
            for pdf in pdf_files[:10]:  # Mostrar primeiros 10
                st.write(f"• {pdf.name}")
            if len(pdf_files) > 10:
                st.write(f"... e mais {len(pdf_files) - 10} arquivos")
        
        # Botão para processar
        if st.button("🔄 Processar Todos os PDFs", type="primary"):
            with st.spinner("📝 Processando PDFs..."):
                try:
                    processor = PDFProcessor()
                    
                    # Barra de progresso
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    resultados = []
                    for i, pdf_path in enumerate(pdf_files):
                        status_text.text(f"Processando: {pdf_path.name}")
                        
                        resultado = processor.process_pdf(pdf_path)
                        if resultado:
                            resultados.append(resultado)
                        
                        progress_bar.progress((i + 1) / len(pdf_files))
                    
                    st.success(f"✅ Processados {len(resultados)} documentos!")
                    st.session_state.processed_docs = resultados
                    
                    # Estatísticas
                    if resultados:
                        total_chars = sum(len(r['cleaned_text']) for r in resultados)
                        st.metric("📝 Total de caracteres extraídos", f"{total_chars:,}")
                
                except Exception as e:
                    st.error(f"❌ Erro no processamento: {str(e)}")
    else:
        st.info("📭 Nenhum PDF encontrado. Use a página 'Coletar PDFs' primeiro.")
        
    # Upload manual
    st.markdown("---")
    st.subheader("📎 Upload Manual de PDFs")
    
    uploaded_files = st.file_uploader(
        "Carregar PDFs:",
        type=['pdf'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Salvar arquivo
            save_path = Path("data/raw_pdfs") / uploaded_file.name
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ {uploaded_file.name} salvo!")

# PÁGINA 4: INDEXAR
elif page == "🎯 Indexar":
    st.header("🎯 Indexação Vetorial")
    st.markdown("**Cria embeddings e indexa documentos para busca por IA**")
    
    # Verificar documentos processados
    processed_files = list(Path("data/processed").glob("*.json"))
    
    if processed_files:
        st.write(f"📁 **Documentos processados:** {len(processed_files)}")
        
        if st.button("🧠 Criar Embeddings e Indexar", type="primary"):
            with st.spinner("🎯 Criando embeddings..."):
                try:
                    # Carregar documentos
                    processor = PDFProcessor()
                    chunker = TextChunker()
                    embeddings_manager = EmbeddingsManager()
                    
                    all_chunks = []
                    
                    # Processar cada arquivo
                    progress_bar = st.progress(0)
                    for i, file_path in enumerate(processed_files):
                        data = processor.load_processed_data(file_path)
                        
                        # Criar chunks
                        chunks = chunker.chunk_text(
                            data['cleaned_text'],
                            data['metadata']
                        )
                        all_chunks.extend(chunks)
                        
                        progress_bar.progress((i + 1) / len(processed_files))
                    
                    # Indexar
                    if all_chunks:
                        st.write(f"📊 Criados {len(all_chunks)} chunks")
                        
                        with st.spinner("💾 Indexando no banco vetorial..."):
                            ids = embeddings_manager.add_documents(all_chunks)
                            
                        st.success(f"✅ Indexados {len(ids)} chunks!")
                        st.session_state.embeddings_ready = True
                        
                        # Mostrar estatísticas
                        stats = embeddings_manager.get_collection_stats()
                        st.json(stats)
                    
                except Exception as e:
                    st.error(f"❌ Erro na indexação: {str(e)}")
                    st.write("💡 Verifique se todas as dependências estão instaladas")
    else:
        st.info("📭 Nenhum documento processado. Use a página 'Processar' primeiro.")

# PÁGINA 5: IA CHAT
else:  # page == "💬 IA Chat"
    st.header("💬 Chat com IA Jurídica")
    st.markdown("**Faça perguntas sobre os documentos indexados**")
    
    # Verificar se IA está configurada
    if not (has_openai or has_google):
        st.error("❌ Configure uma chave de API no arquivo .env primeiro!")
        st.markdown("""
        **Como configurar:**
        1. Abra o arquivo `.env`
        2. Adicione sua chave:
           - `OPENAI_API_KEY=sua_chave` ou
           - `GOOGLE_API_KEY=sua_chave`
        3. Reinicie a aplicação
        
        **Chaves gratuitas:**
        - Google: https://makersuite.google.com/app/apikey
        """)
    else:
        # Verificar se há documentos indexados
        try:
            embeddings_manager = EmbeddingsManager()
            stats = embeddings_manager.get_collection_stats()
            doc_count = stats.get('document_count', 0)
            
            if doc_count == 0:
                st.warning("⚠️ Nenhum documento indexado. Use a página 'Indexar' primeiro.")
            else:
                st.info(f"📚 {doc_count} documentos disponíveis para consulta")
                
                # Chat interface
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
                
                # Input do usuário
                if prompt := st.chat_input("Faça uma pergunta sobre jurisprudência..."):
                    # Adicionar pergunta
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    
                    with st.chat_message("user"):
                        st.write(prompt)
                    
                    # Gerar resposta
                    with st.chat_message("assistant"):
                        with st.spinner("🤖 Analisando documentos..."):
                            try:
                                # Usar o sistema real de IA
                                provider = "google" if has_google else "openai"
                                search_engine = JurisprudenceSearchEngine(llm_provider=provider)
                                
                                response = search_engine.answer_question(prompt, k=3)
                                
                                # Mostrar resposta
                                st.write(response['answer'])
                                
                                # Mostrar fontes
                                if response.get('sources'):
                                    with st.expander("📚 Fontes consultadas"):
                                        for i, source in enumerate(response['sources']):
                                            st.write(f"**Fonte {i+1}:**")
                                            st.write(source['content'])
                                            st.write(f"*Metadados: {source['metadata']}*")
                                            st.divider()
                                
                                # Adicionar ao histórico
                                st.session_state.chat_history.append({
                                    "role": "assistant",
                                    "content": response['answer']
                                })
                                
                            except Exception as e:
                                st.error(f"❌ Erro na IA: {str(e)}")
                                st.write("💡 Verifique se a chave de API está correta")
        
        except Exception as e:
            st.error(f"❌ Erro ao acessar embeddings: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    f"<center>⚖️ Sistema Real de Jurisprudência | "
    f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')} | "
    f"Status: {'🟢 Funcional' if SISTEMA_COMPLETO else '🔴 Incompleto'}</center>",
    unsafe_allow_html=True
)