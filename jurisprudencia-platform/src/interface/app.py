"""
🏛️ INTERFACE PREMIUM - Busca de Jurisprudência TJSP
Sistema Avançado com Busca Local + Tempo Real
"""

import streamlit as st
import sys
import os

# Adicionar o diretório pai ao path para resolver imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from datetime import datetime, timedelta
import hashlib
import base64
from pathlib import Path

# Tentar importar versão completa, senão usar versão lite
try:
    from rag.simple_search import SimpleSearchEngine
except ImportError:
    st.warning("⚠️ Usando versão simplificada do sistema de busca")
    from rag.simple_search_lite import SimpleSearchEngine

# Importar busca em tempo real
try:
    from scraper.realtime_search import RealtimeJurisprudenceSearch
except ImportError:
    st.warning("⚠️ Busca em tempo real não disponível")
    # Criar classe dummy para não quebrar
    class RealtimeJurisprudenceSearch:
        def __init__(self, *args, **kwargs):
            pass
        def get_relevant_chunks(self, query):
            return []

# Configuração da página
st.set_page_config(
    page_title='🏛️ Jurisprudência TJSP Premium',
    page_icon='⚖️',
    layout='wide',
    initial_sidebar_state='expanded'
)

# CSS customizado para interface premium
st.markdown("""
<style>
    /* Tema principal */
    .main {
        padding-top: 2rem;
    }
    
    /* Toggle de modo personalizado */
    .search-mode-toggle {
        display: flex;
        background: linear-gradient(90deg, #f0f8ff 0%, #e6f3ff 100%);
        border-radius: 15px;
        padding: 8px;
        margin: 15px 0;
        border: 2px solid #4a90e2;
    }
    
    /* Cards de estatísticas */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Status indicators */
    .status-online {
        color: #00d084;
        font-weight: bold;
    }
    
    .status-local {
        color: #ffa500;
        font-weight: bold;
    }
    
    .status-offline {
        color: #ff4444;
        font-weight: bold;
    }
    
    /* Badges de resultado */
    .badge-realtime {
        background: linear-gradient(90deg, #00d084, #00a86b);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }
    
    .badge-local {
        background: linear-gradient(90deg, #ffa500, #ff8c00);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }
    
    /* Animação de loading */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Cards de exemplo */
    .example-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .example-card:hover {
        background: #e9ecef;
        border-color: #4a90e2;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Progress bar customizada */
    .custom-progress {
        width: 100%;
        height: 25px;
        background-color: #f0f0f0;
        border-radius: 12px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #4a90e2, #67b3f3);
        border-radius: 12px;
        transition: width 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES DE CACHE E ESTADO ====================

@st.cache_resource
def load_local_search_engine():
    """Carrega o sistema de busca local (cached)"""
    return SimpleSearchEngine()

@st.cache_resource  
def load_realtime_search_engine():
    """Carrega o sistema de busca em tempo real (cached)"""
    return RealtimeJurisprudenceSearch(max_results=20)

def init_session_state():
    """Inicializa estado da sessão"""
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'search_stats' not in st.session_state:
        st.session_state.search_stats = {
            'total_searches': 0,
            'local_searches': 0,
            'realtime_searches': 0,
            'successful_realtime': 0,
            'avg_response_time': 0,
            'searches_today': 0,
            'last_reset': datetime.now().date()
        }
    
    if 'query_cache' not in st.session_state:
        st.session_state.query_cache = {}
    
    if 'saved_results' not in st.session_state:
        st.session_state.saved_results = []
    
    if 'tjsp_status' not in st.session_state:
        st.session_state.tjsp_status = 'unknown'  # online, local, offline
    
    # Reset diário de estatísticas
    today = datetime.now().date()
    if st.session_state.search_stats['last_reset'] != today:
        st.session_state.search_stats['searches_today'] = 0
        st.session_state.search_stats['last_reset'] = today

# ==================== FUNÇÕES DE INTERFACE ====================

def render_header():
    """Renderiza cabeçalho premium"""
    st.markdown("""
    <div style='text-align: center; padding: 30px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px; color: white;'>
        <h1 style='margin: 0; font-size: 2.5em;'>🏛️ Jurisprudência TJSP</h1>
        <h3 style='margin: 10px 0 0 0; opacity: 0.9;'>Sistema Premium de Busca Jurídica</h3>
        <p style='margin: 5px 0 0 0; opacity: 0.8; font-size: 1.1em;'>
            Base Local (10 docs) + Busca Tempo Real (TJSP Oficial)
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_search_mode_toggle():
    """Renderiza toggle premium para modo de busca"""
    st.markdown("### 🔍 Modo de Busca")
    
    # Toggle customizado
    col1, col2 = st.columns(2)
    
    with col1:
        local_selected = st.button(
            "🏠 **BUSCA LOCAL**\n⚡ Rápida (1-3s)\n📚 10 acórdãos indexados", 
            key="local_mode",
            help="Busca na base local - sempre disponível e rápida",
            use_container_width=True
        )
    
    with col2:
        realtime_selected = st.button(
            "🌐 **TEMPO REAL**\n🔗 Site oficial TJSP\n📈 Milhares de documentos", 
            key="realtime_mode",
            help="Busca direta no site do TJSP - pode demorar 30-60s",
            use_container_width=True
        )
    
    # Determinar modo selecionado
    if local_selected:
        st.session_state.search_mode = 'local'
    elif realtime_selected:
        st.session_state.search_mode = 'realtime'
    elif 'search_mode' not in st.session_state:
        st.session_state.search_mode = 'local'
    
    # Exibir modo atual com status
    mode = st.session_state.search_mode
    if mode == 'local':
        st.success("🏠 **MODO ATIVO:** Busca Local - Rápida e Confiável")
    else:
        status_color = get_tjsp_status_color()
        st.info(f"🌐 **MODO ATIVO:** Tempo Real - {status_color}")
    
    return mode

def get_tjsp_status_color():
    """Retorna status colorido do TJSP"""
    status = st.session_state.tjsp_status
    if status == 'online':
        return '<span class="status-online">🟢 TJSP Online</span>'
    elif status == 'local':
        return '<span class="status-local">🟡 Usando Cache Local</span>'
    else:
        return '<span class="status-offline">🔴 Status Desconhecido</span>'

def render_example_queries():
    """Renderiza botões de consultas de exemplo"""
    st.markdown("### 💡 Consultas Rápidas")
    
    examples = [
        {"title": "💰 Dano Moral", "query": "dano moral indenização valor", "desc": "Casos de indenização"},
        {"title": "🏦 Negativação", "query": "negativação indevida banco serasa", "desc": "Inscrição indevida"},
        {"title": "📋 CDC", "query": "código defesa consumidor", "desc": "Direito do consumidor"},
        {"title": "⚖️ Condenação", "query": "valor condenação acórdão", "desc": "Valores de condenação"},
        {"title": "🏛️ Unanimidade", "query": "decisão unânime acórdão", "desc": "Decisões unânimes"},
        {"title": "📅 Recente 2024", "query": "2024 julgamento", "desc": "Casos de 2024"}
    ]
    
    cols = st.columns(3)
    for i, example in enumerate(examples):
        with cols[i % 3]:
            if st.button(
                f"**{example['title']}**\n{example['desc']}", 
                key=f"example_{i}",
                help=f"Buscar: {example['query']}",
                use_container_width=True
            ):
                st.session_state.example_query = example['query']
                st.rerun()

def render_search_input():
    """Renderiza campo de busca principal"""
    st.markdown("### 🔍 Digite sua Consulta")
    
    # Campo de entrada com query de exemplo se houver
    query = ""
    if 'example_query' in st.session_state:
        query = st.session_state.example_query
        del st.session_state.example_query
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        search_query = st.text_input(
            "Consulta:",
            value=query,
            placeholder="Ex: dano moral banco, negativação indevida, valor indenização...",
            label_visibility="collapsed",
            key="search_input"
        )
    
    with col2:
        search_clicked = st.button("🔍 BUSCAR", type="primary", use_container_width=True)
    
    return search_query, search_clicked

def render_progress_bar(progress, message):
    """Renderiza barra de progresso animada"""
    st.markdown(f"""
    <div class="custom-progress">
        <div class="progress-fill" style="width: {progress}%">
            {progress}% - {message}
        </div>
    </div>
    """, unsafe_allow_html=True)

def perform_search_with_progress(query, mode):
    """Executa busca com barra de progresso"""
    start_time = time.time()
    
    # Container para progresso
    progress_container = st.container()
    result_container = st.container()
    
    try:
        if mode == 'local':
            # Busca local rápida
            with progress_container:
                render_progress_bar(20, "Carregando sistema local...")
                time.sleep(0.5)
                
                render_progress_bar(60, "Processando consulta...")
                engine = load_local_search_engine()
                
                render_progress_bar(90, "Finalizando busca...")
                results = engine.search(query, top_k=10)
                
                render_progress_bar(100, "Busca concluída!")
                time.sleep(0.3)
            
            # Atualizar estatísticas
            st.session_state.search_stats['local_searches'] += 1
            st.session_state.tjsp_status = 'local'
            
        else:  # realtime
            # Busca em tempo real com progresso detalhado
            with progress_container:
                render_progress_bar(10, "Iniciando conexão com TJSP...")
                time.sleep(1)
                
                render_progress_bar(25, "Conectando ao site oficial...")
                engine = load_realtime_search_engine()
                time.sleep(1)
                
                render_progress_bar(40, "Enviando consulta...")
                time.sleep(1)
                
                render_progress_bar(60, "Analisando resultados...")
                results = engine.get_relevant_chunks(query)
                
                render_progress_bar(80, "Aplicando busca semântica...")
                time.sleep(0.5)
                
                render_progress_bar(100, "Busca concluída!")
                time.sleep(0.3)
            
            # Verificar se usou fallback
            if results and results[0].get('source') == 'local_data':
                st.session_state.tjsp_status = 'local'
                st.warning("🟡 **TJSP indisponível** - Resultados da base local")
            else:
                st.session_state.tjsp_status = 'online'
                st.session_state.search_stats['successful_realtime'] += 1
                st.success("🟢 **TJSP conectado** - Resultados em tempo real")
            
            st.session_state.search_stats['realtime_searches'] += 1
        
        # Limpar progresso
        progress_container.empty()
        
        # Calcular estatísticas
        response_time = time.time() - start_time
        update_search_stats(query, mode, len(results), response_time)
        
        return results, response_time
        
    except Exception as e:
        progress_container.empty()
        st.error(f"❌ Erro na busca: {str(e)}")
        return [], 0

def update_search_stats(query, mode, result_count, response_time):
    """Atualiza estatísticas de busca"""
    stats = st.session_state.search_stats
    
    # Estatísticas gerais
    stats['total_searches'] += 1
    stats['searches_today'] += 1
    
    # Tempo médio
    total_time = stats['avg_response_time'] * (stats['total_searches'] - 1) + response_time
    stats['avg_response_time'] = total_time / stats['total_searches']
    
    # Adicionar ao histórico
    search_entry = {
        'query': query,
        'mode': mode,
        'results': result_count,
        'time': response_time,
        'timestamp': datetime.now(),
        'status': st.session_state.tjsp_status
    }
    
    st.session_state.search_history.insert(0, search_entry)
    
    # Manter apenas últimas 10 buscas
    if len(st.session_state.search_history) > 10:
        st.session_state.search_history = st.session_state.search_history[:10]

def render_results(results, mode, response_time):
    """Renderiza resultados com badges e funcionalidades premium"""
    if not results:
        st.warning("❌ Nenhum resultado encontrado")
        st.info("💡 **Dicas:** Tente palavras-chave diferentes ou use os botões de exemplo")
        return
    
    # Header dos resultados
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        badge_class = "badge-realtime" if mode == "realtime" and st.session_state.tjsp_status == "online" else "badge-local"
        badge_text = "TEMPO REAL" if mode == "realtime" and st.session_state.tjsp_status == "online" else "LOCAL"
        
        st.markdown(f"""
        **✅ {len(results)} resultados encontrados** 
        <span class="{badge_class}">{badge_text}</span>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("⏱️ Tempo", f"{response_time:.1f}s")
    
    with col3:
        if st.button("💾 Salvar Busca", help="Salvar esta busca nos favoritos"):
            save_search_results(results, mode)
            st.success("Busca salva!")
    
    st.divider()
    
    # Exibir cada resultado
    for i, result in enumerate(results):
        with st.container():
            # Header do resultado
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### 📄 Resultado #{i+1}")
                
                # Informações específicas por tipo
                if mode == "realtime" and result.get('source') != 'local_data':
                    if result.get('processo', 'N/A') != 'N/A':
                        st.markdown(f"**⚖️ Processo:** `{result['processo']}`")
                    if result.get('relator', 'N/A') != 'N/A':
                        st.markdown(f"**👨‍⚖️ Relator:** {result['relator']}")
                    if result.get('data', 'N/A') != 'N/A':
                        st.markdown(f"**📅 Data:** {result['data']}")
                    
                    # Link direto para TJSP
                    if result.get('url'):
                        st.markdown(f"**🔗 [Ver Acórdão Completo no TJSP]({result['url']})**")
                else:
                    arquivo = result.get('metadata', {}).get('file', result.get('arquivo_local', 'N/A'))
                    st.markdown(f"**📁 Arquivo:** `{arquivo}`")
            
            with col2:
                # Score com indicador visual
                score = result.get('score', 0)
                if score > 0.7:
                    color = "🟢"
                elif score > 0.5:
                    color = "🟡"
                else:
                    color = "🟠"
                
                st.metric("Relevância", f"{score:.3f}", delta=None)
                st.markdown(f"**{color} Qualidade**")
            
            with col3:
                # Botão de ação
                if st.button(f"⭐ Favoritar", key=f"fav_{i}"):
                    add_to_favorites(result)
                    st.success("Adicionado aos favoritos!")
            
            # Conteúdo do resultado
            st.markdown("**📝 Trecho Relevante:**")
            st.markdown(f"> {result.get('text', '')}")
            
            # Separador visual
            if i < len(results) - 1:
                st.divider()

def save_search_results(results, mode):
    """Salva resultados da busca"""
    saved_search = {
        'id': hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
        'timestamp': datetime.now(),
        'mode': mode,
        'results': results,
        'count': len(results)
    }
    
    st.session_state.saved_results.insert(0, saved_search)
    
    # Manter apenas últimas 20 buscas salvas
    if len(st.session_state.saved_results) > 20:
        st.session_state.saved_results = st.session_state.saved_results[:20]

def add_to_favorites(result):
    """Adiciona resultado aos favoritos"""
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    favorite = {
        'id': hashlib.md5(str(result).encode()).hexdigest()[:8],
        'timestamp': datetime.now(),
        'result': result
    }
    
    st.session_state.favorites.insert(0, favorite)

# ==================== SIDEBAR ====================

def render_sidebar_content():
    """Conteúdo da sidebar (separado para reutilização)"""
    st.markdown("## 📊 Dashboard")
    
    # Estatísticas principais
    stats = st.session_state.search_stats
    
    # Cards de estatísticas
    st.markdown(f"""
    <div class="stat-card">
        <h3 style="margin: 0;">📈 Hoje</h3>
        <h2 style="margin: 5px 0;">{stats['searches_today']}</h2>
        <p style="margin: 0;">buscas realizadas</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stat-card">
        <h3 style="margin: 0;">⚡ Tempo Médio</h3>
        <h2 style="margin: 5px 0;">{stats['avg_response_time']:.1f}s</h2>
        <p style="margin: 0;">por consulta</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Taxa de sucesso TJSP
    if stats['realtime_searches'] > 0:
        success_rate = (stats['successful_realtime'] / stats['realtime_searches']) * 100
        st.markdown(f"""
        <div class="stat-card">
            <h3 style="margin: 0;">🎯 Taxa TJSP</h3>
            <h2 style="margin: 5px 0;">{success_rate:.0f}%</h2>
            <p style="margin: 0;">de sucesso</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Status do sistema
    st.markdown("## 🔧 Status do Sistema")
    
    # Status TJSP
    status = st.session_state.tjsp_status
    if status == 'online':
        st.success("🟢 **TJSP Online**\nConectado ao site oficial")
    elif status == 'local':
        st.warning("🟡 **Modo Local**\nUsando base indexada")
    else:
        st.info("⚪ **Status Desconhecido**\nAinda não testado")
    
    # Botão para testar conexão
    if st.button("🔄 Testar TJSP", use_container_width=True):
        test_tjsp_connection()
    
    st.divider()
    
    # Histórico de buscas
    if st.session_state.search_history:
        st.markdown("## 🕒 Histórico Recente")
        
        for i, search in enumerate(st.session_state.search_history[:5]):
            with st.expander(f"🔍 {search['query'][:20]}...", expanded=False):
                st.write(f"**Modo:** {search['mode']}")
                st.write(f"**Resultados:** {search['results']}")
                st.write(f"**Tempo:** {search['time']:.1f}s")
                st.write(f"**Quando:** {search['timestamp'].strftime('%H:%M:%S')}")
    
    st.divider()
    
    # Configurações
    st.markdown("## ⚙️ Configurações")
    
    if st.button("🗑️ Limpar Histórico", use_container_width=True):
        st.session_state.search_history = []
        st.session_state.query_cache = {}
        st.success("Histórico limpo!")
    
    if st.button("📊 Resetar Estatísticas", use_container_width=True):
        st.session_state.search_stats = {
            'total_searches': 0,
            'local_searches': 0,
            'realtime_searches': 0,
            'successful_realtime': 0,
            'avg_response_time': 0,
            'searches_today': 0,
            'last_reset': datetime.now().date()
        }
        st.success("Estatísticas resetadas!")

def test_tjsp_connection():
    """Testa conexão com TJSP"""
    with st.spinner("🔄 Testando conexão com TJSP..."):
        try:
            engine = load_realtime_search_engine()
            test_results = engine.get_relevant_chunks("teste conexao")
            
            if test_results and test_results[0].get('source') != 'local_data':
                st.session_state.tjsp_status = 'online'
                st.success("🟢 TJSP Online!")
            else:
                st.session_state.tjsp_status = 'local'
                st.warning("🟡 TJSP indisponível - usando cache")
                
        except Exception as e:
            st.session_state.tjsp_status = 'offline'
            st.error(f"🔴 Erro na conexão: {str(e)}")

def render_mcp_interface():
    """Renderizar interface MCP (funcionalidades extras)"""
    try:
        # Importar módulo MCP
        from mcp_tab import render_mcp_tab
        render_mcp_tab()
    except ImportError as e:
        st.error("⚠️ Módulos MCP não estão disponíveis")
        st.info("Certifique-se de que os arquivos MCP estão instalados corretamente")
        
        # Oferecer funcionalidade básica como fallback
        st.markdown("### 📁 Gestão Básica de Documentos")
        st.info("Interface MCP completa não disponível. Funcionalidade básica:")
        
        # Upload simples como fallback
        uploaded_file = st.file_uploader("Upload de documento", type=['txt', 'pdf'])
        if uploaded_file:
            st.success(f"Arquivo recebido: {uploaded_file.name}")
            
            # Salvar na pasta principal
            docs_path = Path("data/documents/juridicos")
            docs_path.mkdir(parents=True, exist_ok=True)
            
            file_path = docs_path / uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            st.success(f"✅ Arquivo salvo em: {file_path}")
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar interface MCP: {e}")
        st.info("A aba principal de busca continua funcionando normalmente")

# ==================== FUNÇÃO PRINCIPAL ====================

def main():
    """Função principal da aplicação"""
    # Inicializar estado
    init_session_state()
    
    # Renderizar interface
    render_header()
    
    # NOVA FUNCIONALIDADE: Tabs principais para separar Busca e MCP
    main_tab1, main_tab2 = st.tabs(["🔍 Busca Jurisprudência", "📁 Gestão MCP"])
    
    with main_tab1:
        # Layout original da busca (mantido intacto)
        col_main, col_side = st.columns([3, 1])
        
        with col_main:
            # Modo de busca
            search_mode = render_search_mode_toggle()
            
            st.divider()
            
            # Consultas de exemplo
            render_example_queries()
            
            st.divider()
            
            # Campo de busca
            query, search_clicked = render_search_input()
            
            # Executar busca
            if search_clicked and query.strip():
                with st.container():
                    st.markdown("## 📊 Resultados da Busca")
                    results, response_time = perform_search_with_progress(query, search_mode)
                    
                    if results:
                        render_results(results, search_mode, response_time)
            
            elif search_clicked:
                st.error("❌ Por favor, digite uma consulta!")
        
        # Sidebar sempre visível na aba de busca
        with col_side:
            render_sidebar_content()
    
    with main_tab2:
        # Nova aba MCP (funcionalidades extras)
        render_mcp_interface()
    
    # NOVA FUNCIONALIDADE: Botão para Interface Premium
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 ACESSAR INTERFACE PREMIUM", type="primary", use_container_width=True):
            st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin: 20px 0;'>
                <h2>🚀 INTERFACE PREMIUM DISPONÍVEL!</h2>
                <p>Execute: <code>streamlit run src/interface/interface_premium.py</code></p>
                <p><strong>Funcionalidades Premium:</strong></p>
                <p>📋 Análise Estruturada | 📝 Gerador de Minutas | 🧠 Análise Jurídica | 🔍 Busca Inteligente</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>🏛️ Sistema Premium de Jurisprudência TJSP</strong></p>
        <p>🤖 Powered by Sentence Transformers | 🔍 Busca Semântica + Web Scraping</p>
        <p>⚖️ Desenvolvido para profissionais do Direito</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()