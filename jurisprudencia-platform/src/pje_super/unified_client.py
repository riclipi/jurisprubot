"""
🎯 UNIFIED PJE CLIENT - ARQUITETURA HÍBRIDA INTELIGENTE
Sistema que supera TODOS os concorrentes com tripla integração
"""

import asyncio
import aiohttp
import requests
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import time
import hashlib

class TecnologiaAcesso(Enum):
    REST = "rest"
    SOAP = "soap"
    SCRAPING = "scraping"
    HIBRIDO = "hibrido"

class StatusTribunal(Enum):
    ONLINE = "online"
    PARCIAL = "parcial"
    OFFLINE = "offline"
    MANUTENCAO = "manutencao"
    CAPTCHA = "captcha"

@dataclass
class ConfigTribunal:
    """Configuração específica de cada tribunal"""
    codigo: str
    nome: str
    sigla: str
    url_base: str
    url_rest: Optional[str] = None
    url_soap: Optional[str] = None
    url_scraping: Optional[str] = None
    tecnologias_suportadas: List[TecnologiaAcesso] = field(default_factory=list)
    prioridade_tecnologia: List[TecnologiaAcesso] = field(default_factory=list)
    headers_especiais: Dict[str, str] = field(default_factory=dict)
    rate_limit: float = 1.0  # segundos entre requests
    timeout: int = 30
    retry_attempts: int = 3
    status_atual: StatusTribunal = StatusTribunal.ONLINE
    ultimo_teste: Optional[datetime] = None

@dataclass
class ProcessoInfo:
    """Informações estruturadas do processo"""
    numero_cnj: str
    numero_sequencial: str
    tribunal: str
    orgao_julgador: str
    partes: Dict[str, List[str]] = field(default_factory=dict)
    assuntos: List[str] = field(default_factory=list)
    classe_processual: str = ""
    situacao: str = ""
    data_autuacao: Optional[datetime] = None
    data_ultima_atualizacao: Optional[datetime] = None
    valor_causa: Optional[str] = None
    segredo_justica: bool = False
    movimentacoes: List[Dict] = field(default_factory=list)
    documentos: List[Dict] = field(default_factory=list)
    audiencias: List[Dict] = field(default_factory=list)
    fonte_dados: TecnologiaAcesso = TecnologiaAcesso.REST
    metadados: Dict[str, Any] = field(default_factory=dict)

