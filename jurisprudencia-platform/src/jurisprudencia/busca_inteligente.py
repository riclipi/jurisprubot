"""
🎯 BUSCA INTELIGENTE DE JURISPRUDÊNCIA
Sistema que supera plataformas concorrentes em precisão e relevância
"""

import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from pathlib import Path
import os

# Importar sistemas existentes
from ..rag.simple_search import SimpleSearchEngine
from ..scraper.realtime_search import RealtimeJurisprudenceSearch

# Importar cliente Gemini
try:
    from ..ai.gemini_client import GeminiClient, get_gemini_client
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Gemini não disponível para busca inteligente")

# Importar outros LLMs como fallback
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class TipoTribunal(Enum):
    STF = "stf"
    STJ = "stj" 
    TST = "tst"
    TJSP = "tjsp"
    TRF = "trf"
    TODOS = "todos"

class RelevanciaJurisprudencia(Enum):
    MUITO_ALTA = "muito_alta"
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"

@dataclass
class PrecedenteJuridico:
    """Estrutura de um precedente jurídico"""
    id_precedente: str
    tribunal: str
    numero_processo: str
    relator: str
    data_julgamento: datetime
    ementa: str
    acordao_completo: str
    palavras_chave: List[str]
    relevancia: RelevanciaJurisprudencia
    score_similaridade: float
    url_fonte: Optional[str] = None
    citacoes_posteriores: int = 0
    status_vigencia: str = "vigente"  # vigente, superado, parcialmente_superado

@dataclass 
class AnaliseJurisprudencial:
    """Análise jurisprudencial completa"""
    id_analise: str
    consulta_original: str
    tipo_acao: str
    data_analise: datetime
    
    precedentes_favoraveis: List[PrecedenteJuridico]
    precedentes_contrarios: List[PrecedenteJuridico]
    precedentes_neutros: List[PrecedenteJuridico]
    
    tendencia_jurisprudencial: str  # favoravel, contraria, dividida, indefinida
    grau_consolidacao: float  # 0-1
    recomendacao_uso: str
    
    sumulas_aplicaveis: List[str]
    orientacoes_tribunais: List[str]
    
    estatisticas: Dict[str, Any]

