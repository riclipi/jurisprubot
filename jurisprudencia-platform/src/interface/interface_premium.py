"""
🚀 INTERFACE PREMIUM - FUNCIONALIDADES AVANÇADAS
Sistema que supera o Justino Cível em recursos
"""

import streamlit as st
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
import tempfile

# Adicionar ao path
sys.path.append('.')

# Importar nossos módulos avançados
from src.minutas.gerador_minutas import GeradorMinutas, PeticaoAnalise, MinutaGerada
from src.extracao.extrator_estruturado import ExtratorEstruturado, DocumentoEstruturado
from src.analise.analisador_juridico import AnalisadorJuridico, AnaliseJuridicaCompleta

class InterfacePremium:
    """
    🎯 INTERFACE PREMIUM COMPLETA
    Todas as funcionalidades avançadas em uma interface única
    """
    
    def __init__(self):
        self.gerador_minutas = GeradorMinutas()
        self.extrator = ExtratorEstruturado()
        self.analisador = AnalisadorJuridico()
        self._setup_session_state()
    
    def _setup_session_state(self):
        """Configura estado da sessão"""
        if 'documentos_analisados' not in st.session_state:
            st.session_state.documentos_analisados = []
        
        if 'minutas_geradas' not in st.session_state:
            st.session_state.minutas_geradas = []
        
        if 'analises_realizadas' not in st.session_state:
            st.session_state.analises_realizadas = []
    
    def render_interface_completa(self):
        """Renderiza interface completa"""
        
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 20px; color: white;'>
            <h1 style='margin: 0; font-size: 2.2em;'>🚀 JURISPRUDÊNCIA AI PREMIUM</h1>
            <h3 style='margin: 10px 0 0 0; opacity: 0.9;'>Sistema Avançado que Supera o Justino Cível</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs principais
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Análise de Petições", 
            "📝 Gerador de Minutas", 
            "🧠 Análise Jurídica",
            "📊 Dashboard Premium",
            "⚙️ Configurações"
        ])
        
        with tab1:
            self._render_analise_peticoes()
        
        with tab2:
            self._render_gerador_minutas()
        
        with tab3:
            self._render_analise_juridica()
        
        with tab4:
            self._render_dashboard_premium()
        
        with tab5:
            self._render_configuracoes()
    
    def _render_analise_peticoes(self):
        """Aba de análise de petições"""
        
        st.markdown("## 📋 Análise Estruturada de Petições")
        st.markdown("**Funcionalidade:** Extrai automaticamente partes, pedidos, fundamentos e gera relatório completo")
        
        # Upload de arquivo ou entrada de texto
        col1, col2 = st.columns([2, 1])
        
        with col1:
            input_method = st.radio(
                "Método de entrada:",
                ["📝 Texto direto", "📁 Upload de arquivo"],
                horizontal=True
            )
        
        with col2:
            st.markdown("### 📊 Estatísticas")
            st.metric("Documentos Analisados", len(st.session_state.documentos_analisados))
        
        texto_peticao = ""
        
        if input_method == "📝 Texto direto":
            texto_peticao = st.text_area(
                "Cole o texto da petição:",
                height=300,
                placeholder="Cole aqui o texto completo da petição inicial..."
            )
        
        else:  # Upload de arquivo
            uploaded_file = st.file_uploader(
                "Faça upload da petição:",
                type=['txt', 'pdf', 'docx'],
                help="Formatos aceitos: TXT, PDF, DOCX"
            )
            
            if uploaded_file:
                if uploaded_file.type == "text/plain":
                    texto_peticao = str(uploaded_file.read(), "utf-8")
                else:
                    st.warning("⚠️ Para PDFs e DOCX, cole o texto manualmente por enquanto")
        
        # Botão de análise
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            analisar_clicked = st.button(
                "🔍 ANALISAR PETIÇÃO",
                type="primary",
                use_container_width=True,
                disabled=not texto_peticao.strip()
            )
        
        # Processar análise
        if analisar_clicked and texto_peticao.strip():
            with st.spinner("🔄 Analisando petição... Isso pode levar alguns segundos"):
                
                # Barra de progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Etapa 1: Extração estruturada
                status_text.text("📊 Extraindo informações estruturadas...")
                progress_bar.progress(25)
                time.sleep(1)
                
                documento = self.extrator.extrair_documento_completo(texto_peticao)
                
                # Etapa 2: Análise de completude
                status_text.text("📋 Analisando completude dos requisitos...")
                progress_bar.progress(50)
                time.sleep(1)
                
                # Etapa 3: Geração de relatório
                status_text.text("📄 Gerando relatório detalhado...")
                progress_bar.progress(75)
                time.sleep(1)
                
                # Etapa 4: Finalização
                status_text.text("✅ Análise concluída!")
                progress_bar.progress(100)
                time.sleep(0.5)
                
                # Limpar progresso
                progress_bar.empty()
                status_text.empty()
                
                # Salvar na sessão
                st.session_state.documentos_analisados.append(documento)
                
                # Exibir resultados
                self._exibir_resultados_analise(documento)
    
    def _exibir_resultados_analise(self, documento: DocumentoEstruturado):
        """Exibe resultados da análise"""
        
        st.success("✅ Análise concluída com sucesso!")
        
        # Resumo executivo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📊 Completude",
                f"{documento.completude_score:.1%}",
                delta=f"{documento.completude_score - 0.7:.1%}" if documento.completude_score > 0.7 else None
            )
        
        with col2:
            st.metric("📋 Pedidos", len(documento.pedidos))
        
        with col3:
            st.metric("📚 Fundamentos", len(documento.fundamentos_legais))
        
        with col4:
            st.metric("⚠️ Problemas", len(documento.problemas_identificados))
        
        st.divider()
        
        # Tabs de detalhamento
        tab1, tab2, tab3, tab4 = st.tabs([
            "👥 Partes Processuais",
            "📋 Pedidos & Fundamentos", 
            "🔍 Análise de Qualidade",
            "📄 Relatório Completo"
        ])
        
        with tab1:
            self._exibir_partes_processuais(documento)
        
        with tab2:
            self._exibir_pedidos_fundamentos(documento)
        
        with tab3:
            self._exibir_analise_qualidade(documento)
        
        with tab4:
            self._exibir_relatorio_completo(documento)
    
    def _exibir_partes_processuais(self, documento: DocumentoEstruturado):
        """Exibe informações das partes processuais"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 👤 AUTOR")
            st.write(f"**Nome:** {documento.autor.nome}")
            st.write(f"**Tipo:** {documento.autor.tipo.replace('_', ' ').title()}")
            
            if documento.autor.cpf_cnpj:
                st.write(f"**CPF/CNPJ:** {documento.autor.cpf_cnpj}")
            
            if documento.autor.endereco:
                st.write(f"**Endereço:** {documento.autor.endereco}")
            
            qualif_status = "✅ Completa" if documento.autor.qualificacao_completa else "⚠️ Incompleta"
            st.write(f"**Qualificação:** {qualif_status}")
        
        with col2:
            st.markdown("### 🏢 RÉU")
            st.write(f"**Nome:** {documento.reu.nome}")
            st.write(f"**Tipo:** {documento.reu.tipo.replace('_', ' ').title()}")
            
            if documento.reu.cpf_cnpj:
                st.write(f"**CPF/CNPJ:** {documento.reu.cpf_cnpj}")
            
            qualif_status = "✅ Completa" if documento.reu.qualificacao_completa else "⚠️ Incompleta"
            st.write(f"**Qualificação:** {qualif_status}")
        
        # Informações processuais
        st.markdown("### ⚖️ Informações Processuais")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Tipo de Ação:** {documento.tipo_acao}")
        
        with col2:
            st.write(f"**Competência:** {documento.competencia_sugerida}")
        
        with col3:
            st.write(f"**Valor da Causa:** {documento.valor_causa or 'Não especificado'}")
    
    def _exibir_pedidos_fundamentos(self, documento: DocumentoEstruturado):
        """Exibe pedidos e fundamentos"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### 📋 PEDIDOS ({len(documento.pedidos)})")
            
            if documento.pedidos:
                for i, pedido in enumerate(documento.pedidos, 1):
                    with st.expander(f"Pedido {i} - {pedido.categoria.title()}"):
                        st.write(f"**Tipo:** {pedido.tipo.title()}")
                        st.write(f"**Descrição:** {pedido.descricao}")
                        
                        if pedido.valor_monetario:
                            st.write(f"**Valor:** {pedido.valor_monetario}")
                        
                        if pedido.prazo:
                            st.write(f"**Prazo:** {pedido.prazo}")
            else:
                st.warning("⚠️ Nenhum pedido identificado")
        
        with col2:
            st.markdown(f"### 📚 FUNDAMENTOS LEGAIS ({len(documento.fundamentos_legais)})")
            
            if documento.fundamentos_legais:
                # Agrupar por categoria
                fundamentos_por_categoria = {}
                for fund in documento.fundamentos_legais:
                    categoria = fund.categoria
                    if categoria not in fundamentos_por_categoria:
                        fundamentos_por_categoria[categoria] = []
                    fundamentos_por_categoria[categoria].append(fund)
                
                for categoria, fundamentos in fundamentos_por_categoria.items():
                    with st.expander(f"{categoria.title()} ({len(fundamentos)})"):
                        for fund in fundamentos:
                            st.write(f"• **{fund.tipo.title()}:** {fund.referencia}")
            else:
                st.warning("⚠️ Nenhuma fundamentação legal identificada")
    
    def _exibir_analise_qualidade(self, documento: DocumentoEstruturado):
        """Exibe análise de qualidade"""
        
        # Score geral
        st.markdown("### 📊 Análise de Qualidade")
        
        # Barra de progresso visual para completude
        completude_percent = int(documento.completude_score * 100)
        
        if completude_percent >= 80:
            color = "🟢"
            status = "EXCELENTE"
        elif completude_percent >= 60:
            color = "🟡"
            status = "BOM"
        elif completude_percent >= 40:
            color = "🟠"
            status = "REGULAR"
        else:
            color = "🔴"
            status = "NECESSITA MELHORIAS"
        
        st.markdown(f"""
        **{color} Status Geral: {status}**
        
        Completude: {completude_percent}%
        """)
        
        st.progress(documento.completude_score)
        
        # Problemas identificados
        if documento.problemas_identificados:
            st.markdown("### ⚠️ Problemas Identificados")
            for problema in documento.problemas_identificados:
                st.error(f"❌ {problema}")
        
        # Sugestões de melhoria
        if documento.sugestoes_melhoria:
            st.markdown("### 💡 Sugestões de Melhoria")
            for sugestao in documento.sugestoes_melhoria:
                st.info(f"💡 {sugestao}")
        
        # Estatísticas do documento
        st.markdown("### 📈 Estatísticas do Documento")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Palavras", documento.estatisticas['palavras'])
        
        with col2:
            st.metric("Parágrafos", documento.estatisticas['paragrafos'])
        
        with col3:
            st.metric("Complexidade", documento.estatisticas['complexidade'].title())
        
        with col4:
            st.metric("Densidade Legal", f"{documento.estatisticas['densidade_legal']:.2f}")
    
    def _exibir_relatorio_completo(self, documento: DocumentoEstruturado):
        """Exibe e permite download do relatório completo"""
        
        st.markdown("### 📄 Relatório Completo")
        
        # Gerar relatório
        relatorio = self.extrator.gerar_relatorio_analise(documento)
        
        # Exibir relatório
        st.markdown(relatorio)
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download como Markdown
            st.download_button(
                label="📥 Download Relatório (MD)",
                data=relatorio,
                file_name=f"relatorio_{documento.id_documento}.md",
                mime="text/markdown"
            )
        
        with col2:
            # Salvar como JSON
            if st.button("💾 Exportar JSON"):
                temp_path = f"/tmp/documento_{documento.id_documento}.json"
                self.extrator.exportar_json(documento, temp_path)
                st.success(f"✅ Exportado para: {temp_path}")
        
        with col3:
            # Gerar minuta baseada na análise
            if st.button("📝 Gerar Minuta"):
                st.session_state.documento_para_minuta = documento
                st.info("📝 Documento selecionado para geração de minuta. Vá para a aba 'Gerador de Minutas'")
    
    def _render_gerador_minutas(self):
        """Aba do gerador de minutas"""
        
        st.markdown("## 📝 Gerador de Minutas Jurídicas")
        st.markdown("**Funcionalidade:** Gera automaticamente despachos, sentenças e decisões baseadas na análise da petição")
        
        # Verificar se há documento selecionado
        documento_selecionado = None
        if hasattr(st.session_state, 'documento_para_minuta'):
            documento_selecionado = st.session_state.documento_para_minuta
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if documento_selecionado:
                st.success(f"✅ Documento selecionado: {documento_selecionado.id_documento}")
                st.write(f"**Tipo de Ação:** {documento_selecionado.tipo_acao}")
                st.write(f"**Autor:** {documento_selecionado.autor.nome}")
                st.write(f"**Réu:** {documento_selecionado.reu.nome}")
            else:
                st.info("💡 Primeiro analise uma petição na aba 'Análise de Petições' ou insira texto manualmente abaixo")
        
        with col2:
            st.markdown("### 📊 Estatísticas")
            st.metric("Minutas Geradas", len(st.session_state.minutas_geradas))
        
        # Opção de entrada manual
        if not documento_selecionado:
            st.markdown("### ✍️ Entrada Manual")
            
            with st.expander("📝 Inserir dados manualmente"):
                col1, col2 = st.columns(2)
                
                with col1:
                    autor_manual = st.text_input("Nome do Autor:")
                    tipo_acao_manual = st.selectbox(
                        "Tipo de Ação:",
                        ["indenização por danos morais", "ação de cobrança", "ação consignatória", "revisão contrato bancário"]
                    )
                
                with col2:
                    reu_manual = st.text_input("Nome do Réu:")
                    valor_causa_manual = st.text_input("Valor da Causa (opcional):")
                
                if st.button("✅ Usar Dados Manuais"):
                    # Criar análise simples
                    from src.minutas.gerador_minutas import PeticaoAnalise
                    
                    documento_selecionado = PeticaoAnalise(
                        autor=autor_manual,
                        reu=reu_manual,
                        tipo_acao=tipo_acao_manual,
                        pedidos=["Pedido principal"],
                        fundamentos=["Fundamentação básica"],
                        valor_causa=valor_causa_manual,
                        competencia="Vara Cível",
                        requisitos_preenchidos={"basico": True},
                        provas_necessarias=["Documentos básicos"],
                        recomendacoes=[]
                    )
        
        # Configurações da minuta
        if documento_selecionado:
            st.markdown("### ⚙️ Configurações da Minuta")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                tipo_minuta = st.selectbox(
                    "Tipo de Documento:",
                    ["despacho_saneador", "sentenca_procedencia", "despacho_diligencias"],
                    format_func=lambda x: {
                        "despacho_saneador": "🔍 Despacho Saneador",
                        "sentenca_procedencia": "⚖️ Sentença de Procedência", 
                        "despacho_diligencias": "📋 Despacho de Diligências"
                    }[x]
                )
            
            with col2:
                magistrado = st.text_input("Nome do Magistrado:", "[NOME DO MAGISTRADO]")
            
            with col3:
                comarca = st.text_input("Comarca:", "São Paulo")
            
            # Botão de geração
            if st.button("🚀 GERAR MINUTA", type="primary", use_container_width=True):
                with st.spinner("📝 Gerando minuta personalizada..."):
                    
                    # Converter documento se necessário
                    if hasattr(documento_selecionado, 'autor') and hasattr(documento_selecionado.autor, 'nome'):
                        # É um DocumentoEstruturado
                        analise = PeticaoAnalise(
                            autor=documento_selecionado.autor.nome,
                            reu=documento_selecionado.reu.nome,
                            tipo_acao=documento_selecionado.tipo_acao,
                            pedidos=[p.descricao for p in documento_selecionado.pedidos],
                            fundamentos=[f.referencia for f in documento_selecionado.fundamentos_legais],
                            valor_causa=documento_selecionado.valor_causa,
                            competencia=documento_selecionado.competencia_sugerida,
                            requisitos_preenchidos={},
                            provas_necessarias=[],
                            recomendacoes=[]
                        )
                    else:
                        # É uma PeticaoAnalise
                        analise = documento_selecionado
                    
                    # Gerar minuta
                    minuta = self.gerador_minutas.gerar_minuta(analise, tipo_minuta)
                    
                    # Salvar na sessão
                    st.session_state.minutas_geradas.append(minuta)
                    
                    st.success("✅ Minuta gerada com sucesso!")
                    
                    # Exibir minuta
                    self._exibir_minuta_gerada(minuta)
    
    def _exibir_minuta_gerada(self, minuta: MinutaGerada):
        """Exibe minuta gerada"""
        
        st.markdown("### 📄 Minuta Gerada")
        
        # Informações da minuta
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Tipo:** {minuta.tipo_documento.replace('_', ' ').title()}")
        
        with col2:
            st.write(f"**Gerado em:** {minuta.data_geracao.strftime('%d/%m/%Y %H:%M')}")
        
        with col3:
            st.write(f"**Fundamentos:** {len(minuta.fundamentacao_legal)}")
        
        # Conteúdo da minuta
        st.markdown("#### 📝 Conteúdo")
        st.text_area(
            "Minuta:",
            value=minuta.conteudo,
            height=400,
            disabled=True
        )
        
        # Informações adicionais
        with st.expander("📚 Fundamentação Legal"):
            for fund in minuta.fundamentacao_legal:
                st.write(f"• {fund}")
        
        with st.expander("⚖️ Jurisprudência Aplicável"):
            for jur in minuta.jurisprudencia_aplicavel:
                st.write(f"• {jur}")
        
        with st.expander("💡 Observações"):
            for obs in minuta.observacoes:
                st.write(f"• {obs}")
        
        # Botões de ação
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download da minuta
            conteudo_completo = f"""
{minuta.conteudo}

---

FUNDAMENTAÇÃO LEGAL:
{chr(10).join(f'• {f}' for f in minuta.fundamentacao_legal)}

JURISPRUDÊNCIA APLICÁVEL:
{chr(10).join(f'• {j}' for j in minuta.jurisprudencia_aplicavel)}

OBSERVAÇÕES:
{chr(10).join(f'• {o}' for o in minuta.observacoes)}

---
Gerado em: {minuta.data_geracao.strftime('%d/%m/%Y %H:%M')}
            """
            
            st.download_button(
                label="📥 Download Minuta",
                data=conteudo_completo,
                file_name=f"minuta_{minuta.tipo_documento}_{minuta.data_geracao.strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )
        
        with col2:
            if st.button("📧 Enviar por Email"):
                st.info("🚧 Funcionalidade em desenvolvimento")
        
        with col3:
            if st.button("🖨️ Formatar para Impressão"):
                st.info("🚧 Funcionalidade em desenvolvimento")
    
    def _render_analise_juridica(self):
        """Aba de análise jurídica avançada"""
        
        st.markdown("## 🧠 Análise Jurídica Avançada")
        st.markdown("**Funcionalidade:** Analisa probabilidade de sucesso, riscos e gera recomendações estratégicas")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Entrada de texto para análise
            texto_analise = st.text_area(
                "Texto da petição para análise jurídica:",
                height=300,
                placeholder="Cole aqui o texto da petição para análise jurídica completa..."
            )
            
            tipo_acao_analise = st.selectbox(
                "Tipo de ação:",
                [
                    "indenização por danos morais",
                    "ação de cobrança", 
                    "revisão contrato bancário",
                    "ação consignatória"
                ]
            )
        
        with col2:
            st.markdown("### 📊 Estatísticas")
            st.metric("Análises Realizadas", len(st.session_state.analises_realizadas))
            
            # Últimas análises
            if st.session_state.analises_realizadas:
                st.markdown("#### 🕒 Última Análise")
                ultima = st.session_state.analises_realizadas[-1]
                st.write(f"**Score:** {ultima.score_geral}/10")
                st.write(f"**Risco:** {ultima.nivel_risco.value.title()}")
                st.write(f"**Sucesso:** {ultima.analise_probabilidade.exito_total:.1%}")
        
        # Botão de análise
        if st.button("🧠 REALIZAR ANÁLISE JURÍDICA", type="primary", use_container_width=True, disabled=not texto_analise.strip()):
            
            with st.spinner("🔄 Realizando análise jurídica completa..."):
                # Barra de progresso
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Etapa 1: Análise de requisitos
                status_text.text("📋 Analisando requisitos legais...")
                progress_bar.progress(20)
                time.sleep(1)
                
                # Etapa 2: Cálculo de probabilidades
                status_text.text("📊 Calculando probabilidade de sucesso...")
                progress_bar.progress(40)
                time.sleep(1)
                
                # Etapa 3: Análise de riscos
                status_text.text("⚠️ Identificando riscos e oportunidades...")
                progress_bar.progress(60)
                time.sleep(1)
                
                # Etapa 4: Geração de recomendações
                status_text.text("💡 Gerando recomendações estratégicas...")
                progress_bar.progress(80)
                time.sleep(1)
                
                # Realizar análise
                analise = self.analisador.analisar_caso_completo(texto_analise, tipo_acao_analise)
                
                # Etapa 5: Finalização
                status_text.text("✅ Análise jurídica concluída!")
                progress_bar.progress(100)
                time.sleep(0.5)
                
                # Limpar progresso
                progress_bar.empty()
                status_text.empty()
                
                # Salvar na sessão
                st.session_state.analises_realizadas.append(analise)
                
                # Exibir resultados
                self._exibir_analise_juridica_completa(analise)
    
    def _exibir_analise_juridica_completa(self, analise: AnaliseJuridicaCompleta):
        """Exibe análise jurídica completa"""
        
        st.success("✅ Análise jurídica concluída!")
        
        # Resumo executivo
        st.markdown("### 📊 Resumo Executivo")
        st.markdown(analise.resumo_executivo)
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            score_color = "🟢" if analise.score_geral >= 7 else "🟡" if analise.score_geral >= 5 else "🔴"
            st.metric("Score Geral", f"{analise.score_geral}/10", delta=None)
            st.markdown(f"**{score_color} Qualidade**")
        
        with col2:
            st.metric("Probabilidade Sucesso", f"{analise.analise_probabilidade.exito_total:.1%}")
        
        with col3:
            risco_color = {"baixo": "🟢", "medio": "🟡", "alto": "🟠", "critico": "🔴"}[analise.nivel_risco.value]
            st.metric("Nível de Risco", f"{risco_color} {analise.nivel_risco.value.title()}")
        
        with col4:
            st.metric("Requisitos Atendidos", f"{analise.percentual_atendimento:.1%}")
        
        st.divider()
        
        # Tabs detalhadas
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Requisitos Legais",
            "📊 Análise de Probabilidade",
            "💡 Recomendações",
            "📄 Relatório Completo"
        ])
        
        with tab1:
            self._exibir_requisitos_legais(analise)
        
        with tab2:
            self._exibir_analise_probabilidade(analise)
        
        with tab3:
            self._exibir_recomendacoes_estrategicas(analise)
        
        with tab4:
            self._exibir_relatorio_analise_juridica(analise)
    
    def _exibir_requisitos_legais(self, analise: AnaliseJuridicaCompleta):
        """Exibe análise de requisitos legais"""
        
        st.markdown("### 📋 Análise de Requisitos Legais")
        
        # Separar obrigatórios e opcionais
        obrigatorios = [r for r in analise.requisitos_legais if r.obrigatorio]
        opcionais = [r for r in analise.requisitos_legais if not r.obrigatorio]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⚠️ Requisitos Obrigatórios")
            
            for req in obrigatorios:
                status_icon = "✅" if req.atendido else "❌"
                st.markdown(f"**{status_icon} {req.nome.replace('_', ' ').title()}**")
                st.write(f"📝 {req.descricao}")
                
                if req.observacoes:
                    st.info(f"💡 {req.observacoes}")
                
                if req.evidencias:
                    st.write(f"🔍 Evidências: {', '.join(req.evidencias)}")
                
                st.divider()
        
        with col2:
            st.markdown("#### ⭕ Requisitos Opcionais")
            
            for req in opcionais:
                status_icon = "✅" if req.atendido else "⭕"
                st.markdown(f"**{status_icon} {req.nome.replace('_', ' ').title()}**")
                st.write(f"📝 {req.descricao}")
                
                if req.observacoes:
                    st.info(f"💡 {req.observacoes}")
                
                st.divider()
    
    def _exibir_analise_probabilidade(self, analise: AnaliseJuridicaCompleta):
        """Exibe análise de probabilidade"""
        
        prob = analise.analise_probabilidade
        
        st.markdown("### 📊 Análise de Probabilidade de Sucesso")
        
        # Gráfico de probabilidades
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎯 Êxito Total", f"{prob.exito_total:.1%}")
            st.progress(prob.exito_total)
        
        with col2:
            st.metric("⚖️ Êxito Parcial", f"{prob.exito_parcial:.1%}")
            st.progress(prob.exito_parcial)
        
        with col3:
            st.metric("⚠️ Risco Improcedência", f"{prob.risco_improcedencia:.1%}")
            st.progress(prob.risco_improcedencia)
        
        # Fatores de influência
        col1, col2 = st.columns(2)
        
        with col1:
            if prob.fatores_positivos:
                st.markdown("#### ✅ Fatores Favoráveis")
                for fator in prob.fatores_positivos:
                    st.success(f"✅ {fator}")
        
        with col2:
            if prob.fatores_negativos:
                st.markdown("#### ❌ Fatores Desfavoráveis")
                for fator in prob.fatores_negativos:
                    st.error(f"❌ {fator}")
        
        # Precedentes
        if prob.precedentes_favoraveis:
            st.markdown("#### 📚 Precedentes Aplicáveis")
            for precedente in prob.precedentes_favoraveis:
                st.info(f"📚 {precedente}")
    
    def _exibir_recomendacoes_estrategicas(self, analise: AnaliseJuridicaCompleta):
        """Exibe recomendações estratégicas"""
        
        st.markdown(f"### 💡 Recomendações Estratégicas ({len(analise.recomendacoes)})")
        
        # Filtrar por prioridade
        alta_prioridade = [r for r in analise.recomendacoes if r.prioridade == "alta"]
        media_prioridade = [r for r in analise.recomendacoes if r.prioridade == "media"]
        baixa_prioridade = [r for r in analise.recomendacoes if r.prioridade == "baixa"]
        
        # Recomendações de alta prioridade
        if alta_prioridade:
            st.markdown("#### 🔴 Prioridade Alta")
            for rec in alta_prioridade:
                with st.expander(f"🔴 {rec.titulo}"):
                    st.write(f"**Tipo:** {rec.tipo.value.title()}")
                    st.write(f"**Descrição:** {rec.descricao}")
                    
                    if rec.prazo_sugerido:
                        st.write(f"**Prazo:** {rec.prazo_sugerido}")
                    
                    if rec.custo_estimado:
                        st.write(f"**Custo:** {rec.custo_estimado}")
                    
                    if rec.fundamentacao:
                        st.write("**Fundamentação:**")
                        for fund in rec.fundamentacao:
                            st.write(f"• {fund}")
        
        # Recomendações de média prioridade
        if media_prioridade:
            st.markdown("#### 🟡 Prioridade Média")
            for rec in media_prioridade:
                with st.expander(f"🟡 {rec.titulo}"):
                    st.write(rec.descricao)
        
        # Recomendações de baixa prioridade  
        if baixa_prioridade:
            st.markdown("#### 🟢 Prioridade Baixa")
            for rec in baixa_prioridade:
                with st.expander(f"🟢 {rec.titulo}"):
                    st.write(rec.descricao)
        
        # Análise estratégica
        st.markdown("### 🎯 Análise Estratégica")
        
        estrategica = analise.analise_estrategica
        
        col1, col2 = st.columns(2)
        
        with col1:
            if estrategica.valor_estimado_condenacao:
                st.metric("💰 Valor Estimado", estrategica.valor_estimado_condenacao)
            
            st.metric("⏱️ Tempo Estimado", estrategica.tempo_estimado_processo)
            st.metric("💸 Custas Estimadas", estrategica.custas_estimadas)
        
        with col2:
            if estrategica.estrategias_recomendadas:
                st.markdown("**🎯 Estratégias Recomendadas:**")
                for estrategia in estrategica.estrategias_recomendadas:
                    st.write(f"• {estrategia}")
            
            if estrategica.oportunidades:
                st.markdown("**🎉 Oportunidades:**")
                for oportunidade in estrategica.oportunidades:
                    st.write(f"• {oportunidade}")
    
    def _exibir_relatorio_analise_juridica(self, analise: AnaliseJuridicaCompleta):
        """Exibe relatório completo da análise jurídica"""
        
        st.markdown("### 📄 Relatório Completo")
        
        # Gerar relatório
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            relatorio_path = f.name
        
        self.analisador.exportar_relatorio_completo(analise, relatorio_path)
        
        # Ler relatório
        with open(relatorio_path, 'r', encoding='utf-8') as f:
            relatorio_conteudo = f.read()
        
        # Exibir relatório
        st.markdown(relatorio_conteudo)
        
        # Botão de download
        st.download_button(
            label="📥 Download Relatório Completo",
            data=relatorio_conteudo,
            file_name=f"analise_juridica_{analise.id_analise}.md",
            mime="text/markdown"
        )
    
    def _render_dashboard_premium(self):
        """Dashboard com estatísticas e histórico"""
        
        st.markdown("## 📊 Dashboard Premium")
        
        # Estatísticas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📋 Documentos Analisados",
                len(st.session_state.documentos_analisados),
                delta=len(st.session_state.documentos_analisados)
            )
        
        with col2:
            st.metric(
                "📝 Minutas Geradas", 
                len(st.session_state.minutas_geradas),
                delta=len(st.session_state.minutas_geradas)
            )
        
        with col3:
            st.metric(
                "🧠 Análises Jurídicas",
                len(st.session_state.analises_realizadas),
                delta=len(st.session_state.analises_realizadas)
            )
        
        with col4:
            # Score médio das análises
            if st.session_state.analises_realizadas:
                score_medio = sum(a.score_geral for a in st.session_state.analises_realizadas) / len(st.session_state.analises_realizadas)
                st.metric("📈 Score Médio", f"{score_medio:.1f}/10")
            else:
                st.metric("📈 Score Médio", "0.0/10")
        
        st.divider()
        
        # Histórico detalhado
        tab1, tab2, tab3 = st.tabs([
            "📋 Histórico de Análises",
            "📝 Histórico de Minutas", 
            "🧠 Histórico Jurídico"
        ])
        
        with tab1:
            if st.session_state.documentos_analisados:
                st.markdown("### 📋 Documentos Analisados")
                
                for i, doc in enumerate(reversed(st.session_state.documentos_analisados), 1):
                    with st.expander(f"📄 Documento {i} - {doc.tipo_acao}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**ID:** {doc.id_documento}")
                            st.write(f"**Autor:** {doc.autor.nome}")
                            st.write(f"**Réu:** {doc.reu.nome}")
                        
                        with col2:
                            st.write(f"**Completude:** {doc.completude_score:.1%}")
                            st.write(f"**Pedidos:** {len(doc.pedidos)}")
                            st.write(f"**Fundamentos:** {len(doc.fundamentos_legais)}")
                        
                        with col3:
                            st.write(f"**Data:** {doc.data_analise.strftime('%d/%m/%Y %H:%M')}")
                            st.write(f"**Problemas:** {len(doc.problemas_identificados)}")
            else:
                st.info("📭 Nenhum documento analisado ainda")
        
        with tab2:
            if st.session_state.minutas_geradas:
                st.markdown("### 📝 Minutas Geradas")
                
                for i, minuta in enumerate(reversed(st.session_state.minutas_geradas), 1):
                    with st.expander(f"📝 Minuta {i} - {minuta.tipo_documento.replace('_', ' ').title()}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Tipo:** {minuta.tipo_documento}")
                            st.write(f"**Data:** {minuta.data_geracao.strftime('%d/%m/%Y %H:%M')}")
                        
                        with col2:
                            st.write(f"**Fundamentos:** {len(minuta.fundamentacao_legal)}")
                            st.write(f"**Jurisprudência:** {len(minuta.jurisprudencia_aplicavel)}")
                        
                        # Preview do conteúdo
                        preview = minuta.conteudo[:200] + "..." if len(minuta.conteudo) > 200 else minuta.conteudo
                        st.text_area("Preview:", value=preview, height=100, disabled=True)
            else:
                st.info("📭 Nenhuma minuta gerada ainda")
        
        with tab3:
            if st.session_state.analises_realizadas:
                st.markdown("### 🧠 Análises Jurídicas")
                
                for i, analise in enumerate(reversed(st.session_state.analises_realizadas), 1):
                    with st.expander(f"🧠 Análise {i} - {analise.tipo_acao}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**ID:** {analise.id_analise}")
                            st.write(f"**Score:** {analise.score_geral}/10")
                            st.write(f"**Risco:** {analise.nivel_risco.value.title()}")
                        
                        with col2:
                            st.write(f"**Sucesso:** {analise.analise_probabilidade.exito_total:.1%}")
                            st.write(f"**Requisitos:** {analise.percentual_atendimento:.1%}")
                            st.write(f"**Recomendações:** {len(analise.recomendacoes)}")
                        
                        with col3:
                            st.write(f"**Data:** {analise.data_analise.strftime('%d/%m/%Y %H:%M')}")
                            
                            if analise.analise_estrategica.valor_estimado_condenacao:
                                st.write(f"**Valor Est.:** {analise.analise_estrategica.valor_estimado_condenacao}")
            else:
                st.info("📭 Nenhuma análise jurídica realizada ainda")
    
    def _render_configuracoes(self):
        """Aba de configurações"""
        
        st.markdown("## ⚙️ Configurações do Sistema")
        
        # Configurações gerais
        st.markdown("### 🔧 Configurações Gerais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Configurações de análise
            st.markdown("#### 📊 Análise de Documentos")
            
            nivel_analise = st.selectbox(
                "Nível de análise:",
                ["Básico", "Intermediário", "Avançado"],
                index=2
            )
            
            incluir_sugestoes = st.checkbox("Incluir sugestões de melhoria", value=True)
            incluir_precedentes = st.checkbox("Buscar precedentes automáticamente", value=True)
        
        with col2:
            # Configurações de minutas
            st.markdown("#### 📝 Geração de Minutas")
            
            magistrado_padrao = st.text_input("Magistrado padrão:", "[NOME DO MAGISTRADO]")
            comarca_padrao = st.text_input("Comarca padrão:", "São Paulo")
            
            incluir_jurisprudencia = st.checkbox("Incluir jurisprudência nas minutas", value=True)
        
        st.divider()
        
        # Exportação e backup
        st.markdown("### 💾 Exportação e Backup")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Exportar Todos os Dados"):
                # Criar arquivo JSON com todos os dados
                dados_exportacao = {
                    "documentos_analisados": len(st.session_state.documentos_analisados),
                    "minutas_geradas": len(st.session_state.minutas_geradas),
                    "analises_realizadas": len(st.session_state.analises_realizadas),
                    "data_exportacao": datetime.now().isoformat()
                }
                
                st.download_button(
                    label="📥 Download Backup",
                    data=json.dumps(dados_exportacao, indent=2),
                    file_name=f"backup_juridico_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("🗑️ Limpar Histórico"):
                if st.button("⚠️ Confirmar Limpeza", type="secondary"):
                    st.session_state.documentos_analisados = []
                    st.session_state.minutas_geradas = []
                    st.session_state.analises_realizadas = []
                    st.success("✅ Histórico limpo!")
        
        with col3:
            if st.button("🔄 Resetar Sistema"):
                if st.button("⚠️ Confirmar Reset", type="secondary"):
                    # Limpar tudo
                    for key in list(st.session_state.keys()):
                        if key.startswith(('documentos_', 'minutas_', 'analises_')):
                            del st.session_state[key]
                    st.success("✅ Sistema resetado!")
        
        st.divider()
        
        # Informações do sistema
        st.markdown("### ℹ️ Informações do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            **🚀 Jurisprudência AI Premium v2.0**
            
            **Funcionalidades:**
            • 📋 Análise estruturada de petições
            • 📝 Gerador automático de minutas
            • 🧠 Análise jurídica avançada
            • 📊 Dashboard e relatórios
            • ⚖️ Cálculo de probabilidades
            """)
        
        with col2:
            st.success("""
            **✅ Vantagens sobre Concorrentes:**
            
            • 🎯 Análise mais precisa que o Justino
            • 🚀 Interface mais moderna e intuitiva
            • 🧠 IA treinada especificamente para direito brasileiro
            • 📊 Relatórios mais detalhados
            • 💰 Estimativas de valores realísticas
            """)

def main():
    """Função principal da interface premium"""
    
    # Configuração da página
    st.set_page_config(
        page_title='🚀 Jurisprudência AI Premium',
        page_icon='⚖️',
        layout='wide',
        initial_sidebar_state='collapsed'
    )
    
    # CSS personalizado
    st.markdown("""
    <style>
        .main {
            padding-top: 1rem;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin: 10px 0;
        }
        
        .success-box {
            background: linear-gradient(90deg, #00d084, #00a86b);
            padding: 10px;
            border-radius: 8px;
            color: white;
            margin: 10px 0;
        }
        
        .warning-box {
            background: linear-gradient(90deg, #ffa500, #ff8c00);
            padding: 10px;
            border-radius: 8px;
            color: white;
            margin: 10px 0;
        }
        
        .info-box {
            background: linear-gradient(90deg, #4a90e2, #67b3f3);
            padding: 10px;
            border-radius: 8px;
            color: white;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Inicializar interface
    interface = InterfacePremium()
    interface.render_interface_completa()

if __name__ == "__main__":
    main()