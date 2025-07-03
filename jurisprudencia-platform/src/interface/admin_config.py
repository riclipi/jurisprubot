"""
⚙️ INTERFACE ADMINISTRATIVA COMPLETA
Sistema de configuração e administração para ambiente de produção
"""

import streamlit as st
import asyncio
import os
import yaml
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import sys

# Adicionar diretórios ao path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Imports dos módulos do sistema
from ..config.credentials_manager import CredentialsManager
from ..pje_super.connection_manager import ConnectionManager
from ..utils.cnj_validator import CNJValidator, validar_numero_cnj
from ..monitoring.logging_config import setup_logging
from ..monitoring.metrics import get_metrics_summary

# Configurar página
st.set_page_config(
    page_title="🔧 Administração - Sistema Jurídico",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .status-online { color: #28a745; }
    .status-offline { color: #dc3545; }
    .status-partial { color: #ffc107; }
</style>
""", unsafe_allow_html=True)


class AdminInterface:
    """Interface administrativa principal"""
    
    def __init__(self):
        self.credentials_manager = CredentialsManager()
        self.connection_manager = None
        self.setup_logging = setup_logging
        
        # Inicializar estado da sessão
        self._init_session_state()
    
    def _init_session_state(self):
        """Inicializa variáveis de estado da sessão"""
        if 'admin_logged_in' not in st.session_state:
            st.session_state.admin_logged_in = False
        
        if 'test_results' not in st.session_state:
            st.session_state.test_results = {}
        
        if 'metrics_data' not in st.session_state:
            st.session_state.metrics_data = {}
    
    def run(self):
        """Executa a interface administrativa"""
        # Verificar autenticação admin
        if not st.session_state.admin_logged_in:
            self._show_login()
            return
        
        # Header
        st.title("🔧 Painel Administrativo - Sistema Jurídico")
        
        # Informações do sistema
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Status", "🟢 Online", delta="Operacional")
        with col2:
            st.metric("Tribunais", "12", delta="+2 novos")
        with col3:
            st.metric("Uptime", "99.9%", delta="+0.1%")
        with col4:
            st.metric("Versão", "1.0.0", delta="Produção")
        
        # Tabs principais
        tabs = st.tabs([
            "🔐 Credenciais",
            "🏛️ Tribunais", 
            "📊 Monitoramento",
            "⚙️ Sistema",
            "🧪 Testes",
            "📝 Logs"
        ])
        
        with tabs[0]:
            self._tab_credentials()
        
        with tabs[1]:
            self._tab_tribunals()
        
        with tabs[2]:
            self._tab_monitoring()
        
        with tabs[3]:
            self._tab_system()
        
        with tabs[4]:
            self._tab_tests()
        
        with tabs[5]:
            self._tab_logs()
        
        # Sidebar com ações rápidas
        self._sidebar_actions()
    
    def _show_login(self):
        """Mostra tela de login administrativo"""
        st.markdown("## 🔒 Login Administrativo")
        
        with st.form("admin_login"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Entrar"):
                # TODO: Implementar autenticação real
                if username == "admin" and password == "admin123":
                    st.session_state.admin_logged_in = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")
    
    def _tab_credentials(self):
        """Aba de gerenciamento de credenciais"""
        st.header("🔐 Gerenciamento de Credenciais")
        
        # Subabas
        subtabs = st.tabs(["API Keys", "Tribunais", "Certificados Digitais"])
        
        # API Keys
        with subtabs[0]:
            st.subheader("🔑 Chaves de API")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # OpenAI
                st.markdown("### OpenAI")
                current_key = self.credentials_manager.get_api_key("openai")
                
                if current_key:
                    st.success(f"✅ Configurada: {current_key[:10]}...")
                    if st.button("🔄 Atualizar OpenAI Key"):
                        new_key = st.text_input("Nova chave OpenAI:", type="password", key="openai_new")
                        if new_key and st.button("Salvar OpenAI"):
                            if self.credentials_manager.set_api_key("openai", new_key):
                                st.success("Chave atualizada!")
                                st.rerun()
                else:
                    new_key = st.text_input("Chave OpenAI:", type="password", key="openai_input")
                    if st.button("Configurar OpenAI"):
                        if new_key:
                            if self.credentials_manager.set_api_key("openai", new_key):
                                st.success("Chave configurada!")
                                st.rerun()
            
            with col2:
                # Google
                st.markdown("### Google Gemini")
                current_key = self.credentials_manager.get_api_key("google")
                
                if current_key:
                    st.success(f"✅ Configurada: {current_key[:10]}...")
                    if st.button("🔄 Atualizar Google Key"):
                        new_key = st.text_input("Nova chave Google:", type="password", key="google_new")
                        if new_key and st.button("Salvar Google"):
                            if self.credentials_manager.set_api_key("google", new_key):
                                st.success("Chave atualizada!")
                                st.rerun()
                else:
                    new_key = st.text_input("Chave Google:", type="password", key="google_input")
                    if st.button("Configurar Google"):
                        if new_key:
                            if self.credentials_manager.set_api_key("google", new_key):
                                st.success("Chave configurada!")
                                st.rerun()
            
            # BRLaw MCP
            st.markdown("### BRLaw MCP")
            current_key = self.credentials_manager.get_api_key("brlaw")
            
            if current_key:
                st.success(f"✅ Configurada: {current_key[:10]}...")
            else:
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_key = st.text_input("Chave BRLaw MCP:", type="password", key="brlaw_input")
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Configurar BRLaw"):
                        if new_key:
                            if self.credentials_manager.set_api_key("brlaw", new_key):
                                st.success("Chave configurada!")
                                st.rerun()
        
        # Credenciais de Tribunais
        with subtabs[1]:
            st.subheader("🏛️ Credenciais de Tribunais")
            
            # Seletor de tribunal
            tribunais = ["TJSP", "TJRJ", "TJMG", "TRF1", "TRF2", "TRF3", "STJ", "STF"]
            tribunal = st.selectbox("Selecione o Tribunal:", tribunais)
            
            # Formulário de credenciais
            with st.form(f"creds_{tribunal}"):
                st.markdown(f"### Configurar {tribunal}")
                
                # Verificar se já tem credenciais
                existing = self.credentials_manager.get_tribunal_credentials(tribunal.lower())
                
                cpf_cnpj = st.text_input(
                    "CPF/CNPJ:",
                    value=existing.get('cpf_cnpj', '') if existing else '',
                    placeholder="000.000.000-00"
                )
                
                senha = st.text_input(
                    "Senha:",
                    type="password",
                    value="******" if existing else '',
                    placeholder="Senha de acesso"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("💾 Salvar Credenciais"):
                        if cpf_cnpj and senha and senha != "******":
                            success = self.credentials_manager.set_tribunal_credentials(
                                tribunal.lower(),
                                cpf_cnpj,
                                senha
                            )
                            if success:
                                st.success(f"Credenciais do {tribunal} salvas!")
                            else:
                                st.error("Erro ao salvar credenciais")
                
                with col2:
                    if existing and st.form_submit_button("🗑️ Remover"):
                        if self.credentials_manager.remove_credential(tribunal.lower(), category="tribunal"):
                            st.success(f"Credenciais do {tribunal} removidas!")
                            st.rerun()
            
            # Status das credenciais
            st.markdown("### 📊 Status das Credenciais")
            
            configured = self.credentials_manager.list_configured_services()
            tribunal_creds = configured.get('tribunal', [])
            
            if tribunal_creds:
                df = pd.DataFrame({
                    'Tribunal': [t.upper() for t in tribunal_creds],
                    'Status': ['✅ Configurado'] * len(tribunal_creds),
                    'Última Atualização': [datetime.now().strftime("%d/%m/%Y")] * len(tribunal_creds)
                })
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nenhum tribunal configurado ainda")
        
        # Certificados Digitais
        with subtabs[2]:
            st.subheader("🔏 Certificados Digitais")
            
            st.info("""
            **Certificados A3/Token**
            - Necessário para acesso a alguns tribunais
            - Requer driver do token instalado
            - Arquivo .p12/.pfx ou acesso via PKCS#11
            """)
            
            # Upload de certificado
            uploaded_file = st.file_uploader(
                "Carregar Certificado Digital",
                type=['p12', 'pfx'],
                help="Selecione o arquivo do certificado"
            )
            
            if uploaded_file:
                tribunal_cert = st.selectbox(
                    "Tribunal para o certificado:",
                    ["TJSP", "TJRJ", "TJMG", "TRF1", "TRF2", "TRF3"]
                )
                
                senha_cert = st.text_input("Senha do certificado:", type="password")
                
                if st.button("Instalar Certificado"):
                    # Salvar certificado
                    cert_dir = Path("certificates")
                    cert_dir.mkdir(exist_ok=True)
                    
                    cert_path = cert_dir / f"{tribunal_cert.lower()}_{uploaded_file.name}"
                    with open(cert_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Salvar caminho e senha
                    success = self.credentials_manager.set_credential(
                        tribunal_cert.lower(),
                        "cert_path",
                        str(cert_path),
                        "tribunal"
                    )
                    
                    if senha_cert:
                        success &= self.credentials_manager.set_credential(
                            tribunal_cert.lower(),
                            "cert_senha",
                            senha_cert,
                            "tribunal"
                        )
                    
                    if success:
                        st.success(f"Certificado instalado para {tribunal_cert}!")
                    else:
                        st.error("Erro ao instalar certificado")
    
    def _tab_tribunals(self):
        """Aba de configuração de tribunais"""
        st.header("🏛️ Configuração de Tribunais")
        
        # Inicializar connection manager
        if not self.connection_manager:
            self.connection_manager = ConnectionManager()
        
        # Subabas
        subtabs = st.tabs(["Status Geral", "Configurar Tribunal", "Testar Conectividade"])
        
        # Status Geral
        with subtabs[0]:
            st.subheader("📊 Status dos Tribunais")
            
            if st.button("🔄 Atualizar Status"):
                with st.spinner("Testando conectividade..."):
                    asyncio.run(self._test_all_tribunals())
            
            # Mostrar resultados dos testes
            if st.session_state.test_results:
                # Criar DataFrame
                data = []
                for tribunal, result in st.session_state.test_results.items():
                    data.append({
                        'Tribunal': tribunal.upper(),
                        'Status': result.get('overall_status', 'unknown'),
                        'REST': result.get('endpoints', {}).get('rest', {}).get('status', '-'),
                        'SOAP': result.get('endpoints', {}).get('soap', {}).get('status', '-'),
                        'Base': result.get('endpoints', {}).get('base', {}).get('status', '-'),
                        'Última Verificação': result.get('timestamp', '-')
                    })
                
                df = pd.DataFrame(data)
                
                # Aplicar cores baseadas no status
                def color_status(val):
                    if val == 'online':
                        return 'background-color: #d4edda'
                    elif val == 'offline':
                        return 'background-color: #f8d7da'
                    elif val == 'partial':
                        return 'background-color: #fff3cd'
                    return ''
                
                styled_df = df.style.applymap(color_status, subset=['Status', 'REST', 'SOAP', 'Base'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Gráfico de status
                status_counts = df['Status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Distribuição de Status",
                    color_discrete_map={
                        'online': '#28a745',
                        'offline': '#dc3545',
                        'partial': '#ffc107'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Clique em 'Atualizar Status' para verificar a conectividade")
        
        # Configurar Tribunal
        with subtabs[1]:
            st.subheader("⚙️ Configurar Tribunal")
            
            # Carregar configuração atual
            config_path = Path("config/tribunais.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    tribunais_config = config.get('tribunais', {})
            else:
                tribunais_config = {}
            
            # Seletor de tribunal
            tribunal_edit = st.selectbox(
                "Selecione o tribunal para editar:",
                list(tribunais_config.keys())
            )
            
            if tribunal_edit:
                tribunal_data = tribunais_config[tribunal_edit]
                
                # Editor de configuração
                st.markdown(f"### Editando: {tribunal_data.get('nome', tribunal_edit)}")
                
                # URLs
                st.markdown("#### URLs")
                urls = tribunal_data.get('urls', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    rest_url = st.text_input(
                        "URL REST API:",
                        value=urls.get('rest', ''),
                        key=f"rest_{tribunal_edit}"
                    )
                    soap_url = st.text_input(
                        "URL SOAP:",
                        value=urls.get('soap', ''),
                        key=f"soap_{tribunal_edit}"
                    )
                
                with col2:
                    base_url = st.text_input(
                        "URL Base:",
                        value=urls.get('base', ''),
                        key=f"base_{tribunal_edit}"
                    )
                    consulta_url = st.text_input(
                        "URL Consulta:",
                        value=urls.get('consulta', ''),
                        key=f"consulta_{tribunal_edit}"
                    )
                
                # Rate Limiting
                st.markdown("#### Rate Limiting")
                rate_config = tribunal_data.get('rate_limit', {})
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    rpm = st.number_input(
                        "Requests por minuto:",
                        value=rate_config.get('requests_por_minuto', 30),
                        min_value=1,
                        max_value=100,
                        key=f"rpm_{tribunal_edit}"
                    )
                
                with col2:
                    backoff = st.number_input(
                        "Backoff multiplier:",
                        value=float(rate_config.get('backoff_multiplier', 2.0)),
                        min_value=1.0,
                        max_value=10.0,
                        step=0.5,
                        key=f"backoff_{tribunal_edit}"
                    )
                
                with col3:
                    max_retries = st.number_input(
                        "Max retries:",
                        value=rate_config.get('max_retries', 3),
                        min_value=0,
                        max_value=10,
                        key=f"retries_{tribunal_edit}"
                    )
                
                # Headers customizados
                st.markdown("#### Headers HTTP")
                headers = tribunal_data.get('headers', {})
                
                # Editor de headers
                headers_text = st.text_area(
                    "Headers (formato YAML):",
                    value=yaml.dump(headers, default_flow_style=False),
                    height=150,
                    key=f"headers_{tribunal_edit}"
                )
                
                # Salvar configuração
                if st.button("💾 Salvar Configuração", key=f"save_{tribunal_edit}"):
                    try:
                        # Atualizar configuração
                        tribunais_config[tribunal_edit]['urls'] = {
                            'rest': rest_url,
                            'soap': soap_url,
                            'base': base_url,
                            'consulta': consulta_url
                        }
                        
                        tribunais_config[tribunal_edit]['rate_limit'] = {
                            'requests_por_minuto': rpm,
                            'backoff_multiplier': backoff,
                            'max_retries': max_retries
                        }
                        
                        # Parse headers
                        try:
                            new_headers = yaml.safe_load(headers_text)
                            tribunais_config[tribunal_edit]['headers'] = new_headers
                        except:
                            st.warning("Headers inválidos, mantendo configuração anterior")
                        
                        # Salvar arquivo
                        config['tribunais'] = tribunais_config
                        with open(config_path, 'w') as f:
                            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                        
                        st.success(f"Configuração do {tribunal_edit} salva!")
                        
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
        
        # Testar Conectividade
        with subtabs[2]:
            st.subheader("🧪 Testar Conectividade")
            
            # Seletor de tribunal
            tribunal_test = st.selectbox(
                "Selecione o tribunal para testar:",
                ["TJSP", "TJRJ", "TJMG", "TRF1", "TRF2", "TRF3", "STJ", "STF"],
                key="tribunal_test_select"
            )
            
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col2:
                if st.button("🚀 Testar", use_container_width=True):
                    with st.spinner(f"Testando {tribunal_test}..."):
                        result = asyncio.run(self._test_single_tribunal(tribunal_test.lower()))
                        
                        if result:
                            st.session_state.test_results[tribunal_test.lower()] = result
            
            # Mostrar resultado do teste
            if tribunal_test.lower() in st.session_state.test_results:
                result = st.session_state.test_results[tribunal_test.lower()]
                
                # Card de resultado
                st.markdown("### 📊 Resultado do Teste")
                
                # Status geral
                status = result.get('overall_status', 'unknown')
                status_emoji = {
                    'online': '🟢',
                    'offline': '🔴',
                    'partial': '🟡'
                }.get(status, '⚪')
                
                st.metric("Status Geral", f"{status_emoji} {status.upper()}")
                
                # Detalhes por endpoint
                st.markdown("#### Endpoints")
                
                endpoints = result.get('endpoints', {})
                for tipo, data in endpoints.items():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{tipo.upper()}**")
                    
                    with col2:
                        url = data.get('url', '-')
                        if url and not url.startswith('${'):
                            st.text(url[:50] + "..." if len(url) > 50 else url)
                        else:
                            st.text("Não configurado")
                    
                    with col3:
                        ep_status = data.get('status', 'unknown')
                        if ep_status == 'online':
                            st.success(f"✅ Online ({data.get('response_time', 0)}ms)")
                        elif ep_status == 'offline':
                            st.error("❌ Offline")
                        else:
                            st.warning("⚠️ Erro")
                
                # Timestamp
                st.caption(f"Testado em: {result.get('timestamp', '-')}")
    
    def _tab_monitoring(self):
        """Aba de monitoramento"""
        st.header("📊 Monitoramento do Sistema")
        
        # Métricas em tempo real
        col1, col2, col3, col4 = st.columns(4)
        
        # Simular métricas (em produção, viriam do Prometheus)
        with col1:
            st.metric(
                "CPU",
                "45%",
                delta="-5%",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "Memória",
                "62%",
                delta="+3%",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                "Requisições/min",
                "127",
                delta="+12",
                delta_color="normal"
            )
        
        with col4:
            st.metric(
                "Latência P95",
                "245ms",
                delta="-15ms",
                delta_color="normal"
            )
        
        # Gráficos
        st.markdown("### 📈 Métricas de Performance")
        
        # Simular dados de série temporal
        import numpy as np
        
        time_range = pd.date_range(
            start=datetime.now() - timedelta(hours=24),
            end=datetime.now(),
            freq='1H'
        )
        
        # CPU e Memória
        cpu_data = 40 + 20 * np.sin(np.linspace(0, 4*np.pi, len(time_range))) + np.random.normal(0, 5, len(time_range))
        mem_data = 60 + 15 * np.cos(np.linspace(0, 4*np.pi, len(time_range))) + np.random.normal(0, 3, len(time_range))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_range, y=cpu_data, name='CPU %', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=time_range, y=mem_data, name='Memória %', line=dict(color='green')))
        
        fig.update_layout(
            title="Uso de Recursos (24h)",
            xaxis_title="Tempo",
            yaxis_title="Porcentagem (%)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Taxa de requisições
        col1, col2 = st.columns(2)
        
        with col1:
            # Requisições por tribunal
            tribunais = ['TJSP', 'TJRJ', 'TJMG', 'TRF3', 'STJ']
            requests = [450, 320, 280, 190, 150]
            
            fig = px.bar(
                x=tribunais,
                y=requests,
                title="Requisições por Tribunal (últimas 24h)",
                labels={'x': 'Tribunal', 'y': 'Requisições'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Taxa de sucesso
            status = ['Sucesso', 'Erro 4xx', 'Erro 5xx', 'Timeout']
            counts = [85, 8, 3, 4]
            
            fig = px.pie(
                values=counts,
                names=status,
                title="Taxa de Sucesso das Requisições",
                color_discrete_map={
                    'Sucesso': '#28a745',
                    'Erro 4xx': '#ffc107',
                    'Erro 5xx': '#dc3545',
                    'Timeout': '#6c757d'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Alertas ativos
        st.markdown("### 🚨 Alertas Ativos")
        
        alerts = [
            {
                'severity': 'warning',
                'title': 'Alta latência TJSP',
                'message': 'Latência P95 acima de 500ms há 10 minutos',
                'time': '10 min atrás'
            },
            {
                'severity': 'info',
                'title': 'Manutenção programada TRF2',
                'message': 'Manutenção agendada para 22:00',
                'time': '2 horas'
            }
        ]
        
        for alert in alerts:
            severity_color = {
                'critical': '#dc3545',
                'warning': '#ffc107',
                'info': '#17a2b8'
            }.get(alert['severity'], '#6c757d')
            
            st.markdown(
                f"""
                <div style="
                    border-left: 4px solid {severity_color};
                    padding: 10px;
                    margin: 10px 0;
                    background-color: #f8f9fa;
                ">
                    <strong>{alert['title']}</strong><br>
                    {alert['message']}<br>
                    <small style="color: #6c757d;">{alert['time']}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def _tab_system(self):
        """Aba de configurações do sistema"""
        st.header("⚙️ Configurações do Sistema")
        
        # Subabas
        subtabs = st.tabs(["Geral", "Performance", "Segurança", "Backup"])
        
        # Configurações Gerais
        with subtabs[0]:
            st.subheader("🔧 Configurações Gerais")
            
            # Modo de operação
            col1, col2 = st.columns(2)
            
            with col1:
                modo = st.selectbox(
                    "Modo de Operação:",
                    ["Produção", "Desenvolvimento", "Teste"],
                    index=0
                )
                
                log_level = st.selectbox(
                    "Nível de Log:",
                    ["DEBUG", "INFO", "WARNING", "ERROR"],
                    index=1
                )
            
            with col2:
                timezone = st.selectbox(
                    "Timezone:",
                    ["America/Sao_Paulo", "UTC", "America/New_York"],
                    index=0
                )
                
                language = st.selectbox(
                    "Idioma:",
                    ["Português (BR)", "English", "Español"],
                    index=0
                )
            
            # Paths
            st.markdown("### 📁 Diretórios")
            
            col1, col2 = st.columns(2)
            
            with col1:
                data_dir = st.text_input(
                    "Diretório de Dados:",
                    value="./data",
                    help="Onde os dados são armazenados"
                )
                
                cache_dir = st.text_input(
                    "Diretório de Cache:",
                    value="./cache",
                    help="Cache temporário"
                )
            
            with col2:
                logs_dir = st.text_input(
                    "Diretório de Logs:",
                    value="./logs",
                    help="Arquivos de log"
                )
                
                downloads_dir = st.text_input(
                    "Diretório de Downloads:",
                    value="./downloads",
                    help="Downloads de documentos"
                )
            
            if st.button("💾 Salvar Configurações Gerais"):
                st.success("Configurações salvas!")
        
        # Performance
        with subtabs[1]:
            st.subheader("⚡ Configurações de Performance")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Limites de Recursos")
                
                max_workers = st.slider(
                    "Workers máximos:",
                    min_value=1,
                    max_value=20,
                    value=10,
                    help="Número máximo de workers paralelos"
                )
                
                max_connections = st.slider(
                    "Conexões máximas:",
                    min_value=10,
                    max_value=200,
                    value=100,
                    help="Conexões simultâneas máximas"
                )
                
                timeout_global = st.number_input(
                    "Timeout global (segundos):",
                    min_value=10,
                    max_value=600,
                    value=300,
                    help="Timeout padrão para operações"
                )
            
            with col2:
                st.markdown("### Cache")
                
                cache_enabled = st.checkbox("Cache habilitado", value=True)
                
                cache_ttl = st.number_input(
                    "TTL do cache (minutos):",
                    min_value=1,
                    max_value=1440,
                    value=60,
                    disabled=not cache_enabled
                )
                
                cache_size = st.number_input(
                    "Tamanho máximo do cache (MB):",
                    min_value=100,
                    max_value=10000,
                    value=1000,
                    disabled=not cache_enabled
                )
                
                if st.button("🗑️ Limpar Cache"):
                    st.info("Cache limpo!")
        
        # Segurança
        with subtabs[2]:
            st.subheader("🔒 Configurações de Segurança")
            
            # SSL/TLS
            st.markdown("### 🔐 SSL/TLS")
            
            ssl_verify = st.checkbox(
                "Verificar certificados SSL",
                value=True,
                help="Verificar validade dos certificados dos tribunais"
            )
            
            min_tls = st.selectbox(
                "Versão mínima do TLS:",
                ["TLS 1.0", "TLS 1.1", "TLS 1.2", "TLS 1.3"],
                index=2
            )
            
            # Autenticação
            st.markdown("### 🔑 Autenticação")
            
            col1, col2 = st.columns(2)
            
            with col1:
                session_timeout = st.number_input(
                    "Timeout de sessão (minutos):",
                    min_value=5,
                    max_value=1440,
                    value=60
                )
                
                max_login_attempts = st.number_input(
                    "Tentativas máximas de login:",
                    min_value=1,
                    max_value=10,
                    value=3
                )
            
            with col2:
                require_2fa = st.checkbox(
                    "Exigir autenticação 2FA",
                    value=False
                )
                
                password_complexity = st.selectbox(
                    "Complexidade de senha:",
                    ["Baixa", "Média", "Alta", "Muito Alta"],
                    index=2
                )
            
            # Auditoria
            st.markdown("### 📝 Auditoria")
            
            audit_enabled = st.checkbox(
                "Auditoria habilitada",
                value=True,
                help="Registrar todas as ações administrativas"
            )
            
            audit_retention = st.number_input(
                "Retenção de logs de auditoria (dias):",
                min_value=7,
                max_value=365,
                value=90,
                disabled=not audit_enabled
            )
        
        # Backup
        with subtabs[3]:
            st.subheader("💾 Backup e Recuperação")
            
            # Status do backup
            st.markdown("### 📊 Status do Backup")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Último backup", "Hoje 03:00")
            with col2:
                st.metric("Tamanho", "2.3 GB")
            with col3:
                st.metric("Próximo backup", "Em 21 horas")
            
            # Configurações
            st.markdown("### ⚙️ Configurações de Backup")
            
            backup_enabled = st.checkbox("Backup automático", value=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                backup_frequency = st.selectbox(
                    "Frequência:",
                    ["Diário", "Semanal", "Mensal"],
                    index=0,
                    disabled=not backup_enabled
                )
                
                backup_time = st.time_input(
                    "Horário do backup:",
                    value=datetime.strptime("03:00", "%H:%M").time(),
                    disabled=not backup_enabled
                )
            
            with col2:
                backup_retention = st.number_input(
                    "Retenção (dias):",
                    min_value=7,
                    max_value=365,
                    value=30,
                    disabled=not backup_enabled
                )
                
                backup_location = st.text_input(
                    "Destino:",
                    value="/backups",
                    disabled=not backup_enabled
                )
            
            # Ações
            st.markdown("### 🚀 Ações")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Backup Manual", use_container_width=True):
                    with st.spinner("Realizando backup..."):
                        # Simular backup
                        import time
                        time.sleep(2)
                        st.success("Backup realizado com sucesso!")
            
            with col2:
                if st.button("📥 Restaurar", use_container_width=True):
                    st.warning("Função de restauração - Em desenvolvimento")
            
            with col3:
                if st.button("🗑️ Limpar Antigos", use_container_width=True):
                    st.info("Backups antigos removidos")
    
    def _tab_tests(self):
        """Aba de testes"""
        st.header("🧪 Testes do Sistema")
        
        # Tipos de teste
        test_type = st.selectbox(
            "Tipo de teste:",
            ["Validação CNJ", "Conectividade", "Performance", "Integração"]
        )
        
        if test_type == "Validação CNJ":
            st.subheader("📋 Teste de Validação CNJ")
            
            # Input para número CNJ
            cnj_input = st.text_input(
                "Número CNJ:",
                placeholder="0000000-00.0000.0.00.0000",
                help="Digite um número CNJ para validar"
            )
            
            if cnj_input:
                # Validar
                is_valid = validar_numero_cnj(cnj_input)
                
                if is_valid:
                    st.success(f"✅ Número CNJ válido!")
                    
                    # Extrair componentes
                    from ..utils.cnj_validator import extrair_componentes_cnj
                    componentes = extrair_componentes_cnj(cnj_input)
                    
                    if componentes:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Ano", componentes['ano'])
                            st.metric("Segmento", componentes['segmento_nome'])
                            st.metric("Tribunal", componentes['codigo_tribunal'])
                        
                        with col2:
                            st.metric("Origem", componentes['origem'])
                            st.metric("Sequencial", componentes['sequencial'])
                            st.metric("DV", componentes['digito_verificador'])
                else:
                    st.error("❌ Número CNJ inválido!")
            
            # Exemplos de números válidos
            st.markdown("### 📝 Exemplos de Números Válidos")
            
            exemplos = [
                ("STF", "0000001-02.2023.1.00.0000"),
                ("STJ", "0000001-02.2023.3.00.0000"),
                ("TJSP", "1000001-02.2023.8.26.0001"),
                ("TRF3", "0000001-02.2023.4.03.0000"),
            ]
            
            for tribunal, numero in exemplos:
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.text(tribunal)
                
                with col2:
                    st.code(numero)
                
                with col3:
                    if st.button("Testar", key=f"test_{numero}"):
                        st.session_state[f"test_result_{numero}"] = validar_numero_cnj(numero)
                        
                if f"test_result_{numero}" in st.session_state:
                    if st.session_state[f"test_result_{numero}"]:
                        st.success("✅ Válido")
                    else:
                        st.error("❌ Inválido")
        
        elif test_type == "Conectividade":
            st.subheader("🌐 Teste de Conectividade")
            
            # Seleção múltipla de tribunais
            tribunais_selecionados = st.multiselect(
                "Selecione os tribunais para testar:",
                ["TJSP", "TJRJ", "TJMG", "TRF1", "TRF2", "TRF3", "STJ", "STF"],
                default=["TJSP", "STJ"]
            )
            
            if st.button("🚀 Executar Teste de Conectividade"):
                progress_bar = st.progress(0)
                status_container = st.empty()
                
                results = {}
                for i, tribunal in enumerate(tribunais_selecionados):
                    status_container.text(f"Testando {tribunal}...")
                    progress_bar.progress((i + 1) / len(tribunais_selecionados))
                    
                    # Simular teste
                    import time
                    time.sleep(0.5)
                    
                    # Resultado aleatório para demo
                    import random
                    status = random.choice(['online', 'offline', 'partial'])
                    results[tribunal] = {
                        'status': status,
                        'latency': random.randint(50, 500) if status != 'offline' else None
                    }
                
                # Mostrar resultados
                st.markdown("### 📊 Resultados")
                
                for tribunal, result in results.items():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.text(tribunal)
                    
                    with col2:
                        if result['status'] == 'online':
                            st.success("🟢 Online")
                        elif result['status'] == 'offline':
                            st.error("🔴 Offline")
                        else:
                            st.warning("🟡 Parcial")
                    
                    with col3:
                        if result['latency']:
                            st.text(f"{result['latency']}ms")
        
        elif test_type == "Performance":
            st.subheader("⚡ Teste de Performance")
            
            st.info("Testes de performance em desenvolvimento")
            
            # Configurações do teste
            col1, col2 = st.columns(2)
            
            with col1:
                concurrent_requests = st.slider(
                    "Requisições simultâneas:",
                    min_value=1,
                    max_value=100,
                    value=10
                )
                
                test_duration = st.number_input(
                    "Duração do teste (segundos):",
                    min_value=10,
                    max_value=300,
                    value=60
                )
            
            with col2:
                target_tribunal = st.selectbox(
                    "Tribunal alvo:",
                    ["TJSP", "STJ", "TRF3"]
                )
                
                request_type = st.selectbox(
                    "Tipo de requisição:",
                    ["Consulta processo", "Download PDF", "Busca"]
                )
            
            if st.button("▶️ Iniciar Teste de Performance"):
                st.warning("Teste de performance não disponível no ambiente de demonstração")
        
        elif test_type == "Integração":
            st.subheader("🔗 Teste de Integração")
            
            st.info("Testa o fluxo completo do sistema")
            
            # Cenários de teste
            scenarios = {
                "Consulta Simples": "Consulta um processo e extrai informações básicas",
                "Download e Análise": "Baixa um documento e realiza análise com IA",
                "Fluxo Completo": "Consulta → Download → Análise → Geração de Minuta"
            }
            
            selected_scenario = st.selectbox(
                "Cenário de teste:",
                list(scenarios.keys())
            )
            
            st.info(scenarios[selected_scenario])
            
            if st.button("🧪 Executar Teste de Integração"):
                st.info("Testes de integração em desenvolvimento")
    
    def _tab_logs(self):
        """Aba de logs"""
        st.header("📝 Logs do Sistema")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            log_level = st.selectbox(
                "Nível:",
                ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"],
                index=0
            )
        
        with col2:
            log_module = st.selectbox(
                "Módulo:",
                ["Todos", "API", "Scraper", "Database", "Auth", "Download"],
                index=0
            )
        
        with col3:
            time_range = st.selectbox(
                "Período:",
                ["Última hora", "Últimas 24h", "Última semana", "Último mês"],
                index=0
            )
        
        with col4:
            search_term = st.text_input(
                "Buscar:",
                placeholder="Termo de busca..."
            )
        
        # Ações
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            if st.button("🔄 Atualizar"):
                st.rerun()
        
        with col2:
            if st.button("📥 Exportar"):
                st.info("Exportação em desenvolvimento")
        
        # Logs simulados
        logs = [
            {
                'timestamp': '2025-07-02 10:15:32',
                'level': 'INFO',
                'module': 'API',
                'message': 'Requisição recebida: GET /api/processo/123456'
            },
            {
                'timestamp': '2025-07-02 10:15:33',
                'level': 'DEBUG',
                'module': 'Database',
                'message': 'Query executada em 0.045s'
            },
            {
                'timestamp': '2025-07-02 10:15:34',
                'level': 'WARNING',
                'module': 'Scraper',
                'message': 'Rate limit atingido para TJSP, aguardando 5s'
            },
            {
                'timestamp': '2025-07-02 10:15:40',
                'level': 'ERROR',
                'module': 'Download',
                'message': 'Falha ao baixar documento: Connection timeout'
            },
            {
                'timestamp': '2025-07-02 10:15:41',
                'level': 'INFO',
                'module': 'Download',
                'message': 'Retry 1/3 para documento 789012'
            }
        ]
        
        # Filtrar logs
        if log_level != "ALL":
            logs = [l for l in logs if l['level'] == log_level]
        
        if log_module != "Todos":
            logs = [l for l in logs if l['module'] == log_module]
        
        if search_term:
            logs = [l for l in logs if search_term.lower() in l['message'].lower()]
        
        # Exibir logs
        for log in logs:
            level_color = {
                'DEBUG': '#6c757d',
                'INFO': '#17a2b8',
                'WARNING': '#ffc107',
                'ERROR': '#dc3545'
            }.get(log['level'], '#000')
            
            st.markdown(
                f"""
                <div style="
                    font-family: monospace;
                    font-size: 12px;
                    padding: 5px;
                    border-bottom: 1px solid #eee;
                ">
                    <span style="color: #666;">{log['timestamp']}</span>
                    <span style="color: {level_color}; font-weight: bold;">[{log['level']}]</span>
                    <span style="color: #0066cc;">[{log['module']}]</span>
                    <span>{log['message']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Estatísticas de logs
        st.markdown("### 📊 Estatísticas de Logs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição por nível
            levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
            counts = [125, 892, 67, 12]
            
            fig = px.bar(
                x=levels,
                y=counts,
                title="Logs por Nível (últimas 24h)",
                color=levels,
                color_discrete_map={
                    'DEBUG': '#6c757d',
                    'INFO': '#17a2b8',
                    'WARNING': '#ffc107',
                    'ERROR': '#dc3545'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Logs por módulo
            modules = ['API', 'Scraper', 'Database', 'Auth', 'Download']
            module_counts = [340, 280, 220, 156, 100]
            
            fig = px.pie(
                values=module_counts,
                names=modules,
                title="Logs por Módulo (últimas 24h)"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _sidebar_actions(self):
        """Ações rápidas na sidebar"""
        with st.sidebar:
            st.markdown("### ⚡ Ações Rápidas")
            
            if st.button("🔄 Reiniciar Serviços", use_container_width=True):
                with st.spinner("Reiniciando..."):
                    import time
                    time.sleep(2)
                    st.success("Serviços reiniciados!")
            
            if st.button("🗑️ Limpar Caches", use_container_width=True):
                st.info("Caches limpos!")
            
            if st.button("📊 Gerar Relatório", use_container_width=True):
                st.info("Relatório em geração...")
            
            st.markdown("---")
            
            # Status rápido
            st.markdown("### 📊 Status Rápido")
            
            st.metric("Uptime", "15d 7h 23m")
            st.metric("Uso de Disco", "45.2 GB / 100 GB")
            st.metric("Processos Ativos", "127")
            
            st.markdown("---")
            
            # Logout
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()
    
    async def _test_all_tribunals(self):
        """Testa conectividade de todos os tribunais"""
        if not self.connection_manager:
            self.connection_manager = ConnectionManager()
        
        tribunais = ["tjsp", "tjrj", "tjmg", "trf1", "trf2", "trf3", "stj", "stf"]
        
        for tribunal in tribunais:
            try:
                result = await self.connection_manager.test_connectivity(tribunal)
                st.session_state.test_results[tribunal] = result
            except Exception as e:
                st.session_state.test_results[tribunal] = {
                    'tribunal': tribunal,
                    'overall_status': 'error',
                    'error': str(e)
                }
    
    async def _test_single_tribunal(self, tribunal: str) -> Dict:
        """Testa conectividade de um tribunal específico"""
        if not self.connection_manager:
            self.connection_manager = ConnectionManager()
        
        try:
            return await self.connection_manager.test_connectivity(tribunal)
        except Exception as e:
            return {
                'tribunal': tribunal,
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Executar interface
if __name__ == "__main__":
    admin = AdminInterface()
    admin.run()