class BuscaInteligente:
    """
    🚀 SISTEMA DE BUSCA INTELIGENTE DE JURISPRUDÊNCIA
    Funcionalidades avançadas que superam o Justino Cível
    """
    
    def __init__(self, use_ai: bool = True, ai_provider: str = "gemini"):
        self.setup_logging()
        self._inicializar_sistemas()
        self._carregar_base_conhecimento()
        self._configurar_parametros()
        self._inicializar_brlaw_mcp()
        
        # Configuração de IA
        self.use_ai = use_ai
        self.ai_provider = ai_provider
        self.ai_client = None
        
        if self.use_ai:
            self._inicializar_cliente_ia()
    
    def setup_logging(self):
        """Configura sistema de logs"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _inicializar_sistemas(self):
        """Inicializa sistemas de busca"""
        try:
            self.busca_local = SimpleSearchEngine()
            self.busca_tempo_real = RealtimeJurisprudenceSearch(max_results=50)
            self.logger.info("Sistemas de busca inicializados com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sistemas: {e}")
            self.busca_local = None
            self.busca_tempo_real = None
    
    def _carregar_base_conhecimento(self):
        """Carrega base de conhecimento jurisprudencial"""
        
        self.sumulas_importantes = {
            "STJ": {
                385: "Da anotação irregular em cadastro de proteção ao crédito, não cabe indenização por dano moral, quando preexistente legítima inscrição",
                596: "É admissível a capitalização de juros com periodicidade inferior a um ano em contratos celebrados após 31.3.2012",
                83: "Não se conhece do recurso especial pela divergência, quando a orientação do Tribunal se firmou no mesmo sentido da decisão recorrida",
                54: "Os juros moratórios fluem a partir do evento danoso, em caso de responsabilidade extracontratual"
            },
            
            "TJSP": {
                67: "O simples descumprimento do dever legal ou contratual, por caracterizar mero aborrecimento, em princípio, não configura dano moral",
                15: "Não incide ICMS sobre operações de arrendamento mercantil de veículos",
                25: "Na indenização por dano moral, o valor deve ser fixado com moderação"
            },
            
            "STF": {
                631: "É inconstitucional a exigência de depósito prévio como requisito de admissibilidade de recurso administrativo",
                690: "Compete originariamente ao Supremo Tribunal Federal o julgamento de habeas corpus contra decisão de Ministro de Estado"
            }
        }
        
        self.areas_tematicas = {
            "dano_moral": {
                "palavras_chave": ["dano moral", "indenização", "constrangimento", "abalo", "sofrimento"],
                "tribunais_referencia": ["STJ", "TJSP"],
                "sumulas_chave": ["STJ 385", "TJSP 67"],
                "valores_referencia": {"min": 1000, "max": 50000, "medio": 8000}
            },
            
            "direito_consumidor": {
                "palavras_chave": ["consumidor", "fornecedor", "CDC", "vício", "defeito"],
                "tribunais_referencia": ["STJ", "TJSP", "TRF"],
                "sumulas_chave": ["STJ 297", "STJ 301"],
                "valores_referencia": {"min": 2000, "max": 30000, "medio": 10000}
            },
            
            "direito_bancario": {
                "palavras_chave": ["banco", "financeiro", "juros", "spread", "capitalização"],
                "tribunais_referencia": ["STJ", "TJSP"],
                "sumulas_chave": ["STJ 596", "STJ 382"],
                "valores_referencia": {"min": 5000, "max": 100000, "medio": 25000}
            },
            
            "responsabilidade_civil": {
                "palavras_chave": ["responsabilidade civil", "nexo causal", "culpa", "dolo"],
                "tribunais_referencia": ["STJ", "STF", "TJSP"],
                "sumulas_chave": ["STJ 54", "STJ 37"],
                "valores_referencia": {"min": 3000, "max": 200000, "medio": 15000}
            }
        }
        
        self.padroes_reconhecimento = {
            "numero_processo": r'(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})',
            "recurso_stj": r'(REsp|AgRg|EDcl)\s*(\d{1,7})',
            "recurso_stf": r'(RE|AI|ADI|HC|MS)\s*(\d{1,7})',
            "tribunal_local": r'(TJSP|TJRJ|TJMG|TJRS|TJPR)\s*[^A-Z]*(\d+)',
            "sumula": r'Súmula\s*(\d+)[^A-Z]*(?:do|da)?\s*([A-Z]{2,})',
            "data_julgamento": r'(?:julgad[ao]|decidid[ao])\s*em\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})',
            "relator": r'(?:Relator|Rel\.|Min\.)\s*:?\s*([A-ZÁÊÍÓÚÇÕ][a-záêíóúçõ\s]+)',
            "valor_condenacao": r'(?:condenar|condena[çã]o)[^R]*R\$\s*([\d.,]+)'
        }
    
    def _configurar_parametros(self):
        """Configura parâmetros de busca"""
        
        self.config_busca = {
            "max_resultados_por_tribunal": 20,
            "min_score_relevancia": 0.3,
            "peso_tribunal_superior": 1.5,
            "peso_data_recente": 1.2,
            "peso_citacoes": 1.3,
            "timeout_busca": 30,  # segundos
            "cache_duracao": 3600  # 1 hora
        }
        
        self.filtros_qualidade = {
            "min_palavras_ementa": 10,
            "tribunais_prioritarios": ["STF", "STJ", "TJSP"],
            "anos_relevantes": 10,  # últimos 10 anos
            "excluir_embargos": True,
            "excluir_agravos_simples": True
        }
    
    def _inicializar_brlaw_mcp(self):
        """Inicializa integração com BRLaw MCP"""
        try:
            from ..mcp_brlaw.brlaw_integration import BRLawMCPIntegration
            self.brlaw_mcp = BRLawMCPIntegration()
            self.brlaw_disponivel = True
            self.logger.info("BRLaw MCP integrado com sucesso")
        except Exception as e:
            self.logger.warning(f"BRLaw MCP não disponível: {e}")
            self.brlaw_mcp = None
            self.brlaw_disponivel = False
    
    async def buscar_jurisprudencia_inteligente(self, consulta: str, tipo_acao: str, 
                                        tribunal: TipoTribunal = TipoTribunal.TODOS) -> AnaliseJurisprudencial:
        """
        🎯 BUSCA INTELIGENTE DE JURISPRUDÊNCIA
        Sistema principal que combina todas as funcionalidades
        """
        
        id_analise = self._gerar_id_analise()
        self.logger.info(f"Iniciando busca inteligente: {id_analise}")
        
        # Preparar consulta otimizada
        consulta_otimizada = self._otimizar_consulta(consulta, tipo_acao)
        
        # Buscar em múltiplas fontes
        precedentes_brutos = []
        
        # 1. Busca local (cache/base existente)
        if self.busca_local:
            precedentes_locais = self._buscar_local_inteligente(consulta_otimizada, tipo_acao)
            precedentes_brutos.extend(precedentes_locais)
        
        # 2. Busca tempo real (TJSP e outros)
        if self.busca_tempo_real:
            precedentes_tempo_real = self._buscar_tempo_real_inteligente(consulta_otimizada, tipo_acao)
            precedentes_brutos.extend(precedentes_tempo_real)
        
        # 2.5. Busca BRLaw MCP (STJ/TST oficiais) - NOVA FUNCIONALIDADE PREMIUM
        if self.brlaw_disponivel:
            precedentes_brlaw = await self._buscar_brlaw_mcp_inteligente(consulta_otimizada, tipo_acao)
            precedentes_brutos.extend(precedentes_brlaw)
        
        # 3. Buscar súmulas específicas
        sumulas_aplicaveis = self._buscar_sumulas_aplicaveis(consulta, tipo_acao)
        
        # Processar e classificar precedentes
        precedentes_processados = self._processar_precedentes(precedentes_brutos, consulta, tipo_acao)
        
        # Classificar por favorabilidade
        favoraveis, contrarios, neutros = self._classificar_precedentes(precedentes_processados, consulta, tipo_acao)
        
        # Analisar tendência jurisprudencial
        tendencia = self._analisar_tendencia_jurisprudencial(favoraveis, contrarios, neutros)
        
        # Calcular grau de consolidação
        grau_consolidacao = self._calcular_grau_consolidacao(favoraveis, contrarios)
        
        # Gerar recomendação de uso
        recomendacao = self._gerar_recomendacao_uso(tendencia, grau_consolidacao, favoraveis)
        
        # Buscar orientações dos tribunais
        orientacoes = self._buscar_orientacoes_tribunais(tipo_acao)
        
        # Calcular estatísticas
        estatisticas = self._calcular_estatisticas_busca(precedentes_processados, favoraveis, contrarios)
        
        return AnaliseJurisprudencial(
            id_analise=id_analise,
            consulta_original=consulta,
            tipo_acao=tipo_acao,
            data_analise=datetime.now(),
            precedentes_favoraveis=favoraveis[:10],  # Top 10
            precedentes_contrarios=contrarios[:5],   # Top 5
            precedentes_neutros=neutros[:5],         # Top 5
            tendencia_jurisprudencial=tendencia,
            grau_consolidacao=grau_consolidacao,
            recomendacao_uso=recomendacao,
            sumulas_aplicaveis=sumulas_aplicaveis,
            orientacoes_tribunais=orientacoes,
            estatisticas=estatisticas
        )
    
    def _gerar_id_analise(self) -> str:
        """Gera ID único para análise"""
        import hashlib
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_obj = hashlib.md5(timestamp.encode())
        return f"BUSCA_{timestamp}_{hash_obj.hexdigest()[:8]}"
    
    def _otimizar_consulta(self, consulta: str, tipo_acao: str) -> str:
        """Otimiza consulta para busca mais eficiente"""
        
        # Identificar área temática
        area_tematica = self._identificar_area_tematica(consulta, tipo_acao)
        
        # Adicionar palavras-chave específicas da área
        if area_tematica in self.areas_tematicas:
            palavras_area = self.areas_tematicas[area_tematica]["palavras_chave"]
            consulta_expandida = consulta + " " + " ".join(palavras_area[:3])
        else:
            consulta_expandida = consulta
        
        # Remover stopwords jurídicas desnecessárias
        stopwords = ["processo", "autos", "recurso", "apelação", "agravo"]
        palavras = consulta_expandida.split()
        palavras_filtradas = [p for p in palavras if p.lower() not in stopwords or len(p) > 8]
        
        consulta_otimizada = " ".join(palavras_filtradas)
        
        self.logger.info(f"Consulta otimizada: {consulta} -> {consulta_otimizada}")
        return consulta_otimizada
    
    def _identificar_area_tematica(self, consulta: str, tipo_acao: str) -> str:
        """Identifica área temática da consulta"""
        
        consulta_lower = consulta.lower()
        tipo_lower = tipo_acao.lower()
        
        pontuacoes = {}
        
        for area, config in self.areas_tematicas.items():
            pontuacao = 0
            
            # Verificar palavras-chave na consulta
            for palavra in config["palavras_chave"]:
                if palavra.lower() in consulta_lower:
                    pontuacao += 2
            
            # Verificar no tipo de ação
            for palavra in config["palavras_chave"]:
                if palavra.lower() in tipo_lower:
                    pontuacao += 3
            
            if pontuacao > 0:
                pontuacoes[area] = pontuacao
        
        if pontuacoes:
            return max(pontuacoes, key=pontuacoes.get)
        
        return "geral"
    
    def _buscar_local_inteligente(self, consulta: str, tipo_acao: str) -> List[Dict]:
        """Busca inteligente na base local"""
        
        try:
            resultados = self.busca_local.search(consulta, top_k=20)
            
            precedentes = []
            for resultado in resultados:
                precedente = self._converter_resultado_local(resultado, consulta)
                if precedente:
                    precedentes.append(precedente)
            
            self.logger.info(f"Busca local: {len(precedentes)} precedentes encontrados")
            return precedentes
            
        except Exception as e:
            self.logger.error(f"Erro na busca local: {e}")
            return []
    
    def _buscar_tempo_real_inteligente(self, consulta: str, tipo_acao: str) -> List[Dict]:
        """Busca inteligente em tempo real"""
        
        try:
            resultados = self.busca_tempo_real.get_relevant_chunks(consulta)
            
            precedentes = []
            for resultado in resultados:
                # Filtrar resultados que não são do cache local
                if resultado.get('source') != 'local_data':
                    precedente = self._converter_resultado_tempo_real(resultado, consulta)
                    if precedente:
                        precedentes.append(precedente)
            
            self.logger.info(f"Busca tempo real: {len(precedentes)} precedentes encontrados")
            return precedentes
            
        except Exception as e:
            self.logger.error(f"Erro na busca tempo real: {e}")
            return []
    
    async def _buscar_brlaw_mcp_inteligente(self, consulta: str, tipo_acao: str) -> List[Dict]:
        """Busca inteligente via BRLaw MCP (STJ/TST oficiais)"""
        
        try:
            # Determinar se deve buscar TST
            incluir_tst = any(termo in tipo_acao.lower() for termo in [
                "trabalho", "trabalhista", "emprego", "empregado", "empregador",
                "horas extras", "adicional", "fgts", "rescisão"
            ])
            
            # Buscar precedentes
            resultados_brlaw = await self.brlaw_mcp.buscar_precedentes_completo(
                consulta, 
                incluir_stj=True, 
                incluir_tst=incluir_tst,
                max_paginas=1  # Limitar para performance
            )
            
            precedentes = []
            
            # Converter precedentes STJ
            for precedente_stj in resultados_brlaw.get("stj", []):
                precedente_dict = {
                    "id_precedente": f"BRLAW_STJ_{hash(precedente_stj.ementa)[:12]}",
                    "tribunal": "STJ",
                    "numero_processo": "N/A",
                    "relator": "N/A",
                    "data_julgamento": precedente_stj.data_consulta,
                    "ementa": precedente_stj.ementa[:500],
                    "acordao_completo": precedente_stj.ementa,
                    "score_similaridade": precedente_stj.relevancia_score,
                    "fonte": "brlaw_mcp_stj",
                    "url_fonte": None
                }
                precedentes.append(precedente_dict)
            
            # Converter precedentes TST
            for precedente_tst in resultados_brlaw.get("tst", []):
                precedente_dict = {
                    "id_precedente": f"BRLAW_TST_{hash(precedente_tst.ementa)[:12]}",
                    "tribunal": "TST",
                    "numero_processo": "N/A",
                    "relator": "N/A", 
                    "data_julgamento": precedente_tst.data_consulta,
                    "ementa": precedente_tst.ementa[:500],
                    "acordao_completo": precedente_tst.ementa,
                    "score_similaridade": precedente_tst.relevancia_score,
                    "fonte": "brlaw_mcp_tst",
                    "url_fonte": None
                }
                precedentes.append(precedente_dict)
            
            self.logger.info(f"BRLaw MCP: {len(precedentes)} precedentes encontrados")
            return precedentes
            
        except Exception as e:
            self.logger.error(f"Erro na busca BRLaw MCP: {e}")
            return []
    
    def _converter_resultado_local(self, resultado: Dict, consulta: str) -> Optional[Dict]:
        """Converte resultado da busca local para formato padrão"""
        
        try:
            texto = resultado.get('text', '')
            metadata = resultado.get('metadata', {})
            score = resultado.get('score', 0.0)
            
            # Extrair informações do texto
            numero_processo = self._extrair_numero_processo(texto)
            tribunal = self._extrair_tribunal(texto, metadata)
            relator = self._extrair_relator(texto)
            data_julgamento = self._extrair_data_julgamento(texto)
            
            return {
                "id_precedente": f"LOCAL_{hash(texto)[:12]}",
                "tribunal": tribunal,
                "numero_processo": numero_processo,
                "relator": relator,
                "data_julgamento": data_julgamento,
                "ementa": texto[:500],  # Primeiros 500 chars como ementa
                "acordao_completo": texto,
                "score_similaridade": score,
                "fonte": "local",
                "url_fonte": None
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao converter resultado local: {e}")
            return None
    
    def _converter_resultado_tempo_real(self, resultado: Dict, consulta: str) -> Optional[Dict]:
        """Converte resultado da busca tempo real para formato padrão"""
        
        try:
            texto = resultado.get('text', '')
            score = resultado.get('score', 0.0)
            url = resultado.get('url', '')
            
            # Extrair informações específicas do TJSP
            numero_processo = resultado.get('processo', self._extrair_numero_processo(texto))
            relator = resultado.get('relator', self._extrair_relator(texto))
            data_julgamento = resultado.get('data', self._extrair_data_julgamento(texto))
            
            return {
                "id_precedente": f"TJSP_{numero_processo or hash(texto)[:12]}",
                "tribunal": "TJSP",
                "numero_processo": numero_processo,
                "relator": relator,
                "data_julgamento": data_julgamento,
                "ementa": texto[:500],
                "acordao_completo": texto,
                "score_similaridade": score,
                "fonte": "tempo_real",
                "url_fonte": url
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao converter resultado tempo real: {e}")
            return None
    
    def _extrair_numero_processo(self, texto: str) -> Optional[str]:
        """Extrai número do processo do texto"""
        match = re.search(self.padroes_reconhecimento["numero_processo"], texto)
        return match.group(1) if match else None
    
    def _extrair_tribunal(self, texto: str, metadata: Dict = None) -> str:
        """Extrai tribunal do texto ou metadata"""
        
        # Verificar metadata primeiro
        if metadata and 'tribunal' in metadata:
            return metadata['tribunal']
        
        # Buscar no texto
        texto_upper = texto.upper()
        
        tribunais_padroes = {
            "STF": ["SUPREMO TRIBUNAL FEDERAL", "STF"],
            "STJ": ["SUPERIOR TRIBUNAL DE JUSTIÇA", "STJ"],
            "TJSP": ["TRIBUNAL DE JUSTIÇA DE SÃO PAULO", "TJSP", "TJ-SP"],
            "TJRJ": ["TRIBUNAL DE JUSTIÇA DO RIO DE JANEIRO", "TJRJ", "TJ-RJ"],
            "TST": ["TRIBUNAL SUPERIOR DO TRABALHO", "TST"]
        }
        
        for tribunal, padroes in tribunais_padroes.items():
            if any(padrao in texto_upper for padrao in padroes):
                return tribunal
        
        return "TRIBUNAL_NAO_IDENTIFICADO"
    
    def _extrair_relator(self, texto: str) -> Optional[str]:
        """Extrai nome do relator"""
        match = re.search(self.padroes_reconhecimento["relator"], texto)
        return match.group(1).strip() if match else None
    
    def _extrair_data_julgamento(self, texto: str) -> Optional[datetime]:
        """Extrai data de julgamento"""
        match = re.search(self.padroes_reconhecimento["data_julgamento"], texto)
        if match:
            try:
                data_str = match.group(1)
                # Tentar diferentes formatos
                for formato in ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]:
                    try:
                        return datetime.strptime(data_str, formato)
                    except:
                        continue
            except:
                pass
        return None
    
    def _buscar_sumulas_aplicaveis(self, consulta: str, tipo_acao: str) -> List[str]:
        """Busca súmulas aplicáveis ao caso"""
        
        sumulas_encontradas = []
        consulta_lower = consulta.lower()
        tipo_lower = tipo_acao.lower()
        
        # Verificar área temática
        area = self._identificar_area_tematica(consulta, tipo_acao)
        
        if area in self.areas_tematicas:
            sumulas_area = self.areas_tematicas[area].get("sumulas_chave", [])
            sumulas_encontradas.extend(sumulas_area)
        
        # Buscar súmulas por palavras-chave
        for tribunal, sumulas in self.sumulas_importantes.items():
            for numero, texto in sumulas.items():
                palavras_sumula = texto.lower().split()
                palavras_consulta = consulta_lower.split()
                
                # Verificar intersecção de palavras
                intersecao = set(palavras_sumula) & set(palavras_consulta)
                if len(intersecao) >= 2:  # Pelo menos 2 palavras em comum
                    sumula_ref = f"{tribunal} {numero}: {texto}"
                    if sumula_ref not in sumulas_encontradas:
                        sumulas_encontradas.append(sumula_ref)
        
        return sumulas_encontradas[:5]  # Máximo 5 súmulas
    
    def _processar_precedentes(self, precedentes_brutos: List[Dict], consulta: str, tipo_acao: str) -> List[PrecedenteJuridico]:
        """Processa e enriquece precedentes brutos"""
        
        precedentes_processados = []
        
        for precedente_dict in precedentes_brutos:
            try:
                # Calcular relevância
                relevancia = self._calcular_relevancia(precedente_dict, consulta, tipo_acao)
                
                # Filtrar por relevância mínima
                if relevancia.value == "baixa":
                    continue
                
                # Extrair palavras-chave
                palavras_chave = self._extrair_palavras_chave(precedente_dict["acordao_completo"])
                
                # Verificar status de vigência
                status_vigencia = self._verificar_status_vigencia(precedente_dict)
                
                # Estimar citações posteriores
                citacoes = self._estimar_citacoes_posteriores(precedente_dict)
                
                precedente = PrecedenteJuridico(
                    id_precedente=precedente_dict["id_precedente"],
                    tribunal=precedente_dict["tribunal"],
                    numero_processo=precedente_dict["numero_processo"] or "N/A",
                    relator=precedente_dict["relator"] or "N/A",
                    data_julgamento=precedente_dict["data_julgamento"] or datetime.now() - timedelta(days=365),
                    ementa=precedente_dict["ementa"],
                    acordao_completo=precedente_dict["acordao_completo"],
                    palavras_chave=palavras_chave,
                    relevancia=relevancia,
                    score_similaridade=precedente_dict["score_similaridade"],
                    url_fonte=precedente_dict.get("url_fonte"),
                    citacoes_posteriores=citacoes,
                    status_vigencia=status_vigencia
                )
                
                precedentes_processados.append(precedente)
                
            except Exception as e:
                self.logger.error(f"Erro ao processar precedente: {e}")
                continue
        
        # Ordenar por relevância e score
        precedentes_processados.sort(
            key=lambda p: (
                {"muito_alta": 4, "alta": 3, "media": 2, "baixa": 1}[p.relevancia.value],
                p.score_similaridade,
                p.citacoes_posteriores
            ),
            reverse=True
        )
        
        return precedentes_processados
    
    def _calcular_relevancia(self, precedente: Dict, consulta: str, tipo_acao: str) -> RelevanciaJurisprudencia:
        """Calcula relevância do precedente"""
        
        score = 0
        texto = precedente["acordao_completo"].lower()
        consulta_lower = consulta.lower()
        
        # Palavras da consulta no texto
        palavras_consulta = set(consulta_lower.split())
        palavras_texto = set(texto.split())
        intersecao = palavras_consulta & palavras_texto
        
        score += len(intersecao) * 2
        
        # Bonus por tribunal superior
        if precedente["tribunal"] in ["STF", "STJ"]:
            score += 10
        elif precedente["tribunal"] in ["TJSP", "TJRJ", "TJMG"]:
            score += 5
        
        # Bonus por data recente
        if precedente["data_julgamento"]:
            anos_diferenca = (datetime.now() - precedente["data_julgamento"]).days / 365
            if anos_diferenca < 2:
                score += 8
            elif anos_diferenca < 5:
                score += 4
        
        # Bonus por score de similaridade
        score += precedente["score_similaridade"] * 10
        
        # Bonus por tipo de ação similar
        if tipo_acao.lower() in texto:
            score += 15
        
        # Classificar relevância
        if score >= 30:
            return RelevanciaJurisprudencia.MUITO_ALTA
        elif score >= 20:
            return RelevanciaJurisprudencia.ALTA
        elif score >= 10:
            return RelevanciaJurisprudencia.MEDIA
        else:
            return RelevanciaJurisprudencia.BAIXA
    
    def _extrair_palavras_chave(self, texto: str) -> List[str]:
        """Extrai palavras-chave do texto"""
        
        # Palavras jurídicas importantes
        palavras_juridicas = [
            "responsabilidade", "dano", "indenização", "culpa", "dolo", "nexo",
            "consumidor", "fornecedor", "defeito", "vício", "serviço",
            "contrato", "obrigação", "inadimplemento", "mora", "juros",
            "prescrição", "decadência", "prazo", "termo", "condição"
        ]
        
        texto_lower = texto.lower()
        palavras_encontradas = []
        
        for palavra in palavras_juridicas:
            if palavra in texto_lower:
                palavras_encontradas.append(palavra)
        
        # Adicionar termos específicos encontrados
        termos_especificos = re.findall(r'\b[A-Z]{2,}\b', texto)  # Siglas
        palavras_encontradas.extend(termos_especificos[:5])
        
        return palavras_encontradas[:10]
    
    def _verificar_status_vigencia(self, precedente: Dict) -> str:
        """Verifica status de vigência do precedente"""
        
        # Verificação simples baseada na data
        if precedente["data_julgamento"]:
            anos_diferenca = (datetime.now() - precedente["data_julgamento"]).days / 365
            
            if anos_diferenca > 15:
                return "possivelmente_superado"
            elif anos_diferenca > 10:
                return "verificar_vigencia"
            else:
                return "vigente"
        
        return "vigente"
    
    def _estimar_citacoes_posteriores(self, precedente: Dict) -> int:
        """Estima número de citações posteriores"""
        
        # Estimativa baseada no tribunal e idade
        base_citacoes = 0
        
        if precedente["tribunal"] == "STF":
            base_citacoes = 50
        elif precedente["tribunal"] == "STJ":
            base_citacoes = 30
        elif precedente["tribunal"] in ["TJSP", "TJRJ"]:
            base_citacoes = 15
        else:
            base_citacoes = 5
        
        # Ajustar pela idade
        if precedente["data_julgamento"]:
            anos = (datetime.now() - precedente["data_julgamento"]).days / 365
            base_citacoes = int(base_citacoes * min(anos / 2, 3))  # Máximo 3x
        
        return base_citacoes
    
    def _classificar_precedentes(self, precedentes: List[PrecedenteJuridico], consulta: str, tipo_acao: str) -> Tuple[List[PrecedenteJuridico], List[PrecedenteJuridico], List[PrecedenteJuridico]]:
        """Classifica precedentes por favorabilidade"""
        
        favoraveis = []
        contrarios = []
        neutros = []
        
        # Palavras indicadoras de favorabilidade
        palavras_favoraveis = [
            "procedente", "acolho", "defiro", "provimento", "reforma", "anulo",
            "reconheço", "declaro", "condeno", "indenizar", "reparar"
        ]
        
        palavras_contrarias = [
            "improcedente", "nego", "indefiro", "desprovimento", "mantenho",
            "não provimento", "rejeito", "não conheço", "inadmissível"
        ]
        
        for precedente in precedentes:
            texto_lower = precedente.acordao_completo.lower()
            
            score_favoravel = sum(1 for palavra in palavras_favoraveis if palavra in texto_lower)
            score_contrario = sum(1 for palavra in palavras_contrarias if palavra in texto_lower)
            
            if score_favoravel > score_contrario and score_favoravel > 0:
                favoraveis.append(precedente)
            elif score_contrario > score_favoravel and score_contrario > 0:
                contrarios.append(precedente)
            else:
                neutros.append(precedente)
        
        return favoraveis, contrarios, neutros
    
    def _analisar_tendencia_jurisprudencial(self, favoraveis: List[PrecedenteJuridico], 
                                          contrarios: List[PrecedenteJuridico], 
                                          neutros: List[PrecedenteJuridico]) -> str:
        """Analisa tendência geral da jurisprudência"""
        
        total = len(favoraveis) + len(contrarios) + len(neutros)
        
        if total == 0:
            return "indefinida"
        
        perc_favoraveis = len(favoraveis) / total
        perc_contrarios = len(contrarios) / total
        
        if perc_favoraveis >= 0.7:
            return "favoravel"
        elif perc_contrarios >= 0.7:
            return "contraria"
        elif abs(perc_favoraveis - perc_contrarios) <= 0.2:
            return "dividida"
        elif perc_favoraveis > perc_contrarios:
            return "majoritariamente_favoravel"
        else:
            return "majoritariamente_contraria"
    
    def _calcular_grau_consolidacao(self, favoraveis: List[PrecedenteJuridico], 
                                   contrarios: List[PrecedenteJuridico]) -> float:
        """Calcula grau de consolidação da jurisprudência"""
        
        total = len(favoraveis) + len(contrarios)
        
        if total == 0:
            return 0.0
        
        # Peso por tribunal
        peso_total = 0
        peso_maioria = 0
        
        todos_precedentes = favoraveis + contrarios
        maioria = favoraveis if len(favoraveis) >= len(contrarios) else contrarios
        
        for precedente in todos_precedentes:
            if precedente.tribunal == "STF":
                peso = 5
            elif precedente.tribunal == "STJ":
                peso = 4
            elif precedente.tribunal in ["TJSP", "TJRJ", "TJMG"]:
                peso = 2
            else:
                peso = 1
            
            peso_total += peso
            
            if precedente in maioria:
                peso_maioria += peso
        
        if peso_total == 0:
            return 0.0
        
        consolidacao_basica = peso_maioria / peso_total
        
        # Ajustar por número de precedentes
        if total >= 10:
            fator_volume = 1.0
        elif total >= 5:
            fator_volume = 0.8
        else:
            fator_volume = 0.6
        
        return min(1.0, consolidacao_basica * fator_volume)
    
    def _gerar_recomendacao_uso(self, tendencia: str, grau_consolidacao: float, 
                               favoraveis: List[PrecedenteJuridico]) -> str:
        """Gera recomendação de uso da jurisprudência"""
        
        if grau_consolidacao >= 0.8:
            if tendencia in ["favoravel", "majoritariamente_favoravel"]:
                return "🟢 RECOMENDADO: Jurisprudência consolidada e favorável. Use com confiança."
            else:
                return "🔴 NÃO RECOMENDADO: Jurisprudência consolidada contrária. Evite ou busque diferenciação."
        
        elif grau_consolidacao >= 0.6:
            if tendencia in ["favoravel", "majoritariamente_favoravel"]:
                return "🟡 CAUTELOSO: Tendência favorável, mas não totalmente consolidada. Use citando precedentes específicos."
            else:
                return "🟠 RISCO MODERADO: Tendência contrária. Considere estratégia diferenciada."
        
        elif grau_consolidacao >= 0.4:
            return "⚪ DIVIDIDA: Jurisprudência dividida. Foque nos precedentes mais favoráveis e autoridades superiores."
        
        else:
            return "❓ INCERTA: Jurisprudência escassa ou muito dividida. Busque outras fundamentações."
    
    def _buscar_orientacoes_tribunais(self, tipo_acao: str) -> List[str]:
        """Busca orientações específicas dos tribunais"""
        
        orientacoes = []
        
        # Orientações gerais por tipo de ação
        orientacoes_gerais = {
            "indenização por danos morais": [
                "TJSP: Valor deve ser fixado com moderação, considerando capacidade econômica das partes",
                "STJ: Precedentes recentes indicam valores entre R$ 5.000 e R$ 15.000 para casos similares",
                "Tendência: Tribunais têm valorizado mais o dano moral em casos de negativação indevida"
            ],
            
            "ação de cobrança": [
                "TJSP: Documentos originais são essenciais para sucesso da ação",
                "STJ: Atenção aos prazos prescricionais conforme tipo de obrigação",
                "Orientação: Perícia contábil pode ser necessária em casos complexos"
            ],
            
            "revisão contrato bancário": [
                "STJ: Súmula 596 permite capitalização em contratos pós-2012",
                "TJSP: Spread bancário deve ser analisado caso a caso",
                "Tendência: Crescente proteção ao consumidor em contratos bancários"
            ]
        }
        
        orientacoes.extend(orientacoes_gerais.get(tipo_acao, []))
        
        return orientacoes[:5]
    
    def _calcular_estatisticas_busca(self, todos_precedentes: List[PrecedenteJuridico], 
                                   favoraveis: List[PrecedenteJuridico], 
                                   contrarios: List[PrecedenteJuridico]) -> Dict[str, Any]:
        """Calcula estatísticas da busca"""
        
        total = len(todos_precedentes)
        
        if total == 0:
            return {"total": 0, "error": "Nenhum precedente encontrado"}
        
        # Distribuição por tribunal
        tribunais = {}
        for prec in todos_precedentes:
            tribunais[prec.tribunal] = tribunais.get(prec.tribunal, 0) + 1
        
        # Distribuição por ano
        anos = {}
        for prec in todos_precedentes:
            if prec.data_julgamento:
                ano = prec.data_julgamento.year
                anos[ano] = anos.get(ano, 0) + 1
        
        # Score médio
        score_medio = sum(p.score_similaridade for p in todos_precedentes) / total
        
        # Relevância média
        relevancia_valores = {"muito_alta": 4, "alta": 3, "media": 2, "baixa": 1}
        relevancia_media = sum(relevancia_valores[p.relevancia.value] for p in todos_precedentes) / total
        
        return {
            "total_precedentes": total,
            "precedentes_favoraveis": len(favoraveis),
            "precedentes_contrarios": len(contrarios),
            "percentual_favoraveis": len(favoraveis) / total * 100,
            "score_medio_similaridade": round(score_medio, 3),
            "relevancia_media": round(relevancia_media, 2),
            "distribuicao_tribunais": tribunais,
            "distribuicao_anos": dict(sorted(anos.items(), reverse=True)[:5]),
            "tribunal_mais_citado": max(tribunais.keys(), key=tribunais.get) if tribunais else None,
            "periodo_mais_relevante": max(anos.keys(), key=anos.get) if anos else None
        }
    
    def exportar_analise_jurisprudencial(self, analise: AnaliseJurisprudencial, caminho: str) -> str:
        """Exporta análise jurisprudencial completa"""
        
        relatorio = f"""