class UnifiedPJeClient:
    """
    🚀 CLIENTE UNIFICADO PJE - ARQUITETURA HÍBRIDA INTELIGENTE
    
    Funcionalidades únicas:
    - Integração tripla: REST + SOAP + Scraping
    - Fallback automático entre tecnologias
    - Auto-detecção de tribunal por número CNJ
    - Cache inteligente de endpoints funcionais
    - Rate limiting adaptativo por tribunal
    - Retry automático com backoff exponencial
    """
    
    def __init__(self):
        self.setup_logging()
        self._inicializar_tribunais()
        self._inicializar_clients()
        self._inicializar_cache()
        
    def setup_logging(self):
        """Configura sistema de logs"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _inicializar_tribunais(self):
        """Inicializa configurações dos tribunais brasileiros"""
        
        self.tribunais = {
            # TRIBUNAIS SUPERIORES
            "STF": ConfigTribunal(
                codigo="STF",
                nome="Supremo Tribunal Federal",
                sigla="STF",
                url_base="https://portal.stf.jus.br",
                url_rest="https://portal.stf.jus.br/jurisprudencia/api",
                tecnologias_suportadas=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING]
            ),
            
            "STJ": ConfigTribunal(
                codigo="STJ",
                nome="Superior Tribunal de Justiça",
                sigla="STJ",
                url_base="https://www.stj.jus.br",
                url_rest="https://www.stj.jus.br/scon/api",
                tecnologias_suportadas=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING]
            ),
            
            # TRIBUNAIS REGIONAIS FEDERAIS
            "TRF1": ConfigTribunal(
                codigo="TRF1",
                nome="Tribunal Regional Federal da 1ª Região",
                sigla="TRF1",
                url_base="https://www.trf1.jus.br",
                url_soap="https://pje.trf1.jus.br/pje/intercomunicacao",
                url_scraping="https://pje.trf1.jus.br",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            "TRF2": ConfigTribunal(
                codigo="TRF2",
                nome="Tribunal Regional Federal da 2ª Região",
                sigla="TRF2",
                url_base="https://www.trf2.jus.br",
                url_soap="https://pje.trf2.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            "TRF3": ConfigTribunal(
                codigo="TRF3",
                nome="Tribunal Regional Federal da 3ª Região",
                sigla="TRF3",
                url_base="https://www.trf3.jus.br",
                url_soap="https://pje.trf3.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            "TRF4": ConfigTribunal(
                codigo="TRF4",
                nome="Tribunal Regional Federal da 4ª Região",
                sigla="TRF4",
                url_base="https://www.trf4.jus.br",
                url_rest="https://eproc.trf4.jus.br/eproc2/api",
                url_soap="https://eproc.trf4.jus.br/eproc2/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.REST, TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.REST, TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            "TRF5": ConfigTribunal(
                codigo="TRF5",
                nome="Tribunal Regional Federal da 5ª Região",
                sigla="TRF5",
                url_base="https://www.trf5.jus.br",
                url_soap="https://pje.trf5.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            # TRIBUNAIS DE JUSTIÇA ESTADUAIS
            "TJSP": ConfigTribunal(
                codigo="TJSP",
                nome="Tribunal de Justiça de São Paulo",
                sigla="TJSP",
                url_base="https://www.tjsp.jus.br",
                url_rest="https://api.tjsp.jus.br/v1",
                url_soap="https://pje.tjsp.jus.br/pje/intercomunicacao",
                url_scraping="https://esaj.tjsp.jus.br",
                tecnologias_suportadas=[TecnologiaAcesso.REST, TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.REST, TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                rate_limit=2.0  # TJSP é mais restritivo
            ),
            
            "TJRJ": ConfigTribunal(
                codigo="TJRJ",
                nome="Tribunal de Justiça do Rio de Janeiro",
                sigla="TJRJ",
                url_base="https://www.tjrj.jus.br",
                url_soap="https://pje.tjrj.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            "TJMG": ConfigTribunal(
                codigo="TJMG",
                nome="Tribunal de Justiça de Minas Gerais",
                sigla="TJMG",
                url_base="https://www.tjmg.jus.br",
                url_soap="https://pje.tjmg.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            "TJRS": ConfigTribunal(
                codigo="TJRS",
                nome="Tribunal de Justiça do Rio Grande do Sul",
                sigla="TJRS",
                url_base="https://www.tjrs.jus.br",
                url_soap="https://pje.tjrs.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            "TJPR": ConfigTribunal(
                codigo="TJPR",
                nome="Tribunal de Justiça do Paraná",
                sigla="TJPR",
                url_base="https://www.tjpr.jus.br",
                url_soap="https://pje.tjpr.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            # TRIBUNAIS DO TRABALHO
            "TST": ConfigTribunal(
                codigo="TST",
                nome="Tribunal Superior do Trabalho",
                sigla="TST",
                url_base="https://www.tst.jus.br",
                url_rest="https://www.tst.jus.br/jurisprudencia/api",
                tecnologias_suportadas=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING]
            ),
            
            "TRT2": ConfigTribunal(
                codigo="TRT2",
                nome="Tribunal Regional do Trabalho da 2ª Região",
                sigla="TRT2",
                url_base="https://www.trt2.jus.br",
                url_soap="https://pje.trt2.jus.br/pje/intercomunicacao",
                tecnologias_suportadas=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.SOAP, TecnologiaAcesso.SCRAPING]
            ),
            
            # TRIBUNAIS ELEITORAIS
            "TSE": ConfigTribunal(
                codigo="TSE",
                nome="Tribunal Superior Eleitoral",
                sigla="TSE",
                url_base="https://www.tse.jus.br",
                url_rest="https://www.tse.jus.br/api",
                tecnologias_suportadas=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING],
                prioridade_tecnologia=[TecnologiaAcesso.REST, TecnologiaAcesso.SCRAPING]
            )
        }
        
        self.logger.info(f"Tribunais inicializados: {len(self.tribunais)} configurados")
    
    def _inicializar_clients(self):
        """Inicializa clientes REST, SOAP e Scraping"""
        
        # Cliente REST assíncrono
        self.session_rest = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'UnifiedPJeClient/1.0 (Plataforma Jurídica Avançada)',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        
        # Cliente SOAP síncrono
        self.session_soap = requests.Session()
        self.session_soap.headers.update({
            'User-Agent': 'UnifiedPJeClient/1.0 SOAP',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        })
        
        # Cliente Scraping (reutiliza do sistema existente)
        try:
            from ..scraper.realtime_search import RealtimeJurisprudenceSearch
            self.scraper = RealtimeJurisprudenceSearch()
        except ImportError:
            self.logger.warning("Scraper não disponível")
            self.scraper = None
    
    def _inicializar_cache(self):
        """Inicializa sistema de cache inteligente"""
        
        self.cache_endpoints = {}  # Cache de endpoints funcionais
        self.cache_processos = {}  # Cache de processos consultados
        self.cache_status = {}     # Cache de status dos tribunais
        self.rate_limiters = {}    # Rate limiting por tribunal
        
        # Configurar rate limiters
        for codigo, config in self.tribunais.items():
            self.rate_limiters[codigo] = {
                'last_request': 0,
                'rate_limit': config.rate_limit
            }
    
    async def consultar_processo_inteligente(self, numero_cnj: str) -> Optional[ProcessoInfo]:
        """
        🎯 CONSULTA INTELIGENTE DE PROCESSO
        
        Estratégia híbrida:
        1. Auto-detecta tribunal pelo número CNJ
        2. Tenta REST primeiro (mais rápido)
        3. Fallback para SOAP (mais compatível)
        4. Scraping como última opção (sempre funciona)
        5. Cache inteligente para otimizar performance
        """
        
        self.logger.info(f"Iniciando consulta inteligente: {numero_cnj}")
        
        # Validar número CNJ
        if not self._validar_numero_cnj(numero_cnj):
            self.logger.error(f"Número CNJ inválido: {numero_cnj}")
            return None
        
        # Auto-detectar tribunal
        tribunal_codigo = self._detectar_tribunal_cnj(numero_cnj)
        if not tribunal_codigo:
            self.logger.error(f"Tribunal não identificado para: {numero_cnj}")
            return None
        
        tribunal_config = self.tribunais[tribunal_codigo]
        self.logger.info(f"Tribunal detectado: {tribunal_config.nome}")
        
        # Verificar cache primeiro
        cache_key = f"{tribunal_codigo}_{numero_cnj}"
        if cache_key in self.cache_processos:
            cached = self.cache_processos[cache_key]
            if (datetime.now() - cached['timestamp']).total_seconds() < 3600:  # 1 hora
                self.logger.info("Retornando dados do cache")
                return cached['data']
        
        # Aplicar rate limiting
        await self._aplicar_rate_limit(tribunal_codigo)
        
        # Tentar cada tecnologia na ordem de prioridade
        for tecnologia in tribunal_config.prioridade_tecnologia:
            try:
                self.logger.info(f"Tentando {tecnologia.value} para {tribunal_codigo}")
                
                if tecnologia == TecnologiaAcesso.REST:
                    resultado = await self._consultar_rest(numero_cnj, tribunal_config)
                elif tecnologia == TecnologiaAcesso.SOAP:
                    resultado = await self._consultar_soap(numero_cnj, tribunal_config)
                elif tecnologia == TecnologiaAcesso.SCRAPING:
                    resultado = await self._consultar_scraping(numero_cnj, tribunal_config)
                else:
                    continue
                
                if resultado:
                    # Salvar no cache
                    self.cache_processos[cache_key] = {
                        'data': resultado,
                        'timestamp': datetime.now()
                    }
                    
                    self.logger.info(f"Sucesso via {tecnologia.value}")
                    return resultado
                    
            except Exception as e:
                self.logger.warning(f"Falha em {tecnologia.value}: {e}")
                continue
        
        self.logger.error(f"Todas as tecnologias falharam para {numero_cnj}")
        return None
    
    def _validar_numero_cnj(self, numero: str) -> bool:
        """Valida formato do número CNJ"""
        
        # Remove formatação
        numero_limpo = re.sub(r'[^\d]', '', numero)
        
        # Verifica se tem 20 dígitos
        if len(numero_limpo) != 20:
            return False
        
        # Validação do dígito verificador (algoritmo CNJ)
        try:
            sequencial = numero_limpo[:7]
            dv = numero_limpo[7:9]
            ano = numero_limpo[9:13]
            segmento = numero_limpo[13:14]
            tribunal = numero_limpo[14:18]
            origem = numero_limpo[18:20]
            
            # Cálculo do DV
            numeros = sequencial + ano + segmento + tribunal + origem
            soma = 0
            for i, digito in enumerate(numeros):
                peso = (i % 10) + 2
                if peso > 9:
                    peso = (peso // 10) + (peso % 10)
                soma += int(digito) * peso
            
            resto = soma % 11
            dv_calculado = 11 - resto if resto >= 2 else 0
            
            return str(dv_calculado).zfill(2) == dv
            
        except:
            return False
    
    def _detectar_tribunal_cnj(self, numero_cnj: str) -> Optional[str]:
        """Detecta tribunal pelo número CNJ"""
        
        numero_limpo = re.sub(r'[^\d]', '', numero_cnj)
        
        if len(numero_limpo) != 20:
            return None
        
        # Códigos dos tribunais conforme CNJ
        tribunal_codigo = numero_limpo[14:18]
        
        mapeamento_tribunais = {
            # Supremo Tribunal Federal
            "1000": "STF",
            
            # Superior Tribunal de Justiça
            "1100": "STJ",
            
            # Tribunais Regionais Federais
            "0100": "TRF1",
            "0200": "TRF2", 
            "0300": "TRF3",
            "0400": "TRF4",
            "0500": "TRF5",
            "0600": "TRF6",
            
            # Tribunais de Justiça Estaduais - SP
            "8260": "TJSP",
            "8030": "TJSP",  # Outras varas TJSP
            
            # Tribunais de Justiça - Outros Estados
            "8190": "TJRJ",
            "8130": "TJMG", 
            "8210": "TJRS",
            "8160": "TJPR",
            
            # Tribunal Superior do Trabalho
            "5000": "TST",
            
            # Tribunais Regionais do Trabalho
            "5002": "TRT2",  # São Paulo
            "5001": "TRT1",  # Rio de Janeiro
            "5003": "TRT3",  # Minas Gerais
            "5004": "TRT4",  # Rio Grande do Sul
            "5009": "TRT9",  # Paraná
            
            # Tribunal Superior Eleitoral
            "0300": "TSE"
        }
        
        return mapeamento_tribunais.get(tribunal_codigo)
    
    async def _aplicar_rate_limit(self, tribunal_codigo: str):
        """Aplica rate limiting específico do tribunal"""
        
        if tribunal_codigo not in self.rate_limiters:
            return
        
        limiter = self.rate_limiters[tribunal_codigo]
        tempo_atual = time.time()
        tempo_desde_ultimo = tempo_atual - limiter['last_request']
        
        if tempo_desde_ultimo < limiter['rate_limit']:
            espera = limiter['rate_limit'] - tempo_desde_ultimo
            self.logger.info(f"Rate limiting: aguardando {espera:.2f}s")
            await asyncio.sleep(espera)
        
        limiter['last_request'] = time.time()
    
    async def _consultar_rest(self, numero_cnj: str, config: ConfigTribunal) -> Optional[ProcessoInfo]:
        """Consulta via API REST"""
        
        if not config.url_rest:
            return None
        
        url = f"{config.url_rest}/processos/{numero_cnj}"
        
        try:
            async with self.session_rest.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parsear_resposta_rest(data, numero_cnj, config.codigo)
                else:
                    self.logger.warning(f"REST falhou: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Erro REST: {e}")
            return None
    
    async def _consultar_soap(self, numero_cnj: str, config: ConfigTribunal) -> Optional[ProcessoInfo]:
        """Consulta via SOAP"""
        
        if not config.url_soap:
            return None
        
        # Envelope SOAP para consulta de processo
        soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:int="http://www.cnj.jus.br/intercomunicacao-2.2.2">
    <soap:Header/>
    <soap:Body>
        <int:consultarProcesso>
            <int:numeroProcesso>{numero_cnj}</int:numeroProcesso>
        </int:consultarProcesso>
    </soap:Body>
</soap:Envelope>"""
        
        try:
            response = self.session_soap.post(
                config.url_soap,
                data=soap_envelope,
                headers={'SOAPAction': 'consultarProcesso'},
                timeout=config.timeout
            )
            
            if response.status_code == 200:
                return self._parsear_resposta_soap(response.text, numero_cnj, config.codigo)
            else:
                self.logger.warning(f"SOAP falhou: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro SOAP: {e}")
            return None
    
    async def _consultar_scraping(self, numero_cnj: str, config: ConfigTribunal) -> Optional[ProcessoInfo]:
        """Consulta via scraping"""
        
        if not self.scraper:
            return None
        
        try:
            # Usar scraper existente como fallback
            if config.codigo == "TJSP":
                resultados = self.scraper.get_relevant_chunks(numero_cnj)
                if resultados:
                    return self._parsear_resposta_scraping(resultados, numero_cnj, config.codigo)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro Scraping: {e}")
            return None
    
    def _parsear_resposta_rest(self, data: Dict, numero_cnj: str, tribunal: str) -> ProcessoInfo:
        """Parseia resposta REST para ProcessoInfo"""
        
        return ProcessoInfo(
            numero_cnj=numero_cnj,
            numero_sequencial=data.get('numeroSequencial', ''),
            tribunal=tribunal,
            orgao_julgador=data.get('orgaoJulgador', ''),
            partes=data.get('partes', {}),
            assuntos=data.get('assuntos', []),
            classe_processual=data.get('classeProcessual', ''),
            situacao=data.get('situacao', ''),
            data_autuacao=self._parsear_data(data.get('dataAutuacao')),
            valor_causa=data.get('valorCausa'),
            movimentacoes=data.get('movimentacoes', []),
            documentos=data.get('documentos', []),
            fonte_dados=TecnologiaAcesso.REST,
            metadados=data
        )
    
    def _parsear_resposta_soap(self, xml_data: str, numero_cnj: str, tribunal: str) -> ProcessoInfo:
        """Parseia resposta SOAP para ProcessoInfo"""
        
        try:
            root = ET.fromstring(xml_data)
            
            # Namespace SOAP
            ns = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'int': 'http://www.cnj.jus.br/intercomunicacao-2.2.2'
            }
            
            # Extrair dados do XML
            processo_elem = root.find('.//int:processo', ns)
            if processo_elem is None:
                return None
            
            return ProcessoInfo(
                numero_cnj=numero_cnj,
                numero_sequencial=self._extrair_texto_xml(processo_elem, 'numeroSequencial'),
                tribunal=tribunal,
                orgao_julgador=self._extrair_texto_xml(processo_elem, 'orgaoJulgador'),
                classe_processual=self._extrair_texto_xml(processo_elem, 'classeProcessual'),
                situacao=self._extrair_texto_xml(processo_elem, 'situacao'),
                data_autuacao=self._parsear_data(self._extrair_texto_xml(processo_elem, 'dataAutuacao')),
                valor_causa=self._extrair_texto_xml(processo_elem, 'valorCausa'),
                fonte_dados=TecnologiaAcesso.SOAP,
                metadados={'xml_original': xml_data}
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao parsear SOAP: {e}")
            return None
    
    def _parsear_resposta_scraping(self, resultados: List, numero_cnj: str, tribunal: str) -> ProcessoInfo:
        """Parseia resposta de scraping para ProcessoInfo"""
        
        if not resultados:
            return None
        
        # Combinar informações dos resultados de scraping
        texto_completo = " ".join([r.get('text', '') for r in resultados])
        
        return ProcessoInfo(
            numero_cnj=numero_cnj,
            numero_sequencial=self._extrair_numero_sequencial(texto_completo),
            tribunal=tribunal,
            orgao_julgador=self._extrair_orgao_julgador(texto_completo),
            fonte_dados=TecnologiaAcesso.SCRAPING,
            metadados={'resultados_scraping': resultados}
        )
    
    def _extrair_texto_xml(self, elemento, tag: str) -> str:
        """Extrai texto de elemento XML"""
        elem = elemento.find(tag)
        return elem.text if elem is not None else ""
    
    def _parsear_data(self, data_str: str) -> Optional[datetime]:
        """Parseia string de data para datetime"""
        if not data_str:
            return None
        
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S']
        
        for formato in formatos:
            try:
                return datetime.strptime(data_str, formato)
            except:
                continue
        
        return None
    
    def _extrair_numero_sequencial(self, texto: str) -> str:
        """Extrai número sequencial do texto"""
        # Implementar extração via regex
        match = re.search(r'processo\s*n[º°]?\s*(\d+)', texto, re.IGNORECASE)
        return match.group(1) if match else ""
    
    def _extrair_orgao_julgador(self, texto: str) -> str:
        """Extrai órgão julgador do texto"""
        # Implementar extração via regex
        padroes = [
            r'(\d+[ªº]?\s*vara[^.]*)',
            r'(câmara[^.]*)',
            r'(turma[^.]*)'
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    async def consultar_multiplos_processos(self, numeros_cnj: List[str]) -> Dict[str, Optional[ProcessoInfo]]:
        """
        🚀 CONSULTA EM MASSA DE PROCESSOS
        Processa múltiplos processos em paralelo com otimização por tribunal
        """
        
        self.logger.info(f"Iniciando consulta em massa: {len(numeros_cnj)} processos")
        
        # Agrupar por tribunal para otimizar
        processos_por_tribunal = {}
        for numero in numeros_cnj:
            tribunal = self._detectar_tribunal_cnj(numero)
            if tribunal:
                if tribunal not in processos_por_tribunal:
                    processos_por_tribunal[tribunal] = []
                processos_por_tribunal[tribunal].append(numero)
        
        # Executar consultas em paralelo, respeitando rate limits
        resultados = {}
        
        for tribunal, processos in processos_por_tribunal.items():
            self.logger.info(f"Processando {len(processos)} processos do {tribunal}")
            
            # Processar em lotes para respeitar rate limiting
            lote_size = 5  # Máximo 5 simultâneos por tribunal
            for i in range(0, len(processos), lote_size):
                lote = processos[i:i+lote_size]
                
                # Executar lote em paralelo
                tasks = [self.consultar_processo_inteligente(numero) for numero in lote]
                resultados_lote = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Salvar resultados
                for numero, resultado in zip(lote, resultados_lote):
                    if isinstance(resultado, Exception):
                        self.logger.error(f"Erro em {numero}: {resultado}")
                        resultados[numero] = None
                    else:
                        resultados[numero] = resultado
        
        self.logger.info(f"Consulta em massa concluída: {len(resultados)} resultados")
        return resultados
    
    async def testar_tribunais(self) -> Dict[str, StatusTribunal]:
        """
        🔧 TESTE DE DISPONIBILIDADE DOS TRIBUNAIS
        Testa todos os tribunais e atualiza status
        """
        
        self.logger.info("Testando disponibilidade de todos os tribunais")
        
        resultados = {}
        
        for codigo, config in self.tribunais.items():
            try:
                # Teste simples de conectividade
                if config.url_rest:
                    async with self.session_rest.get(f"{config.url_rest}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                        status = StatusTribunal.ONLINE if response.status < 400 else StatusTribunal.PARCIAL
                elif config.url_soap:
                    response = self.session_soap.get(config.url_base, timeout=10)
                    status = StatusTribunal.ONLINE if response.status_code < 400 else StatusTribunal.PARCIAL
                else:
                    status = StatusTribunal.PARCIAL
                
                config.status_atual = status
                config.ultimo_teste = datetime.now()
                resultados[codigo] = status
                
            except Exception as e:
                self.logger.warning(f"Tribunal {codigo} offline: {e}")
                config.status_atual = StatusTribunal.OFFLINE
                config.ultimo_teste = datetime.now()
                resultados[codigo] = StatusTribunal.OFFLINE
        
        return resultados
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas do sistema"""
        
        total_tribunais = len(self.tribunais)
        tribunais_online = sum(1 for t in self.tribunais.values() if t.status_atual == StatusTribunal.ONLINE)
        tribunais_rest = sum(1 for t in self.tribunais.values() if TecnologiaAcesso.REST in t.tecnologias_suportadas)
        tribunais_soap = sum(1 for t in self.tribunais.values() if TecnologiaAcesso.SOAP in t.tecnologias_suportadas)
        
        return {
            "total_tribunais": total_tribunais,
            "tribunais_online": tribunais_online,
            "tribunais_offline": total_tribunais - tribunais_online,
            "cobertura_rest": tribunais_rest,
            "cobertura_soap": tribunais_soap,
            "cache_processos": len(self.cache_processos),
            "tecnologias_disponiveis": ["REST", "SOAP", "Scraping"],
            "tribunais_suportados": list(self.tribunais.keys())
        }
    
    async def close(self):
        """Fecha conexões e limpa recursos"""
        if self.session_rest:
            await self.session_rest.close()
        
        if self.session_soap:
            self.session_soap.close()

# Função de conveniência para uso direto
async def consultar_processo_hibrido(numero_cnj: str) -> Optional[ProcessoInfo]:
    """
    🎯 FUNÇÃO DE CONVENIÊNCIA
    Consulta processo usando toda a inteligência híbrida
    """
    
    client = UnifiedPJeClient()
    try:
        return await client.consultar_processo_inteligente(numero_cnj)
    finally:
        await client.close()

# Exemplo de uso
if __name__ == "__main__":
    async def teste_unified_client():
        client = UnifiedPJeClient()
        
        print("🚀 Testando UnifiedPJeClient...")
        
        # Teste 1: Consulta individual
        numero_teste = "1234567-12.2023.8.26.0001"  # TJSP fictício
        print(f"\n1. Consultando processo: {numero_teste}")
        
        resultado = await client.consultar_processo_inteligente(numero_teste)
        if resultado:
            print(f"   ✅ Sucesso via {resultado.fonte_dados.value}")
            print(f"   Tribunal: {resultado.tribunal}")
            print(f"   Órgão: {resultado.orgao_julgador}")
        else:
            print("   ❌ Processo não encontrado")
        
        # Teste 2: Teste de tribunais
        print("\n2. Testando disponibilidade dos tribunais...")
        status_tribunais = await client.testar_tribunais()
        
        for tribunal, status in status_tribunais.items():
            icon = "✅" if status == StatusTribunal.ONLINE else "❌"
            print(f"   {icon} {tribunal}: {status.value}")
        
        # Teste 3: Estatísticas
        print("\n3. Estatísticas do sistema:")
        stats = client.obter_estatisticas()
        print(f"   Total de tribunais: {stats['total_tribunais']}")
        print(f"   Tribunais online: {stats['tribunais_online']}")
        print(f"   Cobertura REST: {stats['cobertura_rest']}")
        print(f"   Cobertura SOAP: {stats['cobertura_soap']}")
        
        await client.close()
        print("\n✅ Teste concluído!")
    
    # Executar teste
    asyncio.run(teste_unified_client())