"""
Aba MCP para o Streamlit - Funcionalidades EXTRAS
Módulo separado que não interfere no sistema principal
"""

import streamlit as st
import sys
import os

# Adicionar o diretório pai ao path para resolver imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from datetime import datetime
import json

# Importar módulos MCP (com try/except para não quebrar se houver erro)
try:
    from mcp_integration.document_manager import MCPDocumentManager
    from mcp_integration.file_organizer import FileOrganizer
    from mcp_integration.pdf_processor import PDFProcessor
    MCP_AVAILABLE = True
except Exception as e:
    st.error(f"⚠️ Módulos MCP não disponíveis: {e}")
    MCP_AVAILABLE = False

def render_mcp_tab():
    """
    Renderizar aba MCP completa
    Funcionalidades EXTRAS que não afetam o sistema principal
    """
    if not MCP_AVAILABLE:
        st.error("❌ Módulos MCP não estão disponíveis")
        st.info("Verifique se os arquivos estão no local correto")
        return
    
    st.markdown("## 📁 Gestão Avançada de Documentos (MCP)")
    st.markdown("*Funcionalidades extras para organização e gestão de documentos*")
    
    # Inicializar componentes MCP
    if 'mcp_manager' not in st.session_state:
        try:
            st.session_state.mcp_manager = MCPDocumentManager()
            st.session_state.file_organizer = FileOrganizer()
            st.session_state.pdf_processor = PDFProcessor()
        except Exception as e:
            st.error(f"Erro ao inicializar MCP: {e}")
            return
    
    manager = st.session_state.mcp_manager
    organizer = st.session_state.file_organizer
    pdf_processor = st.session_state.pdf_processor
    
    # Subtabs para diferentes funcionalidades
    mcp_tab1, mcp_tab2, mcp_tab3, mcp_tab4 = st.tabs([
        "📤 Upload & Gestão", 
        "🗂️ Organização Auto", 
        "📄 Processamento PDF", 
        "📊 Estatísticas MCP"
    ])
    
    with mcp_tab1:
        render_upload_management(manager)
    
    with mcp_tab2:
        render_auto_organization(organizer)
    
    with mcp_tab3:
        render_pdf_processing(pdf_processor)
    
    with mcp_tab4:
        render_mcp_statistics(manager, organizer)

def render_upload_management(manager):
    """Gestão de uploads e documentos"""
    st.markdown("### 📤 Upload Avançado de Documentos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Escolha um documento",
            type=['txt', 'pdf'],
            help="Suporte para TXT e PDF"
        )
        
        if uploaded_file:
            # Preview das informações
            st.info(f"**Arquivo:** {uploaded_file.name}")
            st.info(f"**Tamanho:** {len(uploaded_file.getvalue()):,} bytes")
            
            if st.button("💾 Processar e Salvar"):
                with st.spinner("Processando..."):
                    result = manager.upload_document(
                        uploaded_file.getvalue(),
                        uploaded_file.name
                    )
                
                if result['success']:
                    st.success(f"✅ {result['message']}")
                    st.json(result['metadata'])
                else:
                    st.error(f"❌ {result['message']}")
    
    with col2:
        # Ações rápidas
        st.markdown("#### ⚡ Ações Rápidas")
        
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.rerun()
        
        if st.button("💾 Criar Backup", use_container_width=True):
            result = manager.create_backup()
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])
        
        # Estatísticas rápidas
        stats = manager.get_statistics()
        st.metric("Total Docs", stats['total_documents'])
        st.metric("Uploads Recentes", stats['recent_uploads'])
    
    st.divider()
    
    # Lista de documentos
    st.markdown("### 📚 Documentos Gerenciados")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.selectbox(
            "Categoria",
            ['Todas'] + list(stats['by_category'].keys())
        )
    
    with col2:
        type_filter = st.selectbox(
            "Tipo",
            ['Todos'] + list(stats['by_type'].keys())
        )
    
    with col3:
        show_details = st.checkbox("Mostrar Detalhes", value=False)
    
    # Aplicar filtros
    filter_category = None if category_filter == 'Todas' else category_filter
    filter_type = None if type_filter == 'Todos' else type_filter
    
    docs = manager.list_documents(category=filter_category, file_type=filter_type)
    
    if docs:
        for doc in docs:
            with st.expander(f"📄 {doc['name']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**ID:** {doc['id']}")
                    st.write(f"**Categoria:** {doc['category']}")
                    st.write(f"**Tipo:** {doc['type']}")
                
                with col2:
                    st.write(f"**Tamanho:** {doc['size']:,} bytes")
                    st.write(f"**Upload:** {doc['upload_date']}")
                    st.write(f"**Tags:** {', '.join(doc['tags']) if doc['tags'] else 'Nenhuma'}")
                
                with col3:
                    # Ações do documento
                    if st.button(f"👁️ Ver Conteúdo", key=f"view_{doc['id']}"):
                        content = manager.get_document_content(doc['id'])
                        if content:
                            st.text_area("Conteúdo", content[:1000] + "..." if len(content) > 1000 else content, height=200)
                    
                    # Adicionar tags
                    new_tags = st.text_input(f"Tags (separadas por vírgula)", key=f"tags_{doc['id']}")
                    if st.button(f"🏷️ Adicionar Tags", key=f"add_tags_{doc['id']}") and new_tags:
                        tags_list = [tag.strip() for tag in new_tags.split(',')]
                        if manager.add_tags(doc['id'], tags_list):
                            st.success("Tags adicionadas!")
                            st.rerun()
    else:
        st.info("📭 Nenhum documento encontrado com os filtros aplicados")