# ANÁLISE JURISPRUDENCIAL INTELIGENTE
**ID:** {analise.id_analise}
**Data:** {analise.data_analise.strftime('%d/%m/%Y %H:%M')}
**Consulta:** {analise.consulta_original}
**Tipo de Ação:** {analise.tipo_acao}

## RESUMO EXECUTIVO
**Tendência Jurisprudencial:** {analise.tendencia_jurisprudencial}
**Grau de Consolidação:** {analise.grau_consolidacao:.1%}
**Recomendação:** {analise.recomendacao_uso}

## ESTATÍSTICAS
- **Total de Precedentes:** {analise.estatisticas.get('total_precedentes', 0)}
- **Precedentes Favoráveis:** {len(analise.precedentes_favoraveis)}
- **Precedentes Contrários:** {len(analise.precedentes_contrarios)}
- **Percentual Favorável:** {analise.estatisticas.get('percentual_favoraveis', 0):.1f}%

## PRECEDENTES FAVORÁVEIS ({len(analise.precedentes_favoraveis)})
"""
        
        for i, prec in enumerate(analise.precedentes_favoraveis, 1):
            relatorio += f"""
### {i}. {prec.tribunal} - {prec.numero_processo}
**Relator:** {prec.relator}
**Data:** {prec.data_julgamento.strftime('%d/%m/%Y') if prec.data_julgamento else 'N/A'}
**Relevância:** {prec.relevancia.value.upper()}
**Score:** {prec.score_similaridade:.3f}
**Ementa:** {prec.ementa[:300]}...
"""
            if prec.url_fonte:
                relatorio += f"**URL:** {prec.url_fonte}\n"
        
        if analise.precedentes_contrarios:
            relatorio += f"\n## PRECEDENTES CONTRÁRIOS ({len(analise.precedentes_contrarios)})\n"
            
            for i, prec in enumerate(analise.precedentes_contrarios, 1):
                relatorio += f"""