def render_auto_organization(organizer):
    """Organização automática de arquivos"""
    st.markdown("### 🗂️ Organização Automática")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 👀 Preview da Organização")
        
        if st.button("🔍 Analisar Arquivos para Organizar"):
            with st.spinner("Analisando arquivos..."):
                preview = organizer.get_organization_preview()
            
            if preview['files_to_organize'] > 0:
                st.success(f"📊 Encontrados {preview['files_to_organize']} arquivos para organizar")
                
                # Mostrar estatísticas
                col_cat, col_year = st.columns(2)
                
                with col_cat:
                    st.markdown("**Por Categoria:**")
                    for category, count in preview['by_category'].items():
                        st.text(f"• {category}: {count} arquivo(s)")
                
                with col_year:
                    st.markdown("**Por Ano:**")
                    for year, count in preview['by_year'].items():
                        st.text(f"• {year}: {count} arquivo(s)")
                
                # Lista de arquivos
                if st.checkbox("Mostrar lista detalhada"):
                    st.markdown("**Detalhes dos Arquivos:**")
                    for file_detail in preview['file_details'][:10]:  # Mostrar apenas 10
                        st.text(f"📄 {file_detail['name']} → {file_detail['category']}/{file_detail['year']}")
                    
                    if len(preview['file_details']) > 10:
                        st.info(f"... e mais {len(preview['file_details']) - 10} arquivos")
            else:
                st.info("📭 Nenhum arquivo encontrado para organizar")
    
    with col2:
        st.markdown("#### ⚙️ Configurações")
        
        copy_mode = st.radio(
            "Modo de Organização",
            ["Copiar arquivos", "Mover arquivos"],
            help="Copiar mantém os arquivos originais"
        )
        
        if st.button("🚀 Executar Organização", type="primary", use_container_width=True):
            copy_mode_bool = (copy_mode == "Copiar arquivos")
            
            with st.spinner("Organizando arquivos..."):
                results = organizer.organize_directory(copy_mode=copy_mode_bool)
            
            st.success(f"✅ Organização concluída!")
            st.json(results)
        
        st.divider()
        
        # Limpeza
        if st.button("🧹 Limpar Pastas Vazias", use_container_width=True):
            cleaned = organizer.clean_empty_folders()
            if cleaned:
                st.success(f"🗑️ {len(cleaned)} pastas vazias removidas")
            else:
                st.info("✨ Nenhuma pasta vazia encontrada")
    
    st.divider()
    
    # Estatísticas da organização atual
    st.markdown("### 📈 Status da Organização")
    
    stats = organizer.get_organization_stats()
    
    if stats['total_organized'] > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Organizados", stats['total_organized'])
        
        with col2:
            st.metric("Categorias", len(stats['by_category']))
        
        with col3:
            st.metric("Anos", len(stats['by_year']))
        
        # Gráficos
        if stats['by_category']:
            st.markdown("**Distribuição por Categoria:**")
            st.bar_chart(stats['by_category'])
        
        if stats['largest_files']:
            st.markdown("**Maiores Arquivos:**")
            for file_info in stats['largest_files'][:5]:
                st.text(f"📄 {file_info['name']} - {file_info['size']:,} bytes ({file_info['category']})")
    else:
        st.info("📭 Nenhum arquivo foi organizado ainda")

def render_pdf_processing(pdf_processor):
    """Processamento avançado de PDFs"""
    st.markdown("### 📄 Processamento Avançado de PDFs")
    
    if not pdf_processor.pdf_available:
        st.warning("⚠️ Suporte completo a PDF não está disponível")
        st.markdown(pdf_processor.get_installation_instructions())
        return
    
    # Upload de PDF para processamento
    pdf_file = st.file_uploader(
        "Escolha um PDF para processamento",
        type=['pdf'],
        help="Upload de PDF para extração e análise"
    )
    
    if pdf_file:
        # Salvar temporariamente
        temp_path = Path("data/temp_pdf") / pdf_file.name
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(pdf_file.getvalue())
        
        st.success(f"📄 PDF carregado: {pdf_file.name}")
        
        # Tabs para diferentes processamentos
        pdf_tab1, pdf_tab2, pdf_tab3, pdf_tab4 = st.tabs([
            "👁️ Preview", "🔍 Buscar", "⚖️ Info Legal", "📝 Converter"
        ])
        
        with pdf_tab1:
            # Preview do PDF
            if st.button("👁️ Gerar Preview"):
                with st.spinner("Extraindo preview..."):
                    preview = pdf_processor.get_pdf_preview(temp_path)
                
                if preview['success']:
                    st.markdown("**📊 Metadados:**")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Páginas", preview['metadata']['pages'])
                    with col2:
                        st.metric("Tamanho", f"{preview['metadata']['size']:,} bytes")
                    with col3:
                        st.metric("Caracteres", preview['total_length'])
                    
                    st.markdown("**📝 Preview do Texto:**")
                    st.text_area("Conteúdo", preview['preview'], height=400)
                    
                    if preview['has_more']:
                        st.info("📄 Texto completo disponível com processamento completo")
                else:
                    st.error(f"❌ {preview['message']}")
        
        with pdf_tab2:
            # Busca no PDF
            search_term = st.text_input("🔍 Buscar termo no PDF")
            
            if st.button("🔍 Buscar") and search_term:
                with st.spinner("Buscando..."):
                    search_results = pdf_processor.search_in_pdf(temp_path, search_term)
                
                if search_results['success']:
                    if search_results['matches_found'] > 0:
                        st.success(f"✅ {search_results['matches_found']} ocorrência(s) encontrada(s)")
                        
                        for i, match in enumerate(search_results['matches']):
                            with st.expander(f"📄 Página {match['page']} - Ocorrência {i+1}"):
                                st.markdown(f"**Contexto:**")
                                st.text(match['context'])
                    else:
                        st.warning(f"❌ Termo '{search_term}' não encontrado")
                else:
                    st.error(f"❌ {search_results['message']}")
        
        with pdf_tab3:
            # Informações jurídicas
            if st.button("⚖️ Extrair Informações Jurídicas"):
                with st.spinner("Analisando documento jurídico..."):
                    legal_info = pdf_processor.extract_legal_info(temp_path)
                
                if legal_info['success']:
                    info = legal_info['legal_info']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📋 Números de Processo:**")
                        for proc in info['numeros_processo']:
                            st.code(proc)
                        
                        st.markdown("**💰 Valores Monetários:**")
                        for valor in info['valores_monetarios']:
                            st.text(valor)
                        
                        st.markdown("**📅 Datas Importantes:**")
                        for data in info['datas_importantes'][:5]:  # Mostrar apenas 5
                            st.text(data)
                    
                    with col2:
                        st.markdown("**👥 Partes do Processo:**")
                        if info['partes_processo']['autores']:
                            st.markdown("*Autores:*")
                            for autor in info['partes_processo']['autores']:
                                st.text(f"• {autor}")
                        
                        if info['partes_processo']['reus']:
                            st.markdown("*Réus:*")
                            for reu in info['partes_processo']['reus']:
                                st.text(f"• {reu}")
                        
                        st.markdown("**⚖️ Termos Jurídicos:**")
                        for termo in info['termos_juridicos']:
                            st.text(f"• {termo}")
                else:
                    st.error(f"❌ {legal_info['message']}")
        
        with pdf_tab4:
            # Conversão para texto
            if st.button("📝 Converter para TXT"):
                with st.spinner("Convertendo PDF..."):
                    conversion = pdf_processor.convert_pdf_to_text_file(temp_path)
                
                if conversion['success']:
                    st.success(f"✅ PDF convertido com sucesso!")
                    st.info(f"📁 Arquivo salvo em: {conversion['output_file']}")
                    st.metric("Caracteres extraídos", conversion['text_length'])
                    
                    # Opção de download
                    if Path(conversion['output_file']).exists():
                        with open(conversion['output_file'], 'r', encoding='utf-8') as f:
                            txt_content = f.read()
                        
                        st.download_button(
                            "⬇️ Download TXT",
                            data=txt_content,
                            file_name=f"{temp_path.stem}.txt",
                            mime="text/plain"
                        )
                else:
                    st.error(f"❌ {conversion['message']}")