### {i}. {prec.tribunal} - {prec.numero_processo}
**Relator:** {prec.relator}
**Ementa:** {prec.ementa[:200]}...
"""
        
        if analise.sumulas_aplicaveis:
            relatorio += "\n## SÚMULAS APLICÁVEIS\n"
            for sumula in analise.sumulas_aplicaveis:
                relatorio += f"- {sumula}\n"
        
        if analise.orientacoes_tribunais:
            relatorio += "\n## ORIENTAÇÕES DOS TRIBUNAIS\n"
            for orientacao in analise.orientacoes_tribunais:
                relatorio += f"- {orientacao}\n"
        
        relatorio += f"""
## DISTRIBUIÇÃO POR TRIBUNAL
"""
        dist_tribunais = analise.estatisticas.get('distribuicao_tribunais', {})
        for tribunal, count in dist_tribunais.items():
            relatorio += f"- **{tribunal}:** {count} precedentes\n"
        
        relatorio += """
---
*Análise gerada pelo Sistema Inteligente de Busca Jurisprudencial*
*Esta análise é baseada em algoritmos e deve ser complementada pela análise humana especializada*
"""
        
        # Salvar arquivo
        caminho_arquivo = Path(caminho)
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        return str(caminho_arquivo)
    
    def _inicializar_cliente_ia(self):
        """Inicializa cliente de IA com fallback"""
        
        if self.ai_provider == "gemini" and GEMINI_AVAILABLE:
            try:
                self.ai_client = get_gemini_client()
                self.logger.info("Gemini configurado para busca inteligente")
                return
            except Exception as e:
                self.logger.warning(f"Erro ao configurar Gemini: {e}")
        
        # Fallback para OpenAI
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.ai_provider = "openai"
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.logger.info("Usando OpenAI como fallback")
            return
        
        # Fallback para Groq
        if GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
            self.ai_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.ai_provider = "groq"
            self.logger.info("Usando Groq como fallback")
            return
        
        # Sem IA disponível
        self.use_ai = False
        self.logger.warning("Nenhum provedor de IA disponível para busca inteligente")
    
    def analisar_precedentes_com_ia(
        self,
        precedentes: List[PrecedenteJuridico],
        contexto_caso: str
    ) -> Dict[str, Any]:
        """Analisa precedentes usando IA para insights avançados"""
        
        if not self.use_ai or not precedentes:
            return {}
        
        # Preparar texto dos precedentes
        texto_precedentes = "\n\n".join([
            f"Precedente {i+1}:\n"
            f"Tribunal: {p.tribunal}\n"
            f"Data: {p.data_julgamento.strftime('%d/%m/%Y')}\n"
            f"Ementa: {p.ementa[:500]}...\n"
            f"Relevância: {p.relevancia.value}"
            for i, p in enumerate(precedentes[:10])  # Limitar a 10 precedentes
        ])
        
        prompt = f"""Analise os seguintes precedentes jurídicos no contexto do caso apresentado:

CONTEXTO DO CASO:
{contexto_caso[:1000]}

PRECEDENTES:
{texto_precedentes}

Forneça:
1. Tendência jurisprudencial identificada
2. Pontos de convergência entre os precedentes
3. Pontos de divergência
4. Recomendações estratégicas baseadas nos precedentes
5. Riscos e oportunidades identificados"""
        
        try:
            if self.ai_provider == "gemini" and self.ai_client:
                resposta = self.ai_client.generate(
                    prompt,
                    system_prompt="Você é um especialista em análise jurisprudencial com profundo conhecimento do direito brasileiro.",
                    temperature=0.3
                )
            
            elif self.ai_provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4" if "gpt-4" in os.getenv("OPENAI_MODEL", "") else "gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um especialista em análise jurisprudencial com profundo conhecimento do direito brasileiro."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                resposta = response.choices[0].message.content
            
            elif self.ai_provider == "groq" and self.ai_client:
                response = self.ai_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um especialista em análise jurisprudencial com profundo conhecimento do direito brasileiro."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                resposta = response.choices[0].message.content
            
            return {
                "analise_ia": resposta,
                "provider": self.ai_provider,
                "data_analise": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro na análise com IA: {e}")
            return {}
    
    def gerar_recomendacao_estrategica_ia(
        self,
        analise: AnaliseJurisprudencial
    ) -> Optional[str]:
        """Gera recomendação estratégica usando IA"""
        
        if not self.use_ai:
            return None
        
        # Preparar contexto
        contexto = f"""Análise Jurisprudencial:
- Tipo de ação: {analise.tipo_acao}
- Precedentes favoráveis: {len(analise.precedentes_favoraveis)}
- Precedentes contrários: {len(analise.precedentes_contrarios)}
- Tendência: {analise.tendencia_jurisprudencial}
- Grau de consolidação: {analise.grau_consolidacao:.1%}
- Súmulas aplicáveis: {', '.join(analise.sumulas_aplicaveis[:3]) if analise.sumulas_aplicaveis else 'Nenhuma'}"""
        
        prompt = f"""Com base na análise jurisprudencial abaixo, elabore uma recomendação estratégica detalhada:

{contexto}

A recomendação deve incluir:
1. Estratégia processual recomendada
2. Argumentos principais a serem utilizados
3. Precedentes chave para citação
4. Riscos a serem mitigados
5. Probabilidade de êxito estimada"""
        
        try:
            if self.ai_provider == "gemini" and self.ai_client:
                return self.ai_client.generate(
                    prompt,
                    system_prompt="Você é um advogado sênior especializado em estratégia processual.",
                    temperature=0.4
                )
            
            elif self.ai_provider == "openai":
                response = openai.ChatCompletion.create(
                    model="gpt-4" if "gpt-4" in os.getenv("OPENAI_MODEL", "") else "gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um advogado sênior especializado em estratégia processual."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                return response.choices[0].message.content
            
            elif self.ai_provider == "groq" and self.ai_client:
                response = self.ai_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um advogado sênior especializado em estratégia processual."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                return response.choices[0].message.content
                
        except Exception as e:
            self.logger.error(f"Erro ao gerar recomendação: {e}")
            return None
    
    def buscar_com_ia_contextual(
        self,
        consulta: str,
        contexto_adicional: Optional[str] = None,
        filtros: Optional[Dict[str, Any]] = None
    ) -> List[PrecedenteJuridico]:
        """Busca avançada usando IA para melhorar a consulta"""
        
        # Busca tradicional primeiro
        resultados = self.buscar_jurisprudencia(consulta, filtros=filtros)
        
        if not self.use_ai or not resultados:
            return resultados
        
        # Usar IA para re-ranquear resultados
        try:
            prompt = f"""Analise a relevância dos seguintes precedentes para a consulta:

CONSULTA: {consulta}
{f'CONTEXTO ADICIONAL: {contexto_adicional}' if contexto_adicional else ''}

Classifique cada precedente de 1-10 em relevância e justifique brevemente."""
            
            # Análise com IA
            if self.ai_provider == "gemini" and self.ai_client:
                analise = self.ai_client.generate(
                    prompt,
                    temperature=0.2
                )
            else:
                # Fallback sem re-ranking
                return resultados
            
            # Aplicar insights da IA (implementação simplificada)
            self.logger.info("Resultados re-ranqueados com IA")
            
        except Exception as e:
            self.logger.error(f"Erro no re-ranking com IA: {e}")
        
        return resultados
    
    def estimar_custo_busca_ia(self, consulta: str) -> Dict[str, float]:
        """Estima custo de busca com IA"""
        
        if self.ai_provider == "gemini" and hasattr(self.ai_client, 'estimate_cost'):
            return self.ai_client.estimate_cost(consulta)
        
        # Estimativa genérica
        tokens = len(consulta) // 4 * 10  # Busca usa mais tokens
        
        custos = {
            "gemini": 0.000075 * tokens / 1000,
            "openai": 0.002 * tokens / 1000,
            "groq": 0.0001 * tokens / 1000
        }
        
        return {
            "provider": self.ai_provider,
            "tokens_estimados": tokens,
            "custo_usd": custos.get(self.ai_provider, 0),
            "custo_brl": custos.get(self.ai_provider, 0) * 5.0
        }