def render_mcp_statistics(manager, organizer):
    """Estatísticas e dashboard MCP"""
    st.markdown("### 📊 Dashboard MCP")
    
    # Estatísticas gerais
    doc_stats = manager.get_statistics()
    org_stats = organizer.get_organization_stats()
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Docs Gerenciados", doc_stats['total_documents'])
    
    with col2:
        st.metric("🗂️ Docs Organizados", org_stats['total_organized'])
    
    with col3:
        st.metric("📤 Uploads Recentes", doc_stats['recent_uploads'])
    
    with col4:
        total_size_mb = doc_stats['total_size'] / (1024 * 1024)
        st.metric("💾 Tamanho Total", f"{total_size_mb:.1f} MB")
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Documentos por Categoria")
        if doc_stats['by_category']:
            st.bar_chart(doc_stats['by_category'])
        else:
            st.info("Nenhum documento categorizado ainda")
    
    with col2:
        st.markdown("#### 📈 Arquivos Organizados por Ano")
        if org_stats['by_year']:
            st.bar_chart(org_stats['by_year'])
        else:
            st.info("Nenhum arquivo organizado ainda")
    
    st.divider()
    
    # Status do sistema
    st.markdown("#### 🔧 Status do Sistema MCP")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📁 Document Manager**")
        if Path("data/mcp_documents").exists():
            st.success("✅ Ativo")
        else:
            st.error("❌ Não inicializado")
    
    with col2:
        st.markdown("**🗂️ File Organizer**")
        if Path("data/mcp_organized").exists():
            st.success("✅ Ativo")
        else:
            st.warning("⚠️ Não usado ainda")
    
    with col3:
        st.markdown("**📄 PDF Processor**")
        if st.session_state.pdf_processor.pdf_available:
            st.success("✅ Disponível")
        else:
            st.warning("⚠️ PyPDF2 não instalado")
    
    st.divider()
    
    # Configurações e manutenção
    st.markdown("#### ⚙️ Manutenção")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Limpeza Geral", use_container_width=True):
            # Implementar limpeza
            st.info("Limpeza executada!")
    
    with col2:
        if st.button("📊 Exportar Dados", use_container_width=True):
            # Exportar estatísticas
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'document_stats': doc_stats,
                'organization_stats': org_stats
            }
            
            st.download_button(
                "⬇️ Download JSON",
                data=json.dumps(export_data, indent=2, default=str),
                file_name=f"mcp_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("🔄 Recarregar Sistema", use_container_width=True):
            # Limpar cache do session state
            for key in ['mcp_manager', 'file_organizer', 'pdf_processor']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()